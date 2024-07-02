# 导入所需库
import torch, time
import torchvision.models as models
import openvino.torch

# 加载Resnet50模型并使用预训练权重
model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
# 创建一个随机输入张量以供推理使用
input = torch.rand([1,3,244,244])

# 不使用OpenVINO后端，运行PyTorch推理
start = time.time()
output = model(input)
# 计算执行时间
exec_time = time.time() - start
# 打印无OpenVINO后端的执行时间
print(f"未使用OpenVINO后端的执行时间:\t{exec_time:0.3f}s")

# 设置OpenVINO后端的配置选项
opts = {
    "device" : "GPU.1",          # 指定设备为英特尔独立显卡
    "config" : {"PERFORMANCE_HINT" : "LATENCY"}, # 优化目标为延迟优先
    "model_caching" : True,      # 启用模型缓存
    "cache_dir": "./model_cache" # 指定模型缓存的目录
}
# 指定OpenVINO为后端，使用torch.compile()编译模型
model = torch.compile(model, backend="openvino", options=opts)

# 运行一次预热执行,以完成编译过程
output = model(input)

# 使用OpenVINO后端，再次运行PyTorch推理
start = time.time()
output = model(input)
# 计算执行时间
exec_time = time.time() - start
# 打印使用OpenVINO后端的执行时间
print(f"使用OpenVINO后端的执行时间:\t{exec_time:0.3f}s")





