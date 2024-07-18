import torch
from transformers import (
    TextIteratorStreamer,
    StoppingCriteria,
    StoppingCriteriaList,
)
# 导入HuggingFacePipeline用于载入大语言模型，OpenVINOReranker用于文档重排序，OpenVINOBgeEmbeddings用于生成文本嵌入向量
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.document_compressors.openvino_rerank import OpenVINOReranker
from langchain_community.embeddings import OpenVINOBgeEmbeddings

# 设置路径
model_dir = r"D:\chapter_7\llama3_int4_ov"
rerank_model_dir = r"D:\chapter_7\bge-reranker-large_ov"
embedding_model_dir = r"D:\chapter_7\bge-small-en-v1.5_ov"

# 初始化OpenVINOReranker对象，指定模型路径、运行设备为CPU，并设置返回的最相关文档数量为2
reranker = OpenVINOReranker(
    model_name_or_path=rerank_model_dir,
    model_kwargs={"device": "CPU"},
    top_n=2,
)

# 初始化OpenVINOBgeEmbeddings对象，传入模型路径、模型参数和编码参数
embedding = OpenVINOBgeEmbeddings(
    model_name_or_path=embedding_model_dir,
    model_kwargs={"device": "CPU", "compile": True},
    encode_kwargs={ "mean_pooling": False,          # 不使用平均池化
                    "normalize_embeddings": True,   # 对嵌入向量进行归一化处理
                    "batch_size": 4,                # 批处理大小设为4
    },
)

# 设置OpenVINO编译模型的配置参数，这里优先考虑低延迟
ov_config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}
# 实例化HuggingFacePipeline类，并指定参数backend="openvino"
llama3 = HuggingFacePipeline.from_model_id(
    model_id=str(model_dir),
    task="text-generation",
    backend="openvino",
    model_kwargs={
        "device": "GPU",                  # LLM的推理设备为GPU
        "ov_config": ov_config,
        "trust_remote_code": True,
    },
    pipeline_kwargs={"max_new_tokens": 100},
)

# 导入类型注解库，用于指定函数参数和返回值的类型
from typing import List

# 从langchain.text_splitter模块导入多个文本分割器类，用于将长文本切分为更小的段落或句子
from langchain.text_splitter import (
    CharacterTextSplitter,          # 基于字符数进行分割
    RecursiveCharacterTextSplitter, # 基于递归方式分割，尝试找到最佳的分割点
    MarkdownTextSplitter,           # 专为Markdown格式文本设计的分割器
)

# 从langchain_community.document_loaders模块导入多个文档加载器类，用于读取不同格式的文件
from langchain_community.document_loaders import (
    CSVLoader,                      # 用于加载CSV文件
    EverNoteLoader,                 # 用于加载Evernote导出的.enex文件
    PyPDFLoader,                    # 用于加载PDF文件
    TextLoader,                     # 用于加载纯文本文件
    UnstructuredEPubLoader,         # 用于加载ePub电子书
    UnstructuredHTMLLoader,         # 用于加载HTML网页文件
    UnstructuredMarkdownLoader,     # 用于加载Markdown文件
    UnstructuredODTLoader,          # 用于加载OpenDocument文本(.odt)文件
    UnstructuredPowerPointLoader,   # 用于加载PowerPoint演示文稿
    UnstructuredWordDocumentLoader, # 用于加载Word文档(.doc, .docx)
)

# 定义一个字典，存储了各种文本分割器的名称与对应的类
TEXT_SPLITTERS = {
    "Character": CharacterTextSplitter,   # 字符分割器
    "RecursiveCharacter": RecursiveCharacterTextSplitter, # 递归字符分割器
    "Markdown": MarkdownTextSplitter,    # Markdown文本分割器
}

