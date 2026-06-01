#!/usr/bin/env python3
"""
竞品情报雷达 - OpenClaw框架商业化产品
官网更新监控 + 竞品动态搜索

监控逻辑：
  1. 抓取竞品官网，对比页面内容 MD5，有变化则视为"有更新"
  2. 辅助以关键词搜索，获取近期新闻动态

依赖：
  uv run scripts/competitor-radar.py
  python3 scripts/competitor-radar.py

作者：June (六月)
更新：2026-05-21
"""

import os
import sys
import json
import re
import hashlib
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

# ============================================================
# 竞品配置（官网URL + 搜索关键词）
# ============================================================

COMPETITORS = {
    "QClaw": {
        "name": "QClaw",
        "vendor": "腾讯",
        "category": "互联网大厂",
        "description": "微信通道最强玩家，C端AI助手标杆",
        "url": "https://qclaw.qq.com/",
        "news_keywords": ["QClaw", "腾讯 AI Agent", "OpenClaw 腾讯"],
        "update_indicators": ["/changelog", "/docs", "/update", "/news", "/blog"],
    },
    "WorkBuddy": {
        "name": "WorkBuddy",
        "vendor": "腾讯",
        "category": "互联网大厂",
        "description": "企业级AI助手，审计日志+权限控制",
        "url": "https://workbuddy.qq.com/",
        "news_keywords": ["WorkBuddy 腾讯", "企业级 AI 助手 腾讯"],
        "update_indicators": ["/docs", "/news", "/changelog"],
    },
    "ArkClaw": {
        "name": "ArkClaw",
        "vendor": "火山引擎（字节）",
        "category": "互联网大厂",
        "description": "飞书生态企业级AI Agent",
        "url": "https://www.volcengine.com/product/arkclaw",
        "news_keywords": ["ArkClaw", "火山引擎 AI Agent", "OpenClaw 字节"],
        "update_indicators": ["/product/arkclaw", "/docs", "/changelog", "/news"],
    },
    "CoPaw": {
        "name": "CoPaw",
        "vendor": "阿里云",
        "category": "互联网大厂",
        "description": "钉钉/飞书/QQ全家桶集成，电商运营全流程",
        "url": "https://www.aliyun.com/",
        "news_keywords": ["CoPaw 阿里云", "阿里云 AI Agent Copaw"],
        "update_indicators": ["/product", "/news", "/blog"],
    },
    "钉钉悟空": {
        "name": "钉钉悟空",
        "vendor": "钉钉",
        "category": "互联网大厂",
        "description": "智能办公助手，钉钉深度集成",
        "url": "https://www.dingtalk.com/",
        "news_keywords": ["钉钉悟空", "钉钉 AI 助手"],
        "update_indicators": ["/qidian", "/news", "/blog"],
    },
    "DuClaw": {
        "name": "DuClaw",
        "vendor": "百度",
        "category": "互联网大厂",
        "description": "搜索+知识图谱，百度AI云集成",
        "url": "https://cloud.baidu.com/",
        "news_keywords": ["DuClaw 百度", "百度 AI Agent"],
        "update_indicators": ["/product", "/docs", "/news"],
    },
    "MaxClaw": {
        "name": "MaxClaw",
        "vendor": "MiniMax",
        "category": "AI厂商",
        "description": "性价比之选，MoE模型低成本",
        "url": "https://www.minimaxi.com/",
        "news_keywords": ["MaxClaw", "MiniMax AI 产品"],
        "update_indicators": ["/product", "/docs", "/changelog", "/news"],
    },
    "KimiClaw": {
        "name": "KimiClaw",
        "vendor": "月之暗面",
        "category": "AI厂商",
        "description": "知识工作者利器，超长上下文",
        "url": "https://www.moonshot.cn/",
        "news_keywords": ["KimiClaw", "月之暗面 AI 产品"],
        "update_indicators": ["/product", "/docs", "/changelog", "/news"],
    },
    "AutoClaw": {
        "name": "AutoClaw",
        "vendor": "智谱AI",
        "category": "AI厂商",
        "description": "隐私本地党首选，一键本地部署",
        "url": "https://www.zhipuai.cn/",
        "news_keywords": ["AutoClaw", "智谱 AI Agent"],
        "update_indicators": ["/product", "/docs", "/changelog", "/news"],
    },
    "QeeClaw": {
        "name": "QeeClaw",
        "vendor": "第三方",
        "category": "垂直专业版",
        "description": "企业超级秘书，私有化部署",
        "url": None,  # 无官网，跳过URL抓取
        "news_keywords": ["QeeClaw", "OpenClaw 企业版", "私有化部署 Agent"],
        "update_indicators": [],
    },
    "RetailClaw": {
        "name": "RetailClaw",
        "vendor": "第三方",
        "category": "垂直专业版",
        "description": "亚马逊品牌运营自动化",
        "url": None,
        "news_keywords": ["RetailClaw", "亚马逊 Vendor Central 自动化"],
        "update_indicators": [],
    },
}

