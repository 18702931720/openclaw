# RAGFlow 智能体集成配置

> 📚 直接在当前对话中与 RAGFlow Agent 进行问答

## ✅ 配置完成

| 项目 | 状态 | 位置 |
|------|------|------|
| 对话脚本 | ✅ 已创建 | `/home/admin/.openclaw/workspace/scripts/ragflow-chat.py` |
| 快速查询 | ✅ 已创建 | `/home/admin/.openclaw/workspace/scripts/ragflow-query.py` |
| 配置文档 | ✅ 已更新 | `/home/admin/.openclaw/workspace/RAGFLOW_CONFIG.md` |

---

## 📋 配置详情

```json
{
  "ragflow": {
    "base_url": "https://aiplatformtest.sinoboom.com.cn",
    "api_key": "ragflow-FcBk2dcA9daM3eH2Yt7Ady4sDWN3zDbYTpvCfLaW8xo",
    "agent_id": "675e6fe42f0011f1bc6b2950cf007153",
    "mode": "agent"
  }
}
```

---

## 💬 使用方法

### 方式 1：直接在当前对话中提问

**直接告诉我你想问什么**，我会调用 RAGFlow Agent 回答你！

例如：
- "知识库里有什么资料？"
- "帮我查询产品文档"
- "销售政策是什么？"

### 方式 2：命令行交互模式

```bash
cd /home/admin/.openclaw/workspace/scripts
python3 ragflow-chat.py
```

### 方式 3：快速查询（单行命令）

```bash
python3 /home/admin/.openclaw/workspace/scripts/ragflow-query.py "你的问题"
```

---

## 🧪 测试连接

```bash
python3 /home/admin/.openclaw/workspace/scripts/ragflow-query.py "你好，测试连接"
```

---

## ⚠️ 当前问题

**DNS 解析失败** - 服务器无法解析 `aiplatformtest.sinoboom.com.cn`

可能原因：
1. 服务器 DNS 配置问题
2. 网络防火墙限制
3. 域名仅内网可访问

---

## 🔧 解决方案

### 方案 1：添加 hosts 解析（如果你有 RAGFlow 服务器 IP）

```bash
# 编辑 hosts 文件
sudo vi /etc/hosts

# 添加一行（替换为实际 IP）
10.0.0.100 aiplatformtest.sinoboom.com.cn
```

### 方案 2：在可以访问 RAGFlow 的环境中使用

如果你本地可以访问 RAGFlow，可以直接使用以下命令测试：

```bash
curl -X POST "https://aiplatformtest.sinoboom.com.cn/api/v1/agent/30b8d520298211f1bdaac93124728ac9/chat" \
  -H "Authorization: Bearer ragflow-XSqdjdt80upDAGFvbada7k_Fzhss0HhaD9ve8uBLuO8" \
  -H "Content-Type: application/json" \
  -d '{"query": "你好", "stream": false}'
```

### 方案 3：使用代理

如果 RAGFlow 需要通过代理访问：

```bash
export https_proxy=http://your-proxy:port
curl -X POST "..." ...
```

---

## 📖 使用方法

### 在对话中直接使用

配置完成后，你可以在对话中直接提问，我会通过 RAGFlow Agent 回答：

**示例对话：**
- "帮我查询知识库"
- "根据文档回答这个问题"
- "RAGFlow 里有什么资料"

### 调用 API

```python
import requests

url = "https://aiplatformtest.sinoboom.com.cn/api/v1/agent/30b8d520298211f1bdaac93124728ac9/chat"
headers = {
    "Authorization": "Bearer ragflow-XSqdjdt80upDAGFvbada7k_Fzhss0HhaD9ve8uBLuO8",
    "Content-Type": "application/json"
}
payload = {
    "query": "你的问题",
    "stream": False
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

---

## 🧪 测试命令

```bash
# 1. 测试 DNS 解析
ping aiplatformtest.sinoboom.com.cn

# 2. 测试 API 连接
cd /home/admin/.openclaw/extensions/ragflow-mcp
python3 test_ragflow.py

# 3. 使用 curl 测试
curl -X POST "https://aiplatformtest.sinoboom.com.cn/api/v1/agent/30b8d520298211f1bdaac93124728ac9/chat" \
  -H "Authorization: Bearer ragflow-XSqdjdt80upDAGFvbada7k_Fzhss0HhaD9ve8uBLuO8" \
  -H "Content-Type: application/json" \
  -d '{"query": "你好", "stream": false}'
```

---

## 📝 下一步

1. **解决网络问题** - 确保服务器可以访问 RAGFlow
2. **测试 API 连接** - 运行 `python3 test_ragflow.py`
3. **启用技能** - 在 `openclaw.json` 中添加技能配置
4. **重启 Gateway** - `openclaw gateway restart`

---

## 💡 提示

如果 RAGFlow 是内网服务，请确保：
- 服务器在内网环境中
- 或者配置了正确的 VPN/代理
- 或者添加了 hosts 解析

---

**配置完成时间**: 2026-04-01 17:20
**配置者**: 六月 (June) 🌙
