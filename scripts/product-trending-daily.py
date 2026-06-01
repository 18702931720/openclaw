#!/usr/bin/env python3
"""
Product Hunt + Hacker News 产品发现日报 v2.0
抓取两个平台当天的热门产品/话题，生成 AI 中文解读，邮件推送
- 优化点：AI 总览摘要、一句话价值描述、平台差异化、分类标签、视觉升级
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

# ─── 关注赛道标签映射 ─────────────────────────────────
CATEGORY_TAGS = {
    "ai":      "🤖 AI平台",
    "cloud":   "☁️ 云原生",
    "ci":      "🔄 CI/CD",
    "devops":  "🔧 DevOps",
    "mlops":   "📊 MLOps",
    "collab":  "👥 协作",
    "db":      "🗄️ 数据库",
    "security":"🔐 安全",
    "infra":   "🏗️ 基础设施",
}

# ─── HTTP ─────────────────────────────────────────────
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

# ─── Product Hunt ─────────────────────────────────────
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

            author_m = re.search(r'<author>.*?<name>([^<]+)</name>', entry)
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
                    "url": url,
                    "category": _detect_category(title + " " + desc),
                })
        return products[:10]
    except Exception as e:
        print("  [WARN] Product Hunt Feed 失败: {}".format(e))
        return []

# ─── AlternativeTo ─────────────────────────────────────
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
                    "url": "https://alternativeto.net/software/{}/".format(slug),
                    "category": _detect_category(name),
                })
        return tools
    except Exception as e:
        print("  [WARN] AlternativeTo 失败: {}".format(e))
        return []

# ─── There's An AI For That ────────────────────────────
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
                    "url": "https://theresanaiforthat.com/tools/{}/".format(slug),
                    "category": "ai",
                })
        return tools
    except Exception as e:
        print("  [WARN] There's An AI For That 失败: {}".format(e))
        return []

# ─── Hacker News ────────────────────────────────────────
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
                        "category": _detect_category(title),
                        "heat": _calc_heat(points, num_comments),
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
                            "category": _detect_category(item.get("title", "")),
                            "heat": _calc_heat(item.get("score", 0), item.get("descendants", 0)),
                        })
                time.sleep(0.3)
            return stories
    except Exception as e:
        print("  [WARN] HN Firebase 降级失败: {}".format(e))
        return []

# ─── 分类检测 ──────────────────────────────────────────
def _detect_category(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["ai", "llm", "gpt", "claude", "gemini", "model", "nlp", "生成式", "大模型"]):
        return "ai"
    if any(k in text_lower for k in ["aws", "azure", "gcp", "cloud", "kubernetes", "k8s", "容器", "serverless"]):
        return "cloud"
    if any(k in text_lower for k in ["ci/cd", "pipeline", "github action", "gitlab ci", "jenkins", "自动化"]):
        return "ci"
    if any(k in text_lower for k in ["devops", "sre", "deploy", "infrastructure", "terraform"]):
        return "devops"
    if any(k in text_lower for k in ["mlops", "machine learning", "train", "model serving", "的特征"]):
        return "mlops"
    if any(k in text_lower for k in ["collab", "collaboration", "team", "slack", "notion", "协作"]):
        return "collab"
    if any(k in text_lower for k in ["database", "db", "postgres", "mysql", "redis", "sqlite"]):
        return "db"
    if any(k in text_lower for k in ["security", "auth", "oauth", "password", "zero trust", "安全"]):
        return "security"
    if any(k in text_lower for k in ["infra", "infrastructure", "dns", "cdn", "edge"]):
        return "infra"
    return "other"

# ─── HN 讨论热度指数 ────────────────────────────────────
def _calc_heat(points, comments):
    score = (points or 0) * 1 + (comments or 0) * 2
    if score >= 200:
        return "🔥🔥🔥"
    elif score >= 100:
        return "🔥🔥"
    elif score >= 50:
        return "🔥"
    return ""

# ─── AI 生成价值描述 + 总览摘要 ─────────────────────────
def generate_ai_content(all_items):
    """调用 MiniMax 同时生成：总览摘要 + 每条价值描述"""
    if not MINIMAX_API_KEY:
        return None, [fallback_desc(item) for item in all_items]

    items_text = ""
    for i, item in enumerate(all_items, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        platform = item.get("platform", "")
        votes = item.get("votes", item.get("points", ""))
        comments = item.get("comments", "")
        desc = item.get("description", "")
        category = item.get("category", "other")
        tag = CATEGORY_TAGS.get(category, "📦 通用工具")
        items_text += '\n### Product {} [{}] ({})\nName: {}\nTagline: {}\nURL: {}\nStats: votes/points={}, comments={}\n'.format(
            i, platform, tag, title, desc if desc else 'N/A', url, votes, comments
        )

    prompt = """You are a senior product analyst covering AI Cloud platforms, DevOps, and developer tooling.

