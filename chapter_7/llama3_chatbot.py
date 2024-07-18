# 导入必要的库和模块
from transformers import AutoConfig, AutoTokenizer, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer
from optimum.intel.openvino import OVModelForCausalLM
import torch
from threading import Event, Thread
from uuid import uuid4
from typing import List, Tuple
import gradio as gr

# 设置OpenVINO编译模型的配置参数，这里优先考虑低延迟
config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}
# 指定llama3 INT4模型的本地路径
model_dir = r"D:\llama3_int4_ov"
# 设定推理设备为CPU，可根据实际情况改为"GPU"或"AUTO"
DEVICE = "CPU"

# 编译并载入Llama3模型到指定DEVICE
ov_model = OVModelForCausalLM.from_pretrained(
    model_dir,
    device=DEVICE,
    ov_config=config,
    config=AutoConfig.from_pretrained(model_dir, trust_remote_code=True),
    trust_remote_code=True,
)

# 初始化Llama3模型的分词器
tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
# 定义Llama3的多轮对话消息模板
# refer to: https://github.com/meta-llama/llama-recipes
model_name = "Meta-Llama-3-8B-Instruct"
start_message = f" <|start_header_id|>system<|end_header_id|>\n\n" + "" + "<|eot_id|>"
# 对话历史记录的模板定义
history_template = "<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{assistant}<|eot_id|>"
current_message_template = "<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{assistant}"
# 停止生成的特殊标记
stop_tokens = ["<|eot_id|>"]
tokenizer_kwargs = {}
# 示例对话输入
examples = [
    ["Hi there, How are you?"],
    ["In a tree, there are 7 birds. If 1 bird is shot, how many birds are left?"],
]
# 最大生成的新token数
max_new_tokens = 200

# 自定义停止条件类，当生成的token匹配到停止序列时终止生成
class StopOnTokens(StoppingCriteria):
    def __init__(self, token_ids):
        self.token_ids = token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

# 如果设置了停止标记，将其转换为对应的ID
if stop_tokens is not None:
    if isinstance(stop_tokens[0], str):
        stop_tokens = tok.convert_tokens_to_ids(stop_tokens)

    stop_tokens = [StopOnTokens(stop_tokens)]

# 默认的部分文本处理器，用于累积和更新生成的文本
def default_partial_text_processor(partial_text: str, new_text: str):

    partial_text += new_text
    return partial_text


text_processor = default_partial_text_processor

# 将对话历史转换为模型所需的token格式
def convert_history_to_token(history: List[Tuple[str, str]]):

    if history_template is None:
        # 构建消息结构，包含系统消息和历史对话
        messages = [{"role": "system", "content": start_message}]
        for idx, (user_msg, model_msg) in enumerate(history):
            if idx == len(history) - 1 and not model_msg: # 如果是最新一轮且模型尚未回复
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})

        input_token = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_tensors="pt")
    else:
        # 根据模板构造文本，并转换为token
        text = start_message + "".join(
            ["".join([history_template.format(num=round, user=item[0], assistant=item[1])]) for round, item in enumerate(history[:-1])]
        )
        text += "".join(
            [
                "".join(
                    [
                        current_message_template.format(
                            num=len(history) + 1,
                            user=history[-1][0],
                            assistant=history[-1][1],
                        )
                    ]
                )
            ]
        )
        input_token = tok(text, return_tensors="pt", **tokenizer_kwargs).input_ids
    return input_token

# 用户消息处理回调函数，用于在界面上添加用户的消息到对话历史
def user(message, history):
    
    # 将用户的消息添加到对话历史的末尾，并清空模型回复
    return "", history + [[message, ""]]


