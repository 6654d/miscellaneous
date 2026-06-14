---
name: bpm
description: Feishu BPM (Business Process Management) user interface for workflow tasks. Use when: (1) query pending approval tasks (待办任务), (2) query completed tasks (已办任务), (3) approve or reject workflow tasks, (4) add comments to tasks without completing, (5) search tasks by date, title, or process type, (6) review approval history.
---

# BPM - Feishu Business Process Management (User Interface)

## Environment Configuration

**Before using this skill, you need to configure your BPM API endpoint.**

### First-Time Setup

1. **Set your API base URL** as environment variable or pass it with each command:
   ```bash
   export BPM_BASE_URL="http://your-server:port"
   ```

2. **Or configure it in the CLI tool** by editing the default value in `scripts/bpm.py`

### Configuration Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `base_url` | Your BPM API server address | `http://localhost:8001` |
| `token` | Your authentication token | Provided by admin |
| `openid` | Your Feishu OpenID | `ou_xxx` |

> **Note:** Replace `{{BASE_URL}}` in the examples below with your configured base URL.

## Overview

This is the **user interface** for processing BPM workflow tasks. It provides four key APIs:

### User APIs

1. **Query Pending Tasks** - Get tasks awaiting YOUR approval (基于当前token/openid)
2. **Query Completed Tasks** - Review YOUR approval history
3. **Approve/Reject Task** - Process a workflow task (同意或拒绝)
4. **Add Comment** - Add comments to tasks WITHOUT completing them (预审，不办结任务)

### Important: Understanding "Pending Tasks"

**⚠️ Key Concept:** The "pending tasks" (待办任务) returned by the API are **tasks assigned to the current user** (based on their `token` and `openid`).

- These are tasks **waiting for YOUR approval decision**
- They are NOT necessarily tasks where you are listed as the "task assignee" in the workflow
- The system determines your pending tasks based on your user identity and workflow routing
- Always query pending tasks first to see what's assigned to YOU, not based on task field values

### Typical Workflow

```
1. Query Pending Tasks (查询待办)
   ↓
2. Display Task Details to User (展示表单数据)
   ↓
3. User Makes Decision (用户决策)
   ↓
4. Approve/Reject OR Add Comment (审批 或 添加意见)
```

**Step-by-Step Example:**

1. **Query your pending tasks**
   ```bash
   curl "/api/bpm/v2/todos?token=YOUR_TOKEN&openid=YOUR_OPENID&limit=10"
   ```

2. **Present task information to user**:
   - Task title (任务标题)
   - Process name (流程名称)
   - Form data (表单数据，如果有)
   - History comments (审批历史)

3. **User reviews and decides**: Approve, Reject, or Add Comment

4. **Execute action** based on user's decision

**Prerequisites:** You must have a valid `token` and `openid` to access these APIs. Contact your BPM administrator if you don't have these credentials.

---

## Authentication

The BPM API uses token-based authentication. Follow these steps to get started.

### Step 1: Obtain Token from Administrator

Contact your BPM administrator to generate a token for you. The administrator will need:
- Your BPM user ID (e.g., "zhangsan", "lisi")
- Optional remark/note

The administrator will generate a token and send it to you through a secure channel.

### Step 2: Bind Your OpenID to Token (One-Time Setup)

**Before using the APIs, you must bind your OpenID to the token.** This activates the token.

#### Using curl

```bash
curl -X POST "{{BASE_URL}}/api/bpm/token/bind" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN",
    "openid": "YOUR_OPENID"
  }'
```

**Success Response:**
```json
{
  "code": 0,
  "message": "绑定成功",
  "data": {
    "user_id": "zhangsan",
    "is_active": 1
  }
}
```

**⚠️ IMPORTANT: Token Security and Usage**

After receiving your token from the administrator:

1. **Save Your Token Permanently**
   - Store your token in a secure location (password manager, secure notes, etc.)
   - **DO NOT lose your token** - it is your permanent credential for BPM access
   - You will need this token for every BPM API call

2. **Token is Non-Transferable**
   - **DO NOT share your token** with anyone else
   - Each token is bound to ONE specific OpenID (yours)
   - Using someone else's token will NOT work for you

3. **Token is Exclusive to You**
   - Only the OpenID used to bind the token can use it
   - Other users cannot use your token even if they have it
   - If you lose your token, contact your administrator to generate a new one

4. **Keep Token Confidential**
   - Treat your token like a password
   - Never commit tokens to version control
   - Never share tokens in chat, email, or documents

**Note:** You only need to bind once. After successful binding, the token becomes active and can be used for all API calls.

**Token Status:**
- `is_active: 0` - Token inactive (not bound or deactivated)
- `is_active: 1` - Token active (bound to OpenID and ready to use)