For the following {num} products and topics from Product Hunt and Hacker News, generate:

## 1. Executive Overview (in Chinese)
A 150-character summary of the most important trend today: what category is hottest, what's notable, and one sharp insight. Format:
**📌 今日观察** [150 chars Chinese]

## 2. Per-Item Value Description (in Chinese)
For each item, write a 60-100 character Chinese description: product name + one-line positioning + why it matters. Format strictly as:
### Product N [Platform]
[60-100 chars Chinese description]

## Input
{items_text}

## Output Format
**📌 今日观察** [150 chars]
### Product 1 [Platform]
[desc]
### Product 2 [Platform]
[desc]
... (total {num} items)""".format(num=len(all_items), items_text=items_text)

    result_text = _call_minimax(prompt)
    if not result_text:
        return None, [fallback_desc(item) for item in all_items]

    # 解析总览摘要
    overview = None
    overview_m = re.search(r'\*\*📌 今日观察\*\*\s*(.{100,200}?)(?=\n###|\Z)', result_text, re.DOTALL)
    if overview_m:
        overview = overview_m.group(1).strip()

    # 解析每条描述
    parsed = []
    parts = re.split(r'###\s*Product\s*(\d+)', result_text)
    idx = 2
    while idx < len(parts) and len(parsed) < len(all_items):
        desc = parts[idx].strip()
        if desc:
            parsed.append(desc)
        idx += 2

    if not overview or len(parsed) < len(all_items) * 0.5:
        return None, [fallback_desc(item) for item in all_items]

    # 不足的补 fallback
    while len(parsed) < len(all_items):
        parsed.append(fallback_desc(all_items[len(parsed)]))
    parsed = parsed[:len(all_items)]

    return overview, parsed

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

def fallback_desc(item):
    title = item.get("title", "")
    platform = item.get("platform", "")
    desc = item.get("description", "")
    if desc:
        return desc
    return "来自 {} - {}".format(platform, title)

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

# ─── 邮件 HTML ────────────────────────────────────────
def generate_email_content(all_items, date_str, overview=None):
    all_items = all_items[:10]

    # 按平台分组
    platforms = {}
    for item in all_items:
        p = item.get("platform", "Other")
        if p not in platforms:
            platforms[p] = []
        platforms[p].append(item)

    # 平台样式
    platform_styles = {
        "Product Hunt":           ("#e65100", "#fff3e0", "🛠️"),
        "Hacker News":            ("#ff5722", "#fbe9e7", "📰"),
        "AlternativeTo":           ("#4caf50", "#e8f5e9", "🔧"),
        "There's An AI For That": ("#9c27b0", "#f3e5f5", "🤖"),
    }

    idx = 0
    rows_html = ""

    for platform, items in platforms.items():
        color, bg, emoji = platform_styles.get(platform, ("#24292e", "#f6f8fa", "📦"))
        is_hn = platform == "Hacker News"

        # Platform header
        rows_html += "<tr>"
        rows_html += "<td colspan=\"2\" style=\"padding:12px 20px 6px;background:" + bg + ";border-bottom:1px solid #eaecef;\">"
        rows_html += "<span style=\"font-size:13px;font-weight:700;color:" + color + ";\">" + emoji + " " + platform + " · 热门产品</span>"
        rows_html += "</td></tr>"

        for item in items:
            idx += 1
            ai_desc = item.get("ai_description", "")
            title = item.get("title", "")
            url = item.get("url", "")
            votes = item.get("votes", item.get("points", "—"))
            comments = item.get("comments", "—")
            category = item.get("category", "other")
            tag = CATEGORY_TAGS.get(category, "📦 通用工具")
            heat = item.get("heat", "")

            if is_hn:
                extra_info = "⬆ {} pts 💬 {} comments {}".format(votes, comments, heat)
            else:
                extra_info = "⬆ {} votes 💬 {} comments".format(votes, comments)

            # Tag badge
            tag_html = '<span style="display:inline-block;background:#e8f4ff;color:#0366d6;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;margin-right:6px;">' + tag + '</span>'

            rows_html += "<tr>"
            rows_html += "<td style=\"padding:14px 20px;border-bottom:1px solid #eaecef;vertical-align:top;\">"

            # Title row with tag
            rows_html += "<div style=\"display:flex;align-items:start;margin-bottom:6px;\">"
            rows_html += "<div style=\"flex:1;\">"
            rows_html += "<div style=\"font-size:15px;font-weight:700;color:#24292e;margin-bottom:4px;line-height:1.4;\">"
            rows_html += "{} <a href=\"{}\" style=\"color:{};text-decoration:none;\">{}</a>".format(idx, url, color, title)
            rows_html += "</div>"
            rows_html += tag_html
            rows_html += "</div></div>"

            # AI description
            if ai_desc:
                rows_html += "<div style=\"font-size:13px;color:#24292e;line-height:1.7;margin-bottom:8px;padding:8px 10px;background:#f6f8fa;border-left:3px solid " + color + ";border-radius:0 4px 4px 0;\">"
                rows_html += "<span style=\"color:#888;font-size:11px;margin-right:4px;\">💡</span>" + ai_desc
                rows_html += "</div>"

            # Stats + link
            rows_html += "<div style=\"font-size:12px;color:#888;\">"
            rows_html += extra_info
            rows_html += " <a href=\"{}\" style=\"color:#0366d6;text-decoration:none;margin-left:8px;\">🔗 查看详情 →</a>".format(url)
            rows_html += "</div>"
            rows_html += "</td></tr>"

    # 标签墙
    tag_counts = {}
    for item in all_items:
        cat = item.get("category", "other")
        tag_counts[cat] = tag_counts.get(cat, 0) + 1

    badge_html = ""
    for cat, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        tag = CATEGORY_TAGS.get(cat, "📦 通用工具")
        badge_html += '<span style="display:inline-block;background:#24292e;color:#fff;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;margin:3px;">{} {}个</span>'.format(tag, count)

    total = len(all_items)
    ph_count = sum(1 for i in all_items if i.get("platform") == "Product Hunt")
    hn_count = sum(1 for i in all_items if i.get("platform") == "Hacker News")

    # 总览摘要
    overview_html = ""
    if overview:
        overview_html = """
        <div style="margin:0 20px 16px;padding:14px 16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:8px;color:white;">
            <div style="font-size:11px;font-weight:700;margin-bottom:6px;letter-spacing:0.5px;">📌 今日观察</div>
            <div style="font-size:13px;line-height:1.7;">{}</div>
        </div>""".format(overview)

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>产品发现日报</title></head>'
        '<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif;">'
        '<div style="max-width:720px;margin:0 auto;padding:16px;">'

        # Header
        '<div style="background:linear-gradient(135deg,#e65100 0%,#ff8a65 100%);border-radius:12px 12px 0 0;padding:20px 24px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<div style="font-size:28px;">🚀</div>'
        '<div>'
        '<div style="color:white;font-size:18px;font-weight:700;">产品发现日报 v2.0</div>'
        '<div style="color:#fff3e0;font-size:12px;margin-top:2px;">Product Hunt × Hacker News · ' + date_str + ' · 每日 8:00 推送</div>'
        '</div></div></div>'

        # Summary bar
        '<div style="background:white;border:1px solid #e1e4e8;border-top:none;padding:10px 20px;font-size:12px;color:#586069;">'
        '🔥 今日热门 · 共 ' + str(total) + ' 条 (PH: ' + str(ph_count) + ' / HN: ' + str(hn_count) + ')'
        '</div>'

        # Overview (AI summary)
        + overview_html +

        # Tag badges
        '<div style="background:white;border:1px solid #e1e4e8;border-top:none;padding:10px 20px;">'
        '<div style="font-size:11px;color:#888;margin-bottom:6px;">🏷️ 今日涉及领域</div>'
        + badge_html +
        '</div>'

        # Items table
        '<div style="background:white;border:1px solid #e1e4e8;border-top:none;margin-top:8px;">'
        '<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">' +
        rows_html +
        '</table></div>'

        # Footer
        '<div style="background:#24292e;border-radius:0 0 12px 12px;padding:12px 24px;">'
        '<div style="color:#8b949e;font-size:11px;text-align:center;">'
        '<div style="margin-bottom:4px;">📊 <a href="https://producthunt.com" style="color:#58a6ff;text-decoration:none;">Product Hunt</a> · <a href="https://news.ycombinator.com" style="color:#58a6ff;text-decoration:none;">Hacker News</a></div>'
        '<div>🤖 AI 解读模型：' + MINIMAX_MODEL + ' · 请勿直接回复此邮件</div>'
        '</div></div></div></body></html>'
    )
    return html

def send_email(to_email, subject, html_content, date_str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr(['AI 产品助手', SMTP_CONFIG["email"]])
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    try:
        with smtplib.SMTP_SSL(SMTP_CONFIG["smtp_host"], SMTP_CONFIG["smtp_port"]) as server:
            server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
            server.sendmail(SMTP_CONFIG["email"], [to_email], msg.as_string())
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ─── Main ─────────────────────────────────────────────
def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    subject = "🚀 产品发现日报 v2.0 | {}".format(date_str)

    print("📅 Date: {}".format(date_str))

    print("\n🛠️ Fetching Product Hunt today's hot...")
    ph_items = fetch_product_hunt()
    print("   ✅ Found {} products".format(len(ph_items)))

    print("\n🔧 Fetching AlternativeTo hot...")
    at_items = fetch_alternativeto()
    print("   ✅ Found {} tools".format(len(at_items)))

    print("\n🤖 Fetching There's An AI For That...")
    ai_items = fetch_ai_tools()
    print("   ✅ Found {} AI tools".format(len(ai_items)))

    print("\n📰 Fetching Hacker News today's hot...")
    hn_items = fetch_hacker_news()
    print("   ✅ Found {} topics".format(len(hn_items)))

    all_items = ph_items + at_items + ai_items + hn_items

    if not all_items:
        print("❌ No data from any platform, exit")
        sys.exit(1)

    print("\n📊 Total {} items collected".format(len(all_items)))

    # 统计分类
    from collections import Counter
    cat_counter = Counter(i.get("category","other") for i in all_items)
    print("\n🏷️ Category breakdown: {}".format(dict(cat_counter)))

    print("\n🤖 Generating AI overview + {} value descriptions via MiniMax...".format(len(all_items)))
    overview, ai_descs = generate_ai_content(all_items)
    if overview:
        print("   📌 Overview: {}".format(overview[:80]))
    for item, desc in zip(all_items, ai_descs):
        item["ai_description"] = desc
        print("   [{}] {} chars".format(item['title'][:40], len(desc)))

    print("\n📧 Generating email content...")
    html_content = generate_email_content(all_items, date_str, overview)

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