# 定义一个字典，存储了文件扩展名与对应的文档加载器类及其初始化参数
LOADERS = {
    ".csv": (CSVLoader, {}),             # CSV文件加载器
    ".doc": (UnstructuredWordDocumentLoader, {}), # Word文档(.doc)加载器
    ".docx": (UnstructuredWordDocumentLoader, {}), # Word文档(.docx)加载器
    ".enex": (EverNoteLoader, {}),       # Evernote导出文件加载器
    ".epub": (UnstructuredEPubLoader, {}), # ePub电子书加载器
    ".html": (UnstructuredHTMLLoader, {}), # HTML文件加载器
    ".md": (UnstructuredMarkdownLoader, {}), # Markdown文件加载器
    ".odt": (UnstructuredODTLoader, {}),     # OpenDocument文本(.odt)加载器
    ".pdf": (PyPDFLoader, {}),            # PDF文件加载器
    ".ppt": (UnstructuredPowerPointLoader, {}), # PowerPoint演示文稿(.ppt)加载器
    ".pptx": (UnstructuredPowerPointLoader, {}), # PowerPoint演示文稿(.pptx)加载器
    ".txt": (TextLoader, {"encoding": "utf8"}), # 纯文本文件加载器，指定编码为UTF-8
}

# 请从 https://arxiv.org/pdf/2303.18223
# 下载《A Survey of Large Language Models.pdf》到本地
text_example_path = r".\A Survey of Large Language Models.pdf"

# 范例问题
examples = [
    ["请总结一下A Survey of Large Language Models"],
]

# 导入PromptTemplate类，用于创建提示模板
from langchain.prompts import PromptTemplate
# 导入FAISS向量数据库，用于存储和检索文档向量
from langchain_community.vectorstores import FAISS
# 导入create_retrieval_chain函数，用于创建基于检索的链式处理流程
from langchain.chains.retrieval import create_retrieval_chain
# 导入create_stuff_documents_chain函数，用于创建处理文档合并的链式流程
from langchain.chains.combine_documents import create_stuff_documents_chain
# 导入Document类，表示单个文档
from langchain.docstore.document import Document
# 导入ContextualCompressionRetriever类，用于上下文压缩检索器
from langchain.retrievers import ContextualCompressionRetriever
# 导入Thread类，用于多线程操作
from threading import Thread
# 导入gradio库，用于创建交互式界面
import gradio as gr

# 定义停止令牌，用于在生成文本时识别终止点
stop_tokens = ["<|eot_id|>"]
# 默认的RAG（Retrieve-Augmented Generation）提示模板，用于指导模型如何回答问题
DEFAULT_RAG_PROMPT = """\
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\
"""
rag_prompt_template = f"<|start_header_id|>system<|end_header_id|>\n\n{DEFAULT_RAG_PROMPT}<|eot_id|>" + \
      """<|start_header_id|>user<|end_header_id|>

      Question: {input}
      Context: {context}
      Answer:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
      
      """

# 定义一个自定义的停止准则类，用于在生成过程中遇到特定的token时停止
class StopOnTokens(StoppingCriteria):
    def __init__(self, token_ids):
        # 初始化方法，存储需要停止的token的ID列表
        self.token_ids = token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # 调用方法，检查当前生成的token是否在停止列表中
        for stop_id in self.token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

# 如果stop_tokens不为空且其元素为字符串，则将其转换为token的ID列表
if stop_tokens is not None:
    if isinstance(stop_tokens[0], str):
        stop_tokens = llama3.pipeline.tokenizer.convert_tokens_to_ids(stop_tokens)

    # 创建停止准则实例并存储在stop_tokens变量中
    stop_tokens = [StopOnTokens(stop_tokens)]

# 定义load_single_document函数，用于加载单个文档
def load_single_document(file_path: str) -> List[Document]:
    """
    辅助函数，用于加载单个文档

    参数:
      file_path: 文档路径
    返回:
      加载后的文档列表
    """
    # 获取文件扩展名
    ext = "." + file_path.rsplit(".", 1)[-1]
    # 检查扩展名是否在LOADERS字典中
    if ext in LOADERS:
        # 获取对应的加载器类和参数
        loader_class, loader_args = LOADERS[ext]
        # 创建加载器实例并加载文档
        loader = loader_class(file_path, **loader_args)
        return loader.load()

    # 如果文件扩展名不在LOADERS中，抛出ValueError异常
    raise ValueError(f"File does not exist '{ext}'")

