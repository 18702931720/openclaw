# 企业微信 MCP 通讯录权限配置指南

**问题**: 调用 `wecom_mcp` 时返回错误码 `846610` - `unsupported mcp biz type`

**原因**: 企业微信 MCP 功能需要在企业微信管理后台配置应用凭证和 API 权限。

---

## 🔧 配置步骤

### 步骤 1：登录企业微信管理后台

访问：https://work.weixin.qq.com/

使用管理员账号登录。

---

### 步骤 2：创建/选择应用

1. 进入「应用管理」
2. 找到已创建的 AI 机器人应用（或创建新应用）
3. 点击进入应用详情页

---

### 步骤 3：获取企业凭证

在应用详情页，记录以下信息：

| 凭证 | 说明 | 示例 |
|------|------|------|
| **CorpID** | 企业 ID | `ww1234567890abcdef` |
| **AgentID** | 应用 ID | `1000001` |
| **Secret** | 应用密钥 | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

---

### 步骤 4：配置 API 权限

在应用详情页 → 「权限管理」或「API 权限」：

✅ 开通以下权限：
- [ ] 通讯录读取
- [ ] 消息发送
- [ ] 日程管理
- [ ] 待办事项
- [ ] 文档管理
- [ ] 智能表格

---

### 步骤 5：配置可信域名（可选）

如果 MCP 需要回调，配置可信域名：
- 进入「应用详情页」→「开发配置」
- 添加服务器 IP 或域名到白名单

---

### 步骤 6：在 OpenClaw 中配置凭证

创建配置文件 `/home/admin/.openclaw/tools/wecom-mcp-config.json`：

```json
{
  "wecom": {
    "mcp": {
      "enabled": true,
      "corp_id": "ww1234567890abcdef",
      "agent_id": "1000001",
      "secret": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    }
  }
}
```

---

### 步骤 7：测试连通性

```bash
# 测试获取 Access Token
curl "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=YOUR_CORPID&corpsecret=YOUR_SECRET"

# 测试读取通讯录
curl "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=ACCESS_TOKEN&department_id=1&fetch_child=1"
```

---

### 步骤 8：重启 Gateway

```bash
openclaw gateway restart
```

---

## 🔍 验证配置

重启后测试：

```bash
# 测试通讯录读取
wecom_mcp list contact
```

如果返回工具列表，说明配置成功。

---

## 📋 快速配置命令

如果已有凭证，直接执行：

```bash
# 1. 创建配置文件
cat > /home/admin/.openclaw/tools/wecom-mcp-config.json << 'EOF'
{
  "wecom": {
    "mcp": {
      "enabled": true,
      "corp_id": "YOUR_CORPID",
      "agent_id": "YOUR_AGENTID",
      "secret": "YOUR_SECRET"
    }
  }
}
EOF

# 2. 重启 Gateway
openclaw gateway restart
```

---

## ⚠️ 常见问题

### 错误码 846610
**原因**: MCP 功能未开通或凭证配置错误  
**解决**: 确认企业微信后台已开通 MCP 相关 API 权限

### 错误码 40014
**原因**: Access Token 无效  
**解决**: 检查 Secret 是否正确

### 错误码 40016
**原因**: CorpID 或 Secret 不匹配  
**解决**: 重新从企业微信后台复制凭证

---

## 📞 获取帮助

1. 企业微信官方文档：https://open.work.weixin.qq.com/help
2. 开发者社区：https://open.work.weixin.qq.com/community
3. 技术支持：查看企业微信管理后台「技术支持」

---

## 🎯 配置完成后

配置成功后，我可以帮助你：
- 📇 查询企业成员邮箱和联系方式
- 👥 获取部门成员列表
- 📧 自动查找收件人邮箱
- 📅 查询成员日程安排
- ✅ 创建和分配待办事项

---

🌙 六月 整理
