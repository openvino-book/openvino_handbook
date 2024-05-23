import openvino as ov 
from openvino import properties

# 设置模型路径
ov_model_path   = "./yolov8x-cls.xml"
# 选择设备插件
device = ['CPU', 'GPU', 'GPU.0', 'GPU.1', 'AUTO', 'AUTO:-CPU', 'BATCH:CPU(4)'][3]
# 配置性能优化属性
config = {"PERFORMANCE_HINT": "THROUGHPUT"}   #可改为："LATENCY"或"CUMULATIVE_THROUGHPUT"
config["PERFORMANCE_HINT_NUM_REQUESTS"] = "4" #设置自动批处理的批尺寸大小为4
config["AUTO_BATCH_TIMEOUT"] = "500"          #设置超时时间为500ms
config['CACHE_DIR'] = './cache'               #启动模型缓存，并指定模型缓存路径

def main():  

    # 创建Core对象
    core = ov.Core()
    supported_properties= core.get_property(device, properties.supported_properties())
    print(f"SUPPORTED_PROPERTIES={supported_properties}")
    #print(f"config={config}")
    compiled_model = core.compile_model(ov_model_path, device_name=device, config=config)
    supported_properties= compiled_model.get_property(properties.supported_properties)
    print(f"SUPPORTED_PROPERTIES={supported_properties}")

    #compiled_model.set_property({"AUTO_BATCH_TIMEOUT": "500"}) #设置超时时间为500ms
    #auto_batch_timeout = compiled_model.get_property("AUTO_BATCH_TIMEOUT") 
    #auto_batch_timeout = compiled_model.get_property(properties.auto_batch_timeout) 
    #print(f"AUTO_BATCH_TIMEOUT={auto_batch_timeout}")
    num_requests = compiled_model.get_property("OPTIMAL_NUMBER_OF_INFER_REQUESTS")
    print(f"AUTO_BATCH_SIZE={num_requests}")
  
if __name__ == '__main__':  
    main()
