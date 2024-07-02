# 导入HuggingFacePipeline类
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline

# 指定Qwen2-1.5B-Instruct int4模型的本地路径
model_dir = r"D:\chapter_5\qwen2-1.5b-instruct_int4"

# 设定推理设备为CPU，可根据实际情况改为"GPU"或"AUTO"
DEVICE = "CPU"

# 设置OpenVINO编译模型的配置参数，这里优先考虑低延迟
ov_config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}

# 输入的问题示例，可以更改
question = "树上7只鸟,打死1只鸟,还剩几只鸟?"

# 实例化HuggingFacePipeline类，并指定参数backend="openvino"
qwen2 = HuggingFacePipeline.from_model_id(
    model_id=str(model_dir),
    task="text-generation",
    backend="openvino",
    model_kwargs={
        "device": DEVICE,
        "ov_config": ov_config,
        "trust_remote_code": True,
    },
    pipeline_kwargs={"max_new_tokens": 100},
)
# 显示推理结果
print(qwen2.invoke(question))