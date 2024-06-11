import cv2
from PIL import Image
import torchvision.transforms.functional as F

# 使用OpenCV读取图像并转换为RGB
image_cv = cv2.imread('coco.jpg')
image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)

# 使用cv2.resize将图像放缩到[224,224]
image_cv = cv2.resize(image_cv,[224,224])
print(f"image_cv[100,100]的像素值为： {image_cv[100,100]}")
     
# 使用PIL读取图像, 图像默认为：RGB
image_pil = Image.open('coco.jpg')
# 使用F.resize将图像放缩到[224,224]
image_pil = F.resize(image_pil,[224,224])
print(f"image_pil[100,100]的像素值为：{image_pil.getpixel((100, 100))}")

