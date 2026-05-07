# 定时任务脚本说明

## 📰 每日 AI 资讯推送

### 任务配置
- **执行时间：** 每天 07:00（北京时间）
- **推送渠道：** 企业微信
- **推送对象：** J 哥 (004235)
- **资讯数量：** 国内 6 条 + 国外 6 条 = 共 12 条

### 文件位置
- **脚本：** `/home/admin/.openclaw/workspace/scripts/daily-ai-news.sh`
- **日志：** `/home/admin/.openclaw/workspace/logs/ai-news-YYYYMMDD.log`
- **任务标记：** `/home/admin/.openclaw/workspace/tasks/daily-ai-news-pending`

### Cron 配置
```bash
0 7 * * * /home/admin/.openclaw/workspace/scripts/daily-ai-news.sh
```

### 验证命令
```bash
# 查看已配置的 cron 任务
crontab -l

# 手动执行测试
bash /home/admin/.openclaw/workspace/scripts/daily-ai-news.sh

# 查看日志
tail -f /home/admin/.openclaw/workspace/logs/ai-news-$(date +%Y%m%d).log
```

### 日志示例
```
[2026-03-30 07:00:01] ========== AI 资讯推送任务开始 ==========
[2026-03-30 07:00:01] 任务标记已创建：/home/admin/.openclaw/workspace/tasks/daily-ai-news-pending
[2026-03-30 07:00:01] 尝试通过 OpenClaw CLI 触发任务...
[2026-03-30 07:00:02] ========== AI 资讯推送任务结束 ==========
```

---

## 🔧 管理命令

### 暂停任务
```bash
crontab -l | grep -v "daily-ai-news.sh" | crontab -
```

### 恢复任务
```bash
(crontab -l 2>/dev/null; echo "0 7 * * * /home/admin/.openclaw/workspace/scripts/daily-ai-news.sh") | crontab -
```

### 查看任务状态
```bash
crontab -l | grep daily-ai-news
```
