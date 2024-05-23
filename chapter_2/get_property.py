import openvino as ov

model_path = "./yolov8n-cls.onnx"
core = ov.Core()

# 使用core.get_property()获得属性
supported_properties = core.get_property("CPU", "SUPPORTED_PROPERTIES")
print(f"core.get_property(): {supported_properties}")

# 使用compile_model.get_property()获得属性
model = core.compile_model(model_path, "AUTO")
supported_properties = model.get_property("SUPPORTED_PROPERTIES")
print(f"\n compiled_model.get_property: {supported_properties}")