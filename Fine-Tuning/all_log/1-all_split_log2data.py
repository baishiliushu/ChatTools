import re
import os
from datetime import datetime


def extract_requests(log_content):
    """
    从日志内容中提取所有请求的时间戳和prompt内容
    返回格式: [(timestamp, request_id, prompt_content), ...]
    """
    pattern = r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}).*?Received request (\w+-\w+): prompt: \'(.*?)\','
    requests = re.findall(pattern, log_content, re.DOTALL)
    return requests


def parse_prompt_content(prompt_content):
    """
    解析prompt内容，提取对话轮次
    返回格式: [(role, content), ...]
    """
    clean_prompt = prompt_content.replace('\\n', '\n')
    pattern = r'<\|im_start\|>(user|assistant)\n(.*?)<\|im_end\|>'
    dialogues = re.findall(pattern, clean_prompt, re.DOTALL)
    return dialogues


def save_requests(requests, output_file):
    """将请求和对话内容保存到文件"""
    with open(output_file, 'a', encoding='utf-8') as f:  # 使用追加模式
        for timestamp, req_id, prompt_content in requests:
            try:
                dt = datetime.strptime(timestamp, "%m-%d %H:%M:%S.%f")
                formatted_ts = dt.strftime("%m-%d %H:%M:%S")
            except ValueError:
                formatted_ts = timestamp

            dialogues = parse_prompt_content(prompt_content)

            f.write(f"【请求时间】{formatted_ts} (ID: {req_id})\n")

            for i, (role, content) in enumerate(dialogues, 1):
                clean_content = content.replace('```json', '').replace('```', '').strip()
                f.write(f"【对话轮次 {i}】{role}:\n{clean_content}\n\n")

            f.write("-" * 50 + "\n\n")


def process_log_file(input_file, output_file):
    """处理单个日志文件并保存结果到输出文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        log_content = f.read()

    requests = extract_requests(log_content)

    if not requests:
        print(f"{input_file} 中未找到对话内容")
        return 0

    save_requests(requests, output_file)
    print(f"已从 {input_file} 提取 {len(requests)} 个请求的对话")
    return len(requests)


def process_log_directory(input_dir, output_file):
    """
    处理目录中的所有日志文件
    :param input_dir: 包含日志文件的目录路径
    :param output_file: 合并后的输出文件路径
    """
    # 清空或创建输出文件
    open(output_file, 'w', encoding='utf-8').close()

    total_requests = 0
    processed_files = 0

    # 遍历目录中的所有文件
    for filename in os.listdir(input_dir):
        if filename.endswith(".log"):  # 只处理.log文件
            file_path = os.path.join(input_dir, filename)
            if os.path.isfile(file_path):
                count = process_log_file(file_path, output_file)
                total_requests += count
                if count > 0:
                    processed_files += 1

    print("\n处理完成!")
    print(f"共处理 {processed_files} 个文件，提取 {total_requests} 个请求的对话")
    print(f"结果已保存到: {output_file}")


# 使用示例
if __name__ == "__main__":
    input_directory = "/media/indemind/disk2/mount_llm_log/LLM_Runing_Data/logs"  # 包含日志文件的文件夹
    output_file = "all_dialogues.txt"  # 合并后的输出文件

    process_log_directory(input_directory, output_file)