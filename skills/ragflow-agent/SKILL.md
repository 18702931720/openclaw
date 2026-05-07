# RAGFlow Agent 集成技能

> 通过 RAGFlow API 与智能体对话，利用知识库进行问答。

---

## 触发条件

当用户的问题需要查询知识库，或直接要求与 RAGFlow 智能体对话时触发。

---

## 配置

配置文件位置：`/home/admin/.openclaw/workspace/tools/ragflow-config.json`

```json
{
  "ragflow": {
    "enabled": true,
    "base_url": "https://aiplatformtest.sinoboom.com.cn",
    "api_key": "ragflow-api-key-placeholder",
    "mode": "agent",
    "agent_id": "",
    "stream": true
  }
}
```

---

## API 调用方式

### 智能体对话 (Agent Completion)

**端点**: `POST /api/v1/agents_openai/{agent_id}/chat/completions`

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <API_KEY>
```

**请求体**:
```json
{
  "model": "model",
  "messages": [
    {"role": "user", "content": "用户问题"}
  ],
  "stream": true,
  "session_id": "可选 - 会话 ID"
}
```

### 聊天助手对话 (Chat Completion)

**端点**: `POST /api/v1/chats_openai/{chat_id}/chat/completions`

---

## 使用示例

### 使用 exec 调用 RAGFlow API

```bash
curl --request POST \
  --url https://aiplatformtest.sinoboom.com.cn/api/v1/agents_openai/{agent_id}/chat/completions \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer <API_KEY>' \
  --data '{
    "model": "model",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

---

## 会话管理

- 使用 `session_id` 参数保持对话上下文
- 会话 ID 可以存储在 `/home/admin/.openclaw/workspace/tools/ragflow-session.json`

---

## 错误处理

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数无效 |
| 401 | API Key 无效或未授权 |
| 403 | 访问被拒绝 |
| 404 | 智能体/聊天助手不存在 |
| 500 | 服务器内部错误 |

---

## 注意事项

1. **API Key**: 需要从 RAGFlow 管理后台获取
2. **Agent ID**: 需要在 RAGFlow 中先创建智能体
3. **流式响应**: 建议开启 `stream: true` 以获得更好的用户体验
4. **引用**: 开启 `reference: true` 可以获取知识来源

---

## 快速测试

```bash
# 测试 API 连通性
curl -X GET \
  https://aiplatformtest.sinoboom.com.cn/api/v1/system/status \
  -H "Authorization: Bearer <API_KEY>"
```
