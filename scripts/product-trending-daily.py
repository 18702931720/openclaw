#!/usr/bin/env python3
"""
Product Hunt + Hacker News 产品发现日报
抓取两个平台当天的热门产品/话题，生成 AI 中文解读，邮件推送
cron: 0 8 * * *  (每天早上 8 点)
"""

import smtplib, json, sys, re, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import datetime, timedelta
from urllib.request import Request
import time

# ─── 配置 ───────────────────────────────────────────
SMTP_CONFIG = {
    "email": "kim.han@sinoboom.com.cn",
    "smtp_host": "smtp.qiye.163.com",
    "smtp_port": 465,
    "password": "ZE3#PgJe4W#SPgHC"
}
TO_EMAIL = "kim.han@sinoboom.com.cn"

MINIMAX_API_KEY = "sk-cp-yrK6QN6yWPmvL2Xzj6FDf9vFI3hdf4DuuINKOzlSnODY2OBwQVhsduhj1UqbGmooYLQbLnhznYT1me6gy66K7PCGDNijxUornhrY_CjqerVMelOQok8WUio"
MINIMAX_MODEL  = "MiniMax-M2.7"

CACHE_FILE = "/home/admin/.openclaw/workspace/tasks/product-trending-cache.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# ─── HTTP ────────────────────────────────────────────
def http_get(url, headers=None, timeout=15):
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    req = Request(url, headers=h)
    try:
        from urllib.request import urlopen
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print("  [WARN] GET {} -> {}".format(url, e))
        return None

# ─── Product Hunt ────────────────────────────────────
def fetch_product_hunt():
    """抓取 Product Hunt 今日热门产品（通过公开 Atom Feed）"""
    try:
        rss = http_get("https://www.producthunt.com/feed", headers={
            "Accept": "application/atom+xml",
            "User-Agent": "Mozilla/5.0"
        })
        if not rss or "<entry>" not in rss:
            return []

        entries = re.findall(r'<entry>(.*?)</entry>', rss, re.DOTALL)
        products = []
        for entry in entries[:10]:
            title_m = re.search(r'<title[^>]*>([^<]+)</title>', entry)
            title = title_m.group(1).strip() if title_m else ""

            link_m = re.search(r'<link[^>]*rel="alternate"[^>]*href="([^"]+)"', entry)
            url = link_m.group(1).strip() if link_m else ""

            content_m = re.search(r'<content[^>]*>(.*?)</content>', entry, re.DOTALL)
            content = content_m.group(1) if content_m else ""
            desc = re.sub(r'<[^>]+>', '', content).strip()
            desc = desc.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

            author_m = re.search(r'<author>.*?<name>([^<]+)</name>', entry, re.DOTALL)
            author = author_m.group(1).strip() if author_m else ""

            published_m = re.search(r'<published>([^<]+)</published>', entry)
            published = published_m.group(1).strip() if published_m else ""

            if title and url:
                slug = url.rstrip("/").split("/")[-1]
                products.append({
                    "path": slug,
                    "title": title,
                    "description": desc[:200] if desc else "",
                    "votes": 0,
                    "comments": 0,
                    "author": author,
                    "published": published,
                    "platform": "Product Hunt",
                    "url": url
                })
        return products[:10]
    except Exception as e:
        print("  [WARN] Product Hunt Feed 失败: {}".format(e))
        return []

# ─── AlternativeTo ────────────────────────────────────
def fetch_alternativeto():
    try:
        html = http_get("https://alternativeto.net/")
        if not html:
            return []
        items = re.findall(
            r'<a[^>]*href="/software/([^/]+)/"[^>]*>\s*<span[^>]*>([^<]+)</span>',
            html
        )
        tools = []
        seen = set()
        for slug, name in items:
            if slug not in seen and len(tools) < 5:
                seen.add(slug)
                tools.append({
                    "path": slug,
                    "title": name.strip(),
                    "platform": "AlternativeTo",
                    "url": "https://alternativeto.net/software/{}/".format(slug)
                })
        return tools
    except Exception as e:
        print("  [WARN] AlternativeTo 失败: {}".format(e))
        return []

# ─── There's An AI For That ───────────────────────────
def fetch_ai_tools():
    try:
        url = "https://theresanaiforthat.com/"
        html = http_get(url)
        if not html:
            return []
        items = re.findall(
            r'<a[^>]*href="/tools/([^"]+)/"[^>]*>.*?<h3[^>]*>([^<]+)</h3>',
            html, re.DOTALL
        )
        tools = []
        seen = set()
        for slug, name in items:
            if slug not in seen and len(tools) < 3:
                seen.add(slug)
                tools.append({
                    "path": slug,
                    "title": name.strip(),
                    "platform": "There's An AI For That",
                    "url": "https://theresanaiforthat.com/tools/{}/".format(slug)
                })
        return tools
    except Exception as e:
        print("  [WARN] There's An AI For That 失败: {}".format(e))
        return []

