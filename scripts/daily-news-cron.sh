#!/bin/bash
# 每日 AI 资讯推送脚本
# 推送时间：每天早上 7:00

WORKSPACE="/home/admin/.openclaw/workspace"
TASKS_DIR="$WORKSPACE/tasks"
DONE_FILE="$TASKS_DIR/daily-ai-news-done-$(date +%Y%m%d)"

cd "$WORKSPACE" || exit 1

# 检查是否已有今日推送记录
if [ -f "$DONE_FILE" ]; then
    echo "今日资讯已推送，退出"
    exit 0
fi

# 触发资讯收集任务（创建 pending 文件）
touch "$TASKS_DIR/daily-ai-news-pending"
echo "已创建任务标记文件"

exit 0