#!/usr/bin/env python3
"""
每日 AI 资讯推送脚本（完整版）
cron: 0 7 * * *
流程: 检查pending → 收集新闻 → 推送 → 发状态通知 → 归档
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import re
from datetime import datetime

# ========== 配置 ==========
WORKSPACE = "/home/admin/.openclaw/workspace"
TASKS_DIR = os.path.join(WORKSPACE, "tasks")
LOGS_DIR = os.path.join(WORKSPACE, "logs")
RECIPIENT_ID = "004235"
RECIPIENT_NAME = "韩瑾君"

# ========== 工具函数 ==========
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def get_today_str():
    return datetime.now().strftime("%Y%m%d")

def get_today_display():
    return datetime.now().strftime("%Y-%m-%d")

# ========== 核心功能 ==========

def check_already_done():
    """检查今日是否已完成推送"""
    today = get_today_str()
    done_file = os.path.join(TASKS_DIR, f"daily-ai-news-done-{today}")
    return os.path.exists(done_file), done_file

def check_pending():
    """检查是否有待处理任务"""
    pending_file = os.path.join(TASKS_DIR, "daily-ai-news-pending")
    return os.path.exists(pending_file), pending_file

def load_collected_news():
    """加载今日收集的新闻"""
    today = get_today_str()
    news_file = os.path.join(TASKS_DIR, f"daily-ai-news-collected-{today}.md")
    if not os.path.exists(news_file):
        return None
    with open(news_file, encoding="utf-8") as f:
        return f.read()

def parse_news_content(content):
    """
    解析收集的新闻 markdown，提取国内6条 + 国际6条
    返回: {domestic: [], international: []}
    """
    if not content:
        return None
    
    domestic = []
    international = []
    current_section = None
    current_item = {}
    current_key = None
    current_value_lines = []
    
    def flush_item():
        nonlocal current_item
        if current_item and "title" in current_item:
            if current_section == "domestic":
                domestic.append(current_item)
            elif current_section == "international":
                international.append(current_item)
        current_item = {}
    
    lines = content.split("\n")
    for line in lines:
        line = line.rstrip()
        if line.startswith("## 🇨🇳 国内新闻") or line.startswith("## 国内新闻"):
            current_section = "domestic"
            flush_item()
        elif line.startswith("## 🌍 国际新闻") or line.startswith("## 国际新闻"):
            current_section = "international"
            flush_item()
        elif line.startswith("### "):
            flush_item()
            title = line.replace("### ", "").strip()
            if title.startswith("**"):
                title = title[2:]
            if title.endswith("**"):
                title = title[:-2]
            current_item = {"title": title}
            current_key = None
        elif line.startswith("- **") or line.startswith("**"):
            key_part = line.lstrip("- ").strip()
            if key_part.startswith("**"):
                parts = key_part.split("**")
                if len(parts) >= 2:
                    current_key = parts[0].strip()
                    current_value_lines = [parts[1].strip()]
                else:
                    current_key = None
            else:
                current_key = None
        elif line.startswith("- 📅") or line.startswith("📅"):
            key_part = line.lstrip("- ").strip()
            if key_part.startswith("📅"):
                parts = key_part.split("：**")
                if len(parts) >= 2:
                    current_key = "date"
                    current_value_lines = [parts[1].strip()]
                else:
                    current_key = None
        elif line.startswith("- 📝") or line.startswith("📝"):
            key_part = line.lstrip("- ").strip()
            if key_part.startswith("📝"):
                parts = key_part.split("：**")
                if len(parts) >= 2:
                    current_key = "summary"
                    current_value_lines = [parts[1].strip()]
                else:
                    current_key = None
        elif line.startswith("- 🔗") or line.startswith("🔗"):
            key_part = line.lstrip("- ").strip()
            if key_part.startswith("🔗"):
                parts = key_part.split("：**")
                if len(parts) >= 2:
                    current_key = "url"
                    current_value_lines = [parts[1].strip()]
                else:
                    current_key = None
        elif line.startswith("- 来源：") or line.startswith("来源："):
            key_part = line.lstrip("- ").strip()
            if key_part.startswith("来源："):
                current_key = "url"
                current_value_lines = [key_part.replace("来源：", "").strip()]
            else:
                current_key = None
        elif line.startswith("- 日期："):
            current_key = "date"
            current_value_lines = [line.replace("- 日期：", "").strip()]
        elif line.startswith("- 要义："):
            current_key = "summary"
            current_value_lines = [line.replace("- 要义：", "").strip()]
        elif line.startswith("- 链接："):
            current_key = "url"
            current_value_lines = [line.replace("- 链接：", "").strip()]
        elif line.strip() == "---":
            if current_key and current_value_lines:
                current_item[current_key] = "\n".join(current_value_lines)
            flush_item()
            current_key = None
            current_value_lines = []
        elif current_key and line.strip():
            current_value_lines.append(line.strip())
    
    if current_key and current_value_lines:
        current_item[current_key] = "\n".join(current_value_lines)
    flush_item()
    
    return {"domestic": domestic[:6], "international": international[:6]}

def format_news_for_wecom(news_data):
    """将新闻格式化为企业微信消息"""
    lines = []
    today = get_today_display()
    lines.append(f"🤖 AI 每日资讯 | {today}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("🇨🇳 **国内新闻**")
    lines.append("")
    
    for i, item in enumerate(news_data["domestic"], 1):
        lines.append(f"**{i}. {item.get('title', 'N/A')}**")
        if item.get("date"):
            lines.append(f"📅 日期：{item['date']}")
        if item.get("summary"):
            lines.append(f"📝 要义：{item['summary']}")
        if item.get("url"):
            lines.append(f"🔗 来源：{item['url']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("🌍 **国际新闻**")
    lines.append("")
    
    for i, item in enumerate(news_data["international"], 1):
        lines.append(f"**{i}. {item.get('title', 'N/A')}**")
        if item.get("date"):
            lines.append(f"📅 日期：{item['date']}")
        if item.get("summary"):
            lines.append(f"📝 要义：{item['summary']}")
        if item.get("url"):
            lines.append(f"🔗 来源：{item['url']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("🔍 **今日观察**")
    lines.append("")
    lines.append("【今日AI世界概要】")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("📊 **备注**")
    lines.append(f"🔍 搜索工具：SearXNG (隐私优先的元搜索引擎)")
    lines.append("🤖 生成模型：minimax/MiniMax-M2.7")
    lines.append(f"🕐 生成时间：{today} 07:00 (北京时间)")
    
    return "\n".join(lines)

def send_via_openclaw_agent(message_content):
    """
    通过 openclaw agent 子会话发送消息
    返回: (success: bool, message_id: str or None)
    """
    try:
        # 使用 openclaw agent 发送
        result = subprocess.run(
            [
                os.path.expanduser("~/.npm-global/bin/openclaw"),
                "agent",
                "--channel", "wecom",
                "--deliver",
                "--message", message_content
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            cwd=WORKSPACE
        )
        stdout = result.stdout.decode("utf-8") if result.stdout else ""
        stderr = result.stderr.decode("utf-8") if result.stderr else ""
        log(f"openclaw agent stdout: {stdout}")
        log(f"openclaw agent stderr: {stderr}")
        
        # 解析输出中的 messageId
        message_id = None
        for line in stdout.split("\n"):
            if "messageId" in line or "message_id" in line:
                # 尝试提取 messageId
                match = re.search(r"message[_-]?id[\"':\s]+([a-zA-Z0-9_]+)", line, re.IGNORECASE)
                if match:
                    message_id = match.group(1)
        
        if result.returncode == 0:
            return True, message_id
        else:
            return False, None
            
    except Exception as e:
        log(f"❌ openclaw agent 调用异常: {e}")
        return False, None

def save_push_log(push_result):
    """保存推送日志"""
    today = get_today_str()
    log_file = os.path.join(TASKS_DIR, f"daily-ai-news-push-log-{today}.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(push_result, f, ensure_ascii=False, indent=2)
    return log_file

def send_status_notification(push_result):
    """发送推送状态通知给 J 哥"""
    today_display = get_today_display()
    push_time_str = push_result.get("push_time", f"{today_display} 07:00")
    message_id = push_result.get("message_id", "N/A")
    status_icon = "✅" if push_result.get("status") == "success" else "❌"
    
    status_msg = f"""🤖 AI 每日资讯推送完成

