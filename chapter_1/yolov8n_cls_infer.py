import cv2, onnx 
import numpy as np  
import openvino as ov 
from ultralytics.data.augment import CenterCrop

# 设置模型路径
onnx_model_path = "./yolov8n-cls.onnx"
ov_model_path   = "./yolov8n-cls.xml"
# 设置图片路径
image_url = "https://storage.openvinotoolkit.org/repositories/openvino_notebooks/data/data/image/coco.jpg"
image_path= "./coco.jpg"

onnx_model = onnx.load(onnx_model_path)
# 从模型的元数据获取标签信息names
class_names = eval(onnx_model.metadata_props[9].value)
# 从模型的元数据获取模型输入节点的width和height
input_w,input_h = eval(onnx_model.metadata_props[8].value)

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


# 数据预处理函数
def preprocess_image(image: np.ndarray, target_size=(input_w, input_h))->np.ndarray:  
# # YOLOv8-Cls使用CenterCrop放缩图像, 参考:
# https://github.com/ultralytics/ultralytics/blob/main/ultralytics/data/augment.py#L1185
    
    # 调整图像尺寸
    center_crop = CenterCrop(size=target_size)
    image = center_crop(image)
    # 将像素值归一化到[0,1] 
    image = image / 255.0
    # 调整数据格式：HWC to CHW, BGR to RGB
    image= image.transpose((2,0,1))[::-1]
    #返回NCHW格式的张量数据
    return np.expand_dims(image, axis=0)


# 后处理函数
def postprocess_output(result, class_names=class_names):  
    # 获得类别的概率值
    prob = np.max(result)
    # 获得类别的标签
    label = class_names[np.argmax(result)]
    # 返回类别的概率值和标签
    return prob, label


def main():  

    # 第一步：创建Core对象
    core = ov.Core()

    # 第二步：从指定路径读取并编译模型  
    compiled_model = core.compile_model(ov_model_path, "CPU")
    input_node = compiled_model.inputs[0]
    output_node = compiled_model.outputs[0]

    # 第三步：获取图像数据  
    img = load_img(image_path)
    
    # 第四步：对图像进行预处理
    blob = preprocess_image(img)
      
    # 第五步：执行推理计算，并从第0号输出节点获取推理结果
    result = compiled_model({input_node:blob})[output_node]
      
    # 第六步：对推理结果进行后处理  
    prob, label = postprocess_output(result)

    # 其他后处理代码，例如显示结果等 ...  
    print(f"The image is {label}: {prob:.2f}.")
    cv2.imshow("YOLOv8n-Cls OpenVINO Demo", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
  
if __name__ == '__main__':  
    main()
