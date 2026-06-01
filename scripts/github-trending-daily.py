#!/usr/bin/env python3
"""
GitHub Trending 每日热门项目抓取脚本
每个项目通过 AI 模型生成不少于 500 字的中文描述
"""

import smtplib, json, sys, re, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import time

# ─── 配置 ───────────────────────────────────────────
SMTP_CONFIG = {
    "email": "kim.han@sinoboom.com.cn",
    "smtp_host": "smtp.qiye.163.com",
    "smtp_port": 465,
    "password": "ZE3#PgJe4W#SPgHC"
}
TO_EMAIL = "kim.han@sinoboom.com.cn"

OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY",  "")
OPENAI_MODEL    = "gpt-4o-mini"
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY",  "")
GEMINI_MODEL    = "gemini-2.0-flash"
MINIMAX_API_KEY = "sk-cp-yrK6QN6yWPmvL2Xzj6FDf9vFI3hdf4DuuINKOzlSnODY2OBwQVhsduhj1UqbGmooYLQbLnhznYT1me6gy66K7PCGDNijxUornhrY_CjqerVMelOQok8WUio"
MINIMAX_MODEL   = "MiniMax-M2.7"

CACHE_FILE = "/home/admin/.openclaw/workspace/tasks/github-trending-cache.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
}

# ─── HTTP ────────────────────────────────────────────
def http_get(url, headers=None, timeout=15):
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    req = Request(url, headers=h)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  [WARN] GET {url} -> {e}")
        return None

# ─── GitHub 抓取 ────────────────────────────────────
def fetch_github_trending():
    """抓取 GitHub Trending 页面，返回项目列表（含基本信息）"""
    url = "https://github.com/trending"
    html = http_get(url, headers={"Accept": "text/html"})
    if not html:
        return []

    projects = []
    rows = re.findall(r'<article[^>]*class="Box-row"[^>]*>(.*?)</article>', html, re.DOTALL)

    for row in rows[:10]:
        # 提取项目路径
        m = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"', row, re.DOTALL)
        if not m:
            continue
        path = m.group(1)

        # 从 HTML 中提取描述（很多项目有）
        desc_m = re.search(r'<p[^>]*>\s*([^\n<]{10,500}?)\s*</p>', row)
        description = desc_m.group(1).strip() if desc_m else ""

        # 提取语言
        lang_m = re.search(r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]+)</span>', row)
        language = lang_m.group(1).strip() if lang_m else "未知"

        # 提取星标数（总数）
        stars_m = re.search(r'aria-label="([0-9,]+)\s+star', row)
        stars_str = stars_m.group(1).replace(',', '') if stars_m else "0"
        stars = int(stars_str) if stars_str.isdigit() else 0

        # 提取今日新增
        today_m = re.search(r'([0-9,]+)\s+stars?\s+today', row)
        today_stars = today_m.group(1).replace(',', '') if today_m else "?"

        projects.append({
            "path": path,
            "description": description,
            "language": language,
            "stars": stars,
            "today_stars": today_stars,
            "topics": [],
            "forks": 0,
            "readme": None,
            "from_html": True,  # 标记为从 HTML 解析（可能有部分数据缺失）
        })
    return projects

def fetch_repo_details(path):
    """通过 GitHub API 获取仓库信息 + README 内容，带缓存和 HTML 降级"""
    # 先查缓存
    cache = _load_cache()
    if path in cache:
        print(f"  [{path}] ... 使用缓存")
        cached = cache[path]
        # 确保 ai_description 不丢失
        result = dict(cached)
        result["from_html"] = False
        return result

    # 尝试 API
    api_url = f"https://api.github.com/repos/{path}"
    data = http_get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
    if not data:
        print(f"  [{path}] ... API 失败，跳过（稍后重试）")
        return None
    try:
        repo = json.loads(data)
    except Exception:
        return None

    readme_content = None
    for readme_name in ["README.md", "readme.md", "README", "readme.txt"]:
        raw_url = f"https://raw.githubusercontent.com/{path}/HEAD/{readme_name}"
        content = http_get(raw_url, timeout=10)
        if content and len(content) > 50:
            readme_content = content[:4000].strip()
            break

    result = {
        "path": path,
        "description": repo.get("description") or "",
        "topics": repo.get("topics", []) or [],
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language") or "未知",
        "forks": repo.get("forks_count", 0),
        "readme": readme_content,
        "from_html": False,
    }

    # 更新缓存
    cache[path] = result
    _save_cache(cache)
    return result

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
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass

# ─── AI 批量摘要 ────────────────────────────────────
def summarize_batch(repo_infos):
    """批量调用 AI 为所有项目生成中文描述"""
    if not MINIMAX_API_KEY and not OPENAI_API_KEY and not GEMINI_API_KEY:
        print("  [WARN] 无可用 API，全部使用 fallback")
        return [fallback_description(r) for r in repo_infos]

    projects_text = ""
    for i, r in enumerate(repo_infos, 1):
        readme = r.get("readme") or ""
        projects_text += f"""
=== 项目 {i}: {r['path']} ===
官方描述: {r.get('description') or '无'}
语言: {r.get('language', '未知')}
README 内容:
{readme[:1200]}
"""

    prompt = f"""你是一位专业的开源技术分析师。请为以下 10 个 GitHub Trending 项目各生成一段不少于 200 字的中文描述，格式要求：
- 每个项目描述前加编号和项目名（格式：### 项目N /path/name）
- 描述需包含：项目背景、功能特点、技术实现、适用场景、亮点
- 语言流畅专业，不要重复

## 项目列表
{projects_text}

## 输出格式
请严格按照以下格式输出，描述正文不少于 200 字/项目：

### 项目 1 /owner/repo
[该项目的中文描述]

### 项目 2 /owner/repo
[该项目的中文描述]

...（共 10 个项目）"""

    # 优先 MiniMax
    result_text = _call_minimax(prompt) if MINIMAX_API_KEY else None

    # 失败则 OpenAI
    if not result_text and OPENAI_API_KEY:
        result_text = _call_openai(prompt)

    # 失败则 Gemini
    if not result_text and GEMINI_API_KEY:
        result_text = _call_gemini(prompt)

    if result_text:
        parsed = _parse_batch_text(result_text, len(repo_infos))
        if len(parsed) >= len(repo_infos):
            return parsed[:len(repo_infos)]

    print("  [WARN] AI 生成失败，全部使用 fallback")
    return [fallback_description(r) for r in repo_infos]

def _call_minimax(prompt):
    """调用 MiniMax M2.7 API（Anthropic 格式）"""
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
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                # MiniMax M2.7 返回 content 可能是多个 block，找 text 类型
                for block in result.get("content", []):
                    if block.get("type") == "text" and block.get("text", "").strip():
                        return block.get("text", "").strip()
                raise ValueError(f"No text block: {result.get('content')}")
        except Exception as e:
            print(f"  [WARN] MiniMax 失败: {e}")
            if attempt < 1:
                time.sleep(3)
    return None

def _call_openai(prompt):
    """调用 OpenAI API"""
    for attempt in range(2):
        try:
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位专业的开源技术分析师，输出格式严格遵守用户要求。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }
            req = Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [WARN] OpenAI 失败: {e}")
            if attempt < 1:
                time.sleep(5)
    return None

