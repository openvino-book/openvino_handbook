#include <iostream>  // 标准输入输出流库
#include <string>    // 字符串处理库
#include <vector>    // 动态数组容器库

#include <openvino/openvino.hpp> // OpenVINO库头文件，用于深度学习模型推理
#include <opencv2/opencv.hpp>    // OpenCV库头文件，用于图像处理与显示

// 定义颜色向量，用于绘制检测框
std::vector<cv::Scalar> colors = { cv::Scalar(0, 0, 255) , cv::Scalar(0, 255, 0) , cv::Scalar(255, 0, 0) ,
                                   cv::Scalar(255, 100, 50) , cv::Scalar(50, 100, 255) , cv::Scalar(255, 50, 100) };

// 定义类别名称向量，与模型预测的类别ID对应
const std::vector<std::string> class_names = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush" };

using namespace cv;
using namespace dnn;

// 保持图像缩放比例的函数，用于图像预处理
Mat letterbox(const cv::Mat& source)
{
    int col = source.cols;
    int row = source.rows;
    int _max = MAX(col, row);
    Mat result = Mat::zeros(_max, _max, CV_8UC3);
    source.copyTo(result(Rect(0, 0, col, row)));
    return result;
}

int main(int argc, char* argv[])
{
    // 步骤1：初始化OpenVINO运行时核心
    ov::Core core;

    // 步骤2：编译模型, 可更换推理设备
    auto compiled_model = core.compile_model("yolov8s.xml", "CPU");

    // 步骤3：创建推理请求
    ov::InferRequest infer_request = compiled_model.create_infer_request();

    // 步骤4：读取图片文件并进行预处理
    Mat img = cv::imread("zidane.jpg");
    /// 保持宽高比缩放
    Mat letterbox_img = letterbox(img);
    float scale = letterbox_img.size[0] / 640.0;
    Mat blob = blobFromImage(letterbox_img, 1.0 / 255.0, Size(640, 640), Scalar(), true);

    // 步骤5：将处理后的图像数据送入模型的输入节点
    auto input_port = compiled_model.input();
    ov::Tensor input_tensor(input_port.get_element_type(), input_port.get_shape(), blob.ptr(0));
    infer_request.set_input_tensor(input_tensor);

    // 步骤6：开始推理
    infer_request.infer();

    // 步骤7：获取推理结果
    auto output = infer_request.get_output_tensor(0);
    auto output_shape = output.get_shape();
    std::cout << "输出张量的形状:" << output_shape << std::endl;
    int rows = output_shape[2];        //8400
    int dimensions = output_shape[1];  //84: box[cx, cy, w, h]+80 classes scores

    // 步骤8：后处理，解析推理结果
    float* data = output.data<float>();
    Mat output_buffer(output_shape[1], output_shape[2], CV_32F, data);
    transpose(output_buffer, output_buffer); // 转置矩阵以便访问
    float score_threshold = 0.25;
    float nms_threshold = 0.5;
    std::vector<int> class_ids;
    std::vector<float> class_scores;
    std::vector<Rect> boxes;

    // 提取边界框、类别ID和类别分数
    for (int i = 0; i < output_buffer.rows; i++) {
        Mat classes_scores = output_buffer.row(i).colRange(4, 84);
        Point class_id;
        double maxClassScore;
        minMaxLoc(classes_scores, 0, &maxClassScore, 0, &class_id);

        if (maxClassScore > score_threshold) {
            class_scores.push_back(maxClassScore);
            class_ids.push_back(class_id.x);
            float cx = output_buffer.at<float>(i, 0);
            float cy = output_buffer.at<float>(i, 1);
            float w = output_buffer.at<float>(i, 2);
            float h = output_buffer.at<float>(i, 3);

            int left = int((cx - 0.5 * w) * scale);
            int top = int((cy - 0.5 * h) * scale);
            int width = int(w * scale);
            int height = int(h * scale);

            boxes.push_back(Rect(left, top, width, height));
        }
    }
    // 非极大值抑制，去除重叠框
    std::vector<int> indices;
    NMSBoxes(boxes, class_scores, score_threshold, nms_threshold, indices);

    // 绘制最终的图像
    for (size_t i = 0; i < indices.size(); i++) {
        int index = indices[i];
        int class_id = class_ids[index];
        rectangle(img, boxes[index], colors[class_id % 6], 2, 8);
        std::string label = class_names[class_id] + ":" + std::to_string(class_scores[index]).substr(0, 4);
        Size textSize = cv::getTextSize(label, FONT_HERSHEY_SIMPLEX, 0.5, 1, 0);
        Rect textBox(boxes[index].tl().x, boxes[index].tl().y - 15, textSize.width, textSize.height + 5);
        cv::rectangle(img, textBox, colors[class_id % 6], FILLED);
        putText(img, label, Point(boxes[index].tl().x, boxes[index].tl().y - 5), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(255, 255, 255));
    }
    // 显示最终的图像
    namedWindow("YOLOv8 OpenVINO 推理 C++ 示例", WINDOW_AUTOSIZE);
    imshow("YOLOv8 OpenVINO 推理 C++ 示例", img);
    waitKey(0);  // 等待按键
    destroyAllWindows(); // 关闭所有窗口
    return 0;
}