import cv2
import numpy as np
import glob
import yaml

def calibrate_fisheye_camera(images_path, chessboard_size, square_size, output_file, img_size = None):
    # 准备棋盘格角点的3D坐标
    objp = np.zeros((1, chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2) * square_size

    # 存储3D点和2D图像点
    objpoints = []  # 真实世界中的3D点
    imgpoints = []  # 图像中的2D点

    # 获取所有标定图片
    images = glob.glob(images_path)
    if not images:
        print("未找到任何图片，请检查路径是否正确")
        return

    cnt_ill = 0
    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue
            
        if img_size is None:
            img_size = (img.shape[1], img.shape[0]) # W, H
        else:
            #resize_types = {"INTER_NEAREST": cv2.INTER_NEAREST, "INTER_LINEAR": cv2.INTER_LINEAR,  "INTER_CUBIC": cv2.INTER_CUBIC, "INTER_AREA": cv2.INTER_AREA, "INTER_LANCZOS4": cv2.INTER_LANCZOS4}
            img = cv2.resize(img, img_size, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite("{}".format(fname.replace("jpgs-org", "jpgs-small")), img)
            
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 查找棋盘格角点
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, 
                                               cv2.CALIB_CB_ADAPTIVE_THRESH +
                                               cv2.CALIB_CB_FAST_CHECK +
                                               cv2.CALIB_CB_NORMALIZE_IMAGE)
        if corners is None:
            print("corners ILL at {}".format(fname))
            cnt_ill = cnt_ill + 1
            continue
        # print("coners type : {}, shape : {} ({})".format(type(corners), corners.shape, ret))
        
        if ret:
            objpoints.append(objp)
            
            # 提高角点检测精度
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

    if not objpoints:
        print("未在任何图片中找到棋盘格角点")
        return
    print("ill image {} among {}".format(cnt_ill, len(images)))

    # 鱼眼相机标定
    calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_CHECK_COND + cv2.fisheye.CALIB_FIX_SKEW
    N_OK = len(objpoints)
    K = np.zeros((3, 3))
    D = np.zeros((4, 1))
    rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(N_OK)]
    tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(N_OK)]
    print("input matrix : objpoints {} , imgpoints {}, gray {}".format(len(objpoints), len(imgpoints), gray.shape))
    
    try:
        ret, K, D, _, _ = cv2.fisheye.calibrate(
            objpoints,
            imgpoints,
            gray.shape[::-1],
            K,
            D,
            rvecs,
            tvecs,
            calibration_flags,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
        )
    except Exception as e :
        print("er is : \n{}".format(e))
        error_index = "{}".format(e).split("Ill-conditioned matrix for input array")[1]
        error_index = error_index.split(" in function 'CalibrateExtrinsics")[0]
        error_index = int(error_index)        
        print("{}\n{}\n{}".format(objpoints[error_index], imgpoints[error_index], images[error_index]))
        print("error array is : {}".format(error_index))
        exit(-1)

    # 计算视场角(FOV)
    hfov = 2 * np.arctan(img_size[0] / (2 * K[0, 0])) * 180 / np.pi
    vfov = 2 * np.arctan(img_size[1] / (2 * K[1, 1])) * 180 / np.pi

    # 准备YAML数据
    data = {
        "CAM_MODEL": "cvfisheye",
        "camera_type": "mono",
        "hfov": float(hfov),
        "vfov": float(vfov),
        "loss_hfov": float(hfov),
        "loss_vfov": float(vfov),
        "K": {
            "rows": 3,
            "cols": 3,
            "dt": "d",
            "data": K.flatten().tolist()
        },
        "D": {
            "rows": 4,
            "cols": 1,
            "dt": "d",
            "data": D.flatten().tolist()
        },
        "R": {
            "rows": 3,
            "cols": 3,
            "dt": "d",
            "data": np.eye(3).flatten().tolist()
        },
        "P": {
            "rows": 3,
            "cols": 3,
            "dt": "d",
            "data": K.flatten().tolist()  # 简化处理，实际P矩阵可能不同
        },
        "lossP": {
            "rows": 3,
            "cols": 3,
            "dt": "d",
            "data": K.flatten().tolist()  # 简化处理
        },
        "imgSize": img_size,
        "errLeft": float(ret)
    }

    # 写入YAML文件
    with open(output_file, 'w') as f:
        f.write("%YAML:1.0\n")
        f.write("---\n")
        yaml.dump(data, f, default_flow_style=None, sort_keys=False)

    print(f"标定完成，结果已保存到 {output_file}")
    return img.shape[::-1], K, D


def undistort(img_path,K,D,DIM,scale=None,imshow=True):
    img = cv2.imread(img_path)
    dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort
    assert dim1[0]/dim1[1] == DIM[0]/DIM[1], "Image to undistort needs to have same aspect ratio as the ones used in calibration"
    if dim1[0]!=DIM[0]:
        img = cv2.resize(img,DIM,interpolation=cv2.INTER_AREA)
    Knew = K.copy()
    if scale:#change fov 0.6
        Knew[(0,1), (0,1)] = scale * Knew[(0,1), (0,1)]
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), Knew, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    if imshow:
        cv2.imshow("undistorted", undistorted_img)
    return undistorted_img

# 使用示例
# cv2.calibrateCamera
#一个12x9的棋盘格（12列×9行方格），其内角点数量是(11,8)（即11列×8行角点）

if __name__ == "__main__":
    # 参数设置
    images_path = "./jpgs-small-INTER_LANCZOS4/*.jpg"  # 标定图片路径 jpgs-small jpgs-org
    chessboard_size = (11, 8)  # 棋盘格内角点数量 (width, height)
    square_size = 0.03  # 棋盘格方格大小 (单位: 米)
    output_file = "python_calibration.yaml"  # 输出文件
    
    resize_size = None # (640, 360)
    
    calibrate_fisheye_camera(images_path, chessboard_size, square_size, output_file, resize_size)



"""
while IFS= read -r nv12_file; do
    echo "inpuy : ${nv12_file}.yuv"
    sleep 2
    ffmpeg -s 1920x1080 -pix_fmt nv12 -i "${nv12_file}.yuv" -pix_fmt rgb24 "../jpgs-org/${nv12_file}.jpg"
    nv12_file=""
    echo "clear : ${nv12_file}"
    sleep 1
done < ../names.txt

for file in *.yuv; do
    if [ -f "$file" ]; then
        nv12_file=${file%.yuv}
        echo "${nv12_file}"  
        ffmpeg -s 1920x1080 -pix_fmt nv12 -i "${nv12_file}.yuv" -pix_fmt rgb24 "../jpgs-org/${nv12_file}.jpg"
        sleep 3
    fi
done
"""
