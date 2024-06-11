import cv2, time
import numpy as np  
import openvino as ov 
from ultralytics import YOLO
import torch, time
from openvino import Tensor

model_path = r".\yolov8s.pt"
ov_model_path   = r".\yolov8s.xml"
IMAGE_PATH = r".\coco.jpg"

core = ov.Core()
device = "CPU"
config = {"PERFORMANCE_HINT": "LATENCY"}  #延迟优先
ov_model = core.compile_model(ov_model_path,
                              device_name=device,
                              config=config)

# 初始化YOLO实例，使用YOLO实例自带的preprocess()和postprocess()方法
det_model = YOLO(model_path)
det_model(IMAGE_PATH)
det_model.predictor.model.pt = False

interations = 2500

# Benchmark 同步推理计算
# 创建一个负责处理当前帧的推理请求
ir = ov_model.create_infer_request()
input_node = ov_model.inputs[0]
output_node = ov_model.outputs[0]

# 记录开始时间，使用高性能计数器获取更精确的时间度量
start = time.perf_counter()
for _ in range(interations):

    # 采集当前帧图像
    ori_img = cv2.imread(IMAGE_PATH)
    # 使用YOLO实例自带的preprocess()对当前帧做预处理
    im = det_model.predictor.preprocess([ori_img])
    # 调用infer()，以阻塞方式启动推理计算
    output = torch.from_numpy(ir.infer(im.numpy())[0])
    # 使用YOLO实例自带的ostprocess()对推理结果做后处理
    res = det_model.predictor.postprocess(output, im, [ori_img])

# 记录结束时间并计算总耗时
end = time.perf_counter()
time_sync = end - start 

# 计算并格式化输出模型的吞吐量（FPS）和平均延迟（毫秒）
print(f"同步推理计算的吞吐量: {(interations/time_sync):.2f}FPS; 平均延迟: {(time_sync/interations):.4f}s")

# Benchmark 异步推理计算
# 创建一个负责处理当前帧的推理请求
ir_curr = ov_model.create_infer_request()
# 创建一个推理请求负责处理下一帧
ir_next = ov_model.create_infer_request()
# 采集当前帧图像
img_curr = cv2.imread(IMAGE_PATH)
# 对当前帧做预处理
im_curr = det_model.predictor.preprocess([img_curr]).numpy()
# 调用start_async()，以非阻塞方式启动当前帧推理计算
ir_curr.set_tensor(input_node, Tensor(im_curr))
ir_curr.start_async()

start = time.perf_counter()
for _ in range(interations):

    # 采集下一帧
    img_next = cv2.imread(IMAGE_PATH)
    # 对下一帧做预处理
    im_next = det_model.predictor.preprocess([img_next]).numpy()
    # 调用start_async()，以非阻塞方式启动当前帧推理计算
    ir_next.set_tensor(input_node, Tensor(im_next))
    ir_next.start_async()
    # 调用wait()，等待当前帧推理计算结束
    ir_curr.wait()
    # 对当前帧推理结果做后处理
    output = torch.from_numpy(ir_curr.get_tensor(output_node).data)
    res = det_model.predictor.postprocess(output, im_curr, [img_curr])
    # 交换当前帧推理请求和下一帧推理请求
    ir_curr, ir_next = ir_next, ir_curr
    # 交换当前帧和下一帧图像数据
    im_curr, im_next = im_next, im_curr
    img_curr, img_next = img_next, img_curr

# 记录结束时间并计算总耗时
end = time.perf_counter()
time_async = end - start 

# 计算并格式化输出模型的吞吐量（FPS）和平均延迟（毫秒）
print(f"异步推理计算的吞吐量: {(interations/time_async):.2f}FPS; 平均延迟: {(time_async/interations):.4f}s")
