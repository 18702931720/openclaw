#!/usr/bin/env python3
"""
每日 AI 资讯推送脚本（修复版）
直接通过企业微信 webhook API 发送消息，绕过 wecom_mcp 的限制
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# 配置
WORKSPACE = "/home/admin/.openclaw/workspace"
TASKS_DIR = os.path.join(WORKSPACE, "tasks")
LOGS_DIR = os.path.join(WORKSPACE, "logs")
RECIPIENT_ID = "004235"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def get_wecom_webhook():
    """获取企业微信 webhook 地址"""
    config_path = os.path.join(WORKSPACE, "wecom-webhook.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            return config.get("webhook_url")
    return None

def send_via_webhook(webhook_url, content):
    """通过 webhook 发送文本消息"""
    if not webhook_url:
        log("❌ 未配置 webhook 地址")
        return False

    # 构建消息（企业微信 markdown 限制：标题/加粗/链接/换行）
    msg_data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    try:
        data = json.dumps(msg_data).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                log("✅ 推送成功")
                return True
            else:
                log(f"❌ 推送失败: {result}")
                return False
    except Exception as e:
        log(f"❌ 推送异常: {e}")
        return False

def load_collected_news():
    """加载今日收集的新闻"""
    today = datetime.now().strftime("%Y%m%d")
    news_file = os.path.join(TASKS_DIR, f"daily-ai-news-collected-{today}.md")

    if not os.path.exists(news_file):
        log(f"❌ 找不到新闻文件: {news_file}")
        return None

    with open(news_file) as f:
        return f.read()

def format_news_md(news_content):
    """将新闻 markdown 转换为企业微信可用的格式"""
    lines = news_content.strip().split("\n")
    output = []
    for line in lines:
        # 企业微信 markdown 不支持多级标题，用加粗替代
        if line.startswith("## "):
            output.append("")
        elif line.startswith("### "):
            # 新闻标题用加粗
            title = line.replace("### ", "").strip()
            output.append(f"**{title}**")
        elif line.startswith("- **"):
            parts = line[4:].split("**")
            if len(parts) >= 2:
                output.append(f"**{parts[0]}** {parts[1]}")
            else:
                output.append(line)
        elif line.startswith("- 📝"):
            output.append(line.replace("- 📝", "📝"))
        elif line.startswith("- 📅"):
            output.append(line.replace("- 📅", "📅"))
        elif line.startswith("- 🔗"):
            output.append(line.replace("- 🔗", "🔗"))
        elif line.startswith("- 要义："):
            # 处理没有 emoji 的要义字段
            output.append(line.replace("- 要义：", "📝 **要义：**"))
        elif line.startswith("- 日期："):
            # 处理没有 emoji 的日期字段
            output.append(line.replace("- 日期：", "📅 **日期：**"))
        elif line.startswith("- 链接："):
            # 处理没有 emoji 的链接字段
            url = line.replace("- 链接：", "").strip()
            output.append(f"🔗 **链接：** {url}")
        elif line.strip() == "---":
            output.append("---")
        elif line.strip():
            output.append(line)

    return "\n".join(output)

def main():
    log("========== 每日 AI 资讯推送开始 ==========")

    # 加载新闻
    news_content = load_collected_news()
    if not news_content:
        log("⚠️ 今日无新闻，跳过推送")
        sys.exit(0)

    # 转换格式
    formatted = format_news_md(news_content)

    # 添加元数据备注
    today_str = datetime.now().strftime("%Y-%m-%d")
    meta = f"""
---
📊 **备注**
🔍 搜索工具：SearXNG (隐私优先的元搜索引擎)
🤖 生成模型：minimax/MiniMax-M2.7
🕐 生成时间：{today_str} 07:18 (北京时间)
"""
    formatted += meta

    # 尝试 webhook 发送
    webhook_url = get_wecom_webhook()
    if webhook_url:
        success = send_via_webhook(webhook_url, formatted)
        if success:
            log("✅ 推送完成")
            sys.exit(0)

    # webhook 失败，输出到日志供人工处理
    log("⚠️ Webhook 发送失败，新闻内容已保存到日志")
    log_file = os.path.join(LOGS_DIR, f"news-push-{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "w") as f:
        f.write(formatted)
    log(f"📝 内容已保存: {log_file}")

    log("========== 每日 AI 资讯推送结束 ==========")

if __name__ == "__main__":
    main()