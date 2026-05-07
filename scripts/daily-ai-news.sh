#!/bin/bash
# AI 资讯日报定时推送脚本
# 每天 7 点执行，创建任务标记，由 Heartbeat 机制检测并执行推送

set -e

WORKSPACE="/home/admin/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/ai-news-$(date +%Y%m%d).log"
TASK_FLAG="$WORKSPACE/tasks/daily-ai-news-pending"

# 确保目录存在
mkdir -p "$LOG_DIR"
mkdir -p "$WORKSPACE/tasks"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯推送任务开始 ==========" >> "$LOG_FILE"

# 创建任务标记文件（包含任务详情）
cat > "$TASK_FLAG" << EOF
{
  "task": "daily_ai_news",
  "created_at": "$(date -Iseconds)",
  "config": {
    "domestic_count": 6,
    "international_count": 6,
    "channel": "wecom",
    "recipient": "J 哥",
    "recipient_id": "004235"
  }
}
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 任务标记已创建：$TASK_FLAG" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 配置：国内 6 条 + 国外 6 条，推送至企业微信" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏳ 等待 Heartbeat 机制检测并执行推送..." >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯推送任务结束 ==========" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 输出到 stdout 便于 cron 日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] AI 资讯推送任务已触发，任务文件：$TASK_FLAG"
