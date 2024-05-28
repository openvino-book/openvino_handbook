import cv2, onnx
import numpy as np  
import openvino as ov 
import torch
import torchvision.transforms as T

# 设置模型路径
onnx_model_path = "./yolov8n-cls.onnx"
ov_model_path   = "./yolov8n-cls.xml"
# 设置图片路径
image_url = "https://storage.openvinotoolkit.org/repositories/openvino_notebooks/data/data/image/coco.jpg"
image_path= "./coco.jpg"
config = {}

onnx_model = onnx.load(onnx_model_path)
# 从模型的元数据获取标签信息names
class_names = eval(onnx_model.metadata_props[9].value)

# 检查字符串是否为url
from urllib.parse import urlparse
def is_url(string):
    try:
        # 对字符串进行URL解析
        parsed_url = urlparse(string)
        # 检查解析后的URL是否有效
        if parsed_url.scheme and parsed_url.netloc:
            return True
        else:
            return False
    except ValueError:
        return False
# 获取图像数据   
def load_img(path_or_url:str)->np.ndarray:
    if is_url(path_or_url):
        # 使用cv2.VideoCapture()从网络读取
        cap = cv2.VideoCapture(path_or_url)
        _,img = cap.read()
        cap.release()
    else:
        # 使用cv2.imread()从硬盘读取
        img = cv2.imread(path_or_url)
    return img


# 数据预处理函数，参考yolov8-cls的classify_transforms
# https://github.com/ultralytics/ultralytics/blob/main/ultralytics/data/augment.py#
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
    # 显示分类结果
    print(f"The Top-5 predicted categories:", end=" ") 
    for i in top5_index:
        conf = result[i]
        name = class_names[i]
        print(f"{name} {conf:.2f}, ", end="")

    return top5_index


# 第一步：创建Core对象
core = ov.Core()

# 第二步：从指定路径读取并编译模型  
compiled_model = core.compile_model(model=onnx_model_path, 
                                    device_name="CPU", 
                                    config=config)
input_node = compiled_model.inputs[0]
output_node = compiled_model.outputs[0]

# 第三步：获取图像数据  
img = load_img(image_path)

# 第四步：对图像进行预处理
blob = preprocess_image(img)

# 第五步：执行推理计算，并从输出节点output_node获取推理结果
result = compiled_model({input_node:blob})[output_node][0]

# 第六步：对推理结果进行后处理  
postprocess_output(result)


