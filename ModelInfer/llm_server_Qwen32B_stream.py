import gradio as gr
import requests
import json
import time

DEEPSEEK_API_KEY = "mindo"
API_URL = "http://192.168.50.208:8000/v1/chat/completions"
PROMPT_PATH = "/home/ljx/Code/200sever/work/ljx/scripts/LLM/prompt.txt"


def load_system_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


system_prompt = load_system_prompt()
chat_history = [{"role": "system", "content": system_prompt}]  # 全局对话上下文


def chat(user_input, history_ui):
    chat_history.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "QwQ-32B-AWQ",
        "messages": chat_history,
        "temperature": 0.1,
        "max_tokens": 1000
    }

    time_start = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    time_end = time.time()

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
    else:
        reply = f"API Error: {response.text}"

    chat_history.append({"role": "assistant", "content": reply})
    history_ui.append((user_input, reply))

    return history_ui, history_ui


def reset():
    global chat_history
    chat_history = [{"role": "system", "content": system_prompt}]
    return [], []


with gr.Blocks(title="🧹 MinDo 本地清扫任务助手") as demo:
    gr.Markdown("## 🤖 MinDo 本地指令生成助手\n支持多轮上下文")
    chatbot = gr.Chatbot()
    with gr.Row():
        msg = gr.Textbox(placeholder="请输入指令...")
        submit_btn = gr.Button("发送")
        clear_btn = gr.Button("清空对话")

    submit_btn.click(chat, inputs=[msg, chatbot], outputs=[chatbot, chatbot])
    clear_btn.click(fn=reset, inputs=[], outputs=[chatbot, chatbot])
    msg.submit(chat, inputs=[msg, chatbot], outputs=[chatbot, chatbot])  # 支持回车发送

demo.launch(server_name="192.168.50.222", server_port=7860, share=False)

