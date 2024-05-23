import openvino as ov 
# 设置模型路径
ov_model_path   = "./yolov8x-cls.xml"
config = {"PERFORMANCE_HINT": "THROUGHPUT"} #可改为LATENCY
#config = {"PERFORMANCE_HINT": "LATENCY"}
def main():  

    # 创建Core对象
    core = ov.Core()
    print(config)
    # 获得当前系统中的计算设备
    devices = core.available_devices
    for device in devices:
        # 输出计算设备的完整型号
        device_name = core.get_property(device, "FULL_DEVICE_NAME")
        print(f"{device}: {device_name}")
        # 输出计算设备的最佳推理请求数
        compiled_model = core.compile_model(ov_model_path, device_name=device, config=config)
        num_requests = compiled_model.get_property("OPTIMAL_NUMBER_OF_INFER_REQUESTS")
        print(f"OPTIMAL_NUMBER_OF_INFER_REQUESTS={num_requests}")
  
if __name__ == '__main__':  
    main()
