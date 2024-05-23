# YOLOv8 目标检测模型OpenVINO同步推理程序
import cv2, time
import numpy as np  
import openvino as ov 
from ultralytics.data.augment import LetterBox
from ultralytics.utils import yaml_load
from ultralytics.utils.checks import check_yaml

# 获取类别标签信息CLASSES
CLASSES = yaml_load(check_yaml("coco128.yaml"))["names"]
# 根据类别数量生成对应每个类别的颜色
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))
# 实例化LetterBox
letterbox = LetterBox()

#
def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return


# 预处理函数: letterbox + blobFromImage
def preprocess_image(image: np.ndarray, target_size=(640, 640))->np.ndarray:
    image = letterbox(None, image)    #YOLOv8用letterbox按保持图像原始宽高比方式放缩图像
    blob = cv2.dnn.blobFromImage(image, scalefactor=1 / 255, size=target_size, swapRB=True)
    return blob


# 后处理函数: 从推理结果[1,84,8400]的张量中拆解出：检测框，类别和类别分数
def postprocess_output(outputs):  
    outputs = np.array([cv2.transpose(outputs[0])])
    rows = outputs.shape[1]

    boxes = []
    scores = []
    class_ids = []

    for i in range(rows):
        classes_scores = outputs[0][i][4:]
        (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
        if maxScore >= 0.25:
            box = [
                outputs[0][i][0] - (0.5 * outputs[0][i][2]), outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                outputs[0][i][2], outputs[0][i][3]]
            boxes.append(box)
            scores.append(maxScore)
            class_ids.append(maxClassIndex)
    # 返回检测框，类别和类别分数
    return boxes, scores, class_ids


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
ov_model_path   = "./yolov8s_int8.xml"
# 指定计算设备
device = "GPU"                          #指定英特尔独立显卡
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

while True:
    start = time.time()

    # 1. 读取一帧图像
    ret, frame = cap.read()
    # 如果读取不成功，则退出
    if not ret:
        print("Error: fail to read an image!")
        break
    [height, width, _] = frame.shape
    length = max((height, width))
    scale = length / 640

    # 2. 数据预处理
    blob = preprocess_image(frame)

    # 3. 执行推理计算并获得结果
    result = ir.infer({input_node:blob})[output_node]

    # 4. 对推理结果进行后处理
    boxes, scores, class_ids = postprocess_output(result)
    result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)

    end = time.time()

    # 其他处理代码，例如:显示结果等 ...
    detections = []
    for i in range(len(result_boxes)):
        index = result_boxes[i]
        box = boxes[index]
        detection = {
            'class_id': class_ids[index],
            'class_name': CLASSES[class_ids[index]],
            'confidence': scores[index],
            'box': box,
            'scale': scale}
        detections.append(detection)
        draw_bounding_box(frame, class_ids[index], scores[index], round(box[0] * scale), round(box[1] * scale),
                          round((box[0] + box[2]) * scale), round((box[1] + box[3]) * scale))
    
    # show FPS
    throughput = (1 / (end - start)) 
    performance = f"Throughput: {throughput:.2f}FPS; Latency: {ir.latency:.2f}ms"
    cv2.putText(frame, performance, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
    
    cv2.imshow('YOLOv8 Object Detection OpenVINO Demo', frame)
    # wait key for ending
    if cv2.waitKey(1) > -1:
        print("finished by user")
        break


# 释放摄像头资源
cap.release()
# 关闭所有OpenCV窗口
cv2.destroyAllWindows()



