import onnx
from onnx import version_converter
import os

TARGET_OPSET_VERSION = 11

top_path = "/home/leon/mount_point_d/test-result-moved/rdk_source"
model_name = "models/reid/version23/osnet_ibn"
model_name = os.path.join(top_path, model_name)
# 加载
model = onnx.load("{}.onnx".format(model_name))

print("[INFO]vesrion {} to {}".format(model.opset_import, TARGET_OPSET_VERSION))
print(onnx.helper.printable_graph(model.graph))
# 转换 opset 
converted_model = version_converter.convert_version(model, TARGET_OPSET_VERSION)


# 保存转换后的模型
onnx.save(converted_model, "{}_opset{}.onnx".format(model_name, TARGET_OPSET_VERSION))
onnx.checker.check_model(converted_model)