STATE_FILE = Path(__file__).parent.parent / "tasks" / "competitor-radar-state.json"
SCRIPT_DIR = Path(__file__).parent.parent / "skills" / "searxng" / "scripts" / "searxng.py"
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")
REQUEST_TIMEOUT = 15  # 秒


# ============================================================
# 状态管理
# ============================================================

def load_state():
    """加载上次运行状态（URL -> MD5映射）"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"url_hashes": {}, "last_run": None}


def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============================================================
# 官网更新检测
# ============================================================

def fetch_url_content(url, referer=None):
    """抓取URL页面内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CompetitorRadar/1.0; +https://openclaw.ai)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            content_type = resp.headers.get("Content-Type", "")
            # 跳过非HTML
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None, None, "non-html"
            charset_match = re.search(r'charset=([\w-]+)', content_type)
            charset = charset_match.group(1) if charset_match else "utf-8"
            raw = resp.read()
            try:
                html = raw.decode(charset, errors="replace")
            except Exception:
                html = raw.decode("utf-8", errors="replace")
            return html, resp.headers, "ok"
    except urllib.error.HTTPError as e:
        return None, None, f"http-{e.code}"
    except Exception as e:
        return None, None, f"error-{e}"
    return None, None, "unknown"


def check_url_updates(url, old_hash, indicators=None):
    """
    检查URL是否有内容更新
    返回: (has_update, new_hash, summary, details)
    """
    if not url:
        return False, None, "no-url", []

    referer = url.split("/")[0] + "//" + url.split("/")[2]
    html, headers, status = fetch_url_content(url, referer)

    if status != "ok" or html is None:
        return False, old_hash, f"fetch-fail/{status}", []

    # 计算当前页面的MD5
    new_hash = hashlib.md5(html.encode("utf-8", errors="replace")).hexdigest()

    if new_hash == old_hash:
        return False, new_hash, "unchanged", []

    # 有更新！提取变化摘要
    changes = []

    # 检查指标页面（changelog/news/docs等）
    if indicators:
        for indicator in indicators:
            check_url = urljoin(url, indicator)
            ind_html, _, ind_status = fetch_url_content(check_url, referer)
            if ind_status == "ok" and ind_html:
                changes.append({
                    "type": "indicator_page",
                    "url": check_url,
                    "title": extract_title(ind_html),
                })

    # 从主页提取最新内容片段
    title = extract_title(html)
    latest_content = extract_latest_content(html)

    return True, new_hash, "updated", [{
        "type": "homepage",
        "url": url,
        "title": title,
        "content_preview": latest_content[:300] if latest_content else "",
    }] + changes


def extract_title(html):
    """提取页面标题"""
    m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def extract_latest_content(html):
    """从页面提取最新内容（移除script/style/nav，保留正文）"""
    # 移除script、style、nav标签
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', html)
    # 清理空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ============================================================
# 搜索
# ============================================================

def search_searxng(query, num_results=6):
    """使用searxng执行搜索"""
    if not SCRIPT_DIR.exists():
        return {"results": []}

    uv_cmd = ["uv", "run", str(SCRIPT_DIR), "search", query, "-n", str(num_results), "--format", "json"]
    cmd = [sys.executable, str(SCRIPT_DIR), "search", query, "-n", str(num_results), "--format", "json"]

    try:
        result = subprocess.run(
            uv_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env={**os.environ, "SEARXNG_URL": SEARXNG_URL}
        )
        if result.returncode != 0:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                env={**os.environ, "SEARXNG_URL": SEARXNG_URL}
            )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"results": []}
    except Exception:
        pass
    return {"results": []}


