#!/usr/bin/env python3
import requests, json

SERVER = "http://192.168.50.205:8000"

def chat():
    print("远程 Qwen‑1.5B 对话（exit 退出）")
    while True:
        q = input("用户：").strip()
        if q.lower() in {"exit", "quit"}:
            break
        payload = {"query": q}
        r = requests.post(f"{SERVER}/generate",
                          json=payload, timeout=60)
        if r.status_code == 200:
            print("模型：", r.json()["response"], "\n")
        else:
            print("错误：", r.status_code, r.text)

if __name__ == "__main__":
    chat()
