import os
import glob

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import numpy as np
from werkzeug.wsgi import peek_path_info


def analyse(timestamps,digit = 13, low = 66.7):
    num = 0
    # ss = 0
    interval_dict = {}
    arr = np.zeros(10,dtype=int)
    intervals = []
    for i in range(1,len(timestamps)):
        interval = timestamps[i] - timestamps[i-1]
        if interval  <= low :
            num += 1
        intervals.append(interval)

    min_interval = min(intervals)
    max_interval = max(intervals)
    avg_interval = sum(intervals) / len(intervals)
    per_interval = (max_interval - min_interval) / 10

    for i in range(len(intervals)):
        if intervals[i] <= (min_interval + per_interval):
            arr[0] = arr[0] + 1
        elif min_interval + 2 * per_interval >= intervals[i] > min_interval + per_interval:
            arr[1] = arr[1] + 1
        elif (min_interval + 3 * per_interval) >= intervals[i] > min_interval + 2 * per_interval:
            arr[2] = arr[2] + 1
        elif (min_interval + 4 * per_interval) >= intervals[i] > min_interval + 3 * per_interval:
            arr[3] = arr[3] + 1
        elif (min_interval + 5 * per_interval) >= intervals[i] > min_interval + 4 * per_interval:
            arr[4] = arr[4] + 1
        elif (min_interval + 6 * per_interval) >= intervals[i] > min_interval + 5 * per_interval:
            arr[5] = arr[5] + 1
        elif (min_interval + 7 * per_interval) >= intervals[i] > min_interval + 6 * per_interval:
            arr[6] = arr[6] + 1
        elif (min_interval + 8 * per_interval) >= intervals[i] > min_interval + 7 * per_interval:
            arr[7] = arr[7] + 1
        elif (min_interval + 9 * per_interval) >= intervals[i] > min_interval + 8 * per_interval:
            arr[8] = arr[8] + 1
        elif (min_interval + 10 * per_interval) >= intervals[i] > min_interval + 9 * per_interval:
            arr[9] = arr[9] + 1


    min_interval_index = intervals.index(min_interval)
    max_interval_index = intervals.index(max_interval)

    min_1_timestamp = timestamps[min_interval_index]
    min_2_timestamp = timestamps[min_interval_index + 1]
    max_1_timestamp = timestamps[max_interval_index]
    max_2_timestamp = timestamps[max_interval_index + 1]

    print("low {low} nums are: {num}".format(low=low, num=num))


    if digit == 10:
        print("min_interval = {}s, max_interval = {}s, avg_interval = {}s".format(min_interval,max_interval,avg_interval))
        print("min_qian_timestamp = {}, min_hou_timestamp = {}".format(min_1_timestamp,min_2_timestamp))
        print("max_qian_timestamp = {}, max_hou_timestamp = {}".format(max_1_timestamp,max_2_timestamp))
    elif digit == 13:
        print("min_interval = {}ms, max_interval = {}ms, avg_interval = {}ms".format(min_interval,max_interval,avg_interval))
        print("min_qian_timestamp = {}, min_hou_timestamp = {}".format(min_1_timestamp,min_2_timestamp))
        print("max_qian_timestamp = {}, max_hou_timestamp = {}".format(max_1_timestamp,max_2_timestamp))
    elif digit == 16:
        print("min_interval = {}微秒, max_interval = {}微秒, avg_interval = {}微秒".format(min_interval,max_interval,avg_interval))
        print("min_qian_timestamp = {}, min_hou_timestamp = {}".format(min_1_timestamp,min_2_timestamp))
        print("max_qian_timestamp = {}, max_hou_timestamp = {}".format(max_1_timestamp,max_2_timestamp))

    interval_dict = {}

    for i in range(len(arr)):
        # 计算区间范围和百分比
        lower_bound = min_interval + i * per_interval
        upper_bound = min_interval + (i + 1) * per_interval
        percentage = arr[i] / len(intervals)

        interval_dict.update({
            f"{lower_bound:.2f}到{upper_bound:.2f}": percentage
        })

    # 按百分数值（字典的值）进行倒序排序
    sorted_items = sorted(interval_dict.items(),
                          key=lambda x: x[1],  # 按百分比值排序
                          reverse=True)
    #sorted_items = sorted(interval_dict.items(),
     #                     key=lambda x: x[1],  # 按百分比值排序
      #                    reverse=True)

    # 将排序后的百分比格式化为百分数字符串
    sorted_percentages = [
        (range_str, f"{percentage:.2%}")
        for range_str, percentage in sorted_items
    ]

    #print("时间间隔分布（按占比倒序排序）:")
    print("时间间隔分布:")

    for range_str, percentage_str in sorted_percentages:
        print(f"{range_str} : {percentage_str}")

