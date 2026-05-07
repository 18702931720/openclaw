#!/bin/bash
# 定时推送 AI 资讯（通过 openclaw agent 子会话发送）
# 由 cron 每天 7:00 触发

WORKSPACE="/home/admin/.openclaw/workspace"
TASKS_DIR="$WORKSPACE/tasks"
LOG_DIR="$WORKSPACE/logs"
TODAY=$(date +%Y%m%d)
DONE_FILE="$TASKS_DIR/daily-ai-news-done-$TODAY"
COLLECTED_FILE="$TASKS_DIR/daily-ai-news-collected-$TODAY.md"
LOG_FILE="$LOG_DIR/daily-news-agent-$TODAY.log"

mkdir -p "$LOG_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯定时推送开始 ==========" >> "$LOG_FILE"

# 检查是否已推送
if [ -f "$DONE_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 今日已推送，退出" >> "$LOG_FILE"
    exit 0
fi

# 检查新闻是否已收集
if [ ! -f "$COLLECTED_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 今日新闻未收集，先触发收集任务" >> "$LOG_FILE"
    touch "$TASKS_DIR/daily-ai-news-pending"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] pending 文件已创建，等待下一轮 heartbeat 执行" >> "$LOG_FILE"
    exit 0
fi

# 读取新闻内容
NEWS_CONTENT=$(cat "$COLLECTED_FILE")
META_INFO="📊 **备注**
🔍 搜索工具：SearXNG (隐私优先的元搜索引擎)
🤖 生成模型：minimax/MiniMax-M2.7
🕐 生成时间：$(date '+%Y-%m-%d') 07:18 (北京时间)"

# 构建发送给 agent 的指令
AGENT_PROMPT="请读取文件 $COLLECTED_FILE 的内容，将今日 AI 资讯（国内 6 条 + 国际 6 条）以企业微信消息格式发送给 J 哥（企业微信 ID: 004235）。格式要求：
- 开头：🇨🇳 **国内新闻**
- 每条新闻包含：标题、📝 要义、📅 日期、🔗 链接
- 新闻之间用 --- 分隔
- 末尾附上元数据备注（搜索工具、模型、生成时间）
- 只发送，不再重复解释"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 触发 agent 发送..." >> "$LOG_FILE"

# 通过 openclaw agent --deliver 发送消息
cd "$WORKSPACE" || exit 1

$HOME/.npm-global/bin/openclaw agent \
    --channel wecom \
    --deliver \
    --message "$AGENT_PROMPT" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 推送成功" >> "$LOG_FILE"
    touch "$DONE_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 推送失败，退出码: $EXIT_CODE" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== AI 资讯定时推送结束 ==========" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"