### Step 3: Start Using BPM APIs

After binding, you can use all the BPM APIs with your `token` and `openid`.

---

## API Endpoints

All API endpoints require `token` + `openid` for authentication.

### 1. Get Pending Tasks (V2)

Get tasks that are awaiting your approval.

```
GET {{BASE_URL}}/api/bpm/v2/todos
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `openid` | string | Yes | Your Feishu openid |
| `token` | string | Yes | Your auth token |
| `start` | integer | No | Pagination start (default: 0) |
| `limit` | integer | No | Items per page (default: 20, max: 100) |
| `title` | string | No | Fuzzy search by task title |
| `begin_date` | string | No | Start date (format: yyyy-MM-dd) |
| `end_date` | string | No | End date (format: yyyy-MM-dd) |
| `process_def_id` | string | No | Filter by process definition ID |

**Example:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/todos?openid=ou_xxx&token=abc123...&limit=20"
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 42,
    "items": [
      {
        "taskInstId": "d187e74a-da01-4587-9e97-e5f6b0203ad4",
        "title": "采购申请 - 办公用品",
        "processDefName": "采购流程",
        "processDefId": "PROC_001",
        "startTime": "2026-04-10 09:30:00",
        "status": "pending"
      }
    ]
  }
}
```

---

### 2. Get Completed Tasks (V2)

Get tasks that you have already processed (approved or rejected).

```
GET {{BASE_URL}}/api/bpm/v2/dones
```

**Query Parameters:** (Same as pending tasks)

**Example:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/dones?openid=ou_xxx&token=abc123...&limit=20"
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 128,
    "items": [
      {
        "taskInstId": "c123e74a-da01-4587-9e97-e5f6b0203ad5",
        "title": "请假申请 - 年假",
        "processDefName": "请假流程",
        "processDefId": "PROC_002",
        "startTime": "2026-04-09 14:20:00",
        "endTime": "2026-04-09 15:45:00",
        "status": "approved",
        "action": "approve"
      }
    ]
  }
}
```

---

### 3. Approve/Reject Task (V2)

Process a workflow task by approving or rejecting it.

```
POST {{BASE_URL}}/api/bpm/v2/approve
Content-Type: application/json
```

**Request Body:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `openid` | string | Yes | Your Feishu openid |
| `token` | string | Yes | Your auth token |
| `task_inst_id` | string | Yes | Task instance ID |
| `action` | string | Yes | "approve" or "reject" |
| `comment` | string | No | Approval comment |

**Request Example:**
```json
{
  "openid": "ou_xxx",
  "token": "abc123...",
  "task_inst_id": "d187e74a-da01-4587-9e97-e5f6b0203ad4",
  "action": "approve",
  "comment": "同意申请"
}
```

**Success Response:**
```json
{
  "code": 0,
  "message": "审批成功",
  "data": {
    "taskInstId": "d187e74a-da01-4587-9e97-e5f6b0203ad4",
    "status": "approved"
  }
}
```

**Error Responses:**

| Error | Description |
|-------|-------------|
| `invalid_task_inst_id` | Task doesn't exist or has already been processed |
| `permission_denied` | You don't have permission to approve this task |
| 40001 | Authentication failed |

---

### 4. Add Comment (V2)

Add a comment to a task WITHOUT completing it. The task remains in pending status for others to review.

```
POST {{BASE_URL}}/api/bpm/v2/comment
Content-Type: application/json
```

**Request Body:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `openid` | string | Yes | Your Feishu openid |
| `token` | string | Yes | Your auth token |
| `task_inst_id` | string | Yes | Task instance ID |
| `action_name` | string | Yes | Action name (e.g., "review", "comment") |
| `msg` | string | No | Comment message |

**Request Example:**
```json
{
  "openid": "ou_xxx",
  "token": "abc123...",
  "task_inst_id": "d187e74a-da01-4587-9e97-e5f6b0203ad4",
  "action_name": "review",
  "msg": "请补充相关材料"
}
```

**Success Response:**
```json
{
  "code": 0,
  "message": "评论添加成功",
  "data": {
    "taskInstId": "d187e74a-da01-4587-9e97-e5f6b0203ad4",
    "comment": "请补充相关材料"
  }
}
```

---

## CLI Usage Examples

### Using the Python CLI Tool

**Query pending tasks:**
```bash
python3 scripts/bpm.py todos \
  --base-url "{{BASE_URL}}" \
  --token "YOUR_TOKEN" \
  --openid "YOUR_OPENID" \
  --limit 20
