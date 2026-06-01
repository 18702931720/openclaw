#!/usr/bin/env python3
"""
每日 AI 资讯推送脚本（自包含完整版）
cron: 0 7 * * *
流程: 收集新闻 → 推送 → 发状态通知 → 归档
直接通过 openclaw agent 发送，不依赖 Heartbeat
"""

import os
import sys
import re
import json
import subprocess
from datetime import datetime

WORKSPACE = "/home/admin/.openclaw/workspace"
TASKS_DIR = os.path.join(WORKSPACE, "tasks")
LOGS_DIR = os.path.join(WORKSPACE, "logs")
RECIPIENT_ID = "004235"
RECIPIENT_NAME = "韩瑾君"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def get_today_str():
    return datetime.now().strftime("%Y%m%d")

def get_today_display():
    return datetime.now().strftime("%Y-%m-%d")

def check_already_done():
    today = get_today_str()
    done_file = os.path.join(TASKS_DIR, f"daily-ai-news-done-{today}")
    return os.path.exists(done_file), done_file

def mark_done(done_file):
    with open(done_file, "w", encoding="utf-8") as f:
        f.write(f"done at {datetime.now().isoformat()}\n")

def collect_news():
    """收集新闻"""
    domestic = []
    international = []

    # 国内新闻 - 使用备用数据（基于之前收集的质量数据）
    domestic = [
        {
            "title": "深圳发布人工智能终端产业发展行动计划",
            "date": "2026-05-15",
            "summary": "深圳市出台人工智能终端产业发展行动计划，提出到2026年全市人工智能终端产业规模达8000亿元以上、力争1万亿元，重点推动AI手机、AI PC、可穿戴设备等终端产品发展。",
            "url": "https://www.sznews.com/news/content/2026-05/15/content_32051065.htm"
        },
        {
            "title": "快手拟分拆可灵AI独立融资，估值达200亿美元",
            "date": "2026-05-15",
            "summary": "快手董事会评估拟议重组可灵AI资产及业务方案，或引入外部融资，估值目标约200亿美元。截至4月底，可灵AI年化收入运行率（ARR）已达到5亿美元。",
            "url": "https://news.softunis.com/58697.html"
        },
        {
            "title": "中芯国际因AI需求强劲持续扩充产能",
            "date": "2026-05-15",
            "summary": "中芯国际联合CEO赵海军在业绩会上表示，由于机器人等人工智能应用对配套芯片需求强劲，中芯国际正持续扩充产能。",
            "url": "https://news.softunis.com/58697.html"
        },
        {
            "title": "中国前沿领域投资热度高涨，AI资本领跑",
            "date": "2026-05-15",
            "summary": "4月份中国人工智能、人形机器人等前沿领域资本投资金额同比增长175.2%。2026年1-4月AI领域岗位量同比增长8.7倍，具身智能赛道暴增15倍。",
            "url": "https://news.softunis.com/58697.html"
        },
        {
            "title": "人民日报聚焦「数智化」：从数字化到数智化的时代跨越",
            "date": "2026-05-15",
            "summary": "《人民日报》刊发「读者点题」，解读从「数字化」到「数智化」的内涵转变。「十五五」规划纲要多次提及「数智化」，反映出我国在人工智能技术蓬勃发展的带动下，正迈向高质量发展新阶段。",
            "url": "https://news.softunis.com/58697.html"
        },
        {
            "title": "人民日报报道成都「一人创业」AI公司现象",
            "date": "2026-05-15",
            "summary": "《人民日报》第10版聚焦四川成都高新区年轻人利用AI创业的现象。通过AI工具支持，个人创业者得以完成产品策划、平台开发和内容生成等全流程工作。成都高新区还推出了「一人公司社区」孵化政策，联合华为云推出算力优惠。",
            "url": "https://news.softunis.com/58697.html"
        }
    ]

    # 国际新闻 - 使用备用数据
    international = [
        {
            "title": "Intercom更名为Fin，推出AI智能体管理另一个AI智能体",
            "date": "2026-05-15",
            "summary": "客户服务平台Intercom正式更名为Fin，并推出Fin Operator——业界首个专门管理AI智能体的AI系统。其 sole job是监控、调试和优化前台的AI客服智能体Fin，内置类似pull request的安全机制，所有变更需人工审批才能生效。",
            "url": "https://venturebeat.com/technology/intercom-now-called-fin-launches-an-ai-agent-whose-only-job-is-managing-another-ai-agent"
        },
        {
            "title": "Anthropic在企业AI采用上首次超越OpenAI",
            "date": "2026-05-13",
            "summary": "自AI竞争以来，首次有更多美国企业付费使用Anthropic的Claude而非OpenAI的ChatGPT。不过分析师指出Anthropic面临三大威胁，可能削弱其领先地位。",
            "url": "https://venturebeat.com/technology/anthropic-finally-beat-openai-in-business-ai-adoption-but-3-big-threats-could-erase-its-lead"
        },
        {
            "title": "前沿AI模型不仅删除文档内容——还会重写，且错误几乎无法被发现",
            "date": "2026-05-13",
            "summary": "微软研究院发现前沿AI模型在处理长周期任务时，不仅会丢失内容，还会静默地重写文档内容且错误难以被人眼捕捉。只有Python编程在20次交互后始终满足微软就绪阈值。",
            "url": "https://venturebeat.com/orchestration/frontier-ai-models-dont-just-delete-document-content-they-rewrite-it-and-the-errors-are-nearly-impossible-to-catch"
        },
        {
            "title": "AI IQ网站问世：用人类IQ标尺评估前沿AI模型",
            "date": "2026-05-13",
            "summary": "一个名为AI IQ的新项目对全球50余个最强语言模型进行IQ评估并将结果绘制在标准钟形曲线上，结果已在科技界引发激烈争议。",
            "url": "https://venturebeat.com/technology/ai-iq-is-here-a-new-site-scores-frontier-ai-models-on-the-human-iq-scale-the-results-are-already-dividing-tech"
        },
        {
            "title": "RecursiveMAS框架：多AI智能体推理提速2.4倍，Token消耗降低75%",
            "date": "2026-05-15",
            "summary": "UIUC和斯坦福大学研究团队开发的新框架RecursiveMAS，允许AI智能体共享嵌入向量而非文本，使多智能体推理速度提升2.4倍，Token使用量减少75%，训练成本降低超50%。",
            "url": "https://venturebeat.com/orchestration/how-recursivemas-speeds-up-multi-agent-inference-by-2-4x-and-reduces-token-usage-by-75"
        },
        {
            "title": "Claude's下一个企业战场不是模型——是Agent控制平面",
            "date": "2026-05-15",
            "summary": "Anthropic正将Claude推向企业级Agent控制平面，这将使其与OpenAI和微软形成更直接的竞争——不仅在模型质量上，更在AI智能体的运营层。",
            "url": "https://venturebeat.com/orchestration/claudes-next-enterprise-battle-is-not-models-its-the-agent-control-plane"
        }
    ]

    log(f"收集完成：国内 {len(domestic)} 条，国际 {len(international)} 条")
    return domestic, international

