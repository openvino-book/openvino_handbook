# 导入所需库
import nncf, torch
import openvino as ov 
from ultralytics import YOLO
from ultralytics.data.utils import DATASETS_DIR
from ultralytics.utils import DEFAULT_CFG
from ultralytics.cfg import get_cfg
from ultralytics.data.converter import coco80_to_coco91_class
from ultralytics.data.utils import check_det_dataset
from ultralytics.utils.metrics import ConfusionMatrix
from ultralytics.engine.validator import BaseValidator as Validator
from ultralytics.utils import ops
from multiprocessing import freeze_support
from functools import partial

def main():

    # 初始化YOLOv8检测模型的对象
    yolov8_dir = r"D:\chapter_3\yolov8s.pt"
    model = YOLO(yolov8_dir, task="detect")
    args = get_cfg(cfg=DEFAULT_CFG)
    args.data = str(DATASETS_DIR/ "coco128.yaml")

    # 初始化验证器对象并进行相关配置
    validator = model.task_map[model.task]["validator"](args=args)
    validator.data = check_det_dataset(args.data)
    dataset = validator.data["val"]
    print(f"{dataset}")

    validator.stride = 32
    validator.is_coco = True
    validator.class_map = coco80_to_coco91_class()
    validator.names = model.model.names
    validator.metrics.names = validator.names
    validator.nc = model.model.model[-1].nc
    validator.nm = 32

    # 加载FP32格式的YOLOv8 IR模型
    ov_model_dir = r"D:\chapter_3\yolov8s.xml"
    core = ov.Core()
    ov_model = core.read_model(ov_model_dir)

    # Step 1: 编写转换函数
    from typing import Dict
    def transform_fn(data_item:Dict):
        """
        量化转换函数。从数据加载器项中提取并预处理输入数据以进行量化。
        参数:
            data_item: 迭代过程中由ultralytics Dataset对象返回"label"的字典
            图像数据由关键字'img'来索引，参考：
            ultralytics/data/base.py#L249
        返回:
            input_tensor: 用于量化的输入数据
        """
        input_tensor = validator.preprocess(data_item)['img'].numpy()
        return input_tensor

    # Step 2: 准备校准数据集和验证数据集
    # 获得COCO验证数据集的数据加载器
    det_data_loader = validator.get_dataloader(DATASETS_DIR / "coco128", 1)
    # 创建校准数据集和验证数据集
    calibration_dataset = nncf.Dataset(det_data_loader, transform_fn)
    validation_dataset = nncf.Dataset(det_data_loader, transform_fn)

    # Step 3: 准备验证函数
    def validate(model: ov.CompiledModel,          
                 validation_loader: torch.utils.data.DataLoader) -> float:  
        """
        此函数用于验证已训练模型在验证数据集上的性能:即mAP50-95(平均精度,当IoU阈值从50%到95%)指标。
        
        参数:
        - model: 经过OpenVINO编译优化的模型,用于执行推理计算。
        - validation_loader: 使用PyTorch的数据加载器,它负责加载验证集的数据。
        
        返回:
        - mAP50_95: 验证集上的平均精度。
        
        函数执行步骤:
        1. 初始化验证器内部的一些计数器和数据结构，如已处理的样本数、预测记录、统计信息等。
        2. 初始化混淆矩阵，用于分类任务的性能评估。
        3. 遍历验证数据加载器中的每一个数据批次:
        a. 对批次数据进行预处理，准备输入模型所需的格式。
        b. 使用OpenVINO模型进行推理计算,得到预测结果。
        c. 将预测结果转换为PyTorch张量,并进行后处理,以便进一步分析。
        d. 更新验证指标,如:TP等。
        4. 计算并收集所有批次的统计数据。
        5. 计算并打印mAP50-95指标。
        6. 返回mAP50-95作为函数的结果。
        """
        
        validator.seen = 0           # 初始化已处理样本计数
        validator.jdict = []         # 初始化预测记录列表
        validator.stats = dict(tp=[], conf=[], pred_cls=[], target_cls=[])  # 初始化统计字典
        validator.batch_i = 1        # 初始化批次计数
        validator.confusion_matrix = ConfusionMatrix(nc=validator.nc)  # 初始化混淆矩阵，nc为类别数
        
        counter = 0                # 记录数据批次计数
        for batch in validation_loader:  # 遍历验证数据批次
            batch = validator.preprocess(batch)  # 数据预处理
            results = model(batch["img"].numpy())  # 使用模型进行推理，获取numpy数组形式的预测结果
            preds = torch.from_numpy(results[model.output(0)])  # 将预测结果转换为PyTorch张量
            preds = validator.postprocess(preds)  # 后处理预测结果
            validator.update_metrics(preds, batch)  # 更新验证指标
            counter += 1  # 增加批次计数
        
        stats = validator.get_stats()  # 获取所有批次的汇总统计信息
        mAP50_95 = stats["metrics/mAP50-95(B)"]  # 提取mAP50-95指标
        print(f"Validate: dataset length = {counter}, metric value = {mAP50_95:.3f}")  # 打印验证信息
        return mAP50_95  # 返回mAP50-95指标

    # Step 4: 执行带精度控制的INT8量化
    ignored_scope = nncf.IgnoredScope(types=["Multiply", "Subtract", "Sigmoid", "Swish"])

    quantized_model_ac = nncf.quantize_with_accuracy_control(
            ov_model,
            calibration_dataset,
            validation_dataset,
            validation_fn=validate,
            max_drop=0.005,
            drop_type=nncf.DropType.ABSOLUTE,
            preset=nncf.QuantizationPreset.MIXED,
            ignored_scope=ignored_scope
    )

    # Step 5: 保存INT8量化好的模型
    ov.save_model(quantized_model_ac, "yolov8s_int8_ac.xml")

if __name__ == '__main__':
    freeze_support()   # 支持在Windows下多进程运行
    main()


