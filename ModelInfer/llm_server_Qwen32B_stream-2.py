import gradio as gr
import requests
import json
import time

DEEPSEEK_API_KEY = "mindo"
API_URL = "http://192.168.50.208:8000/v1/chat/completions"
PROMPT_PATH = "/home/ljx/Code/200sever/project/Rubby/extend/prompt.txt"


def load_system_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


system_prompt = load_system_prompt()


def chat(user_input, history_ui, state):
    # 添加用户输入
    state.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "QwQ-32B-AWQ",
        "messages": state,
        "temperature": 0.1,
        "max_tokens": 1000,
        "response_format":{"type": "json_object"},
        "stream": True,
    }

    time_start = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    time_end = time.time()
    print("响应耗时: {:.2f}s".format(time_end - time_start))

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
    else:
        reply = f"API Error: {response.text}"

    state.append({"role": "assistant", "content": reply})
    history_ui.append((user_input, reply))

    return history_ui, history_ui, state


def reset():
    new_state = [{"role": "system", "content": system_prompt}]
    return [], [], new_state


# --- 构建界面 ---
with gr.Blocks(title="🧹 MinDo 本地清扫任务助手") as demo:
    gr.Markdown("## 🤖 MinDo 清扫任务指令生成器\n支持局域网多用户、多轮上下文")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="请输入指令...", label="用户输入")
    state = gr.State([{"role": "system", "content": system_prompt}])  # 每个用户独立上下文

    submit_btn = gr.Button("发送")
    clear_btn = gr.Button("清空对话")

    submit_btn.click(chat, inputs=[msg, chatbot, state], outputs=[chatbot, chatbot, state])
    msg.submit(chat, inputs=[msg, chatbot, state], outputs=[chatbot, chatbot, state])
    clear_btn.click(fn=reset, inputs=[], outputs=[chatbot, chatbot, state])

# 启动服务，供局域网访问
demo.launch(server_name="192.168.50.222", server_port=7860, share=False)
