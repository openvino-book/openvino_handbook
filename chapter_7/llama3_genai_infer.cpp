#include "openvino/genai/llm_pipeline.hpp"
#include <iostream>

int main(int argc, char* argv[]) {
    std::string model_path = "D:/llama3_int4_ov";  // 指定llama3 INT4模型的本地路径
    // 输入的问题示例，可以更改
    std::string question = "In a tree, there are 7 birds. If 1 bird is shot, how many birds are left?";
    // 实例化LLMPipeline类
    ov::genai::LLMPipeline pipe(model_path, "CPU");

    // 配置生成内容时的超参数
    ov::genai::GenerationConfig config;
    config.temperature = 1.2;
    config.top_k = 4;
    config.do_sample = true;
    config.max_new_tokens = 100;     
    // 生成问题的答案
    std::cout << pipe.generate(question, config); 
}