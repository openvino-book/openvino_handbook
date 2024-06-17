# 导入所需模块
import matplotlib
matplotlib.use("TkAgg")
print("TkAgg")
from multiprocessing import freeze_support
from pathlib import Path
from matplotlib import pyplot as plt

from anomalib.data import MVTec       # MVTec 数据加载模块，用于处理来自 MVTec AD 数据集的任务
from anomalib.models import Padim     # Padim 模型模块，实现 Padim 算法的模型定义
from anomalib.engine import Engine    # Engine 引擎模块，负责模型的训练、评估等流程控制
from anomalib.deploy import OpenVINOInferencer, ExportType
from anomalib import TaskType


def main():

    # 初始化数据模块、模型及引擎
    datamodule = MVTec(num_workers=0)  # 创建 MVTec 数据模块实例，用于数据的准备和加载
    datamodule.prepare_data()  # 如果指定的根目录中没有数据集，此方法将下载 MVTec AD 数据集
    datamodule.setup()  # 根据数据集配置，建立训练集、验证集、测试集及预测所需的各类数据集

    # 初始化模型及引擎
    model = Padim()  # 实例化 Patchcore 模型，用于异常检测任务
    engine = Engine(task=TaskType.SEGMENTATION)  # 创建 Engine 实例，用于驱动模型的训练和评估流程

    # 训练模型:使用数据模块和模型，启动训练流程。此步骤将执行模型的训练直至完成
    engine.fit(datamodule=datamodule, model=model) 

    # 在进行评估之前，从检查点加载最佳模型
    # 这里使用了Engine的test方法来进行模型评估
    test_results = engine.test(
        model=model,           # 指定要测试的模型
        datamodule=datamodule, # 提供数据模块，用于获取测试所需的数据
        ckpt_path=engine.trainer.checkpoint_callback.best_model_path,
    )
    print(f"model test results:{test_results}")

    # 导出OpenVINO IR格式模型
    engine.export(
        model=model,
        export_type=ExportType.OPENVINO,
        )
    
    # 指定图像路径
    image_path = r"d:/chapter_6/datasets/MVTec/bottle/test/broken_large/002.png"
    
    # 载入模型
    output_path = Path(engine.trainer.default_root_dir)
    openvino_model_path = output_path / "weights" / "openvino" / "model.bin"
    metadata = output_path / "weights" / "openvino" / "metadata.json"
    inferencer = OpenVINOInferencer(
        path=openvino_model_path,   # 指定OpenVINO IR模型路径.
        metadata=metadata,          # 指定metadata路径
        device="CPU",               # 指定推理设备.
        )
    
    # 执行推理计算
    predictions = inferencer.predict(image=image_path)

    # 输出推理结果
    print(predictions.pred_score, predictions.pred_label)

    # 可视化推理结果
    plt.imshow(predictions.segmentations)
    plt.show()


if __name__ == '__main__':
    freeze_support()
    main()