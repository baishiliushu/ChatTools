import onnx
from onnx import helper, shape_inference
from onnx import TensorProto
import onnxruntime as ort
import os

def downgrade_yolov8pose_opset(input_model_path, output_model_path):
    # 加载原始模型
    model = onnx.load(input_model_path)
    
    # (1) 首先修改 opset 版本为 11
    for opset in model.opset_import:
        if opset.domain == "" or opset.domain == "ai.onnx":
            opset.version = 11
    
    # (2) 查找并替换 Shape 算子
    for node in model.graph.node:
        if node.op_type == "Shape":
            # 创建替代 Shape 算子的方案
            input_name = node.input[0]
            output_name = node.output[0]
            
            # 方案：使用 Constant 节点预先计算形状（适用于静态形状）
            # 获取输入张量的形状
            input_shape = None
            for value_info in model.graph.value_info:
                if value_info.name == input_name:
                    input_shape = [dim.dim_value for dim in value_info.type.tensor_type.shape.dim]
                    break
            
            if input_shape is None:
                raise ValueError(f"Cannot infer shape for tensor: {input_name}")
            
            # 创建 Constant 节点替代 Shape
            const_node = helper.make_node(
                'Constant',
                inputs=[],
                outputs=[output_name],
                value=helper.make_tensor(
                    name='const_shape',
                    data_type=TensorProto.INT64,
                    dims=[len(input_shape)],
                    vals=input_shape
                )
            )
            
            # 替换原始节点
            model.graph.node.remove(node)
            model.graph.node.append(const_node)
    
    # (3) 处理其他可能不兼容的算子（如 Resize）
    for node in model.graph.node:
        if node.op_type == "Resize":
            # 移除不兼容的属性（opset 11 不支持某些属性）
            for attr in list(node.attribute):
                if attr.name in ["coordinate_transformation_mode", "cubic_coeff_a", "nearest_mode"]:
                    node.attribute.remove(attr)
    
    # (4) 运行形状推断以确保模型有效
    model = shape_inference.infer_shapes(model)
    
    # (5) 验证并保存模型
    try:
        onnx.checker.check_model(model)
        print("Model is valid after modification.")
    except Exception as e:
        raise ValueError(f"Model validation failed: {e}")
    
    onnx.save(model, output_model_path)
    print(f"Model saved to {output_model_path} with opset 11.")


TARGET_OPSET_VERSION = 11

top_path = "/home/leon/mount_point_d/test-result-moved/rdk_source"
model_name = "models/kpts/keypoints_yolov8/yolov8n-pose-192_756"
model_name = os.path.join(top_path, model_name)

src_model = "{}.onnx".format(model_name)
dst_model = "{}_opset{}.onnx".format(model_name, TARGET_OPSET_VERSION)
downgrade_yolov8pose_opset(src_model, dst_model)

sess = ort.InferenceSession(src_model)
print("--------{}--------".format(src_model))
print("[INFO]Input info:{}".format(sess.get_inputs()[0]))
print("[INFO]Output info:", sess.get_outputs()[0])

sess = ort.InferenceSession(dst_model)
print("--------{}--------".format(dst_model))
print("[INFO]Input info:{}".format(sess.get_inputs()[0]))
print("[INFO]Output info:", sess.get_outputs()[0])


