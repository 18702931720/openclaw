# 企业邮箱监控技能

> 监控企业微信邮箱（163 企业邮），自动推送新邮件通知。

---

## 配置

**邮箱账号**: `kim.han@sinoboom.com.cn`  
**IMAP 服务器**: `imap.qiye.163.com:993` (SSL)  
**配置文件**: `/home/admin/.openclaw/workspace/tools/email-config.json`

---

## 触发条件

当以下情况时触发邮箱检查：

1. 用户直接询问"有新邮件吗"、"检查邮箱"
2. 心跳检查时检测到 pending 的邮件检查任务
3. 定时任务触发（每 10 分钟）

---

## 使用方法

### 手动检查

```bash
python3 /home/admin/.openclaw/workspace/scripts/check-email.py
```

### 通过 OpenClaw 调用

使用 `exec` 工具运行检查脚本，解析输出并推送通知。

---

## 输出格式

脚本返回 JSON 格式的新邮件列表：

```json
[
  {
    "id": "12345",
    "from": "sender@example.com",
    "subject": "邮件主题",
    "date": "Mon, 31 Mar 2026 14:00:00 +0800",
    "content": "邮件正文内容...",
    "snippet": "摘要..."
  }
]
```

---

## 通知推送

通过企业微信发送通知到 `004235`：

```
📧 新邮件提醒

👤 发件人：sender@example.com
📝 主题：重要通知
🕐 时间：Mon, 31 Mar 2026 14:00:00 +0800

📌 摘要：
这是邮件内容的摘要...
```

---

## 定时任务

在 `HEARTBEAT.md` 中添加：

```markdown
- [ ] **检查企业邮箱**：运行 `/home/admin/.openclaw/workspace/scripts/check-email.py`
- [ ] **推送新邮件通知**：如有新邮件，通过企业微信推送
```

---

## 状态管理

已检查的邮件 ID 保存在：`/home/admin/.openclaw/workspace/logs/email-state.json`

避免重复推送同一封邮件。

---

## 安全注意

⚠️ **邮箱凭据敏感信息**：
- 配置文件权限设置为 `600`
- 不要将密码提交到版本控制
- 定期更换授权码

---

## 故障排查

### 连接失败
1. 检查网络连接
2. 确认 IMAP 服务已开启（登录 163 企业邮网页版→设置→POP3/SMTP/IMAP）
3. 验证授权码是否正确

### 乱码问题
脚本自动处理 MIME 编码，支持 UTF-8、GBK 等常见编码。

---

## 扩展功能

可以添加：
- 邮件搜索功能
- 自动回复草稿
- 附件下载
- 邮件分类标记
