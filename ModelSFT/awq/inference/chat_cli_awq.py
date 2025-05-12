#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_cli_awq_prompt.py
AWQ 量化 Qwen2.5-1.5B-LoRA + 外部 SYSTEM 提示词
"""

import time
import torch
import pathlib
import json
from transformers import AutoTokenizer, GenerationConfig, logging
from awq import AutoAWQForCausalLM

# ─── 配置区 ───
MODEL_DIR   = "/home/spring/WAY/data/models/qwen2_1.5b_merged_scale0.3_awq"
PROMPT_FILE = "/home/spring/WAY/python_project/ddp_qlora/prompt_inference/prompt.txt"

# ─── 读取 SYSTEM 提示词 ───
SYSTEM_PROMPT = pathlib.Path(PROMPT_FILE).read_text(encoding="utf-8").strip()
if not SYSTEM_PROMPT:
    raise RuntimeError(f"SYSTEM prompt 文件为空: {PROMPT_FILE}")

# ─── 抑制 transformers 警告 ───
logging.set_verbosity_error()

print("▶ 加载 tokenizer / AWQ 模型 …")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
# 确保 pad_token 已设，不再打印警告
tokenizer.pad_token_id = tokenizer.eos_token_id

# ---------- 加载量化模型 ----------
model = AutoAWQForCausalLM.from_quantized(
    MODEL_DIR,
    torch_dtype=torch.float16,
    device_map="auto",
    fuse_layers=False,
    trust_remote_code=True,
).eval()

# ---------- 生成配置 ----------
model.generation_config = GenerationConfig(
    do_sample=False,                # 你可以试试 True / False
    repetition_penalty=1.15,        # 防止重复
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id,
)

# ─── 推理设备 ───
infer_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"▶ Inference device: {infer_device}")

print("=== AWQ 量化模型对话（SYSTEM 注入）— exit 退出 ===")
while True:
    try:
        user = input("用户：").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if user.lower() in {"exit", "quit"}:
        break

    # 构造上下文
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user}
    ]
    prompt = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )

    # Tokenize & 移动到推理设备
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(infer_device) for k, v in inputs.items()}

    # 计时 & 生成
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=256,
            generation_config=model.generation_config,
        )
    elapsed = time.time() - t0

    # 解码 & 打印
    reply = tokenizer.decode(
        out[0][inputs["input_ids"].shape[-1]:], 
        skip_special_tokens=True
    ).strip()

    # 尝试把 reply 解析成 JSON，美化输出（可选）
    try:
        obj = json.loads(reply)
        # 用当前时间覆盖 timestamp
        obj["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pretty = json.dumps(obj, ensure_ascii=False, indent=2)
        print(f"模型：\n{pretty}")
    except json.JSONDecodeError:
        print(f"模型：{reply}")

    print(f"（耗时 {elapsed:.1f}s）\n")

torch.cuda.empty_cache()
print("Bye!")