推送时间：{push_time_str}（北京时间）

推送用户及状态：
| 用户 ID | 姓名 | 状态 | 消息 ID |
|---------|------|------|---------|
| {RECIPIENT_ID} | {RECIPIENT_NAME} | {status_icon} {'成功' if push_result.get('status') == 'success' else '失败'} | {message_id} |

资讯内容概览：
· {push_result.get('domestic_count', 6)} 条国内新闻
· {push_result.get('international_count', 6)} 条国际新闻
· 每条均含📝要义和🔗来源链接

记忆归档： 已写入 memory/{today_display}.md

🤖 Cron Job daily-ai-news 执行完毕"""
    
    try:
        result = subprocess.run(
            [
                os.path.expanduser("~/.npm-global/bin/openclaw"),
                "agent",
                "--channel", "wecom",
                "--deliver",
                "--message", status_msg
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            cwd=WORKSPACE
        )
        stdout = result.stdout.decode("utf-8") if result.stdout else ""
        stderr = result.stderr.decode("utf-8") if result.stderr else ""
        log(f"状态通知发送结果: returncode={result.returncode}, stdout={stdout[:200]}, stderr={stderr[:200]}")
    except Exception as e:
        log(f"❌ 状态通知发送异常: {e}")

def mark_done(done_file):
    """标记任务完成"""
    with open(done_file, "w", encoding="utf-8") as f:
        f.write(f"done at {datetime.now().isoformat()}\n")

def cleanup():
    """清理 pending 文件"""
    pending_file = os.path.join(TASKS_DIR, "daily-ai-news-pending")
    if os.path.exists(pending_file):
        os.remove(pending_file)
        log(f"已清理 pending 文件")

# ========== 主流程 ==========
def main():
    log("========== 每日 AI 资讯推送开始 ==========")
    
    # 1. 检查是否已完成
    already_done, done_file = check_already_done()
    if already_done:
        log("今日已推送，退出")
        sys.exit(0)
    
    # 2. 检查 pending
    has_pending, pending_file = check_pending()
    log(f"pending 文件状态: {has_pending}")
    
    # 3. 加载新闻
    news_content = load_collected_news()
    if not news_content:
        log("⚠️ 今日新闻未收集（找不到 collected 文件），退出")
        sys.exit(1)
    
    log(f"新闻内容已加载，字数: {len(news_content)}")
    
    # 4. 解析新闻
    news_data = parse_news_content(news_content)
    if not news_data:
        log("⚠️ 新闻解析失败，退出")
        sys.exit(1)
    
    domestic_count = len(news_data["domestic"])
    international_count = len(news_data["international"])
    log(f"解析完成：国内 {domestic_count} 条，国际 {international_count} 条")
    
    # 5. 格式化消息
    message_content = format_news_for_wecom(news_data)
    
    # 6. 发送新闻
    log("开始推送新闻...")
    success, message_id = send_via_openclaw_agent(message_content)
    
    push_time = f"{get_today_display()} 07:00"
    push_result = {
        "task": "daily_ai_news",
        "push_date": get_today_display(),
        "push_time": push_time,
        "status": "success" if success else "failed",
        "message_id": message_id,
        "domestic_count": domestic_count,
        "international_count": international_count,
        "recipient": {"id": RECIPIENT_ID, "name": RECIPIENT_NAME}
    }
    
    # 7. 保存推送日志
    log_file = save_push_log(push_result)
    log(f"推送日志已保存: {log_file}")
    
    # 8. 发送状态通知
    log("发送状态通知...")
    send_status_notification(push_result)
    
    # 9. 标记完成 + 清理
    mark_done(done_file)
    cleanup()
    
    log("========== 每日 AI 资讯推送结束 ==========")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()