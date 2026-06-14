# OpenClaw 多飞书机器人隔离部署方案

> 适用于需要为多个用户提供独立 AI 助手的企业场景
> 每个用户拥有：独立飞书机器人 + 独立 Agent + 独立 Workspace（完全隔离）

---

## 架构概述

```
┌─────────────────────────────────────────────────────────────┐
│                        OpenClaw Gateway                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Feishu Bot 1│  │ Feishu Bot 2│  │ Feishu Bot N│  ...    │
│  │ (cli_xxx)   │  │ (cli_yyy)   │  │ (cli_zzz)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                         Agent 层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Agent 1     │  │ Agent 2     │  │ Agent N     │  ...    │
│  │ workspace-1 │  │ workspace-2 │  │ workspace-N │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

**核心特点：**
- 每个用户拥有独立的飞书企业应用（App ID + App Secret）
- 每个用户拥有独立的 Agent（隔离的 workspace、会话、记忆）
- 通过 `bindings` 实现账户到 Agent 的精确路由
- 支持自动配对批准，无需人工介入

---

## 前置准备

### 1. 服务器要求
- Linux 服务器（推荐 Ubuntu 20.04+）
- 至少 4GB 内存（根据用户数量调整）
- 域名用于飞书事件订阅（可选，WebSocket 模式可不需要公网地址）

### 2. 飞书开放平台准备
- 企业管理员权限
- 每个用户需要一个独立的企业自建应用

---

## 部署步骤

### 步骤 1：安装 OpenClaw

```bash
# 安装 OpenClaw CLI
npm install -g @openclaw/cli

# 初始化配置
openclaw config init

# 安装飞书插件
openclaw plugins install @openclaw/feishu
# 或安装中国版增强插件
openclaw plugins install openclaw-china
```

### 步骤 2：创建飞书企业应用

为每个用户重复以下步骤：

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用名称（建议：`XXX助手`）
4. 在「凭证与基础信息」中记录：
   - **App ID**（格式：`cli_xxxxxxxx`）
   - **App Secret**
5. 在「权限管理」中添加以下权限：
   ```json
   {
     "scopes": {
       "tenant": [
         "im:message",
         "im:message:readonly",
         "im:message:send_as_bot",
         "im:chat:readonly",
         "im:chat.members:readonly",
         "contact:user.employee_id:readonly"
       ]
     }
   }
   ```
6. 在「事件订阅」→「长连接接收事件」中添加事件：`im.message.receive_v1`
7. 在「应用能力」→「机器人」中启用机器人能力
8. 在「版本管理与发布」中发布应用

### 步骤 3：配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

#### 3.1 添加 Agent 配置

```json5
{
  agents: {
    defaults: {
      model: "kimi/kimi-k2.5",
      workspace: "/home/admin/.openclaw/workspace",
      timeoutSeconds: 1200,
      tools: {
        profile: "full"
      }
    },
    list: [
      // 用户 1
      {
        id: "user1",
        name: "用户1助手",
        workspace: "/home/admin/.openclaw/workspace-user1",
        agentDir: "/home/admin/.openclaw/agents/user1/agent",
        model: "kimi/kimi-k2.5",
        tools: {
          alsoAllow: [
            "feishu_bitable_app",
            "feishu_calendar_event",
            "feishu_task_task",
            // ... 其他需要的工具
          ]
        }
      },
      // 用户 2
      {
        id: "user2",
        name: "用户2助手",
        workspace: "/home/admin/.openclaw/workspace-user2",
        agentDir: "/home/admin/.openclaw/agents/user2/agent",
        model: "kimi/kimi-k2.5"
      }
      // ... 更多用户
    ]
  }
}
```

#### 3.2 添加飞书频道账户

```json5
{
  channels: {
    feishu: {
      autoApprove: true,           // 自动批准用户配对
      autoApproveDomain: "feishu", // 自动批准的域名
      requireMention: true,        // 群聊需要 @ 才回复
      session: {
        dmScope: "per-channel-peer" // 每个频道独立会话
      },
      accounts: {
        // 用户 1 的飞书机器人
        user1: {
          appId: "cli_xxxxxxxxxxx1",
          appSecret: "xxxxxxxxxxxxxx1",
          domain: "feishu",
          enabled: true,
          autoApprove: true
        },
        // 用户 2 的飞书机器人
        user2: {
          appId: "cli_xxxxxxxxxxx2",
          appSecret: "xxxxxxxxxxxxxx2",
          domain: "feishu",
          enabled: true,
          autoApprove: true
        }
        // ... 更多用户
      }
    }
  }
}
```

#### 3.3 添加路由绑定

```json5
{
  bindings: [
    // 用户 1：飞书账户 -> Agent
    {
      agentId: "user1",
      match: {
        channel: "feishu",
        accountId: "user1"
      }
    },
    // 用户 2：飞书账户 -> Agent
    {
      agentId: "user2",
      match: {
        channel: "feishu",
        accountId: "user2"
      }
    }
    // ... 更多绑定
  ]
}
```

### 步骤 4：创建 Workspace 目录

```bash
# 为每个用户创建独立的 workspace
mkdir -p /home/admin/.openclaw/workspace-user1
mkdir -p /home/admin/.openclaw/workspace-user2
# ...

