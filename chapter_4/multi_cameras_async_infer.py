import cv2
import numpy as np
import queue, threading, time
from threading import Thread
from utils_person_detection import preprocess, postprocess
import openvino as ov

# person-detection-0202模型文件的路径
model_path = r"model/intel/person-detection-0202/FP16/person-detection-0202.xml"
# 初始化OpenVINO的Core对象
core = ov.Core()
# 使用Core对象编译模型
ov_model = core.compile_model(model_path, "GPU.1")
# 获取模型的输入层
input_layer = ov_model.input(0)
# 获取输入层的形状，形状格式为(N, C, H, W)，分别代表批次、通道数、高度、宽度
N, C, H, W = input_layer.shape
# 提取输入层的高度和宽度，定义一个名为input_shape的元组
input_shape = (H, W)

# IP摄像头的RTSP URLs
camera_urls = [
    r"cam1\worker-zone-detection.mp4",
    r"cam2\worker-zone-detection.mp4",
    r"cam3\worker-zone-detection.mp4",
    r"cam4\worker-zone-detection.mp4"
    ]

def callback(infer_request, info) -> None:
    """
    回调函数: 用于AsyncInferQueue的推理请求后的操作,
    包括计算延迟、帧率，后处理帧数据，并将处理后的帧放入显示队列中。

    参数:
    - infer_request: 推理请求对象，包含了推理的执行信息和结果。
    - info: 一个元组，包含当前需要处理的帧以及用于显示处理后帧的队列。
             具体结构为 (frame, display_queue)。

    返回:
    无
    """
    # 获取当前推理请求的耗时（latency）
    latency = infer_request.latency
    # 解构传入的info元组，获取当前帧和用于显示的队列
    frame, display_queue = info
    # 计算推理的帧率 (FPS) based on the current latency
    inferqueue_fps = (1.0 / latency) * 1000
    # 从推理请求的输出中获取第一个张量的数据
    res = infer_request.get_output_tensor(0).data[0]
    # 对帧应用后处理操作，如解码、缩放、添加推理结果等，并传入帧、原始帧和推理队列FPS
    frame = postprocess(res, frame, inferqueue_fps)
    # 将处理后的帧放入显示队列中，等待显示
    display_queue.put(frame)

class CameraThread(threading.Thread):
    def __init__(self, camera_url, queue):
        super().__init__()
        self.camera_url = camera_url
        self.queue = queue
        self.cap = cv2.VideoCapture()
        self.open_camera(camera_url)
    
    def open_camera(self, camera_url):
        self.cap.open(camera_url)
        if not self.cap.isOpened():
            print(f"Could not open camera: {camera_url}")
            exit(-1)
    
    def release_camera(self):
        if self.cap.isOpened():
            self.cap.release()
    
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error or camera disconnected.")
                self.release_camera()
                break
            
            # 这里将每一帧图像数据放入队列           
            self.queue.put(frame)
                
    def stop(self):
        self.release_camera()
        self.join()

class InferenceThread(threading.Thread):
    """
    类InferenceThread继承自threading.Thread，用于异步执行模型推理任务，
    包括从摄像头读取视频流、预处理帧、异步推断以及将结果显示到队列中。
    
    属性:
    - display_queue: 用于存放处理后帧的队列，供显示线程使用。
    - infer_queue: OpenVINO的AsyncInferQueue对象，管理推理请求的队列。
    - cap: cv2.VideoCapture对象，用于从指定URL捕获视频流。
    
    方法:
    - __init__: 初始化摄像头URL、显示队列，创建推理请求队列，并初始化摄像头。
    - open_camera: 打开指定URL的摄像头，检查是否成功打开。
    - run: 线程主循环，读取视频帧，预处理后送入推理队列进行异步推理。
    - release_camera: 关闭当前打开的摄像头资源。
    """
    
    def __init__(self, camera_url, display_queue):
        """
        初始化InferenceThread实例。
        
        参数:
        - camera_url: 摄像头的URL或设备索引。
        - display_queue: 用于存放处理后帧的队列。
        - ov_model: 已加载的OpenVINO模型。
        - input_layer: 模型的输入层名称或对象。
        - input_shape: 模型输入所需的数据形状。
        """
        super().__init__()
        self.display_queue = display_queue
        # 创建推理请求队列
        self.infer_queue = ov.AsyncInferQueue(ov_model)
        self.infer_queue.set_callback(callback)  # 设置callback函数
        # 初始化摄像头
        self.cap = cv2.VideoCapture()
        self.open_camera(camera_url)
    
    def open_camera(self, camera_url):
        """
        打开指定URL的摄像头设备。
        
        参数:
        - camera_url: 摄像头的URL或设备索引。
        如果无法打开摄像头，则打印错误信息并退出程序。
        """
        self.cap.open(camera_url)
        if not self.cap.isOpened():
            print(f"Could not open camera: {camera_url}")
            exit(-1)
    
    def run(self):
        """
        线程运行方法，持续从摄像头读取帧，进行预处理，并异步推断。
        如果读取帧失败或摄像头断开连接，则释放摄像头资源并结束线程。
        """
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error or camera disconnected.")
                self.release_camera()
                break
            else:
                resized_image = preprocess(frame, input_shape)  
                self.infer_queue.start_async({input_layer.any_name: resized_image}, 
                                            (frame, self.display_queue))
                
    def release_camera(self):
        """
        释放摄像头资源。
        """
        if self.cap.isOpened():
            self.cap.release()

