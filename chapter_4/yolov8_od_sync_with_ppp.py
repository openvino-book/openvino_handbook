# 导入依赖库
import cv2, time
import numpy as np  
import openvino as ov 
from ultralytics.data.augment import LetterBox

# 指定YOLOv8目标检测模型路径
ov_model_with_ppp_path   = "./yolov8s_with_ppp.xml"
ov_model = "./yolov8s.xml"
# 设置图片路径
image_path= "./coco.jpg"
# 指定计算设备
device = "GPU.1"                          #指定英特尔独立显卡
# 设置OpenVINO运行时属性：同步推理，延迟优先
config = {"PERFORMANCE_HINT": "LATENCY"}  #同步推理，一般配置为延迟优先

# 实例化LetterBox
letterbox = LetterBox()

# YOLOv8预处理函数
def preprocess_image(image: np.ndarray, target_size=(640, 640), enable_ppp=False) -> np.ndarray:
    """
    对输入图像进行预处理，以便用于神经网络模型的输入。

    参数:
    - image: np.ndarray
        输入的图像数组。
    - target_size: tuple, 默认为(640, 640)
        目标图像的尺寸，预处理后图像的宽度和高度将调整为此尺寸。
    - enable_ppp: bool, 默认为False
        根据enable_ppp决定是否启用针对内嵌预处理模型的预处理步骤
        如果enable_ppp=True,则无需调用OpenCV的预处理函数cv2.dnn.blobFromImage
        如果enable_ppp=False,则增加Batch维度,然后返回

    返回:
    - np.ndarray
        预处理后的图像数据,可以直接输入到神经网络中。
   
    """
    # 使用letterbox函数调整图像大小，确保比例不失真
    image = letterbox(None, image)
    
    # 根据enable_ppp标志决定是否仅增加batch维度返回
    if enable_ppp:
        return np.expand_dims(image, axis=0)
    
    # 调用OpenCV的预处理函数cv2.dnn.blobFromImage对数据进行预处理
    blob = cv2.dnn.blobFromImage(image, scalefactor=1 / 255, size=target_size, swapRB=True)
    return blob

# YOLOv8后处理函数
def postprocess_output(outputs):  
    """
    对模型输出进行后处理，提取出预测的边界框、类别ID及相应的置信度分数。

    参数:
    - outputs: 模型的原始输出，通常是一个或多个张量组成的列表。

    返回:
    - boxes: list
        检测到的对象边界框坐标列表，每个元素是一个包含四个值[x_min, y_min, width, height]的列表。
    - scores: list
        每个检测框对应的置信度分数列表。
    - class_ids: list
        每个检测框所属类别的ID列表。

    """
    # 调整输出形状，便于后续处理
    outputs = np.array([cv2.transpose(outputs[0])])
    rows = outputs.shape[1]  # 获取行数，即潜在检测对象的数量

    # 初始化存储结果的列表
    boxes = []      # 存储边界框
    scores = []     # 存储置信度分数
    class_ids = []  # 存储类别ID

    # 遍历每一条检测结果
    for i in range(rows):
        # 提取当前对象对于所有类别的置信度分数
        classes_scores = outputs[0][i][4:]
        
        # 找到最大分数及其位置
        (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
        
        # 如果最大分数超过阈值，则保存该检测结果
        if maxScore >= 0.25:
            # 计算边界框的坐标
            box = [
                outputs[0][i][0] - (0.5 * outputs[0][i][2]),  # x_center - 0.5*width
                outputs[0][i][1] - (0.5 * outputs[0][i][3]),  # y_center - 0.5*height
                outputs[0][i][2],                             # width
                outputs[0][i][3]]                             # height
            
            # 添加到结果列表
            boxes.append(box)
            scores.append(maxScore)
            class_ids.append(maxClassIndex)

    # 返回处理后的结果
    return boxes, scores, class_ids

# 创建Core对象
core = ov.Core()

def benchmark_model(model_path, enable_ppp=False, interations=100):
    """
    该函数用于评估模型的推理性能，包括吞吐量（FPS）和平均延迟（秒）。

    参数:
    - model_path: str
        模型文件的路径。
    - enable_ppp: bool, 默认为False
        根据enable_ppp决定是否启用针对内嵌预处理模型的预处理步骤
        如果enable_ppp=True,则无需调用OpenCV的预处理函数cv2.dnn.blobFromImage
        如果enable_ppp=False,则增加Batch维度,然后返回。
    - interations: int, 默认为100
        用于性能评估的迭代次数。

    返回:
    - perf: str
        评估结果字符串，格式为"吞吐量: X.XXFPS; 平均延迟: XX.XXs"。
    """
    
    # 从指定模型路径加载模型并针对特定设备进行编译
    compiled_model = core.compile_model(model=model_path, 
                                        device_name=device, 
                                        config=config)

    # 记录开始时间，使用高性能计数器获取更精确的时间度量
    start = time.perf_counter()

    # 进行指定次数的迭代以评估模型性能
    for _ in range(interations):
        
        # 读取一张测试图像数据
        frame = cv2.imread(image_path)

        # 对图像进行预处理
        # 根据enable_ppp决定是否启用针对内嵌预处理模型的预处理步骤
        blob = preprocess_image(frame, enable_ppp=enable_ppp)

        # 使用编译后的模型对预处理后的图像数据进行推理计算
        result = compiled_model(blob)[0]

        # 对模型输出的结果进行后处理，比如解码边界框、分数和类别ID
        boxes, scores, class_ids = postprocess_output(result)
        
        # 应用非最大抑制（NMS）算法，去除冗余的边界框，只保留最有可能的检测结果
        result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)

    # 记录结束时间并计算总耗时
    end = time.perf_counter()
    time_ir = end - start 

    # 计算并格式化输出模型的吞吐量（FPS）和平均延迟（毫秒）
    perf = f"吞吐量: {(interations/time_ir):.2f}FPS; 平均延迟: {(time_ir/interations):.4f}s"
    return perf

print("benchmark orginal yolov8s model...")
perf = benchmark_model(ov_model)
print(perf)
print("benchmark yolov8s with embedded preprocessing operations...")
perf = benchmark_model(ov_model_with_ppp_path, enable_ppp=True)
print(perf)






