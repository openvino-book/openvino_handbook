import torch
from diffusers import StableDiffusion3Pipeline
import openvino as ov

#################################################################
#                   加载SD3 Medium模型的预训练权重                #
#################################################################
# 指定Stable Diffusion 3模型文件路径
sd3_model_file = r"d:\sd3_medium_incl_clips.safetensors"
# 从单个文件加载Stable Diffusion 3 Pipeline，设置数据类型为float32，并不加载第三个文本编码器
pipe = StableDiffusion3Pipeline.from_single_file(
    sd3_model_file,
    torch_dtype=torch.float32,
    text_encoder_3=None
)

#################################################################
#   将模型中的各个组件转换为OpenVINO™ IR格式模型，并保存这些模型    #
#################################################################

# 获取Pipeline中的Transformer模块，并设置为评估模式
transformer = pipe.transformer
transformer.eval()

# 使用torch.no_grad()来禁用梯度计算，加快模型推理速度
with torch.no_grad():
    # 将Transformer模块转换为OpenVINO模型
    ov_transformer = ov.convert_model(
        transformer,
        example_input={  # 提供示例输入以帮助OpenVINO优化模型
            "hidden_states": torch.zeros((2, 16, 64, 64)),
            "timestep": torch.tensor([1, 1]),
            "encoder_hidden_states": torch.ones([2, 154, 4096]),
            "pooled_projections": torch.ones([2, 2048]),
        },
    )
# 保存转换后的OpenVINO模型
ov.save_model(ov_transformer, "transformer.xml")
print("Transformer is exported successfully!")  # 输出转换成功的消息

# 获取Pipeline中的第一个文本编码器，并设置为评估模式
text_encoder = pipe.text_encoder
text_encoder.eval()

# 使用functools.partial修改forward方法以返回隐藏状态和字典形式的结果
from functools import partial
with torch.no_grad():
    text_encoder.forward = partial(text_encoder.forward, output_hidden_states=True, return_dict=False)
    # 将第一个文本编码器转换为OpenVINO模型
    ov_text_encoder = ov.convert_model(text_encoder, example_input=torch.ones([1, 77], dtype=torch.long))
# 保存转换后的OpenVINO模型
ov.save_model(ov_text_encoder, "text_encoder.xml")
print("text_encoder is exported successfully!")  # 输出转换成功的消息

# 获取Pipeline中的第二个文本编码器，并设置为评估模式
text_encoder_2 = pipe.text_encoder_2
text_encoder_2.eval()

with torch.no_grad():
    text_encoder_2.forward = partial(text_encoder_2.forward, output_hidden_states=True, return_dict=False)
    # 将第二个文本编码器转换为OpenVINO模型
    ov_text_encoder_2 = ov.convert_model(text_encoder_2, example_input=torch.ones([1, 77], dtype=torch.long))
# 保存转换后的OpenVINO模型
ov.save_model(ov_text_encoder_2, "text_encoder_2.xml")
print("text_encoder_2 is exported successfully!")  # 输出转换成功的消息

# 获取Pipeline中的VAE解码器，并设置为评估模式
vae = pipe.vae
vae.eval()

with torch.no_grad():
    # 修改forward方法为decode方法
    vae.forward = vae.decode
    # 将VAE解码器转换为OpenVINO模型
    ov_vae = ov.convert_model(vae, example_input=torch.ones([1, 16, 64, 64]))
# 保存转换后的OpenVINO模型
ov.save_model(ov_vae, "vae_decoder.xml")
print("vae is exported successfully!")  # 输出转换成功的消息

# 保存Pipeline中的分词器
pipe.tokenizer.save_pretrained("tokenizer")
# 保存Pipeline中的第二个分词器
pipe.tokenizer_2.save_pretrained("tokenizer_2")
# 保存Pipeline中的调度器
pipe.scheduler.save_pretrained("scheduler")
print("tokenizer, tokenizer_2 and scheduler are exported successfully!")  # 输出转换成功的消息

# 清除PyTorch JIT相关的缓存和注册信息
torch._C._jit_clear_class_registry()
torch.jit._recursive.concrete_type_store = torch.jit._recursive.ConcreteTypeStore()
torch.jit._state._clear_class_state()