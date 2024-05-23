# YOLOv8 目标检测模型OpenVINO同步推理程序
import cv2, time
import numpy as np  
import openvino as ov 
from ultralytics.data.augment import LetterBox
from ultralytics.utils import yaml_load
from ultralytics.utils.checks import check_yaml
from ultralytics.utils import ops
from ultralytics.utils.plotting import colors
from typing import Tuple
import torch

# 获取类别标签信息CLASSES
CLASSES = yaml_load(check_yaml("coco128.yaml"))["names"]
# 实例化LetterBox
letterbox = LetterBox()

def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    tl = round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors(class_id)
    c1, c2 = (int(x), int(y)), (int(x_plus_w), int(y_plus_h))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)

    tf = max(tl - 1, 1)  # font thickness
    t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
    c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
    cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
    cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

    return img


# 预处理函数: letterbox + blobFromImage
def preprocess_image(frame: np.ndarray, target_size=(640, 640))->np.ndarray:
    img = letterbox(None, frame)    # YOLOv8用letterbox按保持图像原始宽高比方式放缩图像
    blob = cv2.dnn.blobFromImage(img, scalefactor=1 / 255, size=(640, 640), swapRB=True)
    return blob


# 后处理函数: 从推理结果[1,84,8400]的张量中拆解出：检测框，置信度和类别
def postprocess(
    pred_boxes:np.ndarray, 
    input_hw:Tuple[int, int], 
    orig_img:np.ndarray, 
    min_conf_threshold:float = 0.25, 
    nms_iou_threshold:float = 0.7, 
    agnosting_nms:bool = False, 
    max_detections:int = 300,
):
    """
    YOLOv8 model postprocessing function. Applied non maximum supression algorithm to detections and rescale boxes to original image size
    Parameters:
        pred_boxes (np.ndarray): model output prediction boxes
        input_hw (np.ndarray): preprocessed image
        orig_image (np.ndarray): image before preprocessing
        min_conf_threshold (float, *optional*, 0.25): minimal accepted confidence for object filtering
        nms_iou_threshold (float, *optional*, 0.45): minimal overlap score for removing objects duplicates in NMS
        agnostic_nms (bool, *optiona*, False): apply class agnostinc NMS approach or not
        max_detections (int, *optional*, 300):  maximum detections after NMS
    Returns:
       pred: detected boxes in format [x1, y1, x2, y2, score, label]
    """
    nms_kwargs = {"agnostic": agnosting_nms, "max_det":max_detections}
    pred = ops.non_max_suppression(
        torch.from_numpy(pred_boxes),
        min_conf_threshold,
        nms_iou_threshold,
        nc=80,
        **nms_kwargs
    )[0]

    shape = orig_img.shape
    pred[:, :4] = ops.scale_boxes(input_hw, pred[:, :4], shape).round()
    
    return pred


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

# 指定YOLOv8目标检测模型路径
ov_model_path   = "./yolov8s.xml"
# 指定计算设备
device = "CPU"                            #指定英特尔独立显卡
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

# -- 初始化工作放上面 --------------------

# OpenVINO同步推理计算并统计性能
start = time.time()

# 1. 读取一帧图像
frame = cv2.imread("./coco.jpg")

# 2. 数据预处理
blob = preprocess_image(frame)

# 3. 执行推理计算并获得结果
result = ir.infer({input_node:blob})[output_node]

# 4. 对推理结果进行后处理
input_hw = blob.shape[2:]
bboxes = postprocess(pred_boxes=result, input_hw=input_hw, orig_img=frame)

end = time.time()

# 其他处理代码，例如:显示结果等 ...
for bbox in bboxes:
    #bbox:[x1, y1, x2, y2, score, label]
    draw_bounding_box(frame,int(bbox[5]), bbox[4], bbox[0], bbox[1], bbox[2], bbox[3])
    

# show FPS
throughput = (1 / (end - start)) 
performance = f"Throughput: {throughput:.2f} FPS; Latency: {ir.latency:.2f}ms"
cv2.putText(frame, performance, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

cv2.imshow('YOLOv8 Object Detection OpenVINO Demo', frame)


# wait key for ending
cv2.waitKey(0)

# 关闭所有OpenCV窗口
cv2.destroyAllWindows()



