#!/usr/bin/env python3
"""
每日 AI 资讯收集脚本（联网版）
cron: 0 7 * * *
流程: 联网搜索 → 保存 collected 文件 → 创建发送触发器
通过 SearXNG 搜索真实新闻
"""

import os
import json
import sys
import re
import warnings
import httpx
from datetime import datetime

warnings.filterwarnings('ignore')

WORKSPACE = "/home/admin/.openclaw/workspace"
TASKS_DIR = os.path.join(WORKSPACE, "tasks")
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")
RECIPIENT_ID = "004235"
RECIPIENT_NAME = "韩瑾君"

# Skip these domains (low quality or not AI news)
SKIP_DOMAINS = ["baidu.com", "sina.com", "sohu.com", "ifeng.com", "qq.com", 
                "163.com", "toutiao.com", "baike.com", "wikihow.com", "zhihu.com",
                "weibo.com", "toutiao.com", "wikinews.org"]

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

def search_searxng(query, limit=10, category="news", language="en", time_range=None):
    """Search using SearXNG instance."""
    params = {
        "q": query,
        "format": "json",
        "categories": category,
        "language": language,
        "safesearch": 0,
    }
    if time_range:
        params["time_range"] = time_range

    try:
        response = httpx.get(
            f"{SEARXNG_URL}/search",
            params=params,
            timeout=30,
            verify=False
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])[:limit]
        return results
    except Exception as e:
        log(f"Search error for '{query}': {e}")
        return []

def clean_title(title):
    """Clean title of extra whitespace."""
    if not title:
        return ""
    title = re.sub(r'\s+', ' ', title).strip()
    # Remove common site suffixes
    title = re.sub(r'\s*[-|–—]\s*(VentureBeat|TechCrunch|Wired|Ars Technica|The Verge|Reuters|BBC|CNN|Financial Times|华尔街日报|金融时报).*$', '', title, flags=re.IGNORECASE)
    return title

def is_valid_url(url):
    """Check if URL is valid and not from skipped domains."""
    if not url:
        return False
    url_lower = url.lower()
    for bad in SKIP_DOMAINS:
        if bad in url_lower:
            return False
    return True

def normalize_date(pub_date):
    """Normalize date to YYYY-MM-DD format."""
    if not pub_date:
        return get_today_display()
    if isinstance(pub_date, str):
        # Handle ISO format
        if "T" in pub_date:
            pub_date = pub_date[:10]
        # Handle other formats
        if re.match(r'\d{4}-\d{2}-\d{2}', pub_date):
            return pub_date[:10]
    return get_today_display()

def search_domestic_news():
    """Search for domestic (Chinese) AI news."""
    domestic = []
    
    # Search queries - use pure Chinese terms for better results
    queries = [
        ("人工智能", 8),
        ("AI大模型", 6),
        ("人工智能 行业 动态", 6),
    ]
    
    seen_titles = set()
    
    for query, limit in queries:
        log(f"Searching domestic: {query}")
        results = search_searxng(query, limit=limit, category="news", language="zh")
        
        for r in results:
            title = clean_title(r.get("title", ""))
            url = r.get("url", "")
            
            if not title or not url or title in seen_titles or not is_valid_url(url):
                continue
            
            seen_titles.add(title)
            
            content = r.get("content", "") or ""
            pub_date = normalize_date(r.get("publishedDate", ""))
            
            domestic.append({
                "title": title,
                "date": pub_date,
                "summary": content[:250].strip() if content else title,
                "url": url
            })
            
            if len(domestic) >= 6:
                log(f"Got {len(domestic)} domestic news, stopping early")
                return domestic
    
    log(f"Domestic news collected: {len(domestic)} items")
    return domestic

