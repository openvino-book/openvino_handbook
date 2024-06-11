from openvino import Core, Layout, Type, serialize
from openvino.preprocess import PrePostProcessor, ColorFormat

# 设置模型路径
model_path = "./yolov8s_openvino_model/yolov8s.xml"
# 读入模型
core = Core()
ov_model = core.read_model(model_path)

# Step 1: 实例化PrePostProcessor对象
ppp = PrePostProcessor(ov_model)

# Step 2: 申明用户输入数据信息:
# - 颜色通道顺序：BGR
# - 数据类型：uint8
# - 数据布局：NHWC
ppp.input().tensor() \
    .set_color_format(ColorFormat.BGR) \
    .set_element_type(Type.u8) \
    .set_layout(Layout('NHWC'))  

# Step 3: 申明原始模型输入节点的layout
ppp.input().model().set_layout(Layout('NCHW'))

# Step 4: 定义预处理步骤
# - 数据精度：从 u8 转为 f16
# - 颜色通道：从 BGR 转为 RGB
# - 减去均值(mean),除以放缩系数(scale)
# - 布局转换会在最后一步自动加上
ppp.input().preprocess() \
    .convert_element_type(Type.f16) \
    .convert_color(ColorFormat.RGB) \
    .mean([0.0, 0.0, 0.0]) \
    .scale([255.0, 255.0, 255.0]) 

# Step 5: 将预处理步骤嵌入原始AI模型
print(f'Build preprocessor into original model: {ppp}')
model_with_PPP = ppp.build()

# Step 6: 保存嵌入预处理的AI模型
serialize(model_with_PPP, 'yolov8s_with_ppp.xml', 'yolov8s_with_ppp.bin')