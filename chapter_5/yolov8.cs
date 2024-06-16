// 引用OpenCVSharp深度学习、基础功能、OpenVinoSharp扩展处理、结果处理和OpenVinoSharp主库命名空间
using OpenCvSharp.Dnn;
using OpenCvSharp;
using OpenVinoSharp.Extensions.process;
using OpenVinoSharp.Extensions.result;
using OpenVinoSharp;

// 定义yolov8_det命名空间下的程序类
namespace yolov8_det
{
    // 内部类Program，程序入口点
    internal class Program
    {
        // 主函数，程序执行起点
        static void Main(string[] args)
        {
            // 定义视频文件路径和模型文件路径
            string video_path = "E:\\ModelData\\image\\bus.jpg";
            string model_path = "E:\\Model\\yolo\\yolov8s.onnx";

            // 初始化OpenVINO核心对象
            Core core = new Core();
            // 读取模型
            Model model = core.read_model(model_path);
            // 编译模型以在CPU上运行
            CompiledModel compiled_model = core.compile_model(model, "CPU");
            // 创建推理请求对象
            InferRequest request = compiled_model.create_infer_request();

            // 读取图像
            Mat img = Cv2.ImRead(video_path);
            // 初始化缩放因子
            float factor = 0.0f;
            // 图像预处理，输出预处理后的数据和缩放因子
            float[] input_data = preprocess(img, out factor);
            // 将预处理后的数据送入推理请求的输入张量
            request.get_input_tensor().set_data(input_data);

            // 执行模型推理
            request.infer();
            // 获取推理结果
            float[] output_data = request.get_output_tensor().get_data<float>(8400 * 84);
            // 后处理推理结果，得到检测结果
            DetResult result = postprocess(output_data, factor);
            // 将检测结果显示在原图上
            Mat res_mat = Visualize.draw_det_result(result, img);
            // 显示结果图像
            Cv2.ImShow("Result", res_mat);
            // 等待按键事件，窗口关闭条件
            Cv2.WaitKey(0);
        }

        // 图像预处理方法，包括颜色空间转换、调整尺寸、归一化和维度排列
        public static float[] preprocess(Mat img, out float factor)
        {
            Mat mat = new Mat();
            // 将BGR图像转换为RGB图像
            Cv2.CvtColor(img, mat, ColorConversionCodes.BGR2RGB);
            // 调整图像尺寸并记录缩放因子
            mat = Resize.letterbox_img(mat, 640, out factor);
            // 数据归一化
            mat = Normalize.run(mat, true);
            // 改变数组维度顺序以匹配模型输入要求
            return Permute.run(mat);
        }

        // 推理后处理方法，筛选、非极大值抑制(NMS)并组织检测结果
        public static DetResult postprocess(float[] result, float factor)
        {
            // 初始化边界框、类别ID和置信度列表
            List<Rect> positionBoxes = new List<Rect>();
            List<int> classIds = new List<int>();
            List<float> confidences = new List<float>();

            // 遍历输出结果，提取有效检测框
            for (int i = 0; i < 8400; i++)
            {
                for (int j = 4; j < 84; j++)
                {
                    float source = result[8400 * j + i];
                    int label = j - 4;
                    // 如果该预测的得分大于阈值
                    if (source > 0.2)
                    {
                        float maxSource = source;
                        float cx = result[8400 * 0 + i]; // 中心x坐标
                        float cy = result[8400 * 1 + i]; // 中心y坐标
                        float ow = result[8400 * 2 + i]; // 预测宽度
                        float oh = result[8400 * 3 + i]; // 预测高度
                        // 计算实际边界框位置
                        int x = (int)((cx - 0.5 * ow) * factor);
                        int y = (int)((cy - 0.5 * oh) * factor);
                        int width = (int)(ow * factor);
                        int height = (int)(oh * factor);
                        Rect box = new Rect(x, y, width, height);
                        // 保存有效检测框、类别和置信度
                        positionBoxes.Add(box);
                        classIds.Add(label);
                        confidences.Add(maxSource);
                    }
                }
            }
            // 创建DetResult实例用于存储最终检测结果
            DetResult re = new DetResult();
            // 申请一个索引数组用于NMS处理后的有效框
            int[] indexes = new int[positionBoxes.Count];
            // 应用非极大值抑制，筛选重叠框
            CvDnn.NMSBoxes(positionBoxes, confidences, 0.2f, 0.5f, out indexes);
            // 根据NMS结果组装最终的DetResult对象
            for (int i = 0; i < indexes.Length; i++)
            {
                int index = indexes[i];
                re.add(classIds[index], confidences[index], positionBoxes[index]);
            }
            // 返回处理后的检测结果
            return re;
        }
    }
}