def _call_gemini(prompt):
    for attempt in range(2):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4000}
            }
            req = Request(url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        except Exception as e:
            print(f"  [WARN] Gemini 失败: {e}")
            if attempt < 1:
                time.sleep(5)
    return None

def _parse_batch_text(text, expected):
    """从 AI 输出中解析出每个项目的描述"""
    results = []
    parts = re.split(r'###\s*项目\s*(\d+)', text)
    # parts[0]=前言, parts[1]=编号, parts[2]=描述, ...
    idx = 2
    while idx < len(parts) and len(results) < expected:
        desc = parts[idx].strip()
        if desc:
            results.append(desc)
        idx += 2
    return results

# ─── Fallback 描述 ──────────────────────────────────
def fallback_description(repo_info):
    path = repo_info.get("path", "")
    desc = repo_info.get("description", "") or ""
    topics = repo_info.get("topics", []) or []
    language = repo_info.get("language", "未知")
    stars = repo_info.get("stars", 0)
    forks = repo_info.get("forks", 0)
    readme = repo_info.get("readme", "") or ""

    result = f"【{path}】"
    if desc:
        result += f"\n\n官方简介：{desc}"
    if topics:
        result += f"\n\n项目标签：{' / '.join(topics)}"
    result += f"\n\n技术栈：{language} 语言开发"
    result += f"\n\n社区数据：GitHub Star 数 {stars:,}，Fork 数 {forks:,}，反映了该项目在开发者社区的受欢迎程度和活跃度。"

    if readme:
        first_para = readme.split('\n\n')[0].replace('\n', ' ').strip()
        if len(first_para) > 50:
            result += f"\n\n项目自述：{first_para[:800]}"

    if len(result) < 500:
        result += f"\n\n综合来看，{path.split('/')[-1]} 是当前 GitHub Trending 中的热门项目之一，"
        result += f"由 {path.split('/')[0]} 团队维护，在 {language} 生态中具有较强的创新性和实用价值。"
        result += f"该项目目前在社区中获得了 {stars:,} 个 Star 和 {forks:,} 个 Fork，"
        result += "说明其受到了广泛关注和认可。从项目定位和技术实现来看，"
        result += "适合对相关技术方向感兴趣的开发者关注和学习。"

    return result

# ─── 邮件 HTML ──────────────────────────────────────
def generate_email_content(repos, date_str):
    rows_html = ""
    for i, repo in enumerate(repos, 1):
        desc = repo.get("ai_description", "") or repo.get("description", "暂无描述")
        desc_html = desc.replace('\n', '<br>')
        stars_fmt = f"{repo['stars']:,}" if repo['stars'] else "?"
        topics_html = ''.join([
            f'<span style="background:#e1e4e8;padding:1px 8px;border-radius:10px;margin-right:6px;font-size:12px;color:#444;">{t}</span>'
            for t in (repo.get('topics', []) or [])[:5]
        ]) if repo.get('topics') else ''

        rows_html += '''
        <tr>
            <td style="padding:20px 24px;border-bottom:1px solid #eaecef;vertical-align:top;">
                <div style="font-size:17px;font-weight:700;color:#0366d6;margin-bottom:10px;">
                    ''' + str(i) + '''. <a href="https://github.com/''' + repo['path'] + '''" style="color:#0366d6;text-decoration:none;">''' + repo['path'] + '''</a>
                </div>
                <div style="font-size:14px;color:#24292e;line-height:2;margin-bottom:10px;word-break:break-word;">
                    ''' + desc_html + '''
                </div>
                <div style="font-size:13px;color:#6a737d;margin-top:10px;">
                    <span style="background:#f1f8ff;padding:2px 8px;border-radius:12px;margin-right:12px;color:#0366d6;">''' + repo['language'] + '''</span>
                    <span style="margin-right:12px;">⭐ ''' + stars_fmt + '''</span>
                    <span style="margin-right:12px;">🍴 ''' + str(repo['forks']) + '''</span>
                    ''' + topics_html + '''
                </div>
            </td>
        </tr>'''

    ai_model_str = MINIMAX_MODEL if MINIMAX_API_KEY else (OPENAI_MODEL if OPENAI_API_KEY else GEMINI_MODEL if GEMINI_API_KEY else "N/A")
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GitHub 热门项目日报</title></head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
    <div style="max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#24292e 0%,#2f363d 100%);border-radius:12px 12px 0 0;padding:24px 32px;">
            <div style="display:flex;align-items:center;gap:12px;">
                <svg height="32" viewBox="0 0 16 16" width="32" fill="white"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
                <div>
                    <div style="color:white;font-size:20px;font-weight:700;">GitHub 热门项目日报</div>
                    <div style="color:#8b949e;font-size:13px;margin-top:2px;">""" + date_str + """ · 每日 9:00 定时推送</div>
                </div>
            </div>
        </div>
        <div style="background:white;border:1px solid #e1e4e8;border-top:none;">
            <div style="padding:12px 24px;background:#f6f8fa;border-bottom:1px solid #eaecef;font-size:13px;color:#586069;">
                🔥 今日 GitHub Trending · AI 中文解读 · TOP 10 热门项目
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                """ + rows_html + """
            </table>
        </div>
        <div style="background:#24292e;border-radius:0 0 12px 12px;padding:16px 32px;">
            <div style="color:#8b949e;font-size:12px;text-align:center;">
                <div style="margin-bottom:6px;">📊 数据来源：<a href="https://github.com/trending" style="color:#58a6ff;text-decoration:none;">GitHub Trending</a></div>
                <div style="margin-bottom:6px;">🤖 AI 描述模型：""" + ai_model_str + """</div>
                <div style="margin-top:8px;color:#484f58;">━━━━━━━━━━━━━━━━━━━━</div>
                <div style="color:#484f58;font-size:11px;margin-top:6px;">请勿直接回复此邮件</div>
            </div>
        </div>
    </div>
</body></html>"""
    return html

def send_email(to_email, subject, html_content, date_str):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((Header("GitHub Trending Bot", 'utf-8').encode(), SMTP_CONFIG["email"]))
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(f"GitHub 热门项目日报 {date_str}\n\nhttps://github.com/trending", 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        server = smtplib.SMTP_SSL(SMTP_CONFIG['smtp_host'], SMTP_CONFIG['smtp_port'])
        server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
        server.sendmail(SMTP_CONFIG["email"], [to_email], msg.as_string())
        server.quit()
        return {"success": True}
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback; traceback.print_exc()
        return {"success": False, "message": str(e)}

# ─── 主流程 ──────────────────────────────────────────
def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    subject = f"📈 GitHub 热门项目日报 | {date_str}"

    print(f"📅 日期: {date_str}")
    print("🔥 正在抓取 GitHub Trending 列表...")

    project_paths = fetch_github_trending()
    if not project_paths:
        print("❌ 抓取列表失败，退出"); sys.exit(1)

    print(f"✅ 找到 {len(project_paths)} 个项目，正在获取详情...")

    repos = []
    api_failed_count = 0
    for proj in project_paths:
        path = proj["path"] if isinstance(proj, dict) else proj
        print(f"  [{path}] ...", end=" ", flush=True)
        repo_info = fetch_repo_details(path)
        if repo_info:
            print(f"OK (README: {len(repo_info.get('readme') or '') or 0} 字)")
            repos.append(repo_info)
        else:
            # API 失败了，把 HTML 解析的数据拿来用（README 会缺失）
            if isinstance(proj, dict) and proj.get("description"):
                repo_info = dict(proj)
                repo_info["ai_description"] = None  # 先标记，稍后由 AI 生成
                repos.append(repo_info)
                api_failed_count += 1
                print(f"API 失败，使用 HTML 数据（描述: {len(proj.get('description',''))} 字）")
            else:
                print("API 失败，跳过")

    if not repos:
        print("❌ 所有项目获取失败，退出"); sys.exit(1)

    print(f"\n✅ 成功获取 {len(repos)} 个项目详情")
    print("🤖 正在调用 MiniMax M2.7 生成中文描述（批量模式）...")

    # 检查缓存中是否已有 AI 描述
    cache = _load_cache()
    needs_ai = False
    for repo in repos:
        cached = cache.get(repo["path"], {})
        if cached.get("ai_description"):
            repo["ai_description"] = cached["ai_description"]
            print(f"  [{repo['path']}] 使用已缓存的描述 ({len(repo['ai_description'])} 字)")
        else:
            needs_ai = True

    if needs_ai:
        ai_descs = summarize_batch(repos)
        for repo, desc in zip(repos, ai_descs):
            repo["ai_description"] = desc
            # 回填缓存
            if repo["path"] in cache:
                cache[repo["path"]]["ai_description"] = desc
        _save_cache(cache)
        for repo in repos:
            print(f"  [{repo['path']}] AI 描述长度: {len(repo['ai_description'])} 字")

    print("\n📧 正在生成邮件内容...")
    html_content = generate_email_content(repos, date_str)

    print(f"📤 正在发送邮件到 {TO_EMAIL}...")
    result = send_email(TO_EMAIL, subject, html_content, date_str)

    if result["success"]:
        print("✅ 邮件发送成功！")
        with open("/home/admin/.openclaw/workspace/tasks/github-trending-sent.log", "a") as f:
            f.write(f"[{date_str}] 发送成功，项目数: {len(repos)}\n")
    else:
        print(f"❌ 邮件发送失败: {result.get('message')}")
        sys.exit(1)

    print("\n=== JSON ===")
    print(json.dumps({"success": True, "projects_count": len(repos), "date": date_str}, ensure_ascii=False, indent=2))
    print("=== END JSON ===")

if __name__ == "__main__":
    main()