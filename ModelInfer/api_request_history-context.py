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

INPUT_CONTENT = """去厨房喊妈妈来客厅歇一会。"""

#答案：缺失的数字依次为：19, 16, 19

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
        {"role": "system", "content": f"{load_cleaner_prompt()}"}, #{load_cleaner_prompt()} 
        {"role": "user", "content": """农夫带着一只老虎、一只羊、一条蛇、一只鸡和一筐苹果要过河。

农夫的船一次只能载农夫和一样东西过河。

已知农夫不在的时候，老虎和羊在一起的话，老虎会吃掉羊，如果鸡也在的话，鸡会阻止老虎吃羊；

农夫不在的时候，蛇和鸡在一起的话，蛇会吃掉鸡，如果老虎也在的话，老虎会阻止蛇吃鸡；

农夫不在的时候羊和苹果在一起的话，羊会吃掉苹果，如果蛇也在的话，蛇会阻止羊吃苹果；

老虎不吃鸡(鸡太小不够老虎塞牙缝的)，蛇不吃苹果(蛇不吃素)。

请问农夫如何才能将老虎、羊、蛇、鸡和苹果安全送到对岸？"""},        
        {"role": "assistant", "content": """这是一个经典的逻辑谜题，可以通过一系列的步骤确保所有物品都能安全过河。我们可以通过逐步分析和调整来解决这个问题。下面是详细的步骤：

第一步：带老虎过河

农夫带老虎过河。
农夫单独返回。
第二步：带蛇过河

农夫带蛇过河。
农夫带老虎返回。
第三步：带羊过河

农夫带羊过河。
农夫单独返回。
第四步：带鸡过河

农夫带鸡过河。
农夫带蛇返回。
第五步：带苹果过河

农夫带苹果过河。
农夫单独返回。
第六步：带老虎过河

农夫带老虎过河。
农夫单独返回。
第七步：带蛇过河

农夫带蛇过河。
现在，让我们详细说明每一步的原因：

第一步：带老虎过河

把老虎先带过去，避免老虎和羊单独在一起的情况。
第二步：带蛇过河

带蛇过河，因为老虎已经在对岸，不会吃蛇。
农夫带老虎返回，因为蛇和鸡不能单独在一起。
第三步：带羊过河

带羊过河，因为此时老虎不在对岸。
农夫单独返回。
第四步：带鸡过河

带鸡过河，因为此时老虎在对岸，会阻止蛇吃鸡。
农夫带蛇返回，因为蛇和鸡不能单独在一起。
第五步：带苹果过河

带苹果过河，因为此时蛇和羊不在一起。
农夫单独返回。
第六步：带老虎过河

带老虎过河，因为此时老虎可以保护其他动物。
农夫单独返回。
第七步：带蛇过河

最后带蛇过河，因为此时所有动物都已经在对岸。
通过以上步骤，所有物品都可以安全地到达对岸。"""},
        {"role": "user", "content": "在下列序列中找出规律，并给出后续两个元素：OTTFFSSEN, OTTFFSSETE, ___, ___"},
        {"role": "assistant", "content": """这个序列实际上是由英文单词中的字母组成的，这些字母代表的是从1到某个数字的英文拼写中每个数字出现的第一个字母。

具体来说：

O = One (1)
T = Two (2)
T = Three (3)
F = Four (4)
F = Five (5)
S = Six (6)
S = Seven (7)
E = Eight (8)
N = Nine (9)
所以，这个序列是：

OTTFFSSEN (One to Nine)
OTTFFSSETE (One to Ten)
接下来的两个数字是 Eleven 和 Twelve，因此，它们的第一个字母分别是 E 和 T。

所以，序列的下两个元素是 E 和 T。

完整答案如下：```json\n{
    "content": "序列的下两个元素是E和T。",
    "expression": "喜悦",
    "id": "456",
    "session_id": "99",
    "type": "2",
    "timestamp": "2023-09-21 15:00:00"
}\n```"""},
        {"role": "user", "content": "用python编程实现计算438990637是第多少个质数，要求不要引入外部库。"},
        {"role": "assistant", "content": """要计算一个数是第几个质数，可以通过编写一个函数来判断一个数是否是质数，然后从2开始逐个检查每个数是否是质数，并记录质数的数量，直到达到目标数。

以下是具体的Python代码实现：\n```python\n\n```\n解释代码：
is_prime(n) 函数：

判断一个数 n 是否是质数。
如果 n 小于等于 1，则不是质数。
如果 n 是 2，则是质数。
如果 n 是偶数且大于 2，则不是质数。
对于大于 2 的奇数，检查从 3 到 sqrt(n) 之间的所有奇数是否能整除 n。
find_prime_position(target) 函数：

初始化计数器 count 为 0，从 2 开始逐个检查每个数是否是质数。
每当找到一个质数时，计数器 count 加 1。
当找到的目标数 target 是质数时，返回计数器 count 的值。
主程序：

定义目标数 target 为 438990637。
调用 find_prime_position(target) 函数计算其位置。
输出结果。
运行这段代码将会输出 438990637 是第多少个质数。"""},
        {"role": "user", "content": """分析下列矩阵的模式，并填写空缺处的数值（标记为?）：
2  5  10  17
4  7  12  ?
8  11 ?  23
16 ?  20  27"""

"""
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

"""},
        {"role": "assistant", "content": """综上所述，完整的矩阵如下所示：
```
2  5  10  17
4  7  12  19
8  11 16  23
16 19 20  27
```

因此，空缺处的数值分别为：19, 16, 19。"""},
        #{"role": "system", "content": "**再次强调1个输出内容要求**\n1.禁止根据聊天性质的上下文信息来“幻想出”不切实际的物联网任务\n**再次强调2个输出格式要求**\n1.不要输出任何思考过程；2.输出内容必须全部封装进Json结构（按照SYSTEM中所设定的规则）；\n /nothink"}, #{load_cleaner_prompt()} 
        {"role": "user", "content": f"{INPUT_CONTENT}"},
        #{"role": "assistant", "content": ""}
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
    #    "forced_search": "true"       # 强制搜索（可能覆盖模型默认行为）
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
                        t_text = print_time_length(t_context, "w:{}".format(new_text), False)
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

