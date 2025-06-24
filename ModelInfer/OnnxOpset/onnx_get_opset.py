import onnx
import os
path = "/home/leon/mount_point_d/test-result-moved/rdk_source/models/"
model_name = "kpts/keypoints_yolov8/kpts_i192o756_opset11.onnx"
# 加载ONNX模型
model = onnx.load(os.path.join(path, model_name))

# 获取opset版本信息
for opset in model.opset_import:
    print(f"Domain: {opset.domain}, Version: {opset.version}")
print(model.opset_import)

model = onnx.shape_inference.infer_shapes(model)
try:
    onnx.checker.check_model(model)
    print("Model check pass.")
except Exception as e:
    raise ValueError(f"Model check failed: {e}")
