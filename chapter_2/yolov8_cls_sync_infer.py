import cv2, onnx, time
import numpy as np  
import openvino as ov 
import torch
import torchvision.transforms as T

# 获取标签信息names
onnx_model_path = "./yolov8n-cls.onnx"
onnx_model = onnx.load(onnx_model_path)
class_names = eval(onnx_model.metadata_props[9].value)

# 预处理函数，参考yolov8-cls的classify_transforms
# https://github.com/ultralytics/ultralytics/blob/main/ultralytics/data/augment.py#L1007
def preprocess_image(image: np.ndarray, target_size=(224, 224))->np.ndarray:
    classify_transforms = T.Compose([
        T.ToPILImage(),               # 调整数据格式: HWC -> CHW
        T.Resize(target_size[0]),     # 保持宽高比放缩
        T.CenterCrop(target_size[0]), # 裁剪图像中心，不添加边框，图像部分丢失: 
        T.ToTensor(),
        T.Normalize(                  # 将像素值归一化到[0,1]
            mean=torch.tensor((0.0, 0.0, 0.0)),
            std=torch.tensor((1.0, 1.0, 1.0)),
        ),
    ])
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # 调整数据格式：BGR to RGB
    img = classify_transforms(image)
    img = torch.stack([img], dim=0)    #调整数据格式: CHW -> NCHW
    return img.numpy()


# 后处理函数：返回Top-5类别概率值的索引
def postprocess_output(result):  
    top5_index = (-result).argsort(0)[:5].tolist()

    return top5_index


# 第一步：初始化工作
# 创建Core对象
core = ov.Core()
# 输出OpenVINO版本信息
from openvino import __version__
print("OpenVINO version:", __version__)
# 输出系统计算设备信息
devices = core.available_devices
for device in devices:
    device_name = core.get_property(device, 'FULL_DEVICE_NAME')
    print(f"{device}: {device_name}")

# 指定模型路径
ov_model_path   = "./yolov8x-cls.xml"
# 指定计算设备
device = "GPU.1"                          #指定英特尔独立显卡GPU.1
# 设置OpenVINO运行时属性：同步推理，延迟优先
config = {"PERFORMANCE_HINT": "LATENCY"}  #同步推理，一般配置为延迟优先
config["CACHE_DIR"] = "./cache"           #启动模型缓存，并指定模型缓存路径
# 从指定路径读取并编译模型  
compiled_model = core.compile_model(model=ov_model_path, 
                                    device_name=device, 
                                    config=config)

# 创建推理请求infer request对象
ir = compiled_model.create_infer_request()
# 获取输入输出节点
input_node = compiled_model.inputs[0]
output_node = compiled_model.outputs[0]

# 初始化USB摄像头或IP摄像头
# IP摄像头URL，请根据实际情况修改
# ip_camera_url = 'rtsp://username:password@ip_address:port/path'
usb_camera = 0
# 创建视频捕获对象
cap = cv2.VideoCapture(usb_camera)
# 检查摄像头是否成功打开
if not cap.isOpened():
    print("Error: can not open camera!")
    exit()
print("Open camera successfully!")
# -- 初始化工作放上面 --------------------

# OpenVINO同步推理计算循环并统计性能
# 设置执行次数
num_iterations = 300
latency = []
total_time = 0.0
for _ in range(num_iterations):
    # 1. 读取一帧图像
    ret, frame = cap.read()
    # 如果读取不成功，则退出
    if not ret:
        print("Error: fail to read an image!")
        break

    # 2. 数据预处理
    blob = preprocess_image(frame)

    # 3. 执行推理计算并获得结果
    start_time = time.time()
    # 启动输入共享内存
    result = ir.infer({input_node:blob}, share_inputs=True)[output_node][0]
    latency.append(ir.latency)       # 获取推理计算的延迟
    end_time = time.time()
    total_time += end_time - start_time

    # 4. 对推理结果进行后处理
    top5_index = postprocess_output(result)

# 其他处理代码，例如:显示结果等 ...
# 显示分类结果
print(f"The Top-5 predicted categories:", end=" ") 
for i in top5_index:
    conf = result[i]
    name = class_names[i]
    print(f"{name} {conf:.2f}, ", end="")
print()
# 输出性能统计结果：
# 计算并输出延迟
min_latency = min(latency)
max_latency = max(latency)
mean_latency = (sum(latency) / len(latency))
print(f"MIN Latency: {min_latency:.2f}ms")
print(f"MEAN Latency: {mean_latency:.2f}ms")
print(f"MAX Latency: {max_latency:.2f}ms")
# 计算并输出吞吐量
throughput = num_iterations / total_time
print(f"ir.infer() executed {num_iterations} iterations, total time: {total_time:.4f}s")
print(f"Throughput: {throughput:.2f} FPS")

# 释放摄像头资源
cap.release()
# 关闭所有OpenCV窗口
cv2.destroyAllWindows()



