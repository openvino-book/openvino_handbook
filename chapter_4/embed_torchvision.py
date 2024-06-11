import torch.nn.functional as f
import openvino as ov
import numpy as np
import torchvision
import torch
import os

from openvino.preprocess.torchvision import PreprocessConverter
from PIL import Image


# 1. 创建示例模型
class Convnet(torch.nn.Module):
    def __init__(self, input_channels):
        super(Convnet, self).__init__()
        self.conv1 = torch.nn.Conv2d(input_channels, 6, 5)
        self.conv2 = torch.nn.Conv2d(6, 16, 3)

    def forward(self, data):
        data = f.max_pool2d(f.relu(self.conv1(data)), 2)
        data = f.max_pool2d(f.relu(self.conv2(data)), 2)
        return data


# 2. 定义基于torchvision.transforms的预处理流程
preprocess_pipeline = torchvision.transforms.Compose(
    [
        torchvision.transforms.Resize(256, interpolation=torchvision.transforms.InterpolationMode.NEAREST),
        torchvision.transforms.CenterCrop((216, 218)),
        torchvision.transforms.Pad((2, 3, 4, 5), fill=3),
        torchvision.transforms.ToTensor(),
        torchvision.transforms.ConvertImageDtype(torch.float32),
        torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

# 3. 导出onnx模型    
torch_model = Convnet(input_channels=3)
torch.onnx.export(torch_model, torch.randn(1, 3, 224, 224), "test_convnet.onnx", verbose=False, input_names=["input"], output_names=["output"])
# 4. 用OpenVINO读入onnx模型
core = ov.Core()
ov_model = core.read_model(model="test_convnet.onnx")
if os.path.exists("test_convnet.onnx"):
    os.remove("test_convnet.onnx")
test_input = np.random.randint(255, size=(260, 260, 3), dtype=np.uint16)

# 5. 将torchvision预处理嵌入至OpenVINO模型
ov_model = PreprocessConverter.from_torchvision(
    model=ov_model, transform=preprocess_pipeline, input_example=Image.fromarray(test_input.astype("uint8"), "RGB")
)
# 6. 编译嵌入torchvision预处理的模型
ov_model = core.compile_model(ov_model, "CPU")

# 7. 执行推理计算
ov_input = np.expand_dims(test_input, axis=0)
output = ov_model.output(0)
ov_result = ov_model(ov_input)[output]