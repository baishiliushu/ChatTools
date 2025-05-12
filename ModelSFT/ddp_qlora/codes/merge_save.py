#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_save.py  ·  按给定 scale 把 LoRA 权重合并进基模型并保存

示例：
    python merge_save.py --scale 0.3
"""

import os, argparse, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from peft.tuners.lora import LoraLayer

BASE = "/home/spring/WAY/data/models/Qwen2.5-1.5B-Instruct/Qwen2___5-1___5B-Instruct"
ADPT = "/home/spring/WAY/data/models/qwen2_1.5b_qlora_ddp"        # LoRA 目录
OUT_ROOT = "/home/spring/WAY/data/models/qwen2_1.5b_merged/scale0.3"                         # 输出根目录

def scale_lora_layers(model: PeftModel, factor: float):
    """
    遍历所有 LoRA 层，把 scaling[adapter] *= factor
    兼容 peft ≥0.15（scaling 为 dict）
    """
    for module in model.modules():
        if isinstance(module, LoraLayer):
            for k in module.scaling.keys():
                module.scaling[k] *= factor

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="LoRA 缩放因子 (默认 1.0)")
    return ap.parse_args()

def main():
    args = parse_args()
    if args.scale <= 0:
        raise ValueError("--scale 必须 > 0")

    merged_dir = os.path.join(OUT_ROOT, f"qwen2_1.5b_merged_scale{args.scale}")
    os.makedirs(merged_dir, exist_ok=True)

    # 1️⃣ 基模型
    base = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.float16,
        trust_remote_code=True, device_map="auto"
    )

    # 2️⃣ LoRA
    model = PeftModel.from_pretrained(
        base, ADPT,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # 3️⃣ 缩放
    if args.scale != 1.0:
        scale_lora_layers(model, args.scale)
        print(f"→ 已将所有 LoRA scaling × {args.scale}")

    # 4️⃣ 合并
    merged = model.merge_and_unload().eval()

    # 5️⃣ 保存
    merged.save_pretrained(merged_dir, safe_serialization=True)
    AutoTokenizer.from_pretrained(BASE, trust_remote_code=True) \
                 .save_pretrained(merged_dir)

    print(f"✓ 已保存合并模型到 {merged_dir}")

if __name__ == "__main__":
    main()