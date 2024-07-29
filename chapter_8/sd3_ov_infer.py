import torch
import openvino as ov
from sd3ov import OVStableDiffusion3Pipeline  # 导入自定义的Stable Diffusion 3 OpenVINO Pipeline类
from diffusers.schedulers import FlowMatchEulerDiscreteScheduler
from transformers import AutoTokenizer
#################################################################
#  使用core.compile_model()方法载入模型到指定的计算设备            #
#################################################################

# 初始化OpenVINO的核心组件
core = ov.Core()

# 设置OpenVINO编译模型时的配置参数，这里优先考虑低延迟
ov_config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": "./cache"}
device = "GPU"  # 设定运行设备为GPU
print("Loading transformer... ")  # 输出提示信息
# 编译并载入Transformer模型
transformer = core.compile_model("transformer.xml", device, ov_config)  

# 更新配置参数以提高精度
ov_config["INFERENCE_PRECISION_HINT"] = "f32"
print("Loading text_encoder... ")  # 输出提示信息
# 编译并载入Text Encoder模型
text_encoder = core.compile_model("text_encoder.xml", device, ov_config)  

print("Loading text_encoder_2... ")  # 输出提示信息
# 编译并载入Text Encoder 2模型
text_encoder_2 = core.compile_model("text_encoder_2.xml", device, ov_config)
text_encoder_3 = None  # 第三个Text Encoder未使用

print("Loading vae_decoder... ")  # 输出提示信息
# 编译并载入VAE Decoder模型
vae = core.compile_model("vae_decoder.xml", device, ov_config)

#################################################################
#  使用OVStableDiffusion3Pipeline类创建SD3 Medium模型的工作流水线 #
#################################################################
# 构建OpenVINO版本的Stable Diffusion 3 Pipeline
print("Building OpenVINO SD3 Pipeline... ")
scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained("scheduler")  # 加载调度器
tokenizer = AutoTokenizer.from_pretrained("tokenizer")      # 加载第一个分词器
tokenizer_2 = AutoTokenizer.from_pretrained("tokenizer_2")  # 加载第二个分词器
tokenizer_3 = None  # 第三个分词器未使用
ov_pipe = OVStableDiffusion3Pipeline(transformer, scheduler, vae, text_encoder, tokenizer, text_encoder_2, tokenizer_2, text_encoder_3, tokenizer_3)

#################################################################
#         执行流水线ov_pipe，生成图片                             #
#################################################################
print("Generating image... ")
prompt = "a photo of a cat holding a sign that says: Hello OpenVINO! The OpenVINO font color is purple"
image = ov_pipe(  # 生成图像
    prompt=prompt,
    negative_prompt="",
    num_inference_steps=28,
    guidance_scale=5,
    height=512,
    width=512,
    generator=torch.Generator().manual_seed(1212),  # 设置随机种子
).images[0]

# 保存生成的图像
print("Saving sd3_no_T5_ov.png... ")
image.save("sd3_no_T5_ov.png")

#################################################################
#         将生成的图片保存并合并入海报背景图片                     #
#################################################################
from PIL import Image, ImageDraw, ImageFont

# 生成新海报
print("Generating new poster...")

# 打开图像并更改分辨率为1024x1024
sd3_img = Image.open("sd3_no_T5_ov.png").resize((1024, 1024))

# 打开海报背景图
poster = Image.open("bg.png")

# 创建一个新的画布
draw = ImageDraw.Draw(poster)

# 字体的格式
font = ImageFont.truetype("arial.ttf", 40)  # 使用系统中存在的字体文件和字体大小

# 在指定位置写入文字 (x, y, 文字, 字体=字体, 填充颜色)
prompt = "a photo of a cat holding a sign that says: \nHello OpenVINO! The OpenVINO font color is purple"
draw.text((280, 1750), prompt, font=font, fill=(255, 0, 0))  # 在海报上写入文字

# 插入图片
paste_position = (int(110), int(665))
poster.paste(sd3_img, paste_position)  # 将生成的图像粘贴到海报上

# 保存修改后的海报
print("Saving new_poster.png... ")
poster.save("new_poster.png")