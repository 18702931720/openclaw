#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow Agent 对话工具
直接在对话中调用 RAGFlow Agent API 进行问答
"""

import requests
import json
import sys

# RAGFlow 配置
RAGFLOW_CONFIG = {
    "base_url": "https://aiplatformtest.sinoboom.com.cn",
    "api_key": "ragflow-FcBk2dcA9daM3eH2Yt7Ady4sDWN3zDbYTpvCfLaW8xo",
    "agent_id": "675e6fe42f0011f1bc6b2950cf007153"
}

def ragflow_chat(query, conversation_id=None):
    """
    调用 RAGFlow Agent 进行对话
    
    Args:
        query: 用户问题
        conversation_id: 可选的会话 ID（用于保持上下文）
    
    Returns:
        dict: 包含回答和会话 ID
    """
    url = f"{RAGFLOW_CONFIG['base_url']}/api/v1/agent/{RAGFLOW_CONFIG['agent_id']}/chat"
    
    headers = {
        "Authorization": f"Bearer {RAGFLOW_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "stream": False
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.ok:
            result = response.json()
            return {
                "success": True,
                "answer": result.get("answer", result.get("response", "")),
                "conversation_id": result.get("conversation_id", conversation_id),
                "references": result.get("references", [])
            }
        else:
            return {
                "success": False,
                "error": f"API 错误：{response.status_code} - {response.text}"
            }
            
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"连接失败：{str(e)}\n💡 请检查网络连接或 DNS 配置"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误：{str(e)}"
        }

def main():
    """命令行交互模式"""
    print("🤖 RAGFlow Agent 对话")
    print("=" * 50)
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 50)
    
    conversation_id = None
    
    while True:
        try:
            query = input("\n👤 你：").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 再见！")
                break
            
            if not query:
                continue
            
            print("\n🤖 思考中...", end="\r")
            result = ragflow_chat(query, conversation_id)
            
            if result["success"]:
                print(f"\n🤖 RAGFlow: {result['answer']}")
                conversation_id = result["conversation_id"]
                
                # 显示引用来源（如果有）
                if result.get("references"):
                    print("\n📚 参考来源:")
                    for ref in result["references"][:3]:
                        print(f"  - {ref.get('title', '未知')}")
            else:
                print(f"\n❌ 错误：{result['error']}")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
