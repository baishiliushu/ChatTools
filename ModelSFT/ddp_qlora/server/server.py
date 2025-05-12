#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py · Qwen‑1.5B (合并 LoRA) 推理 API
POST /generate  { "query": "谁是你的设计者？" }
返回            { "response": "您好，我是 MinDo ..." }
"""

import time, torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

MERGED = "/home/spring/WAY/data/models/qwen2_1.5b_merged"   # ← 模型目录

# ───────── 启动时加载模型 ─────────
print("▶ 正在加载 tokenizer / model …（首次~1分钟）")
tok = AutoTokenizer.from_pretrained(MERGED, trust_remote_code=True)
tok.pad_token = tok.pad_token or tok.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MERGED,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
model.eval()
model.generation_config = GenerationConfig(
    do_sample=False,
    repetition_penalty=1.15,
    eos_token_id=tok.eos_token_id,
    pad_token_id=tok.pad_token_id
)
print("✓ 模型已就绪")

# ───────── FastAPI 定义 ─────────
app = FastAPI(title="Qwen1.5B-LoRA API")

class Req(BaseModel):
    query: str
    max_new_tokens: int = 128
    temperature: float = 1.0

@app.post("/generate")
def generate(req: Req):
    t0 = time.time()
    if not req.query.strip():
        raise HTTPException(400, "query 不能为空")

    prompt = tok.apply_chat_template(
        [{"role": "user", "content": req.query}],
        add_generation_prompt=True,
        tokenize=False
    )
    inputs = tok(prompt, return_tensors="pt").to(model.device)

    out = model.generate(
        **inputs,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature
    )
    answer = tok.decode(out[0][inputs["input_ids"].shape[-1]:],
                        skip_special_tokens=True).strip()
    return {
        "response": answer,
        "time": round(time.time() - t0, 3)
    }
