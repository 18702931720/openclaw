#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow API 完整测试脚本
测试多种可能的 API 端点
"""

import requests
import json

BASE_URL = "https://aiplatformtest.sinoboom.com.cn"
API_KEY = "ragflow-FcBk2dcA9daM3eH2Yt7Ady4sDWN3zDbYTpvCfLaW8xo"
AGENT_ID = "675e6fe42f0011f1bc6b2950cf007153"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

endpoints = [
    # Agent 对话端点
    ("POST", f"/api/v1/agents_openai/{AGENT_ID}/chat/completions", {
        "model": "model",
        "messages": [{"role": "user", "content": "财务报销流程"}],
        "stream": False
    }),
    ("POST", f"/api/v1/agent/{AGENT_ID}/chat", {
        "query": "财务报销流程",
        "stream": False
    }),
    ("POST", f"/v1/agents_openai/{AGENT_ID}/chat/completions", {
        "model": "model",
        "messages": [{"role": "user", "content": "测试"}],
        "stream": False
    }),
    # Chat 端点
    ("POST", f"/api/v1/chats_openai/{AGENT_ID}/chat/completions", {
        "model": "model",
        "messages": [{"role": "user", "content": "测试"}],
        "stream": False
    }),
    # 检索端点
    ("POST", "/api/v1/retrieval", {
        "question": "财务报销流程",
        "dataset_ids": []
    }),
    # 列表端点
    ("GET", "/api/v1/agents", None),
    ("GET", "/api/v1/kb", None),
    ("GET", "/api/v1/dataset", None),
]

print("🔍 RAGFlow API 端点测试")
print("=" * 60)

for method, endpoint, data in endpoints:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"  状态码：{response.status_code}")
        
        try:
            result = response.json()
            if result.get("code") == 0:
                print(f"  ✅ 成功！")
                print(f"  响应：{json.dumps(result, ensure_ascii=False)[:500]}")
            else:
                print(f"  ❌ 错误：{result}")
        except:
            print(f"  响应：{response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ 异常：{e}")

print("\n" + "=" * 60)
print("测试完成")
