# AI 自动化工作流 - API 接口文档

> 版本：v1.0.0  
> 更新日期：2026-03-28  
> 基础 URL：`http://localhost:8000`

---

## 📌 认证说明

除 `/api/auth/*` 和健康检查接口外，所有 API **需要认证**。

在请求 Header 中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 获取方式：登录成功后返回 `access_token` 字段。

---

## 📌 通用响应格式

### 成功响应
```json
{
  "id": 1,
  "name": "我的工作流",
  ...
}
```

### 错误响应
```json
{
  "detail": "错误描述"
}
```

### 分页列表响应
```json
{
  "items": [...],
  "total": 100
}
```

---

## 🔐 认证接口 `/api/auth`

### 注册用户
```
POST /api/auth/register
Content-Type: application/json
```

**请求体：**
```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "yourpassword"
}
```

**成功响应 (201)：**
```json
{
  "user": {
    "id": 1,
    "name": "zhangsan",
    "email": "zhangsan@example.com"
  },
  "token": "<access_token>",
  "expires_in": 86400
}
```

---

### 用户登录
```
POST /api/auth/login
Content-Type: application/json
```

**请求体：**
```json
{
  "email": "zhangsan@example.com",
  "password": "yourpassword"
}
```

**成功响应 (200)：**
```json
{
  "access_token": "<access_token>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "name": "zhangsan",
    "email": "zhangsan@example.com"
  }
}
```

---

### 获取当前用户信息
```
GET /api/auth/me
Authorization: Bearer <access_token>
```

**成功响应 (200)：**
```json
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "created_at": "2026-03-28T10:00:00"
}
```

---

## 📋 工作流接口 `/api/workflows`

### 创建工作流
```
POST /api/workflows
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "日报总结助手",
  "description": "每天早上自动总结前一天的工作",
  "trigger_config": {
    "type": "cron",
    "expression": "0 9 * * *",
    "timezone": "Asia/Shanghai"
  },
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "name": "定时触发",
      "config": {
        "type": "cron",
        "cron_expression": "0 9 * * *",
        "timezone": "Asia/Shanghai"
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "ai_1",
      "type": "ai_task",
      "name": "生成总结",
      "config": {
        "prompt": "请总结以下工作内容：\n{{input}}",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 2000
      },
      "position": {"x": 300, "y": 200}
    },
    {
      "id": "tool_1",
      "type": "tool",
      "name": "发送飞书消息",
      "config": {
        "tool_type": "feishu_message",
        "receive_id": "oc_xxxxx",
        "receive_id_type": "chat_id",
        "text": "今日日报：\n{{ai_result}}"
      },
      "position": {"x": 500, "y": 200}
    }
  ]
}
```

**成功响应 (201)：** 返回 `WorkflowResponse`，见下方。

---

### 获取工作流列表
```
GET /api/workflows?skip=0&limit=100
Authorization: Bearer <access_token>
```

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "name": "日报总结助手",
      "description": "每天早上自动总结前一天的工作",
      "trigger_config": {"type": "cron", "expression": "0 9 * * *", "timezone": "Asia/Shanghai"},
      "nodes": [...],
      "status": "draft",
      "created_at": "2026-03-28T10:00:00",
      "updated_at": "2026-03-28T10:00:00"
    }
  ],
  "total": 5
}
```

---

### 获取工作流详情
```
GET /api/workflows/{workflow_id}
Authorization: Bearer <access_token>
```

**成功响应 (200)：** `WorkflowResponse`

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 工作流ID |
| user_id | int | 所属用户ID |
| name | string | 工作流名称 |
| description | string | 描述 |
| trigger_config | object | 触发器配置 |
| nodes | array | 节点列表 |
| status | string | `draft`（草稿）/ `published`（已发布） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 更新工作流
```
PATCH /api/workflows/{workflow_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求体（所有字段可选，只更新提供的字段）：**
```json
{
  "name": "新名称",
  "description": "新描述",
  "nodes": [...],
  "trigger_config": {...}
}
```

**成功响应 (200)：** `WorkflowResponse`

---

### 删除工作流
```
DELETE /api/workflows/{workflow_id}
Authorization: Bearer <access_token>
```

**成功响应：** `204 No Content`

---

### 发布工作流
```
POST /api/workflows/{workflow_id}/publish
Authorization: Bearer <access_token>
```

发布后定时触发器才会生效。

**成功响应 (200)：** `WorkflowResponse`

---

### 执行工作流（手动触发）
```
POST /api/workflows/{workflow_id}/execute
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求体（可选）：**
```json
{
  "input": {
    "key": "value"
  }
}
```

**成功响应 (201)：** `ExecutionResponse`

```json
{
  "id": 10,
  "workflow_id": 1,
  "trigger_type": "manual",
  "status": "running",
  "started_at": "2026-03-28T10:00:00",
  "ended_at": null,
  "error_message": null,
  "trigger_input": {"input": {"key": "value"}},
  "created_at": "2026-03-28T10:00:00"
}
```

---

### 验证工作流配置
```
POST /api/workflows/validate
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求体：** 同创建工作流（可选所有字段）

**成功响应 (200)：**
```json
{
  "valid": true,
  "errors": []
}
```

**验证失败响应：**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "nodes",
      "message": "节点 trigger_1 缺少 type 字段",
      "node_id": "trigger_1"
    }
  ]
}
```

---

## 📊 执行记录接口 `/api`

> Base Path: `/api`（注意不是 `/api/workflows`）

### 获取工作流的执行记录列表
```
GET /api/workflows/{workflow_id}/executions?skip=0&limit=50
Authorization: Bearer <access_token>
```

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": 10,
      "workflow_id": 1,
      "trigger_type": "manual",
      "status": "success",
      "started_at": "2026-03-28T10:00:00",
      "ended_at": "2026-03-28T10:00:05",
      "error_message": null,
      "trigger_input": null,
      "created_at": "2026-03-28T10:00:00"
    }
  ],
  "total": 10
}
```