# ─── Hacker News ─────────────────────────────────────
def fetch_hacker_news():
    try:
        today = datetime.utcnow()
        start_of_day = datetime(today.year, today.month, today.day)
        ts_start = int(start_of_day.timestamp())
        ts_end = int((start_of_day + timedelta(days=1)).timestamp())

        url = "https://hn.algolia.com/api/v1/search?tags=front_page&numericFilters=created_at_i>={},created_at_i<{}&hitsPerPage=10".format(ts_start, ts_end)
        data = http_get(url, headers={"Accept": "application/json"})
        if data:
            result = json.loads(data)
            hits = result.get("hits", [])
            stories = []
            for hit in hits[:10]:
                obj = hit.get("objectID", "")
                title = hit.get("title", "") or hit.get("story_title", "")
                url_val = hit.get("url", "") or "https://news.ycombinator.com/item?id={}".format(obj)
                author = hit.get("author", "unknown")
                points = hit.get("points", 0)
                num_comments = hit.get("num_comments", 0)
                if title:
                    stories.append({
                        "path": obj,
                        "title": title,
                        "url": url_val,
                        "author": author,
                        "points": points,
                        "comments": num_comments,
                        "platform": "Hacker News",
                    })
            if stories:
                return stories
    except Exception as e:
        print("  [WARN] HN Algolia 失败: {}".format(e))

    try:
        from urllib.request import urlopen
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            ids = json.loads(resp.read().decode('utf-8'))[:10]
            stories = []
            for story_id in ids:
                item_url = "https://hacker-news.firebaseio.com/v0/item/{}.json".format(story_id)
                item_req = Request(item_url, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(item_req, timeout=10) as item_resp:
                    item = json.loads(item_resp.read().decode('utf-8'))
                    if item and item.get("title"):
                        stories.append({
                            "path": str(story_id),
                            "title": item.get("title", ""),
                            "url": item.get("url") or "https://news.ycombinator.com/item?id={}".format(story_id),
                            "author": item.get("by", "unknown"),
                            "points": item.get("score", 0),
                            "comments": item.get("descendants", 0),
                            "platform": "Hacker News",
                        })
                time.sleep(0.3)
            return stories
    except Exception as e:
        print("  [WARN] HN Firebase 降级失败: {}".format(e))
        return []

# ─── AI 生成描述 ─────────────────────────────────────
def summarize_items(items):
    if not MINIMAX_API_KEY:
        return [fallback_desc(item) for item in items]

    items_text = ""
    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        platform = item.get("platform", "")
        votes = item.get("votes", item.get("points", ""))
        comments = item.get("comments", "")
        desc = item.get("description", "")
        items_text += "\n=== Product {} [{}]\nName: {}\nTagline: {}\nURL: {}\nStats: votes={}, comments={}\n".format(
            i, platform, title, desc if desc else 'N/A', url, votes, comments
        )

    prompt = "You are a professional product analyst. For each of the following {} items from Product Hunt and Hacker News, write a concise Chinese description of 80-120 characters.\nFormat each item as:\n### Product N [Platform]\n[80-120 char Chinese description]\n\nRequirements:\n- Each description: product name + one-line positioning + core highlight (1-2 sentences)\n- Be specific, not generic\n- Strictly follow the format below (no intro/outro):\n\n### Product 1 [Platform]\n[description]\n\n## Product List\n{}\n\n## Output Format\nStrictly output {} items in the following format:\n### Product 1 [Platform]\n[80-120 chars]\n### Product 2 [Platform]\n[80-120 chars]\n...(total {} items)".format(len(items), items_text, len(items), len(items))

    result_text = _call_minimax(prompt)
    if result_text:
        parsed = _parse_items_text(result_text, len(items))
        if len(parsed) >= len(items) * 0.7:
            result = [fallback_desc(item) for item in items]
            for i, desc in enumerate(parsed[:len(result)]):
                result[i] = desc
            return result

    return [fallback_desc(item) for item in items]

def _call_minimax(prompt):
    for attempt in range(2):
        try:
            import urllib.request
            payload = {
                "model": MINIMAX_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8000,
                "temperature": 0.3,
            }
            req = urllib.request.Request(
                "https://api.minimaxi.com/anthropic/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": "Bearer {}".format(MINIMAX_API_KEY),
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                for block in result.get("content", []):
                    if block.get("type") == "text" and block.get("text", "").strip():
                        return block.get("text", "").strip()
        except Exception as e:
            print("  [WARN] MiniMax 失败: {}".format(e))
            if attempt < 1:
                time.sleep(3)
    return None

def _parse_items_text(text, expected):
    results = []
    parts = re.split(r'###\s*Product\s*(\d+)', text)
    idx = 2
    while idx < len(parts) and len(results) < expected:
        desc = parts[idx].strip()
        if desc:
            results.append(desc)
        idx += 2
    return results

def fallback_desc(item):
    title = item.get("title", "")
    platform = item.get("platform", "")
    desc = item.get("description", "")
    if desc:
        return desc
    return "From {} - {}".format(platform, title)

# ─── 缓存 ─────────────────────────────────────────────
def _load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ─── 邮件 HTML ──────────────────────────────────────
def generate_email_content(all_items, date_str):
    # 只取前 10 条
    all_items = all_items[:10]

    # 按平台分组
    platforms = {}
    for item in all_items:
        p = item.get("platform", "Other")
        if p not in platforms:
            platforms[p] = []
        platforms[p].append(item)

    platform_styles = {
        "Product Hunt": ("#e65100", "#fff3e0"),
        "Hacker News": ("#ff5722", "#fbe9e7"),
        "AlternativeTo": ("#4caf50", "#e8f5e9"),
        "There's An AI For That": ("#9c27b0", "#f3e5f5"),
    }

    idx = 0
    rows_html = ""

    for platform, items in platforms.items():
        color, bg = platform_styles.get(platform, ("#24292e", "#f6f8fa"))
        emoji = "🛠" if platform == "Product Hunt" else "📰" if platform == "Hacker News" else "🔧" if platform == "AlternativeTo" else "🤖"

        # Platform header row
        rows_html += "<tr>"
        rows_html += "<td colspan=\"2\" style=\"padding:12px 20px 6px;background:" + bg + ";border-bottom:1px solid #eaecef;\">"
        rows_html += "<span style=\"font-size:13px;font-weight:700;color:" + color + ";\">" + emoji + " " + platform + " · 热门产品</span>"
        rows_html += "</td></tr>"

        for item in items:
            idx += 1
            desc = item.get("ai_description", "") or ""
            votes = item.get("votes", item.get("points", "—"))
            comments = item.get("comments", "—")
            title = item.get("title", "")[:70]
            url = item.get("url", "")

            if item.get("platform") == "Hacker News":
                extra_info = "⬆ {} pts 💬 {} comments".format(votes, comments)
            elif item.get("platform") == "Product Hunt":
                extra_info = "⬆ {} votes 💬 {} comments".format(votes, comments)
            else:
                extra_info = ""

            # Item row
            rows_html += "<tr>"
            rows_html += "<td style=\"padding:14px 20px;border-bottom:1px solid #eaecef;vertical-align:top;\">"
            rows_html += "<div style=\"font-size:15px;font-weight:700;color:{};margin-bottom:6px;\">".format(color)
            rows_html += "{}. <a href=\"{}\" style=\"color:{};text-decoration:none;\">{}</a>".format(idx, url, color, title)
            rows_html += "</div>"
            rows_html += "<div style=\"font-size:13px;color:#586069;margin-bottom:4px;\">[{}]</div>".format(platform)
            rows_html += "<div style=\"font-size:13px;color:#24292e;line-height:1.8;margin-bottom:6px;word-break:break-word;\">{}</div>".format(desc)
            rows_html += "<div style=\"font-size:12px;color:#888;\">{} <a href=\"{}\" style=\"color:#0366d6;text-decoration:none;margin-left:8px;\">🔗 查看详情 →</a></div>".format(extra_info, url)
            rows_html += "</td></tr>"

    total = len(all_items)

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>产品发现日报</title></head>'
        '<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif;">'
        '<div style="max-width:720px;margin:0 auto;padding:16px;">'
        '<div style="background:linear-gradient(135deg,#e65100 0%,#ff8a65 100%);border-radius:12px 12px 0 0;padding:20px 24px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<div style="font-size:24px;">🚀</div>'
        '<div>'
        '<div style="color:white;font-size:18px;font-weight:700;">产品发现日报</div>'
        '<div style="color:#fff3e0;font-size:12px;margin-top:2px;">Product Hunt × Hacker News · ' + date_str + ' · 每日 8:00 推送</div>'
        '</div></div></div>'
        '<div style="background:white;border:1px solid #e1e4e8;border-top:none;">'
        '<div style="padding:10px 20px;background:#f6f8fa;border-bottom:1px solid #eaecef;font-size:12px;color:#586069;">'
        '🔥 今日热门产品 & 话题 · AI 中文解读 · 共 ' + str(total) + ' 条'
        '</div>'
        '<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">' +
        rows_html +
        '</table></div>'
        '<div style="background:#24292e;border-radius:0 0 12px 12px;padding:12px 24px;">'
        '<div style="color:#8b949e;font-size:11px;text-align:center;">'
        '<div style="margin-bottom:4px;">📊 <a href="https://producthunt.com" style="color:#58a6ff;text-decoration:none;">Product Hunt</a> · <a href="https://news.ycombinator.com" style="color:#58a6ff;text-decoration:none;">Hacker News</a></div>'
        '<div>🤖 AI 解读模型：' + MINIMAX_MODEL + ' · 请勿直接回复此邮件</div>'
        '</div></div></div></body></html>'
    )
    return html

def send_email(to_email, subject, html_content, date_str):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((Header("产品发现日报", 'utf-8').encode(), SMTP_CONFIG["email"]))
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        plain = "产品发现日报 {}\n\nProduct Hunt × Hacker News\n\nhttps://producthunt.com\nhttps://news.ycombinator.com".format(date_str)
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        server = smtplib.SMTP_SSL(SMTP_CONFIG['smtp_host'], SMTP_CONFIG['smtp_port'])
        server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
        server.sendmail(SMTP_CONFIG["email"], [to_email], msg.as_string())
        server.quit()
        return {"success": True}
    except Exception as e:
        print("❌ 发送失败: {}".format(e))
        import traceback; traceback.print_exc()
        return {"success": False, "message": str(e)}

# ─── 主流程 ──────────────────────────────────────────
def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    subject = "🚀 产品发现日报 | {}".format(date_str)

    print("📅 Date: {}".format(date_str))

    print("\n🛠️ Fetching Product Hunt today's hot...")
    ph_items = fetch_product_hunt()
    print("   ✅ Found {} products".format(len(ph_items)))
    for item in ph_items:
        print("   - {}".format(item['title'][:60]))

    print("\n🔧 Fetching AlternativeTo hot...")
    at_items = fetch_alternativeto()
    print("   ✅ Found {} tools".format(len(at_items)))

    print("\n🤖 Fetching There's An AI For That...")
    ai_items = fetch_ai_tools()
    print("   ✅ Found {} AI tools".format(len(ai_items)))

    print("\n📰 Fetching Hacker News today's hot...")
    hn_items = fetch_hacker_news()
    print("   ✅ Found {} topics".format(len(hn_items)))
    for item in hn_items:
        print("   - [{} pts] {}".format(item.get('points',0), item['title'][:60]))

    all_items = ph_items + at_items + ai_items + hn_items

    if not all_items:
        print("❌ No data from any platform, exit")
        sys.exit(1)

    print("\n📊 Total {} items collected".format(len(all_items)))

    print("\n🤖 Generating {} AI descriptions via MiniMax...".format(len(all_items)))
    ai_descs = summarize_items(all_items)
    for item, desc in zip(all_items, ai_descs):
        item["ai_description"] = desc
        print("   [{}] {} chars".format(item['title'][:40], len(desc)))

    print("\n📧 Generating email content...")
    html_content = generate_email_content(all_items, date_str)

    print("📤 Sending email to {}...".format(TO_EMAIL))
    result = send_email(TO_EMAIL, subject, html_content, date_str)

    if result["success"]:
        print("✅ Email sent successfully!")
        with open("/home/admin/.openclaw/workspace/tasks/product-trending-sent.log", "a") as f:
            f.write("[{}] Sent | PH: {}, AT: {}, AI: {}, HN: {}\n".format(
                date_str, len(ph_items), len(at_items), len(ai_items), len(hn_items)))
    else:
        print("❌ Email failed: {}".format(result.get('message')))
        sys.exit(1)

    print("\n=== JSON ===")
    print(json.dumps({
        "success": True,
        "date": date_str,
        "product_hunt_count": len(ph_items),
        "alternativeto_count": len(at_items),
        "ai_tools_count": len(ai_items),
        "hacker_news_count": len(hn_items),
    }, ensure_ascii=False, indent=2))
    print("=== END JSON ===")

if __name__ == "__main__":
    main()