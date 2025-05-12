#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pathlib
import time
from datetime import datetime

from openai import OpenAI
from transformers import AutoTokenizer

# ───── 配置 ─────
API_BASE   = "http://192.168.50.139:8001/v1"
API_KEY    = "indemind"
MODEL_NAME = "qwen2-1.5b-scale0.3"
PROMPT_TXT = pathlib.Path(
    "/home/spring/WAY/python_project/ddp_qlora/prompt_inference/prompt.txt"
)
TEMPERATURE = 0.0
TOP_P       = 1.0
MAX_TOKENS  = 512
EXTRA_BODY  = {"repetition_penalty": 1.15}
# ─────────────────

SYSTEM_PROMPT = PROMPT_TXT.read_text(encoding="utf-8").strip()
if not SYSTEM_PROMPT:
    raise RuntimeError(f"prompt.txt 为空：{PROMPT_TXT}")

# 初始化 OpenAI 兼容客户端
client = OpenAI(api_key=API_KEY, base_url=API_BASE)

# 初始化 tokenizer（Qwen 系列需 trust_remote_code=True）
tokenizer = AutoTokenizer.from_pretrained(
    "/home/spring/WAY/data/models/qwen2.5-7b-instruct", trust_remote_code=True  # 任选一个与服务端兼容的 Qwen tokenizer
)

print("已连接 vLLM-AWQ；输入 /exit 结束。\n")

def count_prompt_tokens(messages):
    """尽量用官方 chat_template 统计 prompt token 数"""
    try:
        prompt_fmt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        # 退化：直接拼 role+content
        prompt_fmt = "\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\nassistant:"
    return len(tokenizer(prompt_fmt).input_ids)

def call_model_stream(user_text: str):
    """流式推理：返回完整内容、计时、token 统计"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_text},
    ]
    prompt_tokens = count_prompt_tokens(messages)

    print("模型：", end="", flush=True)
    t0 = time.time()
    first_token_at, last_token_at = None, None
    full_reply = ""

    resp = client.chat.completions.create(
        model       = MODEL_NAME,
        messages    = messages,
        temperature = TEMPERATURE,
        top_p       = TOP_P,
        max_tokens  = MAX_TOKENS,
        extra_body  = EXTRA_BODY,
        stream      = True,
    )

    for chunk in resp:
        now = time.time()
        if first_token_at is None:
            first_token_at = now
        last_token_at = now

        delta = chunk.choices[0].delta
        content = delta.content if delta and delta.content else ""
        print(content, end="", flush=True)
        full_reply += content

    print()  # 换行
    gen_tokens = len(tokenizer(full_reply).input_ids)
    return (
        full_reply,              # 0
        prompt_tokens,           # 1
        gen_tokens,              # 2
        t0, first_token_at, last_token_at  # 3,4,5
    )

def pretty_print(reply: str):
    """打印 JSON 并刷新 timestamp"""
    try:
        obj = json.loads(reply)
        obj["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(reply)

# ───── 主循环 ─────
while True:
    try:
        user = input("用户：").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBye"); break

    if user.lower() in {"/exit", "exit", "quit"}:
        print("Bye"); break
    if not user:
        continue

    (full_reply,
     prompt_tokens,
     gen_tokens,
     t0, first_token_at, last_token_at) = call_model_stream(user)

    print("—— 结构化输出：")
    pretty_print(full_reply)

    # 生成速度（避免除零）
    gen_duration = max(1e-6, last_token_at - first_token_at)
    speed_tok_s  = gen_tokens / gen_duration

    print("—— 性能统计：")
    print(f"Prompt 长度: {prompt_tokens} tokens")
    print(f"生成长度: {gen_tokens} tokens")
    print(f"首 token 延迟: {first_token_at - t0:.3f}s")
    print(f"生成耗时: {gen_duration:.3f}s")
    print(f"生成速度: {speed_tok_s:.2f} tok/s")
    print(f"总耗时: {last_token_at - t0:.3f}s\n")
