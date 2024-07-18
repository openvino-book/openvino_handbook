import openvino_genai as ov_genai
# 指定llama3 INT4模型的本地路径
model_dir = r"D:\llama3_int4_ov"
# 实例化LLMPipeline
pipe = ov_genai.LLMPipeline(model_dir, "CPU")
# 输入的问题示例，可以更改
question = "In a tree, there are 7 birds. If 1 bird is shot, how many birds are left?"
# 生成问题的答案
print(pipe.generate(question, temperature=1.2, top_k=4, do_sample=True, max_new_tokens=100))