#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 self_cognition.json 转换为
train_dataset.json / test_dataset.json（8:2 分割）
格式： {"messages":[{"role":"user",...},{"role":"assistant",...}]}
"""
import json, random, argparse, pathlib, os

def main(raw_path: str, out_dir: str, seed: int = 42):
    random.seed(seed)

    with open(raw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = [{
        "messages": [
            {"role": "user", "content": item["instruction"]},
            {"role": "assistant", "content": item["output"]}
        ]
    } for item in data]

    random.shuffle(samples)
    split = max(1, int(len(samples) * 0.8))
    train, test = samples[:split], samples[split:]

    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(out_dir, "train_dataset.json"), 'w', encoding='utf-8') as f:
        json.dump(train, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "test_dataset.json"), 'w', encoding='utf-8') as f:
        json.dump(test, f, ensure_ascii=False, indent=2)

    print(f"✓ 生成 train_dataset.json({len(train)}) / test_dataset.json({len(test)})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_path", default="self_cognition.json")
    parser.add_argument("--out_dir",  default=".")
    args = parser.parse_args()
    main(args.raw_path, args.out_dir)