# 创建 Agent 目录
mkdir -p /home/admin/.openclaw/agents/user1/agent
mkdir -p /home/admin/.openclaw/agents/user2/agent
# ...
```

### 步骤 5：启动网关

```bash
# 启动网关
openclaw gateway

# 或后台运行
openclaw gateway --daemon

# 查看日志
openclaw logs --follow
```

---

## 完整配置模板

```json5
{
  meta: {
    lastTouchedVersion: "2026.3.3",
    lastTouchedAt: "2026-06-14T00:00:00.000Z"
  },
  models: {
    providers: {
      kimi: {
        baseUrl: "https://api.moonshot.cn/v1",
        apiKey: "sk-your-api-key",
        auth: "api-key",
        api: "openai-completions",
        models: [
          {
            id: "kimi-k2.5",
            name: "Kimi 2.5",
            api: "openai-completions",
            contextWindow: 200000,
            maxTokens: 8192
          }
        ]
      }
    }
  },
  agents: {
    defaults: {
      model: "kimi/kimi-k2.5",
      workspace: "/home/admin/.openclaw/workspace",
      timeoutSeconds: 1200,
      heartbeat: {
        prompt: "Read HEARTBEAT.md if it exists. Follow it strictly. If nothing needs attention, reply HEARTBEAT_OK."
      },
      tools: {
        alsoAllow: [
          "feishu_bitable_app",
          "feishu_calendar_event",
          "feishu_task_task",
          "feishu_im_user_message",
          "feishu_search_doc_wiki",
          "feishu_sheet"
        ]
      }
    },
    list: [
      {
        id: "user1",
        name: "用户1助手",
        workspace: "/home/admin/.openclaw/workspace-user1",
        agentDir: "/home/admin/.openclaw/agents/user1/agent",
        model: "kimi/kimi-k2.5"
      }
    ]
  },
  channels: {
    feishu: {
      autoApprove: true,
      autoApproveDomain: "feishu",
      requireMention: true,
      session: {
        dmScope: "per-channel-peer"
      },
      accounts: {
        user1: {
          appId: "cli_xxxxxxxxxxx",
          appSecret: "xxxxxxxxxxxxx",
          domain: "feishu",
          enabled: true,
          autoApprove: true
        }
      }
    }
  },
  bindings: [
    {
      agentId: "user1",
      match: {
        channel: "feishu",
        accountId: "user1"
      }
    }
  ],
  commands: {
    native: true,
    nativeSkills: true,
    restart: true
  },
  cron: {
    enabled: true
  }
}
```

---

## 添加新用户脚本

创建 `add-user.sh` 脚本自动化添加新用户：

```bash
#!/bin/bash

# add-user.sh - 添加新用户到 OpenClaw 多飞书部署

USER_ID=$1
USER_NAME=$2
APP_ID=$3
APP_SECRET=$4

if [ -z "$USER_ID" ] || [ -z "$USER_NAME" ] || [ -z "$APP_ID" ] || [ -z "$APP_SECRET" ]; then
    echo "用法: ./add-user.sh <user_id> <user_name> <app_id> <app_secret>"
    echo "示例: ./add-user.sh zhangsan '张三' cli_a92f10746478dbb5 nLlWDVp0NhEwlrQ5lccx8gG58T0ARPLc"
    exit 1
fi

CONFIG_FILE="$HOME/.openclaw/openclaw.json"

# 1. 创建 workspace 目录
mkdir -p "$HOME/.openclaw/workspace-$USER_ID"
mkdir -p "$HOME/.openclaw/agents/$USER_ID/agent"

echo "✓ 创建 workspace: $HOME/.openclaw/workspace-$USER_ID"

