# 导入所需库
import nncf
import openvino as ov 
from ultralytics import YOLO
from ultralytics.data.utils import DATASETS_DIR
from ultralytics.utils import DEFAULT_CFG
from ultralytics.cfg import get_cfg
from ultralytics.data.converter import coco80_to_coco91_class
from ultralytics.data.utils import check_det_dataset
from multiprocessing import freeze_support

def main():

    # 初始化YOLOv8检测模型的对象
    yolov8_dir = r"D:\chapter_3\yolov8s.pt"
    det_model = YOLO(yolov8_dir, task="detect")
    args = get_cfg(cfg=DEFAULT_CFG)
    args.data = str(DATASETS_DIR/ "coco.yaml")
    # 初始化验证器对象并进行相关配置
    det_validator = det_model.task_map[det_model.task]["validator"](args=args)
    det_validator.data = check_det_dataset(args.data)
    det_validator.stride = 32
    det_validator.is_coco = True                        # 使用COCO数据集格式
    det_validator.class_map = coco80_to_coco91_class()  # 类别映射从COCO80到COCO91
    det_validator.names = det_model.model.names         # 获取类别名称列表
    det_validator.metrics.names = det_validator.names   # 设置评估指标的类别名称
    det_validator.nc = det_model.model.model[-1].nc     # 获取模型输出的类别数

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
            data_item: 迭代过程中由DataLoader产生的数据项字典
        返回:
            input_tensor: 用于量化的输入数据
        """
        input_tensor = det_validator.preprocess(data_item)['img'].numpy()
        return input_tensor


    # Step 2: 准备校准数据集
    # 获得COCO验证数据集的数据加载器
    det_data_loader = det_validator.get_dataloader(DATASETS_DIR / "coco", 1)
    # 创建校准数据集对象
    calibration_dataset = nncf.Dataset(det_data_loader, transform_fn)

    # Step 3: 执行INT8量化
    ignored_scope = nncf.IgnoredScope(types=["Multiply", "Subtract", "Sigmoid", "Swish"])

    quantized_model = nncf.quantize(
        ov_model,
        calibration_dataset,
        preset=nncf.QuantizationPreset.MIXED,  # 使用混合量化预设
        ignored_scope=ignored_scope
    )

    # Step 4: 保存INT8量化好的模型
    ov.save_model(quantized_model, "yolov8s_int8.xml")

if __name__ == '__main__':
    freeze_support()   # 支持在Windows下多进程运行
    main()


