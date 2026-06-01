#!/bin/bash
# 每日 AI 资讯收集脚本
# cron: 0 7 * * *
# 流程: 收集新闻 → 保存 collected 文件 → 创建发送触发器
# 注意：不直接发送（gateway 限制），由主 agent 会话通过 message tool 发送

WORKSPACE="/home/admin/.openclaw/workspace"
TASKS_DIR="$WORKSPACE/tasks"
LOGS_DIR="$WORKSPACE/logs"
TODAY=$(date +%Y%m%d)
DONE_FILE="$TASKS_DIR/daily-ai-news-done-$TODAY"
COLLECTED_FILE="$TASKS_DIR/daily-ai-news-collected-$TODAY.md"
SEND_TRIGGER="$TASKS_DIR/daily-ai-news-send-trigger-$TODAY.json"
LOG_FILE="$LOGS_DIR/ai-news-$TODAY.log"

mkdir -p "$LOGS_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯收集开始 ==========" >> "$LOG_FILE"

# 检查是否已完成
if [ -f "$DONE_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 今日已完成，退出" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 调用收集脚本..." >> "$LOG_FILE"
cd "$WORKSPACE" || exit 1

# 调用收集脚本（自包含新闻数据）
python3 "$WORKSPACE/scripts/daily-ai-news-collect.py" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 收集成功，已创建触发器" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 收集失败，退出码: $EXIT_CODE" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯收集结束 ==========" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit 0