import requests
import json
import time

#PROMPT_PATH = "/home/leon/Documents/docs/TCL-2qi/deepseek-research/test-prompt/longlongprompt/speed.txt"
PROMPT_PATH = "/home/leon/Documents/docs/TCL-2qi/deepseek-research/AIOT/repo/llm/prompt.txt" # task0416 task0418-lxy-only-example
INPUT_PATH = "./input1.txt" 
# 配置
#URL = "http://192.168.50.208:8000/v1/chat/completions" # v1/chat/completions

BASE_URL = "http://192.168.50.208:8000" #/v1/chat/completions
API_KEY = "mindo" 
MODEL_NAME = "QwQ-32B-AWQ" 


#BASE_URL = "https://api.deepseek.com" # v1/chat/completions
#API_KEY = "sk-176fa7ce0c5b4d6ea08554cff6f198ac"


def load_cleaner_prompt(path=PROMPT_PATH):
    """加载机器人专用prompt模板"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()



INPUT_CONTENT = "去卧室找爸爸"
INPUT_CONTENT = load_cleaner_prompt(INPUT_PATH)
INPUT_CONTENT = "100的99次方和99的100次方，哪个大？" #"哪咤2票房"

"""
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

"""
# 构建请求头
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

# 构建请求体

OUT_TYPE = "text" # "json_object"  # text

# 输入token长度
DATA = {
    "model": MODEL_NAME,
    "messages": [
        {"role": "system", "content": f"{load_cleaner_prompt()}"}, #
        {"role": "user", "content": f"{INPUT_CONTENT}"},
        #{"role": "assistant", "content": f""}
    ],
    #"top_k": 50,  # 控制生成文本时考虑的最高概率词汇的数量
    #"temperature": 2.0,  # 控制生成文本的随机性0.7 max 2.0
    #"max_tokens": 10000,  # 生成的最大令牌数
    #"presence_penalty": 0.1,  # 控制重复惩罚
    #"frequency_penalty": 0.1,  # 控制频率惩罚
    "stream": True, # 控制流式输出
    #"response_format":{"type": f"{OUT_TYPE}"},
    #"enable_search": "true",          # 启用搜索增强
    #"search_options": {
        #"forced_search": "true"       # 强制搜索（可能覆盖模型默认行为）
    #},
    "stream_options": {
        "include_usage": "true"      # 流式响应中包含token统计信息
    }
    
}
"""
extra_body={
        "enable_search": True, # 开启联网搜索的参数
        "search_options": {
            "forced_search": True, # 强制联网搜索的参数
            "search_strategy": "pro" # 模型将搜索10条互联网信息
            }
        }
"""

def send_request(url, headers, data):
    """发送 POST 请求并返回响应"""
    print("-d {}".format(data))
    response = requests.post(url, headers=headers, json=data, stream=True)
    return response


def print_time_length(s, _info="", _print=True):
    e = time.time()
    if _print:
        print("[TIMER] {} : {:.3f}s".format(_info, e - s))
    return e

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
                print_time_length(t_context, "json loads", False)
                
                choices = data.get('choices', [])
                
                if choices:
                    delta = choices[0].get('delta', {})
                    new_text = delta.get('content', '')
                    generated_text += new_text
                    
                    if new_text != "":
                        t_text = print_time_length(t_context, "w:{}".format(new_text), True)
                        t_cnts.append(t_text)   
                    else:
                        print_time_length(t_context, "c:{}".format(new_text), False)
    return generated_text, t_cnts


def token_size(_text):
    # TODO
    s = len(_text) * 0.6
    return s

def main():
    url = f"{BASE_URL}/v1/chat/completions"

    t_start = time.time()

    response = send_request(url, HEADERS, DATA)

    t_request = print_time_length(t_start, "request", True)
    FISTST_WORD_INDEX = 1 # 7

    if response.status_code == 200:
        generated_text, t_texts = process_stream_response(response)
        print("----Final Generated Text:----\n", generated_text)
        if len(t_texts) > 0:
            print("[time]first token: {}s, last token: {}s".format(t_texts[0] - t_start, t_texts[-1] - t_start))
        if len(t_texts) > FISTST_WORD_INDEX:
            print("[time]first word: {}s".format(t_texts[FISTST_WORD_INDEX - 1] - t_start))
            
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
    print("[time]request: {:.3f}s".format(t_request - t_start))
    t_total_end = print_time_length(t_start, "TOTAL:", True)
    token_length = token_size(generated_text)
    print(f"input is :{INPUT_CONTENT}, string-size:{len(generated_text)}, token-size:{token_length}, avg:{token_length / (t_total_end - t_start)} t/s")
    #print("API PARAM:{}".format(DATA["response_format"]))
    print("prompt path is {}".format(PROMPT_PATH))
    
if __name__ == "__main__":
    main()

