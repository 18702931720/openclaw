# 企业邮箱监控配置完成 ✅

**配置时间**: 2026 年 3 月 31 日  
**配置者**: 六月

---

## 📧 邮箱信息

| 项目 | 配置 |
|------|------|
| 邮箱地址 | kim.han@sinoboom.com.cn |
| 接收服务器 | imap.qiye.163.com:993 (SSL) |
| 发送服务器 | smtp.qiye.163.com:465 (SSL) |
| 监控状态 | ✅ 已启用 |

---

## 📁 配置文件

| 文件 | 用途 |
|------|------|
| `/home/admin/.openclaw/workspace/tools/email-config.json` | 邮箱配置 |
| `/home/admin/.openclaw/workspace/scripts/check-email.py` | 检查脚本 |
| `/home/admin/.openclaw/workspace/scripts/quick-email-check.sh` | 快速检查 |
| `/home/admin/.openclaw/workspace/skills/email-monitor/SKILL.md` | 技能文档 |
| `/home/admin/.openclaw/workspace/logs/email-state.json` | 状态记录 |

---

## ⏰ 监控频率

- **心跳检查**: 每 30 分钟自动检查
- **手动检查**: 随时说"检查邮箱"或"有新邮件吗"

---

## 📬 通知方式

新邮件将通过**企业微信**推送到：`004235`

通知格式：
```
📧 新邮件提醒

👤 发件人：xxx@xxx.com
📝 主题：邮件主题
🕐 时间：2026 年 3 月 31 日 14:00

📌 摘要：
邮件内容摘要...
```

---

## 🎯 快速命令

### 手动检查邮箱
```bash
# 方式 1：完整输出
python3 /home/admin/.openclaw/workspace/scripts/check-email.py

# 方式 2：仅通知内容
/home/admin/.openclaw/workspace/scripts/quick-email-check.sh
```

### 查看状态
```bash
cat /home/admin/.openclaw/workspace/logs/email-state.json
```

---

## 🔐 安全提示

1. ✅ 配置文件已保存在本地，不会上传
2. ⚠️ 定期更换授权码（建议每 90 天）
3. ⚠️ 不要在公共场合分享配置文件
4. ✅ 脚本仅读取未读邮件，不会删除或修改

---

## 🛠️ 故障排查

### 连接失败
```bash
# 测试 IMAP 连接
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.qiye.163.com', 993)
mail.login('kim.han@sinoboom.com.cn', 'ZE3#PgJe4W#SPgHC')
print('连接成功!')
mail.logout()
"
```

### 查看日志
```bash
tail -20 /home/admin/.openclaw/workspace/logs/email-state.json
```

---

## 📊 功能清单

- [x] IMAP 连接配置
- [x] 新邮件检查脚本
- [x] 状态记录（避免重复推送）
- [x] 企业微信通知集成
- [x] 心跳自动检查
- [x] 手动检查命令
- [ ] 邮件搜索（待扩展）
- [ ] 自动回复草稿（待扩展）
- [ ] 附件下载（待扩展）

---

## 💡 下一步

现在你可以：

1. **测试**：说"检查邮箱"测试功能
2. **等待**：心跳会自动检查（每 30 分钟）
3. **扩展**：需要其他功能随时告诉我

---

🌙 六月 配置
