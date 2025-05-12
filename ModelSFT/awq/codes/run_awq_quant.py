#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将已合并的 Qwen‑2.5‑1.5B 模型量化为 4‑bit AWQ
"""

import random, torch
from pathlib import Path
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer
from datasets import load_dataset

# === 路径 ===
model_path = Path("/home/spring/WAY/data/models/qwen2_1.5b_merged_scale0.3")
quant_path = Path("/home/spring/WAY/data/models/qwen2_1.5b_merged_scale0.3_awq")

# === 量化超参 ===
quant_config = {
    "zero_point": True,     # 建议保持开启
    "q_group_size": 128,    # 128 通道一组
    "w_bit": 4,             # 4‑bit
    "version": "GEMM"       # 批量推理通用；若单句请求多，可改为 "GEMV"
}

# === 1. 加载 tokenizer & 模型 ===
print("▶ Loading tokenizer / FP16 model …")
tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
model = AutoAWQForCausalLM.from_pretrained(
    str(model_path),
    device_map="auto",
    safetensors=True
)

# === 2. 读取并格式化校准数据 ===
ds_path = "/home/spring/WAY/data/tuning_json/identity.json"
dataset = load_dataset("json", data_files=ds_path, split="train")

def to_chatml(example):
    """把 {instruction,input,output} 转成 Qwen ChatML 文本"""
    user_text = example["instruction"].strip()
    if example["input"]:
        user_text += "\n" + example["input"].strip()

    messages = [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": example["output"].strip()}
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    ).strip()

# 取全部样本；如需加速随机抽 128‑256 条
calib_texts = [to_chatml(ex) for ex in dataset]
# random.seed(42); calib_texts = random.sample(calib_texts, k=256)

print(f"▶ Calibration samples: {len(calib_texts)}")

# === 3. 量化 ===
print("▶ Quantizing …")
model.quantize(tokenizer, quant_config=quant_config, calib_data=calib_texts)

# === 4. 保存量化模型 ===
quant_path.mkdir(parents=True, exist_ok=True)           # 创建目录
model.save_quantized(str(quant_path), safetensors=True, shard_size="1GB")
tokenizer.save_pretrained(str(quant_path))

print(f"✅ AWQ 量化完成：{quant_path}")