---

### 获取执行详情（含节点日志）
```
GET /api/executions/{execution_id}
Authorization: Bearer <access_token>
```

**成功响应 (200)：** `ExecutionDetailResponse`

```json
{
  "id": 10,
  "workflow_id": 1,
  "trigger_type": "manual",
  "status": "success",
  "started_at": "2026-03-28T10:00:00",
  "ended_at": "2026-03-28T10:00:05",
  "error_message": null,
  "trigger_input": null,
  "created_at": "2026-03-28T10:00:00",
  "logs": [
    {
      "id": 1,
      "execution_id": 10,
      "node_id": "trigger_1",
      "node_type": "trigger",
      "node_name": "定时触发",
      "status": "success",
      "input_data": {"triggered": true, "trigger_type": "manual"},
      "output_data": {"triggered": true, "trigger_time": "2026-03-28T10:00:00"},
      "error": null,
      "duration_ms": 5,
      "created_at": "2026-03-28T10:00:00"
    },
    {
      "id": 2,
      "execution_id": 10,
      "node_id": "ai_1",
      "node_type": "ai_task",
      "node_name": "生成总结",
      "status": "success",
      "input_data": {"triggered": true},
      "output_data": {"result": "AI生成的总结内容..."},
      "error": null,
      "duration_ms": 3000,
      "created_at": "2026-03-28T10:00:01"
    }
  ]
}
```

---

### 获取执行状态（轮询接口）
```
GET /api/executions/{execution_id}/status
Authorization: Bearer <access_token>
```

**成功响应 (200)：** `ExecutionStatusResponse`

```json
{
  "id": 10,
  "workflow_id": 1,
  "status": "running",
  "started_at": "2026-03-28T10:00:00",
  "ended_at": null,
  "error_message": null,
  "current_node_id": "ai_1",
  "current_node_name": "生成总结",
  "progress_percent": 50,
  "created_at": "2026-03-28T10:00:00"
}
```

**status 枚举：** `pending` / `running` / `success` / `failed`

---

### 获取执行日志列表
```
GET /api/executions/{execution_id}/logs
Authorization: Bearer <access_token>
```

**成功响应 (200)：** `ExecutionLogResponse[]`

---

## 🧩 节点类型元数据接口 `/api`

> Base Path: `/api`

### 获取所有节点类型
```
GET /api/node-types
Authorization: Bearer <access_token>
```