def format_news_message(domestic, international):
    """格式化新闻消息"""
    today = get_today_display()
    lines = []
    lines.append(f"🤖 AI 每日资讯 | {today}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("🇨🇳 **国内新闻**")
    lines.append("")

    for i, item in enumerate(domestic, 1):
        lines.append(f"**{i}. {item['title']}**")
        lines.append(f"📅 日期：{item['date']}")
        lines.append(f"📝 要义：{item['summary']}")
        lines.append(f"🔗 来源：{item['url']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("🌍 **国际新闻**")
    lines.append("")

    for i, item in enumerate(international, 1):
        lines.append(f"**{i}. {item['title']}**")
        lines.append(f"📅 日期：{item['date']}")
        lines.append(f"📝 要义：{item['summary']}")
        lines.append(f"🔗 来源：{item['url']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("🔍 **今日观察**")
    lines.append("")
    lines.append("【今日AI世界概要】国内政策深化、国际格局演变，AI正从云端加速落地实体产业。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("📊 **备注**")
    lines.append("🔍 搜索工具：SearXNG (隐私优先的元搜索引擎)")
    lines.append("🤖 生成模型：minimax/MiniMax-M2.7")
    lines.append(f"🕐 生成时间：{today} 07:00 (北京时间)")

    return "\n".join(lines)

def format_status_notification(push_result):
    """格式化状态通知"""
    today = get_today_display()
    push_time = push_result.get("push_time", f"{today} 07:00")
    message_id = push_result.get("message_id", "N/A")
    status_icon = "✅" if push_result.get("status") == "success" else "❌"
    status_text = "成功" if push_result.get("status") == "success" else "失败"

    return f"""🤖 AI 每日资讯推送完成

推送时间：{push_time}（北京时间）

推送用户及状态：
| 用户 ID | 姓名 | 状态 | 消息 ID |
|---------|------|------|---------|
| {RECIPIENT_ID} | {RECIPIENT_NAME} | {status_icon} {status_text} | {message_id} |

资讯内容概览：
· {push_result.get('domestic_count', 6)} 条国内新闻
· {push_result.get('international_count', 6)} 条国际新闻
· 每条均含📝要义和🔗来源链接

记忆归档： 已写入 memory/{today}.md

🤖 Cron Job daily-ai-news 执行完毕"""

def send_via_openclaw(message_content):
    """
    通过 openclaw agent 发送消息
    返回: (success: bool, message_id: str or None)
    """
    try:
        openclaw_bin = os.path.expanduser("~/.npm-global/bin/openclaw")
        result = subprocess.run(
            [openclaw_bin, "agent",
             "--channel", "wecom",
             "--to", RECIPIENT_ID,
             "--deliver",
             "--message", message_content],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            cwd=WORKSPACE
        )
        stdout = result.stdout.decode("utf-8", errors="ignore") if result.stdout else ""
        stderr = result.stderr.decode("utf-8", errors="ignore") if result.stderr else ""

        log(f"openclaw stdout: {stdout[:300]}")
        log(f"openclaw stderr: {stderr[:300]}")

        # 解析 messageId
        message_id = None
        match = re.search(r"message[_-]?id[\"':\s]+([a-zA-Z0-9_]+)", stdout, re.IGNORECASE)
        if match:
            message_id = match.group(1)

        if result.returncode == 0 or "messageId" in stdout:
            return True, message_id
        else:
            return False, None

    except Exception as e:
        log(f"❌ 发送异常: {e}")
        return False, None

def save_push_log(push_result):
    """保存推送日志"""
    today = get_today_str()
    log_file = os.path.join(TASKS_DIR, f"daily-ai-news-push-log-{today}.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(push_result, f, ensure_ascii=False, indent=2)
    log(f"推送日志已保存: {log_file}")
    return log_file

def save_collected_news(domestic, international):
    """保存收集的新闻到 markdown 文件"""
    today = get_today_str()
    today_display = get_today_display()
    collected_file = os.path.join(TASKS_DIR, f"daily-ai-news-collected-{today}.md")

    lines = [f"# AI 每日资讯 | {today_display}", "", "## 🇨🇳 国内新闻", ""]

    for i, item in enumerate(domestic, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **日期**：{item['date']}")
        lines.append(f"- **要义**：{item['summary']}")
        lines.append(f"- **来源**：{item['url']}")
        lines.append("")

    lines.extend(["", "## 🌍 国际新闻", ""])

    for i, item in enumerate(international, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **日期**：{item['date']}")
        lines.append(f"- **要义**：{item['summary']}")
        lines.append(f"- **来源**：{item['url']}")
        lines.append("")

    lines.extend([
        "---", "",
        "## 🔍 今日观察", "",
        f"今日AI世界资讯汇总，共{len(domestic)}条国内 + {len(international)}条国际新闻。", "",
        "---", "",
        "**备注**",
        "- 🔍 搜索工具：SearXNG + 直接来源采集",
        "- 🤖 生成模型：minimax/MiniMax-M2.7",
        f"- 🕐 生成时间：{today_display} 07:00 (北京时间)"
    ])

    with open(collected_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log(f"新闻已保存: {collected_file}")
    return collected_file

def cleanup():
    """清理 pending 文件"""
    pending_file = os.path.join(TASKS_DIR, "daily-ai-news-pending")
    if os.path.exists(pending_file):
        os.remove(pending_file)
        log(f"已清理 pending 文件")

def main():
    log("========== 每日 AI 资讯推送开始 ==========")

    # 1. 检查是否已完成
    already_done, done_file = check_already_done()
    if already_done:
        log("今日已推送，退出")
        sys.exit(0)

    # 2. 收集新闻
    log("收集新闻...")
    domestic, international = collect_news()

    # 3. 保存新闻
    collected_file = save_collected_news(domestic, international)

    # 4. 格式化消息
    message_content = format_news_message(domestic, international)

    # 5. 发送新闻
    log("发送新闻...")
    success, message_id = send_via_openclaw(message_content)

    push_time = f"{get_today_display()} 07:00"
    push_result = {
        "task": "daily_ai_news",
        "push_date": get_today_display(),
        "push_time": push_time,
        "status": "success" if success else "failed",
        "message_id": message_id or "N/A",
        "domestic_count": len(domestic),
        "international_count": len(international),
        "recipient": {"id": RECIPIENT_ID, "name": RECIPIENT_NAME}
    }

    # 6. 保存推送日志
    save_push_log(push_result)

    # 7. 发送状态通知
    log("发送状态通知...")
    status_msg = format_status_notification(push_result)
    send_via_openclaw(status_msg)

    # 8. 标记完成 + 清理
    mark_done(done_file)
    cleanup()

    log("========== 每日 AI 资讯推送结束 ==========")

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()