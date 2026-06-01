# 任务处理器说明

## 🤖 自动任务处理指南

当检测到任务标记文件时，六月应自动执行相应任务。

---

## 📰 每日 AI 资讯推送任务

### 触发条件
检测到文件：`/home/admin/.openclaw/workspace/tasks/daily-ai-news-pending`

### 任务配置
读取任务标记文件中的 JSON 配置：
```json
{
  "task": "daily_ai_news",
  "domestic_count": 6,
  "international_count": 6,
  "channel": "wecom",
  "recipient": "J 哥"
}
```

### 执行步骤

1. **搜索国内 AI 资讯**
   - 使用 web_search 搜索：`AI 人工智能新闻 2026 年 中国`
   - 获取最新 6 条

2. **搜索国外 AI 资讯**
   - 使用 web_search 搜索：`AI artificial intelligence news 2026`
   - 获取最新 6 条

3. **整理格式**
   - 每条包含：📌标题、📅时间、📰来源、📌要义、🔗链接
   - 国内用🇨🇳标识，国外用🌍标识
   - 使用 --- 分隔每条新闻

4. **推送消息**
   - 通过企业微信发送给 J 哥 (004235)
   - 使用 message 工具或 feishu_im_user_message（根据通道选择）

5. **清理任务标记**
   - 执行完成后删除或归档任务标记文件

### 输出格式示例
```
📰 AI 资讯日报 · 2026 年 3 月 30 日

🇨🇳 国内新闻

1️⃣ 新闻标题
📅 时间：2026 年 3 月 30 日
📰 来源：央视网
📌 要义：...
🔗 链接：...

---

🌍 国外新闻
...

🌙 六月 整理
```

---

## 📋 任务标记文件管理

### 位置
`/home/admin/.openclaw/workspace/tasks/`

### 命名规范
- 每日资讯：`daily-ai-news-pending`
- 其他任务：`{task-name}-pending`

### 处理流程
1. 检查任务目录是否有 pending 文件
2. 读取配置并执行
3. 完成后重命名为 `{task-name}-done-{timestamp}`
4. 或移动到 `/home/admin/.openclaw/workspace/tasks/done/`

---

## 🔍 竞品情报雷达任务

### 触发条件
检测到文件：`/home/admin/.openclaw/workspace/tasks/competitor-radar-send-trigger-YYYYMMDD.json`

### 任务配置
读取触发器文件中的 JSON 配置：
```json
{
  "action": "send_competitor_radar",
  "report_file": "/path/to/competitor-radar-YYYYMMDD.md",
  "data_file": "/path/to/competitor-radar-data-YYYYMMDD.json",
  "wecom_file": "/path/to/competitor-radar-wecom-YYYYMMDD.txt",
  "push_date": "YYYYMMDD",
  "recipient": { "id": "004235", "name": "韩瑾君" }
}
```

### 执行步骤

1. **读取 wecom 文件**
   - 读取 `competitor-radar-wecom-YYYYMMDD.txt` 内容
   - 优先发送有官网更新 or 有新闻的产品

2. **推送消息**
   - 通过企业微信发送给 J 哥 (004235)
   - 使用 message 工具，action=send

3. **清理任务标记**
   - 创建 `/home/admin/.openclaw/workspace/tasks/competitor-radar-done-YYYYMMDD` 空文件
   - 删除发送触发器文件

### 推送内容格式
```
🔍 竞品情报日报 | OpenClaw框架商业化产品
📅 YYYYMMDD 下午版

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 官网有更新
• 产品名（厂商）
  摘要内容...

🏷️ 互联网大厂
🔄 产品A（腾讯）📰4条
  → 新闻标题
    摘要...
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 生成时间：HH:MM (GMT+8)
```

---

## 🔍 心跳检查建议

在 HEARTBEAT.md 中添加：
```markdown
- [ ] 检查 /workspace/tasks/ 目录是否有 pending 任务
- [ ] 如有 pending 任务，读取并执行
```
