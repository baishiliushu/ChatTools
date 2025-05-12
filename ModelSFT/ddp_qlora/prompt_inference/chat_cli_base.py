#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_cli_base_prompt.py
官方 Qwen2.5‑1.5B‑Instruct + 外部 SYSTEM 提示词
"""

import time, torch, pathlib
from transformers import (AutoTokenizer, AutoModelForCausalLM,
                          GenerationConfig)

MODEL_DIR   = "/home/spring/WAY/data/models/Qwen2.5-1.5B-Instruct"
PROMPT_FILE = "/home/spring/WAY/python_project/ddp_qlora/prompt_inference/prompt.txt"

# ───────── 读取 SYSTEM 提示词 ─────────
SYSTEM_PROMPT = pathlib.Path(PROMPT_FILE).read_text(encoding="utf-8").strip()
if not SYSTEM_PROMPT:
    raise RuntimeError(f"SYSTEM prompt 文件为空: {PROMPT_FILE}")

print("▶ 加载 tokenizer / base model …")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
).eval()

model.generation_config = GenerationConfig(
    do_sample=False,
    repetition_penalty=1.1,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id
)

print("=== 基模型对话（SYSTEM 提示已注入）— exit 退出 ===")
while True:
    try:
        user = input("用户：").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if user.lower() in {"exit", "quit"}:
        break

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user}
    ]
    prompt = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    t0 = time.time()
    out = model.generate(**inputs, max_new_tokens=256)
    reply = tokenizer.decode(
        out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True
    ).strip()
    print(f"模型：{reply}\n（耗时 {time.time()-t0:.1f}s）\n")