# 2. 使用 jq 更新配置（需要安装 jq）
# 添加 Agent
cat $CONFIG_FILE | jq ".agents.list += [{
  id: \"$USER_ID\",
  name: \"$USER_NAME助手\",
  workspace: \"/home/admin/.openclaw/workspace-$USER_ID\",
  agentDir: \"/home/admin/.openclaw/agents/$USER_ID/agent\",
  model: \"kimi/kimi-k2.5\"
}]" > /tmp/openclaw_temp.json && mv /tmp/openclaw_temp.json $CONFIG_FILE

echo "✓ 添加 Agent 配置"

# 添加飞书账户
cat $CONFIG_FILE | jq ".channels.feishu.accounts[\"$USER_ID\"] = {
  appId: \"$APP_ID\",
  appSecret: \"$APP_SECRET\",
  domain: \"feishu\",
  enabled: true,
  autoApprove: true
}" > /tmp/openclaw_temp.json && mv /tmp/openclaw_temp.json $CONFIG_FILE

echo "✓ 添加飞书账户配置"

# 添加绑定
cat $CONFIG_FILE | jq ".bindings += [{
  agentId: \"$USER_ID\",
  match: {
    channel: \"feishu\",
    accountId: \"$USER_ID\"
  }
}]" > /tmp/openclaw_temp.json && mv /tmp/openclaw_temp.json $CONFIG_FILE

echo "✓ 添加路由绑定"

echo ""
echo "用户 $USER_NAME ($USER_ID) 添加完成！"
echo "请运行 'openclaw gateway restart' 重启网关生效"
```

---

## 管理命令

### 查看所有频道状态
```bash
openclaw channels list
```

### 查看网关状态
```bash
openclaw gateway status
```

### 重启网关
```bash
openclaw gateway restart
```

### 查看日志
```bash
# 实时日志
openclaw logs --follow

# 查看特定频道日志
openclaw channels logs --channel feishu
```

### 验证配置
```bash
openclaw doctor --fix
```

---

## 最佳实践

### 1. 命名规范
- **Agent ID**: 使用小写字母，如 `zhangsan`、`liangsi`
- **Workspace 目录**: `workspace-<agent_id>`
- **飞书账户 ID**: 与 Agent ID 保持一致，便于管理

### 2. 安全配置
- 将 `openclaw.json` 权限设置为 `600`
- 定期轮换飞书 App Secret
- 为敏感用户启用 `pairing` 模式（关闭 `autoApprove`）

### 3. 资源管理
- 每个 workspace 约占用 10-50MB 磁盘空间
- 根据用户数量预留足够的内存（每用户约 50-100MB）

### 4. 备份策略
```bash
# 备份所有 workspace
tar -czvf openclaw-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/workspace-* ~/.openclaw/openclaw.json

# 定期备份到远程存储
rsync -avz ~/.openclaw/workspace-* backup-server:/backups/openclaw/
```

### 5. 监控告警
- 使用 `openclaw logs --follow` 监控异常
- 设置定时任务检查网关状态
- 监控磁盘空间使用情况

---

## 故障排查

### 问题 1：机器人不响应

**排查步骤：**
1. 检查网关是否运行：`openclaw gateway status`
2. 检查日志：`openclaw logs --follow`
3. 确认飞书应用已发布且权限正确
4. 检查事件订阅是否包含 `im.message.receive_v1`

### 问题 2：配对失败

**排查步骤：**
1. 检查 `autoApprove` 是否设置为 `true`
2. 检查 `autoApproveDomain` 是否匹配（`feishu` 或 `lark`）
3. 手动批准配对：`openclaw pairing approve feishu <CODE>`

### 问题 3：消息发送失败

**排查步骤：**
1. 确认应用有 `im:message:send_as_bot` 权限
2. 确认应用已发布
3. 检查 `appId` 和 `appSecret` 是否正确

---

## 进阶配置

### 自定义模型配置
```json5
{
  agents: {
    list: [
      {
        id: "vip-user",
        name: "VIP用户助手",
        workspace: "/home/admin/.openclaw/workspace-vip",
        model: "deepseek/deepseek-v4-pro", // 使用不同模型
        timeoutSeconds: 3000
      }
    ]
  }
}
```

### 群聊配置
```json5
{
  channels: {
    feishu: {
      groups: {
        "oc_xxxxxxxx": {  // 群聊 ID
          requireMention: true,  // 需要 @ 才回复
          allowFrom: ["ou_xxx"]  // 仅允许特定用户
        }
      }
    }
  }
}
```

---

## 参考文档

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [飞书开放平台](https://open.feishu.cn)
- [OpenClaw China 插件](https://github.com/BytePioneer-AI/openclaw-china)

---

**维护者**: 陈泽良  
**最后更新**: 2026-06-14