def bot(history, temperature, top_p, top_k, repetition_penalty, conversation_id):
    """
    回调函数，用于在用户点击提交按钮后运行聊天机器人。

    参数：
      history: 对话历史，包含了用户与AI之前的交互记录。
      temperature: 控制AI生成文本的创造性程度。调整此值可以影响模型的概率分布，使文本更集中或更多样化。
      top_p: 控制AI模型基于累计概率考虑的tokens范围，用于 nucleus 抽样策略。
      top_k: 控制AI模型基于累计概率考虑的最可能的tokens数量，用于top-k抽样策略。
      repetition_penalty: 对重复出现的tokens施加惩罚，以减少冗余。
      conversation_id: 唯一的会话标识符，用于区分不同用户的对话。
    """

    # 构建输入模型的消息字符串，通过连接当前系统消息和对话历史，然后对消息进行分词
    input_ids = convert_history_to_token(history)
    # 如果输入过长，则仅保留最近的一轮对话并重新构建输入
    if input_ids.shape[1] > 2000:
        history = [history[-1]]
        input_ids = convert_history_to_token(history)

    # 初始化一个文本流生成器，用于实时输出生成的文本
    streamer = TextIteratorStreamer(tok, timeout=30.0, skip_prompt=True, skip_special_tokens=True)
    # 准备生成文本的参数字典
    generate_kwargs = dict(
        input_ids=input_ids,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=temperature > 0.0,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        streamer=streamer,
    )
    # 如果有停止标记，则添加到生成参数中
    if stop_tokens is not None:
        generate_kwargs["stopping_criteria"] = StoppingCriteriaList(stop_tokens)
    
    # 初始化事件，用于指示生成完成
    stream_complete = Event()

    def generate_and_signal_complete():
        """单线程生成函数，执行模型生成操作并在完成后设置事件"""
        global start_time
        ov_model.generate(**generate_kwargs)
        stream_complete.set()

    # 启动生成操作的线程
    t1 = Thread(target=generate_and_signal_complete)
    t1.start()

    # 初始化一个空字符串来存储逐步生成的文本
    partial_text = ""
    # 从流生成器中逐块读取新生成的文本并处理
    for new_text in streamer:
        partial_text = text_processor(partial_text, new_text)
        # 更新对话历史中的最后一轮对话的AI回复部分
        history[-1][1] = partial_text
        # 产出更新后的对话历史
        yield history


def request_cancel():
    """请求取消当前的生成任务"""
    ov_model.request.cancel()


def get_uuid():
    """生成一个通用唯一标识符，用于线程标识"""
    return str(uuid4())

# 使用Gradio构建交互式界面
with gr.Blocks(
    theme=gr.themes.Soft(),
    css=".disclaimer {font-variant-caps: all-small-caps;}",
) as demo:
    # 初始化会话ID状态
    conversation_id = gr.State(get_uuid)
    # 显示对话框页面标题
    gr.Markdown(f"""<h1><center>Llama3 Chatbot based on OpenVINO and Gradio</center></h1>""")
    # 创建聊天机器人的UI组件
    chatbot = gr.Chatbot(height=500)
    # 消息输入框及控制按钮布局
    with gr.Row():
        with gr.Column():
            msg = gr.Textbox(
                label="聊天消息框",
                placeholder="在这里输入你的消息...",
                show_label=False,
                container=False,
            )
        with gr.Column():
            with gr.Row():
                submit = gr.Button("提交")
                stop = gr.Button("停止")
                clear = gr.Button("清除")
    with gr.Row():
        with gr.Accordion("高级选项:", open=False):
            with gr.Row():
                # 温度、top-p、top-k、重复惩罚等参数滑块
                with gr.Column():
                    with gr.Row():
                        temperature = gr.Slider(
                            label="Temperature",
                            value=0.1,
                            minimum=0.0,
                            maximum=1.0,
                            step=0.1,
                            interactive=True,
                            info="较高值产生更多样化的输出",
                        )
                with gr.Column():
                    with gr.Row():
                        top_p = gr.Slider(
                            label="Top-p (nucleus sampling)",
                            value=1.0,
                            minimum=0.0,
                            maximum=1,
                            step=0.01,
                            interactive=True,
                            info=(
                                "从累计概率超过top-p的最小可能的tokens集合中采样"
                                "超过top_p. 设置为1: 禁止从所有tokens中采样."
                            ),
                        )
                with gr.Column():
                    with gr.Row():
                        top_k = gr.Slider(
                            label="Top-k",
                            value=50,
                            minimum=0.0,
                            maximum=200,
                            step=1,
                            interactive=True,
                            info="从top-k个最可能的tokens中采样.",
                        )
                with gr.Column():
                    with gr.Row():
                        repetition_penalty = gr.Slider(
                            label="Repetition Penalty",
                            value=1.1,
                            minimum=1.0,
                            maximum=2.0,
                            step=0.1,
                            interactive=True,
                            info="对重复进行惩罚.",
                        )
    # 添加示例对话
    gr.Examples(examples, inputs=msg, label="点击任一示例并按下 提交 按钮")
    # 消息框提交事件处理
    submit_event = msg.submit(
        fn=user,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False,
    ).then(
        fn=bot,
        inputs=[
            chatbot,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            conversation_id,
        ],
        outputs=chatbot,
        queue=True,
    )
    submit_click_event = submit.click(
        fn=user,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False,
    ).then(
        fn=bot,
        inputs=[
            chatbot,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            conversation_id,
        ],
        outputs=chatbot,
        queue=True,
    )
    # 停止按钮事件处理，取消当前的生成任务
    stop.click(
        fn=request_cancel,
        inputs=None,
        outputs=None,
        cancels=[submit_event, submit_click_event],
        queue=False,
    )
    # 清除按钮事件处理，清空聊天记录
    clear.click(lambda: None, None, chatbot, queue=False)

# 启动Gradio应用
demo.launch()