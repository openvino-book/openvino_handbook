import cv2, time, torch, statistics
import logging as log
import openvino as ov 
from openvino import AsyncInferQueue, InferRequest
from ultralytics import YOLO

# 模型文件路径设置
model_path = r".\yolov8s.pt"  # PyTorch模型路径
ov_model_path = r".\yolov8s.xml"  # OpenVINO IR模型路径
IMAGE_PATH = r".\coco.jpg"  # 测试图片路径

# 初始化OpenVINO推理引擎核心并指定设备配置
core = ov.Core()
device = "GPU.1"  # 选择GPU设备，具体编号视情况而定
config = {"PERFORMANCE_HINT": "THROUGHPUT"}  # 配置优先考虑吞吐量
# 编译模型
ov_model = core.compile_model(ov_model_path,
                              device_name=device,
                              config=config)

# 初始化YOLO检测模型实例，利用其预处理和后处理方法
det_model = YOLO(model_path)
det_model(IMAGE_PATH)                  # 加载模型并预热
det_model.predictor.model.pt = False   # 标记不使用PyTorch模型

# 自定义AsyncInferQueue要求的"callback"函数
def postprocess(ir: InferRequest, userdata: tuple):
    output = torch.from_numpy(ir.output_tensors[0].data)
    # 为展示最大化的GPU利用率，Benchmark过程中，不运行后处理
    #res = det_model.predictor.postprocess(output, userdata[1], userdata[2])
    return 

# 创建异步推理请求队列并设置回调函数
ireqs = AsyncInferQueue(ov_model)
print('AsyncInferQueue中的推理请求数量:', len(ireqs))
ireqs.set_callback(postprocess)


# 异步推理队列的基准测试
in_fly = set()   # 记录正在工作的推理请求ID集合
latencies = []   # 存储时延记录
niter = 20000    # 循环次数，可更改

# 采集图像
ori_img = cv2.imread(IMAGE_PATH)
# 使用YOLO实例自带的preprocess()对当前帧做预处理
im = det_model.predictor.preprocess([ori_img]) 

# 注意：为了展示最大化的独立显卡利用率
# 本范例的Benchmark，不包含前处理和后处理
start = time.perf_counter()  # 开始计时
for i in range(niter):
    
    idle_id = ireqs.get_idle_request_id()   # 获取空闲的推理请求ID
    if idle_id in in_fly:
        latencies.append(ireqs[idle_id].latency)
    else:
        in_fly.add(idle_id)
    # 使用推理请求池中空闲的推理请求执行异步推理 
    ireqs.start_async({0:im.numpy()},(i, im, [ori_img]))  # 发起异步推理请求
# 等待所有请求完成
ireqs.wait_all() 

# 输出基准测试结果
duration = time.perf_counter() - start
fps = niter / duration
print(f'Count:          {niter} iterations')
print(f'Duration:       {duration * 1e3:.2f} ms')
print('Latency:')
print(f'    Median:     {statistics.median(latencies):.2f} ms')
print(f'    Average:    {sum(latencies) / len(latencies):.2f} ms')
print(f'    Min:        {min(latencies):.2f} ms')
print(f'    Max:        {max(latencies):.2f} ms')
print(f'Throughput: {fps:.2f} FPS')
