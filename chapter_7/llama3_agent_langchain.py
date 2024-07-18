# 导入必要的库和模块
from langchain.agents import AgentExecutor, AgentType, ZeroShotAgent
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from pydantic import BaseModel, Field
from transformers.generation.stopping_criteria import StoppingCriteriaList, StoppingCriteria
import os

# 第一步：使用HuggingFacePipeline载入LLM，并设置停止条件
model_dir = r"D:\chapter_7\llama3_int4_ov"  # 设置LLM路径

# 定义序列停止生成判断标准的类
class StopSequenceCriteria(StoppingCriteria):
    """
    当遇到特定的令牌序列时，此类可以用于停止文本生成。

    参数:
        stop_sequences (`str` 或 `List[str]`):
            停止执行的序列（或序列列表）。
        tokenizer:
            用于解码模型输出的分词器。
    """

    # 构造函数初始化停止序列和分词器
    def __init__(self, stop_sequences, tokenizer):
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]
        self.stop_sequences = stop_sequences
        self.tokenizer = tokenizer

    # 调用方法检查输出是否包含停止序列
    def __call__(self, input_ids, scores, **kwargs) -> bool:
        decoded_output = self.tokenizer.decode(input_ids.tolist()[0])
        # 如果解码后的输出以任一停止序列结尾，则返回True，停止生成
        return any(decoded_output.endswith(stop_sequence) for stop_sequence in self.stop_sequences)
    
# 设置OpenVINO编译模型的配置参数，这里优先考虑低延迟    
ov_config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}
# 设定停止生成文本的标记，当模型输出这些标记时，会停止继续生成
stop_tokens = ["Observation:"]

# 从指定的模型目录加载模型到HuggingFacePipeline中
# 指定任务为文本生成（text-generation）
# 使用OpenVINO作为后端加速推理
# 设定模型参数，包括运行在GPU.1上，配置OpenVINO环境，允许信任远程代码
# 设置管道参数，最大新生成的token数量为2048
llama3 = HuggingFacePipeline.from_model_id(
    model_id=str(model_dir),
    task="text-generation",
    backend="openvino",
    model_kwargs={
        "device": "GPU.1",   # LLM的推理设备
        "ov_config": ov_config,
        "trust_remote_code": True,
    },
    pipeline_kwargs={"max_new_tokens": 2048},
)

# 绑定额外的参数到pipeline中，跳过提示，设定停止生成的序列
llama3 = llama3.bind(skip_prompt=True, stop=["Observation:"])
tokenizer = llama3.pipeline.tokenizer
llama3.pipeline._forward_params["stopping_criteria"] = StoppingCriteriaList([StopSequenceCriteria(stop_tokens, tokenizer)])

# 第二步：定义并封装天气查询工具
# 设置OpenWeatherMap API密钥: https://home.openweathermap.org/
os.environ['OPENWEATHERMAP_API_KEY'] = 'c6ed13df5cb08087275e0b65c7b19d85'

# 创建OpenWeatherMapAPIWrapper工具实例
weather_api = OpenWeatherMapAPIWrapper()

# 定义工具的输入参数
class WeatherInput(BaseModel):
    location: str = Field(..., description="The location for which to get the weather.")

# 将OpenWeatherMapAPIWrapper包装成LangChain的Tool
# 导入基础工具类
from langchain.tools.base import BaseTool

# 定义一个获取天气的工具类
class GetWeatherTool(BaseTool):
    # 工具名称
    name = "Get Weather"
    # 描述该工具的用途
    description = "Useful for getting the weather in a specific location."
    # 设置工具接受的参数模式，这里假设WeatherInput是一个定义好的数据类
    args_schema = WeatherInput

    # 定义同步执行方法，接收地点参数，返回天气API查询结果
    def _run(self, location: str):
        return weather_api.run(location)

    # 异步执行方法尚未实现，抛出异常
    async def _arun(self, location: str):
        raise NotImplementedError("This tool does not support async")

# 第三步：创建Agent，并将LLM和工具绑定到一起
# 创建Zero-Shot Agent实例，使用预定义的LLM和工具列表
agent = ZeroShotAgent.from_llm_and_tools(
    llm=llama3,                  # 预训练语言模型
    tools=[GetWeatherTool()],   # 工具列表，包含上面定义的GetWeatherTool
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION  # Agent类型为Zero-Shot
)

# 初始化Agent执行器，绑定Agent和工具，并设置详细输出和错误处理
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,                # 已创建的Agent实例
    tools=[GetWeatherTool()],  # 再次指定工具列表，确保Agent可以访问这些工具
    verbose=True,              # 开启详细输出
    handle_parsing_errors=True # 错误处理开关，开启后可以捕获并处理解析错误
)

# 第四步：运行Agent来查询天气
response = agent_executor.invoke("What's the weather like in Shanghai, CN?")
print(response)