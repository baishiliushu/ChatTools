#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_cli_merged.py  ·  直接推理已合并的 Qwen2.5‑1.5B 模型
运行: python chat_cli_merged.py
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

MERGED = "/home/spring/WAY/data/models/qwen2_1.5b_merged"

# 1️⃣ tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    MERGED,
    trust_remote_code=True
)
if tokenizer.pad_token is None:            # 双保险
    tokenizer.pad_token = tokenizer.eos_token

# 2️⃣ 加载合并模型
model = AutoModelForCausalLM.from_pretrained(
    MERGED,
    torch_dtype=torch.float16,
    device_map="auto",                     # 单 3090/4090 或多卡均可
    trust_remote_code=True
)
model.eval()

# 3️⃣ 默认生成参数
model.generation_config = GenerationConfig(
    do_sample=False,
    repetition_penalty=1.15,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id
)

print("=== Qwen‑1.5B ‑ 已合并 LoRA，输入 exit 退出 ===")
while True:
    try:
        user = input("用户：").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if user.lower() in {"exit", "quit"}:
        break

    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        add_generation_prompt=True,
        tokenize=False
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output = model.generate(**inputs, max_new_tokens=128)
    answer = tokenizer.decode(
        output[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    ).strip()
    print("模型：", answer, "\n")
