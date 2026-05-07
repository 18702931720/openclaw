#!/usr/bin/env python3
"""
RAGFlow Agent 调用脚本
用法: uv run ragflow_agent.py "用户的问题"
"""

import sys
import json
import urllib.request
import urllib.error


API_URL = "https://aiplatformtest.sinoboom.com.cn/api/v1/agents_openai/30b8d520298211f1bdaac93124728ac9/chat/completions"
API_KEY = "ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg"


def chat(question: str) -> str:
    payload = {
        "model": "model",
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        content = result["choices"][0]["message"]["content"]
        return content
    except (KeyError, IndexError) as e:
        print(f"解析返回失败: {e}\n原始返回: {json.dumps(result, ensure_ascii=False, indent=2)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ragflow_agent.py \"用户的问题\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    answer = chat(question)
    print(answer)
