# 导入所需的库和模块
from transformers import AutoConfig, AutoTokenizer, pipeline
from optimum.intel.openvino import OVModelForCausalLM

# 设置OpenVINO编译模型的配置参数，这里优先考虑低延迟
config = {
    "PERFORMANCE_HINT": "LATENCY", # 性能提示选择延迟优先
    "CACHE_DIR": "" # 模型缓存目录为空，使用默认位置
}

# 指定Qwen2-1.5B-Instruct int4模型的本地路径
model_dir = r"D:\chapter_5\qwen2-1.5b-instruct_int4"

# 设定推理设备为CPU，可根据实际情况改为"GPU"或"AUTO"
DEVICE = "CPU"

# 输入的问题示例，可以更改
question = "树上7只鸟,打死1只鸟,还剩几只鸟?"

# 使用OpenVINO优化过的模型进行加载，配置包括设备、性能提示及模型配置
ov_model = OVModelForCausalLM.from_pretrained(
    model_dir,
    device=DEVICE,
    ov_config=config,
    config=AutoConfig.from_pretrained(model_dir, trust_remote_code=True), # 加载模型配置，并信任远程代码
    trust_remote_code=True,
)

# 根据模型目录加载tokenizer，并信任远程代码
tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)

# 创建一个用于文本生成的pipeline，指定模型、分词器以及最多生成的新token数
pipe = pipeline("text-generation", model=ov_model, tokenizer=tok, max_new_tokens=50)

# 使用pipeline对问题进行推理
results = pipe(question)

# 打印生成的文本结果
print(results[0]['generated_text'])