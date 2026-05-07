#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow Agent 快速查询 - 单行命令调用
用法：python3 ragflow-query.py "你的问题"
"""

import requests
import json
import sys

# RAGFlow 配置
RAGFLOW_BASE_URL = "https://aiplatformtest.sinoboom.com.cn"
RAGFLOW_API_KEY = "ragflow-FcBk2dcA9daM3eH2Yt7Ady4sDWN3zDbYTpvCfLaW8xo"
RAGFLOW_AGENT_ID = "675e6fe42f0011f1bc6b2950cf007153"

def query_ragflow(question):
    """查询 RAGFlow"""
    url = f"{RAGFLOW_BASE_URL}/api/v1/agent/{RAGFLOW_AGENT_ID}/chat"
    
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": question,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 ragflow-query.py \"你的问题\"")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    result = query_ragflow(question)
    print(json.dumps(result, ensure_ascii=False, indent=2))
