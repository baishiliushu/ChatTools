#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_base_fixed.py — 只测官方 Qwen2.5-1.5B-Instruct（FP16 不量化）
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

BASE = "/home/spring/WAY/data/models/Qwen2.5-1.5B-Instruct/Qwen2___5-1___5B-Instruct"  # ← 注意和目录名精确匹配

# 1) 加载
tokenizer = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
model.eval()

# 2) 覆盖生成配置：纯贪心 + 轻度重复惩罚
model.generation_config = GenerationConfig(
    do_sample=False,
    num_beams=1,
    repetition_penalty=1.1,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id
)

print(">>> 测试原始基模型（exit 或 quit 退出）")
while True:
    q = input("用户：").strip()
    if q.lower() in ("exit", "quit"):
        break
    # 用 Qwen chat 模板
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": q}],
        add_generation_prompt=True,
        tokenize=False
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=64)
    ans = tokenizer.decode(
        out[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    ).strip()
    print("模型：", ans, "\n")
