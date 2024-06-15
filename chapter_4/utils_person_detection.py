import cv2
import numpy as np

def preprocess(image, target_shape):
    """
    定义输入数据的预处理函数

    :param image: 原始输入帧
    :param target_shape: 目标尺寸，用于调整图像大小
    :return resized_image: 处理后的图像
    """
    # 调整图像大小至目标尺寸
    resized_image = cv2.resize(image, target_shape)
    # 将BGR图像转换为RGB图像
    resized_image = cv2.cvtColor(np.array(resized_image), cv2.COLOR_BGR2RGB)
    # 转换图像维度顺序，以便适应模型输入要求（通道数在前）
    resized_image = resized_image.transpose((2, 0, 1))
    # 添加批次维度并在转换为浮点型
    resized_image = np.expand_dims(resized_image, axis=0).astype(np.float32)
    return resized_image


def postprocess(result, image, fps):
    """
    定义输出数据的后处理函数，用于绘制检测框及显示FPS信息

    :param result: 推理结果
    :param image: 原始输入帧
    :param fps: 每帧的平均吞吐量（帧率）
    :return image: 绘制了检测框和FPS信息的图像
    """
    # 将结果重塑为检测框数组，每个检测包含类别ID、图像ID、置信度以及边界框坐标
    detections = result.reshape(-1, 7)
    # 遍历所有检测到的目标
    for i, detection in enumerate(detections):
        _, image_id, confidence, xmin, ymin, xmax, ymax = detection
        # 只保留置信度高于0.5的目标
        if confidence > 0.5:
            # 计算边界框的实际像素位置，并确保其在图像范围内
            xmin = int(max((xmin * image.shape[1]), 10))
            ymin = int(max((ymin * image.shape[0]), 10))
            xmax = int(min((xmax * image.shape[1]), image.shape[1] - 10))
            ymax = int(min((ymax * image.shape[0]), image.shape[0] - 10))
            # 在图像上绘制矩形框
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            # 在图像上显示FPS信息
            cv2.putText(
                image,
                str(round(fps, 2)) + " fps",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                2.0,
                (0, 255, 0),
                3,
            )
    return image