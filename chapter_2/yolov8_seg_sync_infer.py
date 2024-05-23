from ultralytics import YOLO
import torch, time
import openvino as ov

model_path = r".\yolov8s-seg.onnx"
IMAGE_PATH = r".\coco_bike.jpg"

# 用Ultralytics工具包 API实现yolov8-seg模型推理程序
seg_model = YOLO(model_path,task="segment")
seg_model(IMAGE_PATH)

# 使用OpenVINO实现推理计算
core = ov.Core()
device = "GPU.1"                          #指定英特尔独立显卡GPU.1
config = {"PERFORMANCE_HINT": "LATENCY"}  #同步推理，一般配置为延迟优先
# 1. 编译模型到GPU上
compiled_model = core.compile_model(model_path, device, config)

# 2. 替代YOLOv8-seg的原生推理计算方法
def ov_infer(*args):
    result = compiled_model(args)
    return torch.from_numpy(result[0]), torch.from_numpy(result[1])

seg_model.predictor.inference = ov_infer

# 3. 执行基于OpenVINO的推理计算，并复用YOLOv8-seg的原生前后处理程序
seg_model(IMAGE_PATH, show=True)

# 让推理结果显示6秒
time.sleep(6)

