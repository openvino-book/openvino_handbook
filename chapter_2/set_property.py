import openvino as ov
import openvino.properties as props

model_path = "./yolov8n-cls.onnx"
core = ov.Core()

# 使用core.set_property()设置属性
model_priority = core.get_property("AUTO", "MODEL_PRIORITY")
print(f"Model Priority: {model_priority}")
# change the model priority by core.set_property()
print("Change the model priority by core.set_property() ")
core.set_property("AUTO", {"MODEL_PRIORITY": props.hint.Priority.HIGH})
model_priority = core.get_property("AUTO", "MODEL_PRIORITY")
print(f"Model Priority: {model_priority}")

# change the model priority by config bebore compiling model
print("change the model priority by config bebore compiling model")
config = {"MODEL_PRIORITY": props.hint.Priority.LOW}
compiled_model = core.compile_model(model_path, "AUTO", config)
model_priority = compiled_model.get_property("MODEL_PRIORITY")
print(f"Model Priority: {model_priority}")


