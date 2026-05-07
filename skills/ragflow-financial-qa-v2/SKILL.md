---
name: ragflow-financial-qa-v2
description: 财务知识库问答技能（Agent 版）。通过调用 RAGFlow Agent 对话接口，回答企业财务、报销、费用等相关问题。适用场景：报销流程、审批权限、费用标准、借款制度，采购付款、票据要求等财务相关问题。
---

# 财务知识库问答技能（Agent 版）

本技能通过调用 RAGFlow Agent 对话接口，将用户问题交给企业财务知识库 Agent 处理，返回整理后的回答。

## 配置信息

- **API URL:** `https://aiplatformtest.sinoboom.com.cn`
- **API Key:** `ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg`
- **Agent ID:** `30b8d520298211f1bdaac93124728ac9`
- **调用接口:** `POST /api/v1/agents_openai/{agent_id}/chat/completions`

## 触发条件

当用户询问以下类型问题时触发：

- "怎么报销"、"报销流程是什么"
- "费用申请怎么审批"、"报销标准是什么"
- "这个费用能报吗"、"票据有什么要求"
- "借款最高多少"、"事前申请流程"
- "分期付款怎么操作"、"多人收款怎么用"
- "审批超时怎么办"、"报销被退回了"
- "出差补贴标准"、"招待费标准"
- 其他财务、报销、费用、制度相关问题

## 调用方式

在 exec tool 中直接执行以下 curl 命令：

```bash
curl -s --max-time 30 --request POST \
  --url 'https://aiplatformtest.sinoboom.com.cn/api/v1/agents_openai/30b8d520298211f1bdaac93124728ac9/chat/completions' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg' \
  --data '{"model":"model","messages":[{"role":"user","content":"用户的问题"}],"stream":false}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `messages[].content` | string | ✅ | 用户提问（中文） |
| `stream` | bool | ❌ | 是否流式返回，默认 false |

## 返回处理

1. 执行 curl 请求（约等待 5-15 秒）
2. 从 JSON 响应中提取 `choices[0].message.content`
3. 将内容原样返回给用户

## 注意事项

1. Agent 回答基于财务知识库，可能存在幻觉，请以公司正式财务制度文件为准
2. Agent 返回的内容包含 `[ID:xx]` 引用标记，表示来源于哪份文档
3. 如需更精确的制度条文，建议同时查阅原始制度 PDF 文件
4. 接口非流式返回，约需等待 5-15 秒
5. **必须使用单引号包裹 JSON 数据**，避免 shell 转义问题
