#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_save.py  ·  把 LoRA 权重合并进基模型并保存
"""

import torch, os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE   = "/data/lxy/model/Qwen2___5-1___5B-Instruct"          # 基模型
ADPT   = "/data/lxy/outputs/qwen2_1.5b_qlora_ddp"             # LoRA 目录
MERGED = "/data/lxy/outputs/qwen2_1.5b_merged"                # 输出目录

def main():
    # 1️⃣ 载入基础模型（FP16，**不要量化**）
    base = AutoModelForCausalLM.from_pretrained(
        BASE,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map="auto"        # 若显存紧张可 device_map=None + .to("cpu")
    )

    # 2️⃣ 叠加 LoRA
    model = PeftModel.from_pretrained(
        base,
        ADPT,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # 3️⃣ 合并
    model = model.merge_and_unload()      # 返回普通 Transformers 模型
    model.eval()

    # 4️⃣ 保存权重（safetensors）和 config
    os.makedirs(MERGED, exist_ok=True)
    model.save_pretrained(MERGED, safe_serialization=True)

    # 顺手把 tokenizer 也一起保存
    tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
    tok.save_pretrained(MERGED)

    print(f"✓ 已保存合并模型到 {MERGED}")

if __name__ == "__main__":
    main()
