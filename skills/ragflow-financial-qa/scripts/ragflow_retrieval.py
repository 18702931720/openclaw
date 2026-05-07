#!/usr/bin/env python3
"""
RAGFlow 财务知识库检索脚本
用法: python3 ragflow_retrieval.py "用户问题"
"""

import json
import sys
import re
import urllib.request
import urllib.error

# 配置
API_URL = "https://aiplatformtest.sinoboom.com.cn/api/v1/retrieval"
API_KEY = "ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg"
DATASET_ID = "d189caa8274e11f1bdaac93124728ac9"
TOPK = 10


def clean_html(text):
    """清理HTML标签，保留表格结构"""
    # 保留表格基本结构
    text = re.sub(r'<table[^>]*>', '<TABLE>', text)
    text = re.sub(r'</table>', '</TABLE>', text)
    text = re.sub(r'<tr[^>]*>', '<ROW>', text)
    text = re.sub(r'</tr>', '</ROW>', text)
    text = re.sub(r'<td[^>]*>', '<CELL>', text)
    text = re.sub(r'</td>', '</CELL>', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('<TABLE>', '\n【表格】')
    text = text.replace('</TABLE>', '\n【表格完】')
    text = text.replace('<ROW>', '\n  |')
    text = text.replace('</ROW>', '')
    text = text.replace('<CELL>', ' | ')
    text = text.replace('</CELL>', '')
    return text.strip()


def retrieval(question, topk=TOPK):
    """调用RAGFlow检索API"""
    payload = {
        "dataset_ids": [DATASET_ID],
        "question": question,
        "topk": topk
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        return {"code": e.code, "message": str(e)}
    except Exception as e:
        return {"code": -1, "message": str(e)}


def format_results(result):
    """格式化检索结果"""
    if result.get('code') != 0:
        return f"检索失败: {result.get('message', '未知错误')}"
    
    chunks = result.get('data', {}).get('chunks', [])
    if not chunks:
        return "未找到相关结果"
    
    output = []
    for i, chunk in enumerate(chunks, 1):
        doc_name = chunk.get('document_keyword', '未知文档')
        similarity = chunk.get('similarity', 0)
        content = clean_html(chunk.get('content', ''))
        
        output.append(f"--- 结果{i} | 相似度:{similarity:.1%} | {doc_name} ---")
        output.append(content[:500])  # 限制长度
        output.append("")
    
    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 ragflow_retrieval.py \"问题\"")
        sys.exit(1)
    
    question = sys.argv[1]
    result = retrieval(question)
    print(format_results(result))
