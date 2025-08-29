#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量把测试集送入你的 LocalMCPClient / vLLM，大规模自动化评测。
- 兼容 JSONL（每行有 {"text": "..."} 或 {"query": "..."}）和纯 .txt（每行一条）
- 每条样本都会清空历史，保证相互独立
- 记录：索引、输入、输出、耗时（秒）、是否成功
- 输出：结果 JSONL 和 CSV

用法示例：
  python eval_datasets.py prompt_tools.txt \
      --data last_user.jsonl \
      --out-json results.jsonl \
      --out-csv results.csv \
      --max 0 \
      --history_length 6

说明：
  prompt.txt           -> 你的系统提示词文件（和你平时启动 mcp_client 一样）
  --data               -> 测试集文件路径（.jsonl或.txt）
  --max                -> 限制最多评测多少条（0 表示全部）
  其他环境变量（如 VLLM_API_URL / MODEL_NAME / VLLM_API_KEY / MCP_MODE_BY_URL）沿用你现有配置
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from typing import List, Dict, Any

# 确保可以 import 到同目录下的 mcp_client.py
from mcp_client import LocalMCPClient  # noqa: E402

def load_dataset(path: str, limit: int = 0) -> List[str]:
    ext = os.path.splitext(path)[1].lower()
    items: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        if ext == ".jsonl":
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                # 兼容 {"text": "..."} 或 {"query":"..."} 或 {"input":"..."}
                q = obj.get("text") or obj.get("query") or obj.get("input") or ""
                q = str(q).strip()
                if q:
                    items.append(q)
        else:
            # 纯文本：每行一条
            for line in f:
                q = line.strip()
                if q:
                    items.append(q)

    if limit and limit > 0:
        items = items[:limit]
    return items

async def eval_once(client: LocalMCPClient, query: str) -> Dict[str, Any]:
    await client.clear_chat_history()
    t0 = time.time()
    try:
        resp = await client.process_query(query, stream_enable=False)  # 现在返回 dict
        ok = True
        err = ""
    except Exception as e:
        resp = None
        ok = False
        err = str(e)
    t1 = time.time()

    # 兜底
    answer = ""
    first_tool_calls = []
    first_latency_s = None
    second_latency_s = None
    if isinstance(resp, dict):
        answer = resp.get("answer") or ""
        first_tool_calls = resp.get("first_tool_calls") or []
        first_latency_s = resp.get("first_latency_s")
        second_latency_s = resp.get("second_latency_s")

    return {
        "query": query,
        "answer": answer,
        "latency_s": round(t1 - t0, 3),          # 整体耗时（包含二次推理）
        "first_latency_s": first_latency_s,      # 首次模型调用耗时
        "second_latency_s": second_latency_s,    # 二次推理耗时（若无工具则为 0 或 None）
        "first_tool_calls": first_tool_calls,    # 中间 tool_calls 的完整参数
        "ok": ok,
        "error": err,
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_path", help="你的系统提示词文件 prompt.txt")
    ap.add_argument("--data", required=True, help="测试集：.jsonl（含 text/query/input 字段）或 .txt（每行一条）")
    ap.add_argument("--out-json", default="results.jsonl", help="输出 JSONL（默认 results.jsonl）")
    ap.add_argument("--out-csv", default="results.csv", help="输出 CSV（默认 results.csv）")
    ap.add_argument("--max", type=int, default=0, help="最多评测多少条（0 表示全部）")
    ap.add_argument("--history_length", type=int, default=6, help="单次会话的长度限制")
    args = ap.parse_args()

    # 载入数据
    queries = load_dataset(args.data, args.max)
    if not queries:
        print(f"[ERR] 数据为空：{args.data}")
        sys.exit(2)

    # 初始化 client（沿用你现有的环境变量与连接模式）
    client = LocalMCPClient(args.prompt_path, args.history_length)
    try:
        await client.initialize_http_session()
        await client.connect_to_mcp()
    except Exception as e:
        print(f"[ERR] 初始化/连接 MCP 失败：{e}")
        sys.exit(3)

    results: List[Dict[str, Any]] = []
    print(f"🔧 开始评测，共 {len(queries)} 条…")
    for i, q in enumerate(queries, 1):
        r = await eval_once(client, q)
        results.append(r)
        status = "OK" if r["ok"] else "ERR"
        print(f"[{i}/{len(queries)}] {status}  {r['latency_s']}s  {q[:60]}")

    # 收尾
    await client.cleanup()

    # 写 JSONL
    with open(args.out_json, "w", encoding="utf-8") as wj:
        for r in results:
            wj.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 写 CSV
    with open(args.out_csv, "w", encoding="utf-8", newline="") as wc:
        writer = csv.writer(wc)
        writer.writerow([
            "idx",
            "query",
            "answer",
            "latency_s",
            "first_latency_s",
            "second_latency_s",
            "first_tool_calls",  # 序列化为字符串写入
            "ok",
            "error"
        ])
        for i, r in enumerate(results):
            writer.writerow([
                i,
                r.get("query", ""),
                r.get("answer", ""),
                r.get("latency_s", ""),
                r.get("first_latency_s", ""),
                r.get("second_latency_s", ""),
                json.dumps(r.get("first_tool_calls", []), ensure_ascii=False),
                r.get("ok", ""),
                r.get("error", "")
            ])

    print(f"\n✅ 完成！JSONL -> {args.out_json} ，CSV -> {args.out_csv}")

if __name__ == "__main__":
    asyncio.run(main())
