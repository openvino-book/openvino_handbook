# 导入OpenVINOReranker用于文档重排序，以及OpenVINOBgeEmbeddings用于生成文本嵌入向量
from langchain_community.document_compressors.openvino_rerank import OpenVINOReranker
from langchain_community.embeddings import OpenVINOBgeEmbeddings

# 设置重排序模型的目录路径
rerank_model_dir = r"D:\chapter_7\bge-reranker-large_ov"

# 初始化OpenVINOReranker对象，指定模型路径、运行设备为CPU，并设置返回的最相关文档数量为2
reranker = OpenVINOReranker(
    model_name_or_path=rerank_model_dir,
    model_kwargs={"device": "CPU"},
    top_n=2,
)

# 设置嵌入模型的目录路径
embedding_model_dir = r"D:\chapter_7\bge-small-en-v1.5_ov"

# 定义嵌入模型的运行参数，包括设备为CPU，启用编译优化，以及编码时的一些选项
embedding_model_kwargs = {"device": "CPU", "compile": True}
encode_kwargs = {
    "mean_pooling": False,          # 不使用平均池化
    "normalize_embeddings": True,   # 对嵌入向量进行归一化处理
    "batch_size": 4,                # 批处理大小设为4
}

# 初始化OpenVINOBgeEmbeddings对象，传入模型路径、模型参数和编码参数
embedding = OpenVINOBgeEmbeddings(
    model_name_or_path=embedding_model_dir,
    model_kwargs=embedding_model_kwargs,
    encode_kwargs=encode_kwargs,
)

# 定义待处理的文本
text = "This is a test document."

# 使用定义好的嵌入模型对文本进行嵌入向量计算
embedding_result = embedding.embed_query(text)

# 打印嵌入向量的前三个元素
print(embedding_result[:3])