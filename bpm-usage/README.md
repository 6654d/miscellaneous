# BPM Skill

飞书（Feishu）BPM（Business Process Management）工作流审批助手。

## 业务逻辑

围绕**审批任务的全生命周期**，提供四个原子操作：

| 命令 | 操作 | 业务含义 |
|------|------|----------|
| `todos` | 查待办 | 获取当前用户待审批任务列表 |
| `dones` | 查已办 | 获取当前用户已审批历史记录 |
| `approve` | 审批 | 对任务执行**同意**或**拒绝**（终局操作） |
| `comment` | 评论 | 添加预审意见，**不办结**任务 |

标准审批流程：
```
查询待办 → 展示任务详情 → 用户决策 → 执行审批/评论
```

## 架构

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Claude     │      │  BPM CLI     │      │  BPM API    │
│  (Skill)    │─────▶│  (bpm.py)    │─────▶│  Server     │
│  文本协议    │      │  HTTP 客户端 │      │  REST API   │
└─────────────┘      └──────────────┘      └─────────────┘
```

- **SKILL.md**：LLM 可读的业务说明书，指导模型如何与用户交互、调用 API
- **scripts/bpm.py**：无状态 HTTP 客户端，封装认证与四个 API 调用

### 认证机制

- **Token**：管理员发放的用户永久凭证
- **OpenID**：飞书用户唯一标识
- **绑定**：首次使用时将 Token 与 OpenID 绑定激活（`POST /api/bpm/token/bind`）
- **传输**：每次请求均携带 `token` + `openid`，无 Session 状态

### 连接方式

- **无状态短连接**：基于 `urllib.request` 的标准 HTTP 请求/响应
- 无 WebSocket、无连接池、无长连接保持

## 快速使用

```bash
# 1. 查询待办
python3 scripts/bpm.py todos \
  --token YOUR_TOKEN --openid YOUR_OPENID

# 2. 同意任务
python3 scripts/bpm.py approve \
  --token YOUR_TOKEN --openid YOUR_OPENID \
  --task-id TASK_ID --action approve --comment "同意"

# 3. 添加预审意见（不办结）
python3 scripts/bpm.py comment \
  --token YOUR_TOKEN --openid YOUR_OPENID \
  --task-id TASK_ID --action-name review --msg "请补充材料"
```

## 文件结构

```
.
├── SKILL.md          # Skill 文档（LLM 业务协议）
├── scripts/
│   └── bpm.py        # CLI 工具（HTTP 客户端）
└── README.md         # 本文件
```