def collect_news(competitor_key, config, max_results=4):
    """通过关键词搜索收集近期新闻"""
    name = config["name"]
    keywords = config["news_keywords"]
    all_items = []

    for kw in keywords:
        query = f'"{kw}"'
        results = search_searxng(query, num_results=max_results)
        for r in results.get("results", []):
            title = re.sub(r'<[^>]+>', '', r.get("title", ""))
            url = r.get("url", "")
            snippet = re.sub(r'<[^>]+>', '', r.get("content", r.get("snippet", "")))
            if title and len(title) > 5 and "[需手动采集]" not in title:
                # 去重
                if not any(item["url"] == url for item in all_items):
                    all_items.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet[:200] if snippet else "",
                        "engine": r.get("engine", ""),
                    })

    return all_items[:max_results]


# ============================================================
# 采集主流程
# ============================================================

def collect_all(days_back=30):
    """采集所有竞品情报"""
    print(f"\n📡 竞品雷达启动 | {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
    print(f"=" * 60, file=sys.stderr)

    state = load_state()
    url_hashes = state.get("url_hashes", {})

    results = {}

    for key, config in COMPETITORS.items():
        print(f"\n▶️  {key} ({config['name']})", file=sys.stderr)

        competitor_result = {
            "name": config["name"],
            "vendor": config["vendor"],
            "category": config["category"],
            "description": config["description"],
            "url": config["url"],
            "has_url_update": False,
            "url_updates": [],
            "news": [],
        }

        # 1. URL监控
        if config["url"]:
            old_hash = url_hashes.get(key)
            has_update, new_hash, update_status, details = check_url_updates(
                config["url"], old_hash, config.get("update_indicators")
            )
            competitor_result["has_url_update"] = has_update
            competitor_result["url_updates"] = details
            competitor_result["url_status"] = update_status
            if new_hash:
                url_hashes[key] = new_hash
            status_icon = "🔄" if has_update else "➖"
            print(f"  {status_icon} URL: {update_status}", file=sys.stderr)

        # 2. 新闻搜索
        try:
            news = collect_news(key, config)
            competitor_result["news"] = news
            news_count = len(news)
            print(f"  📰 新闻: {news_count} 条", file=sys.stderr)
        except Exception as e:
            print(f"  ❌ 新闻采集失败: {e}", file=sys.stderr)
            competitor_result["news"] = []

        results[key] = competitor_result

    # 保存状态
    state["url_hashes"] = url_hashes
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    print(f"\n✅ 状态已保存", file=sys.stderr)

    return results


# ============================================================
# 报告生成
# ============================================================

def generate_report(all_data) -> str:
    """生成完整Markdown报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 🔍 竞品情报日报 | OpenClaw框架商业化产品",
        f"**日期：** {today}  |  **时间：** {datetime.now().strftime('%H:%M')} (GMT+8)",
        "",
        "---",
        "",
    ]

    categories = {}
    for k, v in all_data.items():
        cat = v.get("category", "其他")
        categories.setdefault(cat, []).append(v)

    has_any_update = any(v.get("has_url_update") for v in all_data.values())

    # 摘要
    lines.append("## 📊 今日概览\n")
    updated = [v for v in all_data.values() if v.get("has_url_update")]
    if updated:
        lines.append(f"**🔄 官网有更新的产品：** {', '.join(v['name'] for v in updated)}")
    else:
        lines.append("**🔄 官网有更新的产品：** 无")

    total_news = sum(len(v.get("news", [])) for v in all_data.values())
    lines.append(f"**📰 近期新闻：** 共 {total_news} 条\n")

    # 按分类展开
    for cat in ["互联网大厂", "AI厂商", "垂直专业版"]:
        if cat not in categories:
            continue
        lines.append(f"\n## 🏷️ {cat}\n")
        for v in categories[cat]:
            name = v["name"]
            vendor = v["vendor"]
            desc = v.get("description", "")
            has_update = v.get("has_url_update", False)
            url_updates = v.get("url_updates", [])
            news = v.get("news", [])

            update_tag = " 🔄" if has_update else ""
            lines.append(f"### {name}（{vendor}）{update_tag}")
            lines.append(f"📌 {desc}\n")

            # 官网更新
            if url_updates and has_update:
                lines.append("**🔄 官网更新：**")
                for upd in url_updates:
                    upd_type = upd.get("type", "")
                    upd_title = upd.get("title", "")
                    upd_url = upd.get("url", "")
                    upd_preview = upd.get("content_preview", "")
                    if upd_type == "homepage" and upd_preview:
                        lines.append(f"- **{upd_title}**")
                        lines.append(f"  {upd_preview}")
                        lines.append(f"  🔗 {upd_url}")
                    elif upd_type == "indicator_page":
                        lines.append(f"- 文档/动态页有变化：{upd_title}")
                        lines.append(f"  🔗 {upd_url}")
                lines.append("")
            elif v.get("url"):
                lines.append(f"➖ 官网无变化 | {v['url']}")
                lines.append("")

            # 新闻
            if news:
                lines.append("**📰 最新动态：**")
                for i, item in enumerate(news[:4], 1):
                    title = item.get("title", "")
                    url = item.get("url", "")
                    snippet = item.get("snippet", "")
                    lines.append(f"{i}. **{title}**")
                    if snippet:
                        lines.append(f"   {snippet[:150]}...")
                    if url:
                        lines.append(f"   🔗 {url}")
                lines.append("")
            else:
                lines.append("*暂无公开新闻*\n")

    lines.extend([
        "---",
        f"🤖 竞品情报雷达 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} (GMT+8)",
        f"💾 状态文件：{STATE_FILE}",
    ])
    return "\n".join(lines)


def generate_wecom_message(all_data) -> str:
    """生成企业微信推送消息"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"🔍 竞品情报日报 | OpenClaw框架商业化产品",
        f"📅 {today} 下午版",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    categories = {}
    for k, v in all_data.items():
        cat = v.get("category", "其他")
        categories.setdefault(cat, []).append(v)

    has_any_update = any(v.get("has_url_update") for v in all_data.values())

    # 有官网更新的产品优先展示
    if has_any_update:
        lines.append("🔄 **官网有更新**\n")
        for cat in ["互联网大厂", "AI厂商", "垂直专业版"]:
            if cat not in categories:
                continue
            for v in categories[cat]:
                if not v.get("has_url_update"):
                    continue
                name = v["name"]
                vendor = v["vendor"]
                updates = v.get("url_updates", [])
                for upd in updates:
                    if upd.get("type") == "homepage":
                        preview = upd.get("content_preview", "")[:100]
                        lines.append(f"• **{name}**（{vendor}）")
                        if preview:
                            lines.append(f"  {preview}...")
                        break
                else:
                    lines.append(f"• **{name}**（{vendor}）")
        lines.append("")

    # 按分类列出所有产品动态
    for cat in ["互联网大厂", "AI厂商", "垂直专业版"]:
        if cat not in categories:
            continue
        lines.append(f"🏷️ **{cat}**\n")

        for v in categories[cat]:
            name = v["name"]
            vendor = v["vendor"]
            has_update = v.get("has_url_update", False)
            news = v.get("news", [])
            update_icon = "🔄" if has_update else "➖"
            news_count = len(news) if news else 0

            if news_count > 0:
                lines.append(f"{update_icon} **{name}**（{vendor}）📰{news_count}条")
                for item in news[:2]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    if len(snippet) > 80:
                        snippet = snippet[:80] + "..."
                    lines.append(f"  → {title}")
                    if snippet:
                        lines.append(f"    {snippet}")
            else:
                lines.append(f"{update_icon} **{name}**（{vendor}）无公开动态")

        lines.append("")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🤖 生成时间：{datetime.now().strftime('%H:%M')} (GMT+8)",
    ])
    return "\n".join(lines)