```

**Approve a task:**
```bash
python3 scripts/bpm.py approve \
  --base-url "{{BASE_URL}}" \
  --token "YOUR_TOKEN" \
  --openid "YOUR_OPENID" \
  --task-id "d187e74a-da01-4587-9e97-e5f6b0203ad4" \
  --action approve \
  --comment "同意申请"
```

**Add a comment:**
```bash
python3 scripts/bpm.py comment \
  --base-url "{{BASE_URL}}" \
  --token "YOUR_TOKEN" \
  --openid "YOUR_OPENID" \
  --task-id "d187e74a-da01-4587-9e97-e5f6b0203ad4" \
  --action-name "review" \
  --msg "请补充相关材料"
```

---

## Common Workflows

### Workflow 1: Complete Approval Process (标准审批流程)

This is the **recommended workflow** for processing tasks:

**Step 1: Query Your Pending Tasks**
```bash
curl "{{BASE_URL}}/api/bpm/v2/todos?openid=YOUR_OPENID&token=YOUR_TOKEN&limit=10"
```

**Step 2: Display Task Details to User**

Extract and present:
- Task title (任务标题)
- Process definition name (流程名称)
- Task form data (表单数据)
- Approval history (审批历史)

**Step 3: User Reviews and Makes Decision**

Show the user the task information and ask for their decision.

**Step 4: Execute User's Decision**

Option A - Approve (同意):
```bash
curl -X POST "{{BASE_URL}}/api/bpm/v2/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "openid": "YOUR_OPENID",
    "token": "YOUR_TOKEN",
    "task_inst_id": "TASK_ID_FROM_STEP_1",
    "action": "approve",
    "comment": "同意申请"
  }'
```

Option B - Reject (拒绝):
```bash
curl -X POST "{{BASE_URL}}/api/bpm/v2/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "openid": "YOUR_OPENID",
    "token": "YOUR_TOKEN",
    "task_inst_id": "TASK_ID_FROM_STEP_1",
    "action": "reject",
    "comment": "需要补充材料"
  }'
```

Option C - Add Comment Without Completing (预审，不办结):
```bash
curl -X POST "{{BASE_URL}}/api/bpm/v2/comment" \
  -H "Content-Type: application/json" \
  -d '{
    "openid": "YOUR_OPENID",
    "token": "YOUR_TOKEN",
    "task_inst_id": "TASK_ID_FROM_STEP_1",
    "action_name": "review",
    "msg": "请补充相关材料后重新提交"
  }'
```

### Workflow 2: Add Pre-Review Comment (预审意见)

When you need to request more information WITHOUT completing the task:

1. **Query pending tasks** to get task list
2. **Select a task** and add a comment for the submitter to review:
   ```bash
   curl -X POST "{{BASE_URL}}/api/bpm/v2/comment" \
     -H "Content-Type: application/json" \
     -d '{
       "openid": "YOUR_OPENID",
       "token": "YOUR_TOKEN",
       "task_inst_id": "TASK_ID",
       "action_name": "review",
       "msg": "请补充相关材料"
     }'
   ```
3. **Task remains in pending** - the comment is added but the task is NOT completed

### Workflow 3: Search and Filter (筛选查询)

**By Date Range:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/todos?openid=YOUR_OPENID&token=YOUR_TOKEN&begin_date=2026-04-01&end_date=2026-04-30"
```

**By Title:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/todos?openid=YOUR_OPENID&token=YOUR_TOKEN&title=请假"
```

**By Process Type:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/todos?openid=YOUR_OPENID&token=YOUR_TOKEN&process_def_id=PROCESS_DEF_ID"
```

### Workflow 4: View Approval History (查看审批历史)

**Query completed tasks to see your approval history:**
```bash
curl "{{BASE_URL}}/api/bpm/v2/dones?openid=YOUR_OPENID&token=YOUR_TOKEN&limit=20"
```

---

## Best Practices for AI Agent

### Token Management (For AI Agents)

**CRITICAL: Token Security**

When handling user tokens:

1. **Save User Token Permanently**
   - When user provides token, **save it to memory or secure storage**
   - User will need this token for ALL future BPM interactions
   - Ask user: "Should I save your token for future BPM tasks?"
   - Store tokens in secure, persistent storage

2. **Token is User-Specific**
   - Each token is bound to ONE specific OpenID
   - Only the user who bound the token can use it
   - Never share or transfer tokens between users

3. **Token Loss Prevention**
   - Warn users: "This token is permanent. If lost, you must contact admin for a new one."
   - Recommend secure storage: password manager, encrypted notes, etc.
   - Never expose tokens in logs, chat history, or error messages

4. **Token Verification**
   - Always verify token belongs to current user before use
   - Check token + openid match before processing tasks
   - If mismatch, inform user immediately

**⚠️ Common Mistakes to Avoid:**