**成功响应 (200)：**
```json
[
  {
    "type": "trigger",
    "name": "触发器",
    "description": "工作流启动条件，支持手动触发和定时触发",
    "icon": "⚡",
    "color": "#FF6B35",
    "category": "触发器",
    "fields": [
      {
        "name": "type",
        "type": "select",
        "label": "触发方式",
        "required": true,
        "options": [
          {"label": "手动触发", "value": "manual"},
          {"label": "定时触发（Cron）", "value": "cron"}
        ],
        "default": "manual"
      }
    ],
    "has_position": true
  },
  {
    "type": "ai_task",
    "name": "AI 任务",
    "description": "调用大语言模型处理任务，输入文本并获得AI生成的结果",
    "icon": "🤖",
    "color": "#4ECDC4",
    "category": "AI任务",
    "fields": [...],
    "has_position": true
  },
  {
    "type": "tool",
    "name": "工具",
    "description": "执行具体操作：发送飞书消息、创建文档、HTTP请求等",
    "icon": "🔧",
    "color": "#45B7D1",
    "category": "工具",
    "fields": [...],
    "has_position": true
  },
  {
    "type": "condition",
    "name": "条件判断",
    "description": "根据条件表达式的结果，决定工作流的执行分支",
    "icon": "🔀",
    "color": "#96CEB4",
    "category": "逻辑",
    "fields": [...],
    "has_position": true
  }
]
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 节点类型标识 |
| name | string | 节点显示名称 |
| description | string | 节点功能描述 |
| icon | string | 节点图标（emoji） |
| color | string | 节点颜色（hex） |
| category | string | 所属分类 |
| fields | array | 配置字段列表 |
| fields[].name | string | 字段名 |
| fields[].type | string | 字段类型：string / number / boolean / select / textarea / json |
| fields[].label | string | 字段显示标签 |
| fields[].required | bool | 是否必填 |
| fields[].options | array | 下拉选项（select类型） |
| fields[].default | any | 默认值 |
| fields[].placeholder | string | 占位提示 |
| fields[].description | string | 字段说明 |
| has_position | bool | 是否在设计器中显示位置 |

---

### 获取指定节点类型
```
GET /api/node-types/{node_type}
Authorization: Bearer <access_token>
```

**node_type 取值：** `trigger` / `ai_task` / `tool` / `condition`

**成功响应 (200)：** `NodeTypeDefinition`（单个对象）

---

## 🔧 通用节点配置说明

### 触发器节点 (type: trigger)
```json
{
  "id": "trigger_1",
  "type": "trigger",
  "name": "定时触发",
  "config": {
    "type": "manual",
    "cron_expression": "0 9 * * *",
    "timezone": "Asia/Shanghai"
  },
  "position": {"x": 100, "y": 200}
}
```

### AI 任务节点 (type: ai_task)
```json
{
  "id": "ai_1",
  "type": "ai_task",
  "name": "生成总结",
  "config": {
    "prompt": "请总结以下工作内容：\n{{input}}",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "position": {"x": 300, "y": 200}
}
```

**prompt 变量引用语法：** `{{variable_name}}`

支持的变量：
- `{{trigger.xxx}}` - 触发器输出
- 上一节点的 `output_data` 中的字段

### 工具节点 (type: tool)

**飞书消息 (tool_type: feishu_message):**
```json
{
  "id": "tool_1",
  "type": "tool",
  "name": "发送飞书消息",
  "config": {
    "tool_type": "feishu_message",
    "receive_id": "oc_xxxxx",
    "receive_id_type": "chat_id",
    "text": "今日日报：\n{{ai_result}}"
  },
  "position": {"x": 500, "y": 200}
}
```

**HTTP请求 (tool_type: http_request):**
```json
{
  "id": "tool_2",
  "type": "tool",
  "name": "调用外部API",
  "config": {
    "tool_type": "http_request",
    "url": "https://api.example.com/notify",
    "method": "POST",
    "headers": {"Authorization": "Bearer xxx"},
    "body": {"message": "{{ai_result}}"},
    "timeout": 30
  },
  "position": {"x": 500, "y": 200}
}
```

### 条件节点 (type: condition)
```json
{
  "id": "cond_1",
  "type": "condition",
  "name": "判断结果",
  "config": {
    "condition": "simple",
    "expression": "trigger.status equals success"
  },
  "position": {"x": 300, "y": 200}
}
```

---

## 📝 工作流 Designer 数据结构

### 完整工作流数据结构
```json
{
  "name": "工作流名称",
  "description": "工作流描述（可选）",
  "trigger_config": {
    "type": "manual",
    "expression": "0 9 * * *",
    "timezone": "Asia/Shanghai"
  },
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "name": "触发器",
      "config": {...},
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "ai_1",
      "type": "ai_task",
      "name": "AI任务",
      "config": {...},
      "position": {"x": 300, "y": 200}
    }
  ]
}
```

---

## 🔄 轮询执行状态方案

前端在调用 `POST /api/workflows/{id}/execute` 后，建议按如下策略轮询状态：

```javascript
// 1. 获取执行ID（立即返回）
const execution = await post('/api/workflows/1/execute');
const executionId = execution.id;

// 2. 轮询状态（建议间隔 1-2 秒）
let status = 'running';
while (status === 'running' || status === 'pending') {
  await sleep(1000);
  const statusResp = await get(`/api/executions/${executionId}/status`);
  status = statusResp.status;
  updateProgress(statusResp.progress_percent, statusResp.current_node_name);
}

// 3. 获取完整结果
const result = await get(`/api/executions/${executionId}`);
renderLogs(result.logs);
```

---

## 🚨 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 400 | 请求参数错误（字段校验失败） |
| 401 | 未认证或 Token 过期 |
| 403 | 无权访问该资源 |
| 404 | 资源不存在 |
| 422 | 请求体格式错误 |
| 500 | 服务器内部错误 |

---

## 📍 Swagger UI

访问 `http://localhost:8000/docs` 查看交互式 API 文档。

点击右上角 **Authorize** 按钮，输入 `Bearer <access_token>` 即可在 Swagger 中测试所有需要认证的接口。
