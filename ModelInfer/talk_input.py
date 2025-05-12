#调用Deepseek API方式
import time

import requests
import json
from datetime import datetime, timezone

# 配置
DEEPSEEK_API_KEY = "mindo"# "sk-176fa7ce0c5b4d6ea08554cff6f198ac"  # 替换为你的API Key
API_URL = "http://192.168.50.208:8000/v1/chat/completions"
PROMPT_PATH = "/home/leon/Documents/docs/TCL-2qi/deepseek-research/test-prompt/0416-ljx/task0416.txt"
MODEL_NAME = "QwQ-32B-AWQ" 

def load_cleaner_prompt():
    """加载机器人专用prompt模板"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_command(user_input):
    """调用DeepSeek API生成清扫指令"""
    full_prompt = f"用户输入：{user_input}"

    time_start = time.time();
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.1,  # 低随机性保证格式准确
        "max_tokens": 500
    }

    response = requests.post(API_URL, headers=headers, json=data)
    time_end = time.time()
    print("time cost: {:.2f} s".format(time_end - time_start))
    if response.status_code == 200:
        return parse_response(response.json())
    else:
        raise Exception(f"API Error: {response.text}")



def parse_response(api_response):
    """解析API响应，提取JSON指令"""
    raw_content = api_response["choices"][0]["message"]["content"]
    print(f"原始输出:\n{raw_content}")
    # # 提取第一个JSON块（适配模型可能的多余输出）
    # try:
    #     start_idx = raw_content.find("{")
    #     end_idx = raw_content.rfind("}") + 1
    #     json_str = raw_content[start_idx:end_idx]
    #     return json.loads(json_str)
    # except Exception as e:
    #     raise ValueError(f"JSON解析失败: {e}\n原始输出:\n{raw_content}")


# 示例调用
if __name__ == "__main__":
    while True:
        # try:
        user_query = input("\n用户指令输入（输入q退出）: ").strip()
        if user_query.lower() == "q":
            break

        print("\n----- 生成的指令 -----")
        command = generate_command(user_query)
        print(json.dumps(command, indent=2, ensure_ascii=Fal
