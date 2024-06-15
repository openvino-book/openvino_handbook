from ultralytics import YOLO
import torch, time
import onnxruntime as ort

device = "CPU_FP32"
IMAGE_PATH = r".\coco_bike.jpg"

# 用Ultralytics工具包 API实现yolov8-seg模型推理程序
seg_model = YOLO("yolov8n-seg.pt",task="segment")
seg_model(IMAGE_PATH)

# 使用OpenVINO™执行提供者实现推理计算
# 指定ONNX模型路径, 指定OpenVINOExecutionProvider
so = ort.SessionOptions()
ovep_model = ort.InferenceSession("yolov8n-seg.onnx", so, 
                           providers=["OpenVINOExecutionProvider"], 
                           provider_options=[{"device_type" : device}])
input_names = ovep_model.get_inputs()[0].name
outputs = ovep_model.get_outputs()
output_names = list(map(lambda output:output.name, outputs))

# 2. 用onnxruntime替代YOLOv8-seg的原生推理计算方法
def ovep_infer(*args):
    result = ovep_model.run(output_names, {input_names: args[0].numpy()})
    return torch.from_numpy(result[0]), torch.from_numpy(result[1])

seg_model.predictor.inference = ovep_infer
seg_model.predictor.model.pt = False

# 3. 执行基于ONNXRuntime OpenVINO™执行提供者的推理计算
# 复用YOLOv8-seg的原生前后处理程序
seg_model(IMAGE_PATH, show=True)

# 让推理结果显示6秒
time.sleep(6)

