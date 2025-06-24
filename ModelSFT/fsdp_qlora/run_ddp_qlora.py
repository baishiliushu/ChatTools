#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fine-tune Qwen-2.5-7B-Instruct with 4-bit QLoRA + DistributedDataParallel (DDP).

启动示例（2 GPU）：
    torchrun --standalone --nproc_per_node 2 --master_port 29500 \
             run_ddp_qlora.py --config qwen7b_ddp_qlora.yaml
"""
import os, argparse, warnings, yaml, torch
from datasets import load_dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM,
                          TrainingArguments, Trainer,
                          DataCollatorForLanguageModeling)
from peft import (prepare_model_for_kbit_training,
                  LoraConfig, get_peft_model)

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:16"
# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True,
                    help="YAML 配置文件路径")
    return ap.parse_args()

# ──────────────────────────────────────────────────────────────────────────────
def load_chat_dataset(train_file, eval_file, tokenizer, max_len):
    """
    读取 self-cognition 划分好的 json 并用 Qwen chat 模板格式化→tokenize
    """
    ds = load_dataset("json",
                      data_files={"train": train_file,
                                  "validation": eval_file})

    def tokenize(example):
        text = tokenizer.apply_chat_template(
            example["messages"],            # list[dict]
            tokenize=False,
            add_generation_prompt=False     # 不追加 assistant 起始标记
        )
        tokens = tokenizer(text,
                           max_length=max_len,
                           truncation=True)
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    return ds.map(tokenize,
                  remove_columns=ds["train"].column_names,
                  num_proc=2,
                  desc="Tokenizing")

# ──────────────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    cfg  = yaml.safe_load(open(args.config, "r", encoding="utf-8"))

    # 本地 rank（torchrun 会设置）
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    torch.cuda.set_device(local_rank)

    # ── 1. tokenizer ──────────────────────────────────────────────────────────
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name_or_path"],
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:          # Qwen 通常无 pad_token
        tokenizer.pad_token = tokenizer.eos_token

    print("# ── 2. base model (4-bit OR 8-bit) ─────────────────────────────────────────────────")
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name_or_path"],
        load_in_8bit      = True,                # bits-and-bytes
        torch_dtype       = torch.float16,
        device_map        = {"": local_rank},    # 每 GPU 一份（数据并行）
        trust_remote_code = True
    )
    model.gradient_checkpointing_enable()# <-- 新增此行
    print("# -- 2-1. gradient_checkpointin :{}".format(model.is_gradient_checkpointing))
    model = prepare_model_for_kbit_training(model)

    print("# ── 3. LoRA 适配 ───────────────────────────────────────────────────────────")
    lora_cfg = LoraConfig(
        r            = cfg["lora_r"],
        lora_alpha   = cfg["lora_alpha"],
        lora_dropout = cfg["lora_dropout"],
        bias         = "none",
        task_type    = "CAUSAL_LM",
        target_modules = cfg["target_modules"]   # list[str]
    )
    model = get_peft_model(model, lora_cfg)
    if local_rank == 0:
        model.print_trainable_parameters()

    print("# ── 4. 数据集 ─────────────────────────────────────────────────────────────")
    ds = load_chat_dataset(
        os.path.join(cfg["dataset_dir"], cfg["train_file"]),
        os.path.join(cfg["dataset_dir"], cfg["eval_file"]),
        tokenizer,
        cfg["max_seq_length"]
    )
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    print("# ── 5. Trainer / DDP ──────────────────────────────────────────────────────")
    train_args = TrainingArguments(
        output_dir                 = cfg["output_dir"],
        per_device_train_batch_size= cfg["per_device_train_batch_size"],
        per_device_eval_batch_size = cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps= cfg["gradient_accumulation_steps"],
        num_train_epochs           = cfg["num_train_epochs"],
        learning_rate              = cfg["learning_rate"],
        fp16                       = cfg["fp16"],
        bf16                       = cfg["bf16"],
        logging_steps              = cfg["logging_steps"],
        evaluation_strategy        = cfg["evaluation_strategy"],
        eval_steps                 = cfg["eval_steps"],
        save_steps                 = cfg["save_steps"],
        save_total_limit           = 3,
        ddp_find_unused_parameters = False,      # LoRA 层不会被丢弃
        report_to                  = "none"
    )

    trainer = Trainer(
        model         = model,
        args          = train_args,
        train_dataset = ds["train"],
        eval_dataset  = ds["validation"],
        tokenizer     = tokenizer,
        data_collator = collator
    )

    print("# ── 6. 训练 ───────────────────────────────────────────────────────────────")
    trainer.train()

    # 只在 rank 0 保存
    if local_rank == 0:
        trainer.save_model(cfg["output_dir"])
        tokenizer.save_pretrained(cfg["output_dir"])

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    warnings.filterwarnings("once")
    main()
