#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fine-tune Qwen-2.5-7B-Instruct with 4-bit QLoRA + DDP on 2×GPU.

示例启动：
    torchrun --standalone --master_port 29500 \
             --nproc_per_node 2 \
             run_ddp_qlora.py \
             --config qwen7b_ddp_qlora.yaml
"""
import sys
# --- 钝化 bitsandbytes Triton 依赖（若 bitsandbytes 版本较旧可能无需）---
import types
_dummy = types.ModuleType("bitsandbytes.triton")
sys.modules['bitsandbytes.triton.triton_utils']       = _dummy
sys.modules['bitsandbytes.triton.dequantize_rowwise'] = _dummy
sys.modules['bitsandbytes.nn.triton_based_modules']   = _dummy

import os
import argparse
import warnings
import yaml
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    default_data_collator,
    BitsAndBytesConfig,
)
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model,
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, help="YAML 配置路径")
    return p.parse_args()


def load_chat_dataset(train_fp, eval_fp, tokenizer, max_len):
    ds = load_dataset("json", data_files={"train": train_fp, "validation": eval_fp})

    def tokenize(example):
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False
        )
        tokens = tokenizer(
            text,
            max_length=max_len,
            truncation=True,
            padding='max_length'
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    return ds.map(
        tokenize,
        remove_columns=ds["train"].column_names,
        num_proc=4,
        desc="Tokenizing"
    )


def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    torch.cuda.set_device(local_rank)

    # 1. Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name_or_path"],
        trust_remote_code=True,
        local_files_only=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. BitsAndBytes 配置（4-bit）
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )

    # 3. 加载模型（量化 + DDP）
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name_or_path"],
        quantization_config=bnb_config,
        device_map={"": local_rank},
        trust_remote_code=True,
        local_files_only=True
    )
    model = prepare_model_for_kbit_training(model)

    # 4. LoRA
    lora_cfg = LoraConfig(
        r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=cfg["target_modules"],
    )
    model = get_peft_model(model, lora_cfg)
    if local_rank == 0:
        model.print_trainable_parameters()

    # 5. 数据集
    ds = load_chat_dataset(
        os.path.join(cfg["dataset_dir"], cfg["train_file"]),
        os.path.join(cfg["dataset_dir"], cfg["eval_file"]),
        tokenizer,
        cfg["max_seq_length"]
    )

    # 6. Trainer + DDP 设置
    training_args = TrainingArguments(
        output_dir=cfg["output_dir"],
        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        num_train_epochs=cfg["num_train_epochs"],
        learning_rate=cfg["learning_rate"],
        fp16=cfg["fp16"],
        bf16=cfg["bf16"],
        logging_steps=cfg["logging_steps"],
        evaluation_strategy=cfg["evaluation_strategy"],
        eval_steps=cfg["eval_steps"],
        save_steps=cfg["save_steps"],
        save_total_limit=3,
        ddp_find_unused_parameters=False,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=ds["train"],
        eval_dataset=ds["validation"],
        tokenizer=tokenizer,
        data_collator=default_data_collator,
    )

    # 7. 开始训练
    trainer.train()

    if local_rank == 0:
        trainer.save_model(cfg["output_dir"])
        tokenizer.save_pretrained(cfg["output_dir"])


if __name__ == "__main__":
    warnings.filterwarnings("once")
    main()
