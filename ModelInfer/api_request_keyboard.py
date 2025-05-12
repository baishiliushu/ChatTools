#调用Deepseek API方式
import time

import requests
import json
from datetime import datetime, timezone

# 配置
API_KEY = "mindo"# "sk-176fa7ce0c5b4d6ea08554cff6f198ac"  # 替换为你的API Key
API_URL = "http://192.168.50.208:8000/v1/chat/completions"
PROMPT_PATH = "/home/leon/Documents/docs/TCL-2qi/deepseek-research/test-prompt/0416-ljx/task0416.txt"
MODEL_NAME = "QwQ-32B-AWQ" 

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}


def replace_session_id(s1, s2):
    # 将s1和s2从JSON字符串解析为字典
    s1_dict = json.loads(s1)
    s2_dict = json.loads(s2)
    
    # 从s1中获取session_id
    session_id = s1_dict.get("session_id", "")
    
    # 替换s2中的session_id
    s2_dict["session_id"] = session_id
    
    # 将修改后的s2字典转换回JSON字符串
    updated_s2 = json.dumps(s2_dict, ensure_ascii=False, indent=4)
    
    return updated_s2

def load_cleaner_prompt(path=PROMPT_PATH):
    """加载机器人专用prompt模板"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def print_time_length(s, _info="", _print=False):
    e = time.time()
    if _print:
        print("[TIMER] {} : {}s".format(_info, e - s))
    return e

def token_size(_text):
    total_len = len(_text) * 1.0
    # TODO: English 0.3 Chinese 0.6
    chinese_pct = 0.1
    chinese_len = total_len * chinese_pct
    english_len = total_len - chinese_len
    s = 0.3 * english_len + 0.6 * chinese_len
    return s

def process_stream_response(response):
    """处理流式响应并实时输出生成的文本"""
    t_cnts = []
    t_context = time.time()
    
    generated_text = ""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            #print(f"Received data: {decoded_line}")
            if decoded_line.startswith('data:'):
                json_data = decoded_line[len('data:'):].strip()
                if json_data == '[DONE]':
                    break
                data = json.loads(json_data)
                print_time_length(t_context, "json loads")
                
                choices = data.get('choices', [])
                
                if choices:
                    delta = choices[0].get('delta', {})
                    new_text = delta.get('content', '')
                    generated_text += new_text
                    
                    if new_text != "":
                        t_text = print_time_length(t_context, "w:{}".format(new_text))
                        t_cnts.append(t_text)   
                    else:
                        print_time_length(t_context, "c:{}".format(new_text))
    return generated_text, t_cnts


def parse_response(api_response):
    time_cnts = []
    t_context = time.time()
    new_text = api_response["choices"][0]["message"]["content"]
    t_text = print_time_length(t_context, "w:{}".format(new_text))
    t_cnts.append(t_text)  
    return text, time_cnts
    
def get_response(_response, _open_stream=True):
    generated_text = None
    t_cnts = []
    if _open_stream:
        generated_text, t_cnts = process_stream_response(_response)
    else:
        generated_text, t_cnts = parse_response(_response.json())
    return generated_text, t_cnts


def generate_command(all_inputs):
    FISTST_WORD_INDEX = 1 # 7
    

    t_start = time.time()
    
    data = {
        "model": MODEL_NAME,
        "messages": all_inputs,
        "top_k": 50,  # 控制生成文本时考虑的最高概率词汇的数量
        "temperature": 0.0,  # 控制生成文本的随机性0.7
        "max_tokens": 10000,  # 生成的最大令牌数
        "presence_penalty": 0.1,  # 控制重复惩罚
        "frequency_penalty": 0.1,  # 控制频率惩罚
        "stream": True # 控制流式输出
        }
    
    response = requests.post(API_URL, headers=HEADERS, json=data, stream=True)
    
    t_request = print_time_length(t_start, "request", True)
    
    if response.status_code == 200:
        generated_text, t_texts = get_response(response)
        print("Final Generated Text:", generated_text)
        if len(t_texts) > 0:
            print("[time]first token: {}s, last token: {}s".format(t_texts[0] - t_start, t_texts[-1] - t_start))
        if len(t_texts) > FISTST_WORD_INDEX:
            print("[time]first word: {}s".format(t_texts[FISTST_WORD_INDEX - 1] - t_start))
        print("[time]request: {:.3f}s".format(t_request - t_start))
        t_total_end = print_time_length(t_start, "TOTAL:", True)
        token_length = token_size(generated_text)
        print(f"string-size:{len(generated_text)}, token-size:{token_length}, avg:{token_length / (t_total_end - t_start)} t/s")
        
        return generated_text, t_texts
    else:
        raise Exception(f"API Error status code {response.status_code} : {response.text}")





# 示例调用
if __name__ == "__main__":
    
    messages_records = list()
    messages_records.append({"role": "system", "content": f"{load_cleaner_prompt()}"})
    mode_timer_test = True
    if mode_timer_test is True:
        sdk_input = load_cleaner_prompt("input1.txt")
        
        inputs_fixed = ["去卧室找爸爸", sdk_input]
        for i in range(0, len(inputs_fixed)):
            print("----------------------- {} -----------------------".format(i))
            messages_records.append({"role": "user", "content": "{}".format(inputs_fixed[i])})
            print("\n----- PUSH USER WORDS m {} -----".format(len(messages_records)))
            
            generated_text, t_texts = generate_command(messages_records)
            
            messages_records.append({"role": "assistant", "content": "{}".format(generated_text)})
            if i == 0:
                inputs_fixed[1] = replace_session_id(generated_text, sdk_input)
            print("\n----- PULL MODEL OUTS m {} -----".format(len(messages_records)))

    else:
    
        while True:
            # try:
            user_query = input("\nPlease input (q FOR exit): ").strip()
            if user_query.lower() == "q":
                break
            messages_records.append({"role": "user", "content": "{}".format(user_query)})
            
            print("\n----- PUSH USER WORDS m {} -----".format(len(messages_records)))
            
            generated_text, t_texts = generate_command(messages_records)

            messages_records.append({"role": "assistant", "content": "{}".format(generated_text)})
            print("\n----- PULL MODEL OUTS m {} -----".format(len(messages_records)))
        
        