❌ **Don't ask for token every time** - Save it permanently after first use
❌ **Don't share tokens** - Each token is exclusive to one user
❌ **Don't lose tokens** - They are permanent credentials, not temporary
❌ **Don't assume token ownership** - Always verify token + openid match

### Recommended Approach

When helping users with BPM tasks:

1. **Always Query First**
   - Start by querying pending tasks for the user
   - Use the user's `token` and `openid`
   - Show a summary of what's pending

2. **Present Information Clearly**
   - Display task title, process name, and key details
   - Show form data if available
   - Include relevant approval history

3. **Ask for User Decision**
   - Present the task information
   - Ask: "Would you like to approve, reject, or add a comment?"
   - Wait for explicit user instruction

4. **Execute Action**
   - Only call approve/comment APIs AFTER user makes decision
   - Include user's comments in the API call
   - Confirm the action result

5. **Save Token for Future Use**
   - After first successful authentication, save token permanently
   - Remind user: "I've saved your token for future BPM tasks"
   - Use saved token for subsequent requests

### Common Mistakes to Avoid

❌ **Don't auto-approve tasks** - Always let user decide
❌ **Don't skip the query step** - Users need to see what's pending first
❌ **Don't assume task context** - Query gives you the actual pending tasks
❌ **Don't use task assignee fields** - Pending tasks are based on token/openid, not field values
❌ **Don't lose user tokens** - Save them permanently for future use
❌ **Don't share tokens** - Each token is bound to one specific user

### Example Conversation Flow

```
User: 我有审批任务吗？

AI: Let me check your pending tasks...
    [API Call: /api/bpm/v2/todos]

    You have 3 pending tasks:
    1. 贷款提前还款流程【DKTQHK2026030015】
    2. 其他合同审批流程【LFKZDQ2026020002】
    3. 员工请假申请【LV2024001】

    Would you like me to show details for any of these tasks?

User: 第一个，看一下详情

AI: [Shows task details, form data, history]

    这是一笔贷款提前还款申请，金额50万元。
    是否同意此项申请？

User: 同意

AI: [API Call: /api/bpm/v2/approve with action=approve]

    ✓ 审批成功！已同意此项申请。
```

## Error Handling

### Common Error Codes

| Error Code | Message | Solution |
|------------|---------|----------|
| 40001 | 认证失败 | Check your token and openid |
| 40002 | Token不存在 | Contact administrator to get a new token |
| 40003 | Token已停用 | Contact administrator |
| 40004 | Token未绑定或已失效 | Bind your openid to the token |
| 403 | IP not in whitelist | Your IP is not in the allowed whitelist |
| `invalid_task_inst_id` | Task doesn't exist or processed | Get fresh task list and try again |
| `permission_denied` | No approval permission | Check workflow permissions |

### IP Whitelist Configuration

The BPM API enforces IP whitelist restrictions. By default, the following IP ranges are allowed:

| IP Range | Description |
|----------|-------------|
| `127.0.0.1` | Local loopback |
| `::1` | Local IPv6 |
| `172.16.0.0/16` | Private network (172.16.x.x) |
| `172.29.0.0/16` | Private network (172.29.x.x) |
| `192.168.0.0/16` | Private network (192.168.x.x) |
| `10.10.132.0/24` | Private network (10.10.132.x) |
| `10.6.10.0/24` | Private network (10.6.10.x) |

**If you receive a 403 error**, contact your BPM administrator to add your IP address to the whitelist configuration.

### Troubleshooting Tips

1. **Token not working:**
   - Verify you've bound your openid: `/api/bpm/token/info?token=YOUR_TOKEN`
   - Check with administrator that token is active

2. **Task processing fails:**
   - Get a fresh task list (tasks may have been processed by others)
   - Verify you have permission for this workflow

3. **Authentication errors:**
   - Double-check your token and openid are correct
   - Ensure IP is whitelisted (if applicable)

---

## Data Fields Reference

### Task Fields

| Field | Description |
|-------|-------------|
| `taskInstId` | Unique task instance identifier |
| `title` | Task title |
| `processDefName` | Workflow/process name |
| `processDefId` | Workflow definition ID |
| `startTime` | When task was created |
| `endTime` | When task was completed |
| `status` | Task status (pending/approved/rejected) |
| `action` | Action taken (approve/reject) |

### Authentication Fields

| Field | Description |
|-------|-------------|
| `token` | Your authentication token (from admin) |
| `openid` | Your Feishu OpenID |
| `user_id` | Your BPM user ID |

---

## API Documentation

- **Interactive API Docs**: `{{BASE_URL}}/docs`
- **OpenAPI Spec**: `{{BASE_URL}}/openapi.json`