def read_dir(path = "",digit = 13):
    times_dir = []
    png_file = glob.glob(os.path.join(img_path, "*.png"))
    print("找到 {len(png_file)}个文件")
    for file_path in png_file:
        file_name = os.path.basename(file_path)
        png_name = file_name.replace(".png", "")
        if digit == 10:
            if len(png_name) == 13 and png_name[:-3].isdigit():
                png_dig = int(png_name)
                te_10 = png_dig // 1000
                times_dir.append(te_10)
            elif len(png_name) == 16 and png_name[:-6].isdigit():
                png_dig = int(png_name)
                te_10 = png_dig // 1000000
                times_dir.append(te_10)
            elif len(png_name) == 10:
                png_dig = int(png_name)
                times_dir.append(png_dig)
            else:
                print("输入图片位数错误!!")

        elif digit == 13:
            if len(png_name) == 16 and png_name[:-3].isdigit():
                png_dig = int(png_name)
                te_13 = png_dig // 1000
                times_dir.append(te_13)
            elif len(png_name) == 13:
                png_dig = int(png_name)
                times_dir.append(png_dig)
            else:
                print("输入图片位数错误!!")

        elif digit == 16:
            print("启用16位时间戳转换")
            if len(png_name) == 16:
                png_dig = int(png_name)
                times_dir.append(png_dig)
            else:
                print("输入图片位数错误!!")

    return times_dir


import os
import re
import datetime
from typing import List


def read_txt(file_path: str) -> List[int]:
    """
    从日志文件中提取时间字符串并转换为时间戳

    参数:
        file_path (str): 日志文件路径

    返回:
        list: 包含时间戳的列表，每个时间戳根据时间字符串的精度决定位数（10位秒级、13位毫秒级、16位微秒级）
    """
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # 提取所有时间字符串
    times = []

    # 正则表达式匹配时间格式 HH:MM:SS[.ssssss]
    time_pattern = r'(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
    matches = re.findall(time_pattern, log_content)

    if not matches:
        print(f"警告: 在文件 {file_path} 中未找到时间字符串")
        return []

    # 确定基准日期（使用当前日期）
    today = datetime.date.today()
    base_date = datetime.datetime(today.year, today.month, today.day)

    for time_str in matches:
        # 判断时间格式并转换为时间戳
        if '.' in time_str:
            # 包含小数部分
            parts = time_str.split('.')
            base_time = parts[0]  # HH:MM:SS
            fractional = parts[1]  # 小数部分

            # 解析基础时间
            hours, minutes, seconds = map(int, base_time.split(':'))

            # 根据小数部分长度确定精度
            fractional_len = len(fractional)
            if fractional_len <= 3:
                # 毫秒级（1-3位小数）
                milliseconds = int(fractional.ljust(3, '0')[:3])
                microseconds = milliseconds * 1000
                dt = base_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)
                timestamp = int(dt.timestamp() * 1000)  # 毫秒级时间戳（13位）
            else:
                # 微秒级（4-6位小数）
                microseconds = int(fractional.ljust(6, '0')[:6])
                dt = base_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)
                timestamp = int(dt.timestamp() * 1e6)  # 微秒级时间戳（16位）
        else:
            # 无小数部分（秒级）
            hours, minutes, seconds = map(int, time_str.split(':'))
            dt = base_date.replace(hour=hours, minute=minutes, second=seconds)
            timestamp = int(dt.timestamp())  # 秒级时间戳（10位）

        times.append(timestamp)

    # 打印处理摘要
    print(f"从文件 {file_path} 中提取了 {len(times)} 个时间戳")
    if times:
        # 确定时间戳精度
        first_ts = times[0]
        ts_len = len(str(first_ts))
        precision = {
            10: "秒级",
            13: "毫秒级",
            16: "微秒级"
        }.get(ts_len, f"未知精度({ts_len}位)")

        # first_dt = datetime.datetime.fromtimestamp(first_ts / (1000 if ts_len > 10 else 1))
        # last_dt = datetime.datetime.fromtimestamp(times[-1] / (1000 if ts_len > 10 else 1))
        #
        # print(f"第一个时间: {first_dt.strftime('%Y-%m-%d %H:%M:%S.%f')} ({precision})")
        # print(f"最后一个时间: {last_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}")
        # print(f"时间跨度: {(last_dt - first_dt).total_seconds():.3f} 秒")

    return times



def main(digit = 13, low = 66.7, fun = 1,path = ""):
    if fun == 1:
        timestamps = read_dir(path, digit)
        timestamps.sort()
        analyse(timestamps, low = low, digit = 13)
    else:
        timestamps = read_txt(path)
        timestamps.sort()
        analyse(timestamps, low = low, digit = len(str(timestamps[0])))





#如果用文件夹中的图片,fun = 1
img_path = "/home/leon/mount_point_c/RDK/rdk_source/datas_capture/0619-run-4-yongqiang-1/log-find-people/"

#如果用txt文件中包含的时间点, fun = 2
file_path = "color_data.recevie-time.log"

main(13,66.7, fun = 2, path = file_path)
# main(digit = 13,low = 66.7, fun = 1, path = img_path)

#/home/leon/mount_point_c/RDK/rdk_source/datas_capture/0619-run-3/