# 定义text_processor函数，用于处理部分生成的回答文本
def text_processor(partial_text: str, new_text: str):
    """
    辅助函数，用于更新部分生成的回答，作为默认处理方法

    参数:
      partial_text: 存储之前已生成文本的缓冲区
      new_text: 当前步骤新生成的文本
    返回:
      更新后的完整文本字符串
    """
    # 将新生成的文本追加到缓冲区中
    partial_text += new_text
    # 返回更新后的文本
    return partial_text


# 定义create_vectordb函数，用于初始化向量数据库
def create_vectordb(docs, spliter_name, chunk_size, chunk_overlap, vector_search_top_k, vector_search_top_n, run_rerank, search_method, score_threshold):
    """
    初始化向量数据库

    参数:
      docs: 用户提供的原始文档列表
      spliter_name: 分割器名称，用于确定文本分割策略
      chunk_size: 单个句子块的大小
      chunk_overlap: 两个句子块之间的重叠大小
      vector_search_top_k: 向量搜索的top-k值
      vector_search_top_n: 重新排序后保留的top-n值
      run_rerank: 是否执行重新排序步骤
      search_method: 向量存储使用的搜索方法
      score_threshold: 相似度得分阈值

    """
    # 初始化空的文档列表
    documents = []
    # 遍历所有原始文档，加载并扩展到documents列表
    for doc in docs:
        documents.extend(load_single_document(doc.name))

    # 使用指定的分隔器名称创建文本分割器实例
    text_splitter = TEXT_SPLITTERS[spliter_name](chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # 使用文本分割器将文档分割成更小的文本块
    texts = text_splitter.split_documents(documents)

    # 初始化全局变量db，使用FAISS向量数据库从文本块构建向量索引
    global db
    db = FAISS.from_documents(texts, embedding)

    # 初始化全局变量retriever，设置向量检索器
    global retriever
    if search_method == "similarity_score_threshold":
        # 如果搜索方法是基于相似度得分阈值的，设置相应的参数
        search_kwargs = {"k": vector_search_top_k, "score_threshold": score_threshold}
    else:
        # 否则，只设置top-k参数
        search_kwargs = {"k": vector_search_top_k}
    retriever = db.as_retriever(search_kwargs=search_kwargs, search_type=search_method)
    # 如果需要运行重新排序，创建上下文压缩检索器
    if run_rerank:
        reranker.top_n = vector_search_top_n
        retriever = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=retriever)
    # 初始化PromptTemplate实例
    prompt = PromptTemplate.from_template(rag_prompt_template)

    # 初始化全局变量combine_docs_chain，用于创建文档合并链
    global combine_docs_chain
    combine_docs_chain = create_stuff_documents_chain(llama3, prompt)

    # 初始化全局变量rag_chain，用于创建检索链
    global rag_chain
    rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

    # 返回数据库准备完成的消息
    return "Vector database is Ready"

# 定义update_retriever函数，用于更新检索器
def update_retriever(vector_search_top_k, vector_rerank_top_n, run_rerank, search_method, score_threshold):
    """
    更新检索器

    参数:
      vector_search_top_k: 搜索结果的数量
      vector_rerank_top_n: 重新排序结果的数量
      run_rerank: 是否执行重新排序步骤
      search_method: 向量存储使用的搜索方法
      score_threshold: 相似度得分阈值

    """
    # 初始化全局变量retriever和db
    global retriever
    global db
    # 初始化全局变量rag_chain和combine_docs_chain
    global rag_chain
    global combine_docs_chain

    # 根据搜索方法设置搜索参数
    if search_method == "similarity_score_threshold":
        search_kwargs = {"k": vector_search_top_k, "score_threshold": score_threshold}
    else:
        search_kwargs = {"k": vector_search_top_k}
    # 更新检索器
    retriever = db.as_retriever(search_kwargs=search_kwargs, search_type=search_method)
    # 如果需要运行重新排序，创建上下文压缩检索器并更新reranker的top_n参数
    if run_rerank:
        retriever = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=retriever)
        reranker.top_n = vector_rerank_top_n
    # 重新创建检索链
    rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

