from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from scipy.spatial.distance import cosine
import logging
import os
import requests
from tqdm import tqdm

# 配置详细日志输出
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 检查模型是否已下载
MODEL_NAME = "uer/sbert-base-chinese-nli"
MODEL_PATH = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub",
                          f"models--{MODEL_NAME.replace('/', '--')}")


def download_with_progress(url, filename):
    """带进度条的文件下载函数"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(filename, 'wb') as file, tqdm(
            desc=f"下载 {os.path.basename(filename)}",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def load_model():
    """加载模型并显示下载进度"""
    logger.info("正在准备语义相似度模型...")

    # 检查模型是否已缓存
    if os.path.exists(os.path.join(MODEL_PATH, "snapshots")):
        logger.info(f"模型已缓存 ({MODEL_NAME})，跳过下载")
    else:
        logger.info(f"首次使用需要下载预训练模型 ({MODEL_NAME})")
        logger.info("模型大小约 420MB，下载时间取决于网络速度...")

        # 实际中transformers会自动下载，这里仅显示提示
        # 真实项目可用上述download_with_progress函数实现自定义下载

    logger.info("加载分词器...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    logger.info("加载模型架构...")
    model = AutoModel.from_pretrained(MODEL_NAME)

    logger.info("模型加载完成!")
    return tokenizer, model


# 加载模型和分词器
logger.info("=" * 50)
logger.info("中文语义相似度分析系统初始化中")
logger.info("=" * 50)
tokenizer, model = load_model()
logger.info(f"模型架构: {type(model).__name__}")
logger.info(f"参数量: {sum(p.numel() for p in model.parameters()):,}")
logger.info("=" * 50 + "\n")


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


def semantic_similarity(text1, text2):
    """计算两个文本的语义相似度"""
    emb1 = get_sentence_embedding(text1)
    emb2 = get_sentence_embedding(text2)
    return 1 - cosine(emb1, emb2)


def is_meaning_similar(text1, text2, threshold=0.7):
    """判断两个字符串含义是否相似"""
    similarity = semantic_similarity(text1, text2)
    logger.debug(f"相似度计算: '{text1}' vs '{text2}' = {similarity:.4f}")
    return similarity >= threshold


if __name__ == "__main__":
    # 测试示例
    test_cases = [
        ("去床下找鞋子", "去床第找鞋子", True),
        ("去床下找鞋子", "在床下找找有没有鞋子", True),
        ("找鞋子在床下", "把鞋子从床底下拿出来", True),
        ("去床下找鞋子", "打开窗户通风", False),
        ("寻找床底的鞋子", "整理书架上的书本", False)
    ]

    logger.info("开始语义相似度测试...")
    logger.info(f"判断阈值: 0.7\n" + "-" * 50)

    for i, (text1, text2, expected) in enumerate(test_cases):
        result = is_meaning_similar(text1, text2)
        status = "✓" if result == expected else "✗"
        similarity = semantic_similarity(text1, text2)

        print(f"测试案例 {i + 1} {status}")
        print(f"文本1: 「{text1}」")
        print(f"文本2: 「{text2}」")
        print(f"相似度: {similarity:.4f}")
        print(f"预测: {'相似' if result else '不相似'} | 预期: {'相似' if expected else '不相似'}")
        print("-" * 50)

    # 额外测试
    text_a = "去床下找鞋子"
    text_b = "在床下找找有没有鞋子"
    similarity_score = semantic_similarity(text_a, text_b)

    print("\n额外分析:")
    print(f"「{text_a}」和「{text_b}」的详细分析:")
    print(f"语义相似度: {similarity_score:.4f}")
    print(f"系统判断: {'含义相似' if is_meaning_similar(text_a, text_b) else '含义不同'}")