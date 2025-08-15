from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from scipy.spatial.distance import cosine
import json
import os
import logging
from tqdm import tqdm

# 配置详细日志输出
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 加载模型和分词器
MODEL_NAME = "uer/sbert-base-chinese-nli"
logger.info("加载分词器...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
logger.info("加载模型架构...")
model = AutoModel.from_pretrained(MODEL_NAME)
logger.info("模型加载完成!")


def get_sentence_embedding(sentence):
    """将句子编码为语义向量"""
    inputs = tokenizer(
        sentence,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=64
    )
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
    return embeddings.numpy()


def semantic_similarity(emb1, emb2):
    """计算两个嵌入向量的语义相似度"""
    return 1 - cosine(emb1, emb2)


def process_file(input_file_path, output_file_path, similarity_threshold=0.7):
    """
    处理文件，对user字段进行语义去重

    参数:
    input_file_path: 输入文件路径
    output_file_path: 输出文件路径
    similarity_threshold: 相似度阈值(0-1之间)
    """
    # 读取文件内容
    with open(input_file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # 解析JSON并提取user字段
    user_data = []
    for line in lines:
        try:
            data = json.loads(line)
            user_text = data.get("user", "").strip()
            if user_text:
                user_data.append({
                    "original_line": line,
                    "user_text": user_text,
                    "embedding": None  # 稍后计算
                })
        except json.JSONDecodeError:
            logger.warning(f"JSON解析错误，跳过行: {line}")

    logger.info(f"找到 {len(user_data)} 个有效user字段")

    # 计算嵌入向量
    logger.info("计算文本嵌入向量...")
    for item in tqdm(user_data, desc="处理文本"):
        item["embedding"] = get_sentence_embedding(item["user_text"])

    # 语义去重
    logger.info("进行语义去重...")
    unique_items = []
    embeddings_cache = []

    for item in tqdm(user_data, desc="去重处理"):
        is_duplicate = False
        current_embedding = item["embedding"]

        # 与已保留项比较相似度
        for emb in embeddings_cache:
            similarity = semantic_similarity(current_embedding, emb)
            if similarity >= similarity_threshold:
                is_duplicate = True
                break

        # 如果不是重复项则保留
        if not is_duplicate:
            unique_items.append(item["original_line"])
            embeddings_cache.append(current_embedding)

    logger.info(f"去重后保留 {len(unique_items)} 个唯一项 (原 {len(user_data)} 项)")

    # 保存结果到新文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for line in unique_items:
            f.write(line + '\n')

    logger.info(f"结果已保存到: {output_file_path}")


if __name__ == "__main__":
    # 文件路径配置
    input_file = "all_chinese_user_reason_data.txt"
    output_file = "different_user_data.txt"

    # 处理文件
    process_file(input_file, output_file, similarity_threshold=0.75)

    logger.info("处理完成!")