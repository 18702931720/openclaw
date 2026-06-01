#!/bin/bash
# 竞品情报雷达 cron 脚本
# cron: 0 14 * * *  (每天下午2点)
# 流程: 采集竞品情报 → 保存报告 → 创建发送触发器
# 注意：不直接发送（gateway 限制），由主 agent 会话通过 message tool 发送

WORKSPACE="/home/admin/.openclaw/workspace"
TASKS_DIR="$WORKSPACE/tasks"
SCRIPTS_DIR="$WORKSPACE/scripts"
LOGS_DIR="$WORKSPACE/logs"
TODAY=$(date +%Y%m%d)
REPORT_FILE="$TASKS_DIR/competitor-radar-$TODAY.md"
DATA_FILE="$TASKS_DIR/competitor-radar-data-$TODAY.json"
WECOM_FILE="$TASKS_DIR/competitor-radar-wecom-$TODAY.txt"
SEND_TRIGGER="$TASKS_DIR/competitor-radar-send-trigger-$TODAY.json"
LOG_FILE="$LOGS_DIR/competitor-radar-$TODAY.log"
DONE_FILE="$TASKS_DIR/competitor-radar-done-$TODAY"

mkdir -p "$LOGS_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 竞品雷达开始 ==========" >> "$LOG_FILE"

# 检查是否已发送过
if [ -f "$DONE_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 今日已发送，跳过" >> "$LOG_FILE"
    exit 0
fi

# 运行采集脚本
cd "$WORKSPACE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 运行采集脚本..." >> "$LOG_FILE"
python3 "$SCRIPTS_DIR/competitor-radar.py" >> "$LOG_FILE" 2>&1

# 检查是否生成了报告
if [ ! -f "$REPORT_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 报告生成失败" >> "$LOG_FILE"
    exit 1
fi

# 检查是否有内容（有更新 or 有新闻）
HAS_UPDATE=false
if [ -f "$WECOM_FILE" ]; then
    # 检查文件是否有实质内容
    if grep -q "官网有更新\|📰.*条" "$WECOM_FILE" 2>/dev/null; then
        HAS_UPDATE=true
    fi
fi

if [ "$HAS_UPDATE" = true ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到竞品动态，创建发送触发器" >> "$LOG_FILE"
    cat > "$SEND_TRIGGER" << EOF
{
    "action": "send_competitor_radar",
    "report_file": "$REPORT_FILE",
    "data_file": "$DATA_FILE",
    "wecom_file": "$WECOM_FILE",
    "push_date": "$TODAY",
    "push_time": "$(date '+%Y-%m-%d %H:%M')",
    "recipient": {
        "id": "004235",
        "name": "韩瑾君"
    },
    "created_at": "$(date -Iseconds)"
}
EOF
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 发送触发器已创建: $SEND_TRIGGER" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 无新动态，仅保存报告" >> "$LOG_FILE"
    # 创建空触发器（用于记录）
    echo "{}" > "$TASKS_DIR/competitor-radar-no-update-$TODAY.json"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 竞品雷达完成 ==========" >> "$LOG_FILE"
exit 0
