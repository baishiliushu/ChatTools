
import cv2
import os

# 保持宽高比的调整方法
def resize_keep_aspect_ratio(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        print(f"错误: 无法读取图像 {input_path}")
        return
    
    h, w = img.shape[:2]
    target_w, target_h = 1920, 1080
    
    # 计算缩放比例
    ratio = min(target_w/w, target_h/h)
    new_size = (int(w*ratio), int(h*ratio))
    
    # 调整大小
    resized = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
    
    # 添加黑边
    delta_w = target_w - new_size[0]
    delta_h = target_h - new_size[1]
    top, bottom = delta_h//2, delta_h-(delta_h//2)
    left, right = delta_w//2, delta_w-(delta_w//2)
    
    resized = cv2.copyMakeBorder(resized, top, bottom, left, right, 
                                cv2.BORDER_CONSTANT, value=[0,0,0])
    
    cv2.imwrite(output_path, resized)
    print(f"图像已调整大小(保持宽高比)并保存到 {output_path}")

def resize_and_save(input_path, output_path):
    """
    读取图像，调整大小到1920x1080，然后保存
    
    参数:
        input_path (str): 输入图像路径
        output_path (str): 输出图像路径
    """
    # 读取图像
    img = cv2.imread(input_path)
    if img is None:
        print(f"错误: 无法读取图像 {input_path}")
        return
    
    # 获取原始尺寸
    original_height, original_width = img.shape[:2]
    print(f"原始尺寸: 宽度={original_width}, 高度={original_height}")
    
    # 设置目标尺寸 (宽, 高)
    target_size = (640, 360)
    
    # 调整图像大小 
    resize_types = {"INTER_NEAREST": cv2.INTER_NEAREST, "INTER_LINEAR": cv2.INTER_LINEAR,  "INTER_CUBIC": cv2.INTER_CUBIC, "INTER_AREA": cv2.INTER_AREA, "INTER_LANCZOS4": cv2.INTER_LANCZOS4}
    for i in resize_types:
        resized_img = cv2.resize(img, target_size, interpolation=resize_types[i])
        
        # 保存调整大小后的图像
        output_name = "-{}".format(i) + ".png"
        output_name = os.path.join(output_path, output_name)
        cv2.imwrite(output_name, resized_img )
        print(f"图像已调整大小并保存到 {output_name}")

# 使用示例
input_path = "/home/leon/mount_point_c/RDK/rdk_source/datas_capture/flip-test" #"/home/leon/mount_point_c/RDK/rdk_source/datas_capture/resize-1920-1080" #"/home/leon/mount_point_c/RDK/rdk_source/datas_capture/dl_1/20250220_1429/cam0/"  
image_name = "55_1740058315845020" # 37_1740061777766796  40_1740061780906828  53_1740061793487946
input_image = os.path.join(input_path, image_name)

output_image = input_image  # 输出图像路径

#resize_and_save(input_image + ".png", output_image)
img = cv2.imread(input_image + ".jpg")
img_flip = cv2.flip(img, -1)
print("{}".format(output_image))
cv2.imwrite(output_image + "_flip-1.jpg",  img_flip)