# 定义user函数，用于处理用户消息提交事件
def user(message, history):
    """
    用户界面提交按钮点击时的回调函数，用于更新用户消息

    参数:
      message: 当前消息
      history: 对话历史记录

    返回:
      无返回值，但会修改history变量以包含新的对话条目

    """
    # 将用户的消息添加到对话历史记录中，同时预留一个空字符串作为助手的回应位置
    return "", history + [[message, ""]]


# 定义bot函数，用于处理聊天机器人的消息生成逻辑
def bot(history, temperature, top_p, top_k, repetition_penalty, hide_full_prompt, do_rag):
    """
    在提交按钮点击时运行聊天机器人的回调函数

    参数:
      history: 对话历史记录
      temperature: 控制AI生成文本创造性的参数。
                   通过调整`temperature`，可以影响AI模型的概率分布，使文本更加聚焦或多样化。
      top_p: 基于累积概率控制AI模型考虑的标记范围的参数。
      top_k: 基于累积概率选择最高概率的标记数量，从而控制AI模型考虑的标记范围的参数。
      repetition_penalty: 基于文本中出现频率对标记进行惩罚的参数。
      hide_full_prompt: 是否在prompt中隐藏搜索结果。
      do_rag: 在生成文本时是否执行RAG（Retrieve-Augmented Generation）。

    """
    # 创建TextIteratorStreamer实例，用于流式处理生成的文本
    streamer = TextIteratorStreamer(
        llama3.pipeline.tokenizer,  # 使用的tokenizer实例
        timeout=60.0,               # 流式处理超时时间
        skip_prompt=hide_full_prompt, # 是否跳过prompt
        skip_special_tokens=True,   # 是否跳过特殊标记
    )
    # 设置llama3.pipeline的_forward_params属性，用于控制文本生成过程中的参数
    llama3.pipeline._forward_params = dict(
        max_new_tokens=512,         # 最大生成的新标记数量
        temperature=temperature,    # 温度参数
        do_sample=temperature > 0.0,# 是否采用随机采样
        top_p=top_p,                # top-p参数
        top_k=top_k,                # top-k参数
        repetition_penalty=repetition_penalty, # 重复惩罚参数
        streamer=streamer,          # 流式处理器实例
    )
    # 如果stop_tokens非空，设置stopping_criteria参数，用于控制文本生成的停止条件
    if stop_tokens is not None:
        llama3.pipeline._forward_params["stopping_criteria"] = StoppingCriteriaList(stop_tokens)

    # 判断是否执行RAG，根据do_rag参数决定调用rag_chain.invoke还是llama3.invoke
    if do_rag:
        # 使用rag_chain.invoke异步处理RAG，传入对话历史记录的最后一条用户输入
        t1 = Thread(target=rag_chain.invoke, args=({"input": history[-1][0]},))
    else:
        # 格式化输入文本，如果do_rag为False，则直接使用用户输入，context设为空字符串
        input_text = rag_prompt_template.format(input=history[-1][0], context="")
        t1 = Thread(target=llama3.invoke, args=(input_text,))
    # 启动异步处理线程
    t1.start()

    # 初始化一个空字符串，用于存储生成的文本
    partial_text = ""
    # 循环遍历流式处理器产生的新文本
    for new_text in streamer:
        # 调用text_processor函数处理部分生成的文本和新生成的文本
        partial_text = text_processor(partial_text, new_text)
        # 更新对话历史记录中最后一条记录的助手回应
        history[-1][1] = partial_text
        # 生成一个迭代器，用于yield每次更新后的对话历史记录
        yield history


# 定义取消请求的函数
def request_cancel():
    llama3.pipeline.model.request.cancel()

