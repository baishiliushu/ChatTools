#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_cli.py  ·  Qwen2.5-1.5B-Instruct + LoRA (FP16 推理)

运行：
    python chat_cli.py
退出：
    输入 exit 或 Ctrl-D
"""
import torch
from transformers import (AutoTokenizer, AutoModelForCausalLM,
                          GenerationConfig)
from peft import PeftModel

# ────────────────── 路径配置 ──────────────────
BASE_MODEL = "/home/spring/WAY/data/models/Qwen2.5-1.5B-Instruct/Qwen2___5-1___5B-Instruct"          # 基础模型
LORA_DIR   = "/home/spring/WAY/data/models/qwen2_1.5b_qlora_ddp"             # LoRA 目录（根目录已有 adapter_config.json）

# ────────────────── 模型 + tokenizer ──────────────────
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token     # 确保有 pad_token

base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,      # 纯 FP16
    device_map="auto",
    trust_remote_code=True
)

model = PeftModel.from_pretrained(      # 动态加载 LoRA
    base,
    LORA_DIR,
    torch_dtype=torch.float16,
    device_map="auto",
    local_files_only=True
)
model.eval()

# ────────────────── 覆盖生成参数 ──────────────────
model.generation_config = GenerationConfig(
    do_sample=False,                  # 纯贪心
    temperature=1.0,
    top_p=1.0,
    top_k=None,
    num_beams=1,
    repetition_penalty=1.15,          # 轻度重复惩罚
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id
)

# ────────────────── 对话循环 ──────────────────
print("=== Qwen2.5-1.5B + LoRA 对话模式（exit 退出）===")
while True:
    try:
        user_input = input("用户：")
    except (EOFError, KeyboardInterrupt):
        print("\n退出。"); break
    if user_input.strip().lower() in {"exit", "quit"}:
        print("退出。"); break

    # 使用 Qwen chat 模板，保持与训练一致
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user_input}],
        add_generation_prompt=True,
        tokenize=False
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=128,
    )
    reply = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    ).strip()

    print(f"模型：{reply}\n")
