#!/bin/bash
# 产品发现日报收集脚本
# cron: 0 8 * * *
# 抓取 Product Hunt + Hacker News 热门产品，生成 AI 中文日报邮件

WORKSPACE="/home/admin/.openclaw/workspace"
SCRIPT="$WORKSPACE/scripts/product-trending-daily.py"
LOG_FILE="$WORKSPACE/logs/product-trending-$(date +%Y%m%d).log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 产品发现日报开始" >> "$LOG_FILE"

cd "$WORKSPACE" || exit 1
python3 "$SCRIPT" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 完成" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 失败，退出码: $EXIT_CODE" >> "$LOG_FILE"
fi

exit 0