# 使用gradio创建界面
with gr.Blocks(
    theme=gr.themes.Soft(),  # 设置主题样式
    css=".disclaimer {font-variant-caps: all-small-caps;}",  # 自定义CSS样式
) as demo:
    # 添加标题
    gr.Markdown("""<h1><center>Local RAG System on your AIPC</center></h1>""")
    gr.Markdown(f"""<center>Powered by LangChain + OpenVINO + Llama3 </center>""")
    
    # 创建行布局
    with gr.Row():
        # 创建左侧列布局
        with gr.Column(scale=1):
            # 文件上传组件
            docs = gr.File(
                label="Step 1: Load text files",  # 组件标签
                value=[text_example_path],  # 默认值
                file_count="multiple",  # 允许多个文件
                file_types=[
                    ".csv", ".doc", ".docx", ".enex", ".epub", ".html", ".md", ".odt", ".pdf", ".ppt", ".pptx", ".txt"
                ],  # 允许的文件类型
            )
            # 构建向量库按钮
            load_docs = gr.Button("Step 2: Build Vector Store")
            # 向量库配置组件
            db_argument = gr.Accordion("Vector Store Configuration", open=False)
            with db_argument:
                # 文本分词器下拉菜单
                spliter = gr.Dropdown(
                    ["Character", "RecursiveCharacter", "Markdown", "Chinese"],
                    value="RecursiveCharacter",
                    label="Text Spliter",
                    info="Method used to splite the documents",
                    multiselect=False,
                )
                # 分块大小滑动条
                chunk_size = gr.Slider(
                    label="Chunk size",
                    value=400,
                    minimum=50,
                    maximum=2000,
                    step=50,
                    interactive=True,
                    info="Size of sentence chunk",
                )
                # 分块重叠滑动条
                chunk_overlap = gr.Slider(
                    label="Chunk overlap",
                    value=50,
                    minimum=0,
                    maximum=400,
                    step=10,
                    interactive=True,
                    info=("Overlap between 2 chunks"),
                )
            
            # 向量库状态文本框
            langchain_status = gr.Textbox(
                label="Vector Store Status",
                value="Vector Store is Not ready",
                interactive=False,
            )
            # RAG开关
            do_rag = gr.Checkbox(
                value=True,
                label="RAG is ON",
                interactive=True,
                info="Whether to do RAG for generation",
            )
            # 生成配置组件
            with gr.Accordion("Generation Configuration", open=False):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            # 温度滑动条
                            temperature = gr.Slider(
                                label="Temperature",
                                value=0.1,
                                minimum=0.0,
                                maximum=1.0,
                                step=0.1,
                                interactive=True,
                                info="Higher values produce more diverse outputs",
                            )
                    with gr.Column():
                        with gr.Row():
                            # Top-p滑动条
                            top_p = gr.Slider(
                                label="Top-p (nucleus sampling)",
                                value=1.0,
                                minimum=0.0,
                                maximum=1,
                                step=0.01,
                                interactive=True,
                                info=(
                                    "Sample from the smallest possible set of tokens whose cumulative probability "
                                    "exceeds top_p. Set to 1 to disable and sample from all tokens."
                                ),
                            )
                    with gr.Column():
                        with gr.Row():
                            # Top-k滑动条
                            top_k = gr.Slider(
                                label="Top-k",
                                value=50,
                                minimum=0.0,
                                maximum=200,
                                step=1,
                                interactive=True,
                                info="Sample from a shortlist of top-k tokens — 0 to disable and sample from all tokens.",
                            )
                    with gr.Column():
                        with gr.Row():
                            # 重复惩罚滑动条
                            repetition_penalty = gr.Slider(
                                label="Repetition Penalty",
                                value=1.1,
                                minimum=1.0,
                                maximum=2.0,
                                step=0.1,
                                interactive=True,
                                info="Penalize repetition — 1.0 to disable.",
                            )
        # 创建右侧列布局
        with gr.Column(scale=4):
            # 聊天机器人组件
            chatbot = gr.Chatbot(
                height=600,
                label="Step 3: Input Query",
            )
            # 消息输入组件
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        msg = gr.Textbox(
                            label="QA Message Box",
                            placeholder="Chat Message Box",
                            show_label=False,
                            container=False,
                        )
                # 按钮组件
                with gr.Column():
                    with gr.Row():
                        submit = gr.Button("Submit")
                        stop = gr.Button("Stop")
                        clear = gr.Button("Clear")
            # 示例输入
            gr.Examples(examples, inputs=msg, label="Click on any example and press the 'Submit' button")
            # 检索器配置组件
            retriever_argument = gr.Accordion("Retriever Configuration", open=True)
            with retriever_argument:
                with gr.Row():
                    with gr.Row():
                        do_rerank = gr.Checkbox(
                            value=True,
                            label="Rerank searching result",
                            interactive=True,
                        )
                        hide_context = gr.Checkbox(
                            value=True,
                            label="Hide searching result in prompt",
                            interactive=True,
                        )
                    with gr.Row():
                        search_method = gr.Dropdown(
                            ["similarity_score_threshold", "similarity", "mmr"],
                            value="similarity_score_threshold",
                            label="Searching Method",
                            info="Method used to search vector store",
                            multiselect=False,
                            interactive=True,
                        )
                    with gr.Row():
                        score_threshold = gr.Slider(
                            0.01,
                            0.99,
                            value=0.5,
                            step=0.01,
                            label="Similarity Threshold",
                            info="Only working for 'similarity score threshold' method",
                            interactive=True,
                        )
                    with gr.Row():
                        vector_rerank_top_n = gr.Slider(
                            1,
                            10,
                            value=2,
                            step=1,
                            label="Rerank top n",
                            info="Number of rerank results",
                            interactive=True,
                        )
                    with gr.Row():
                        vector_search_top_k = gr.Slider(
                            1,
                            50,
                            value=10,
                            step=1,
                            label="Search top k",
                            info="Number of searching results, must >= Rerank top n",
                            interactive=True,
                        )
    
    # 事件绑定
    load_docs.click(  # 点击构建向量库按钮触发事件
        create_vectordb,
        inputs=[docs, spliter, chunk_size, chunk_overlap, vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
        outputs=[langchain_status],
        queue=False,
    )
    submit_event = msg.submit(  # 提交消息触发事件
        user,
        [msg, chatbot],
        [msg, chatbot],
        queue=False,
    ).then(
        bot,
        [chatbot, temperature, top_p, top_k, repetition_penalty, hide_context, do_rag],
        chatbot,
        queue=True,
    )
    submit_click_event = submit.click(  # 点击提交按钮触发事件
        user,
        [msg, chatbot],
        [msg, chatbot],
        queue=False,
    ).then(
        bot,
        [chatbot, temperature, top_p, top_k, repetition_penalty, hide_context, do_rag],
        chatbot,
        queue=True,
    )
    stop.click(  # 点击停止按钮触发事件
        fn=request_cancel,
        inputs=None,
        outputs=None,
        cancels=[submit_event, submit_click_event],
        queue=False,
    )
    clear.click(  # 点击清空按钮触发事件
        lambda: None,
        None,
        chatbot,
        queue=False,
    )
    vector_search_top_k.release(  # 更改搜索结果数量触发事件
        update_retriever,
        [vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
    )
    vector_rerank_top_n.release(  # 更改重新排序结果数量触发事件
        update_retriever,
        [vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
    )
    do_rerank.change(  # 开关重新排序触发事件
        update_retriever,
        [vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
    )
    search_method.change(  # 更改搜索方法触发事件
        update_retriever,
        [vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
    )
    score_threshold.change(  # 更改相似度阈值触发事件
        update_retriever,
        [vector_search_top_k, vector_rerank_top_n, do_rerank, search_method, score_threshold],
    )

# 启用队列并启动Gradio应用
demo.queue()
demo.launch()