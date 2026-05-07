---
name: ragflow-financial-qa
description: 财务知识库问答技能。通过 RAGFlow 知识库检索 API，回答企业财务、报销、费用等相关问题。当用户询问报销流程、费用标准、财务制度、审批权限等问题时触发此技能。
---

# 财务知识库问答技能

本技能通过调用 RAGFlow 知识库检索 API，从企业财务知识库中检索相关内容并整理回答。

## 配置信息

已在 `TOOLS.md` 中配置：
- **API URL:** `https://aiplatformtest.sinoboom.com.cn`
- **API Key:** `ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg`
- **知识库 ID:** `d189caa8274e11f1bdaac93124728ac9`（财务知识库）
- **检索接口:** `POST /api/v1/retrieval`

## 触发条件

当用户询问以下类型问题时触发：
- "怎么报销"、"报销流程是什么"
- "费用申请怎么审批"
- "报销标准是什么"、"报销时限"
- "这个费用能报吗"
- "超过部门经理权限怎么审批"
- 其他财务、报销、费用相关问题

## 调用方式

使用 `exec` tool 调用检索脚本：

```bash
curl -s -X POST "https://aiplatformtest.sinoboom.com.cn/api/v1/retrieval" \
  -H "Authorization: Bearer ragflow-2cYb-zKbD5PT_eC2cKxJ6V1PKbjr8oGcgS0B_4rrAfg" \
  -H "Content-Type: application/json" \
  -d '{"dataset_ids":["d189caa8274e11f1bdaac93124728ac9"],"question":"用户问题","topk":10}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dataset_ids` | array | ✅ | 知识库ID列表，固定传 `["d189caa8274e11f1bdaac93124728ac9"]` |
| `question` | string | ✅ | 用户提问（中文） |
| `topk` | number | ❌ | 返回结果数量，默认10 |

## 返回格式

```json
{
  "code": 0,
  "data": {
    "chunks": [
      {
        "content": "内容文本（可能含HTML标签）",
        "similarity": 0.58,
        "document_keyword": "文档名称.pdf",
        "document_id": "文档ID"
      }
    ]
  }
}
```

## 处理流程

1. **调用检索 API** — 将用户问题传入 `question` 参数
2. **解析结果** — 提取 chunks，按相似度排序
3. **清理内容** — 去除 HTML 标签，整理文本
4. **整理回答** — 根据检索内容整理成易读的答案
5. **注明来源** — 告知用户答案来自哪个文档

## 注意事项

1. **HTML清理**：返回的 content 可能含 `<table>`、`<tr>` 等 HTML 标签，需要清理
2. **表格内容**：财务知识库大量内容是表格，解析时保留表格结构便于理解
3. **多文档交叉**：同一问题可能涉及多份文档（报销管理制度、财务授权制度等），综合整理
4. **专业术语**：财务知识库内容偏正式，整理时保持专业但易懂
5. **检索失败**：若 `code` 不为 0，告知用户检索失败及错误信息

## 典型问答模板

### 报销流程类
用户问报销流程 → 检索"报销流程、审批"相关内容 → 按金额区间整理审批节点

### 报销标准类
用户问报销标准 → 检索"报销时限、票据要求"相关内容 → 整理时限和票据规则

### 审批权限类
用户问超权限审批 → 检索"审批金额区间、审批层级"相关内容 → 按金额区间整理审批路径