# ============================================================
# 文件输出
# ============================================================

def save_outputs(all_data, output_dir=None):
    """保存报告和数据"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "tasks"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")

    md_file = output_dir / f"competitor-radar-{today}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(generate_report(all_data))
    print(f"📄 报告: {md_file}", file=sys.stderr)

    json_file = output_dir / f"competitor-radar-data-{today}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"📊 数据: {json_file}", file=sys.stderr)

    return str(md_file), str(json_file)


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="竞品情报雷达")
    parser.add_argument("--days", "-d", type=int, default=30, help="新闻回溯天数（默认30天）")
    parser.add_argument("--push", "-p", action="store_true", help="标记为推送到企业微信")
    parser.add_argument("--competitor", "-c", type=str, default=None, help="仅采集指定竞品")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告，不采集")
    args = parser.parse_args()

    if args.report_only:
        state = load_state()
        print("⚠️  --report-only 当前需要先采集数据，请省略此参数", file=sys.stderr)
        return 1

    # 采集
    all_data = collect_all(days_back=args.days)

    # 输出
    md_file, json_file = save_outputs(all_data)

    # 打印企业微信消息
    wecom_msg = generate_wecom_message(all_data)
    print("\n" + "=" * 60, file=sys.stderr)
    print("💬 企业微信推送内容：", file=sys.stderr)
    print("=" * 60, file=sys.stdout)
    print(wecom_msg, file=sys.stdout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