class DisplayThread(threading.Thread):
    """
    显示线程类，负责从多个队列中获取图像数据，将其合并成单一图像并在窗口中显示。
    支持通过按键'q'退出显示循环。
    
    属性:
    - queues: 一个包含多个队列的列表，每个队列提供待显示的图像帧。
    - running: 布尔值，表示线程是否应继续运行。
    
    方法:
    - __init__: 初始化DisplayThread实例，设置队列列表和运行标志。
    - run: 线程的主要执行逻辑，循环检查队列获取图像，合并并显示。
    - combine_images: 将给定的图像列表水平和垂直拼接成单个图像。
    - combine_and_resize_images: 拼接图像后进一步调整其尺寸。
    """
    
    def __init__(self, queues):
        """
        初始化DisplayThread实例。
        
        参数:
        - queues: 一个列表，包含用于接收图像帧的队列对象。
        """
        super().__init__()
        self.queues = queues
        self.running = True

    def run(self):
        """
        线程运行方法，循环检查每个队列获取图像帧，当所有队列均有图像时，
        进行拼接、调整尺寸并显示。监听键盘事件允许用户通过按下'q'键退出。
        """
        while self.running:
            frames = []
            # 尝试从每个队列获取图像
            for q in self.queues:
                if not q.empty():
                    frames.append(q.get())
                else:
                    # 若任一队列空，则短暂停顿避免频繁检查
                    time.sleep(0.01)
                    break
            
            # 所有队列均有图像时，进行处理和显示
            if len(frames) == 4:
                combined_image = self.combine_and_resize_images(frames)
                cv2.imshow('Inference Results', combined_image)
                
                # 监听键盘事件，'q'键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False

        # 清理显示窗口
        cv2.destroyAllWindows()

    def combine_images(self, images):
        """
        将提供的图像列表按2x2网格形式拼接成一个大图。
        
        参数:
        - images: 图像列表，假定所有图像尺寸相同。
        
        返回:
        - combined_image: 拼接后的图像。
        """
        rows = [np.concatenate((images[i], images[i+1]), axis=1) for i in range(0, len(images), 2)]
        return np.concatenate(rows, axis=0)

    def combine_and_resize_images(self, images):
        """
        拼接图像后，根据预设的比例调整其尺寸。
        
        参数:
        - images: 待处理的图像列表。
        
        返回:
        - resized_image: 调整尺寸后的拼接图像。
        """
        # 首先拼接图像
        combined_image = self.combine_images(images)
        # 计算新的高度和宽度（这里示例为原尺寸的1/4）
        height, width = combined_image.shape[:2]
        new_height, new_width = height // 4, width // 4
        # 调整图像尺寸
        return cv2.resize(combined_image, (new_width, new_height))

if __name__ == "__main__":

    # 为每个推理结果创建一个专属队列
    display_queues = [queue.Queue() for _ in camera_urls]
    # 为每个摄像头创建一个专属推理线程
    inference_threads = [InferenceThread(url, dq) for url, dq in zip(camera_urls, display_queues)] 
    # 创建一个显示线程
    display_thread = DisplayThread(display_queues)
    
    # 启动所有线程
    for thread in inference_threads + [display_thread]:
        thread.start()
    
    # 等待键盘输入结束
    print("Press 'q' to quit each camera window.")
    while cv2.waitKey(1) != ord('q'):
        pass

    # 清理工作，关闭所有窗口和释放摄像头资源
    display_thread.running = False
    display_thread.join()
    
    cv2.destroyAllWindows()
    for thread in inference_threads + [display_thread]:
        thread.stop()