def search_international_news():
    """Search for international AI news."""
    international = []
    
    queries = [
        ("AI artificial intelligence news", 8),
        ("Anthropic OpenAI Google AI", 6),
        ("AI agent model 2026", 6),
    ]
    
    seen_titles = set()
    
    for query, limit in queries:
        log(f"Searching international: {query}")
        results = search_searxng(query, limit=limit, category="news", language="en", time_range="week")
        
        for r in results:
            title = clean_title(r.get("title", ""))
            url = r.get("url", "")
            
            if not title or not url or title in seen_titles:
                continue
            
            seen_titles.add(title)
            
            content = r.get("content", "") or ""
            pub_date = normalize_date(r.get("publishedDate", ""))
            
            international.append({
                "title": title,
                "date": pub_date,
                "summary": content[:250].strip() if content else title,
                "url": url
            })
            
            if len(international) >= 6:
                log(f"Got {len(international)} international news, stopping early")
                return international
    
    log(f"International news collected: {len(international)} items")
    return international

def save_collected_news(domestic, international):
    """Save collected news to markdown file."""
    today = get_today_str()
    today_display = get_today_display()
    collected_file = os.path.join(TASKS_DIR, f"daily-ai-news-collected-{today}.md")

    lines = [f"# AI 每日资讯 | {today_display}", "", "## 🇨🇳 国内新闻", ""]

    for i, item in enumerate(domestic, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **日期**：{item['date']}")
        summary = item['summary']
        if not summary.endswith(('.', '。', '！', '？')):
            summary = summary + '...'
        lines.append(f"- **要义**：{summary}")
        lines.append(f"- **来源**：{item['url']}")
        lines.append("")

    lines.extend(["", "## 🌍 国际新闻", ""])

    for i, item in enumerate(international, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **日期**：{item['date']}")
        summary = item['summary']
        if not summary.endswith(('.', '。', '！', '？')):
            summary = summary + '...'
        lines.append(f"- **要义**：{summary}")
        lines.append(f"- **来源**：{item['url']}")
        lines.append("")

    lines.extend([
        "---", "",
        "## 🔍 今日观察", "",
        f"今日AI世界资讯汇总，共{len(domestic)}条国内 + {len(international)}条国际新闻。", "",
        "---", "",
        "**备注**",
        "- 🔍 搜索工具：SearXNG (隐私优先的元搜索引擎)",
        "- 🤖 生成模型：minimax/MiniMax-M2.7",
        f"- 🕐 生成时间：{today_display} 07:00 (北京时间)"
    ])

    with open(collected_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log(f"新闻已保存: {collected_file}")
    return collected_file

def create_send_trigger(collected_file, domestic, international):
    """Create send trigger."""
    today = get_today_str()
    today_display = get_today_display()

    trigger = {
        "action": "send_news",
        "collected_file": collected_file,
        "push_date": today_display,
        "push_time": f"{today_display} 07:00",
        "recipient": {"id": RECIPIENT_ID, "name": RECIPIENT_NAME},
        "domestic_count": len(domestic),
        "international_count": len(international),
        "created_at": datetime.now().isoformat()
    }

    send_trigger_file = os.path.join(TASKS_DIR, f"daily-ai-news-send-trigger-{today}.json")
    with open(send_trigger_file, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)

    log(f"发送触发器已创建: {send_trigger_file}")
    return send_trigger_file

def main():
    log("========== 每日 AI 资讯收集开始（联网版）==========")

    # 1. Check if already done
    already_done, done_file = check_already_done()
    if already_done:
        log("今日已收集/推送，退出")
        return

    # 2. Collect domestic news
    log("收集国内新闻...")
    domestic = search_domestic_news()
    log(f"国内新闻收集完成：{len(domestic)} 条")

    # 3. Collect international news
    log("收集国际新闻...")
    international = search_international_news()
    log(f"国际新闻收集完成：{len(international)} 条")

    if not domestic and not international:
        log("错误：未能收集到任何新闻，退出")
        sys.exit(1)

    # 4. Save news
    collected_file = save_collected_news(domestic, international)

    # 5. Create send trigger
    create_send_trigger(collected_file, domestic, international)

    log("========== 每日 AI 资讯收集结束 ==========")
    log("请等待 Heartbeat 机制检测触发器并执行发送...")

if __name__ == "__main__":
    main()
