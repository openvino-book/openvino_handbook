using OpenCvSharp.Dnn;
using OpenCvSharp;
using OpenVinoSharp;
using OpenVinoSharp.Extensions.result;
using OpenVinoSharp.Extensions.process;
using System.Diagnostics;
using OpenVinoSharp.preprocess;

namespace openvino_async_csharp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("YOLOv8 OpenVINO C# Demo!");
            yolov8_async_det();
        }

        static void yolov8_async_det()
        {   
            // Set the video path and model path
            string video_path = "D:/yolov8_async_csharp/test_video.mp4";
            string model_path = "D:/yolov8_async_csharp/yolov8s.xml";
            
            // Create a new Core object and read the model
            Core core = new Core();
            Model model = core.read_model(model_path);
            CompiledModel compiled_model = core.compile_model(model, "GPU");
            // Create a list of InferRequest objects
            List<InferRequest> requests = new List<InferRequest> {compiled_model.create_infer_request(), compiled_model.create_infer_request()};

            // Create a new VideoCapture object and read the video
            VideoCapture capture = new VideoCapture(video_path);
            if (!capture.IsOpened())
            {
                Console.WriteLine("Error: Video not found!");
                return;
            }
            Mat frame = new Mat();
            Mat next_frame = new Mat();
            capture.Read(frame);
            float scale = 0.0f;
            float[] input_data = preprocess(frame, out scale);
            requests[0].get_input_tensor().set_data(input_data);
            requests[0].start_async();
            Stopwatch sw = new Stopwatch();
            float[] total_infs = new float[3];

            while (true)
            {
                
                if(!capture.Read(next_frame))
                {
                    break;
                }

                sw.Restart();
                input_data = preprocess(frame, out scale);
                requests[1].get_input_tensor().set_data(input_data);
                requests[1].start_async();
                requests[0].wait();
                float[] output_data = requests[0].get_output_tensor().get_data<float>(8400 * 84);
                DetResult result = postprocess(output_data, scale);
                sw.Stop();
                total_infs[0] = sw.ElapsedMilliseconds;

                Cv2.PutText(frame, "Inference: " + (1000.0 / total_infs[0]).ToString("0.00") + "FPS " + (total_infs[0]).ToString("0.00") + "ms", new Point(20, 40), HersheyFonts.HersheyPlain, 2, new Scalar(255, 0, 255), 2); 
               
               
                Mat res_mat = Visualize.draw_det_result(result, frame);
                Cv2.ImShow("YOLOv8 OpenVINO C# Demo", frame);

                // Press 'ESC' to exit the program
                if (Cv2.WaitKey(1) == 27)
                {
                    break;
                }
    
                swap(requests);
                frame = next_frame;
            }        
        }
        public static float[] preprocess(Mat frame, out float scale)
        {
            Mat mat = new Mat();
            Cv2.CvtColor(frame, mat, ColorConversionCodes.BGR2RGB);
            mat = Resize.letterbox_img(mat, 640, out scale);
            mat = Normalize.run(mat, true);
            return Permute.run(mat);
        }
        public static DetResult postprocess(float[] result, float scale)
        {
            // Storage results list           
            List<Rect> positionBoxes = new List<Rect>(); 
            List<int> classIds = new List<int>();
            List<float> confidences = new List<float>(); 

            // Preprocessing output results
            for(int i = 0; i < 8400; i++)
            {
                for(int j = 4; j < 84; j++)
                {
                    float conf = result[8400 * j + i];
                    int label = j - 4;
                    if (conf > 0.2)
                    {
                        float cx = result[8400 * 0 + i];
                        float cy = result[8400 * 1 + i];
                        float ow = result[8400 * 2 + i];
                        float oh = result[8400 * 3 + i];    
                        int x = (int)((cx - 0.5 * ow ) * scale);
                        int y = (int)((cy - 0.5 * oh ) * scale);
                        int width = (int)(ow * scale);
                        int height = (int)(oh * scale);
                        Rect box = new Rect(x, y, width, height);
                        positionBoxes.Add(box);
                        classIds.Add(label);
                        confidences.Add(conf);
                    }
                }
                
            }
            DetResult re = new DetResult();
            int[] indices = new int[positionBoxes.Count];
            CvDnn.NMSBoxes(positionBoxes, confidences, 0.2f, 0.5f, out indices);
            for (int i = 0; i < indices.Length; i++)
            {
                int index = indices[i];
                re.add(classIds[index], confidences[index], positionBoxes[index]);
            }

            return re;
        }

        public static void swap(List<InferRequest> requests)
        {
            var temp = requests[0];
            requests[0] = requests[1];
            requests[1] = temp;
        }
    }
}