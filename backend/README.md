# AI自动化工作流 - 后端

基于 FastAPI 的 AI 驱动自动化工作流编排系统后端服务。

## 技术栈

- **Web框架**: FastAPI 0.110+
- **数据库**: SQLAlchemy 2.0 (SQLite for MVP)
- **数据验证**: Pydantic v2
- **认证**: JWT (python-jose + passlib)
- **HTTP客户端**: httpx
- **定时任务**: APScheduler

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由
│   │   ├── auth.py       # 认证接口
│   │   ├── workflows.py  # 工作流接口
│   │   ├── executions.py # 执行记录接口
│   │   └── feishu.py     # 飞书集成接口
│   ├── models/           # SQLAlchemy 数据模型
│   │   ├── user.py       # 用户模型
│   │   ├── workflow.py   # 工作流模型
│   │   └── execution.py  # 执行记录模型
│   ├── schemas/          # Pydantic 数据模型
│   │   ├── user.py       # 用户Schema
│   │   ├── workflow.py   # 工作流Schema
│   │   └── execution.py  # 执行记录Schema
│   ├── services/         # 业务逻辑层
│   │   ├── auth_service.py     # 认证服务
│   │   ├── workflow_service.py  # 工作流服务
│   │   ├── execution_service.py # 执行引擎
│   │   ├── ai_service.py       # OpenAI调用
│   │   ├── feishu_service.py   # 飞书API
│   │   └── http_service.py     # HTTP请求
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库配置
│   └── main.py           # 应用入口
├── tests/                # 测试代码
├── .env.example          # 环境变量示例
├── requirements.txt      # Python依赖
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
python -m uvicorn app.main:app --reload --port 8000

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问API文档

启动服务后访问：http://localhost:8000/docs

## API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/login/form` | OAuth2登录（Swagger用） |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 工作流接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/workflows` | 创建工作流 |
| GET | `/api/workflows` | 获取工作流列表 |
| GET | `/api/workflows/{id}` | 获取工作流详情 |
| PATCH | `/api/workflows/{id}` | 更新工作流 |
| DELETE | `/api/workflows/{id}` | 删除工作流 |
| POST | `/api/workflows/{id}/publish` | 发布工作流 |
| POST | `/api/workflows/{id}/execute` | 手动执行工作流 |

### 执行记录接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workflows/{id}/executions` | 获取执行记录列表 |
| GET | `/api/executions/{id}` | 获取执行详情 |

### 飞书集成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/integrations/feishu/send-message` | 发送飞书消息 |
| POST | `/api/integrations/feishu/create-doc` | 创建飞书文档 |
| POST | `/api/integrations/feishu/read-doc` | 读取飞书文档 |

## 工作流节点类型

### 1. 触发器 (trigger)
工作流的入口节点，支持：
- 手动触发
- 定时触发（CRON表达式）

### 2. AI任务 (ai_task)
调用大语言模型处理内容，支持：
- 模型选择（GPT-4o、GPT-4o-mini）
- 提示词模板（支持 `{{variable}}` 变量替换）
- Temperature 和 Max Tokens 配置

### 3. 工具 (tool)
调用外部工具，包括：
- 飞书消息
- 飞书文档
- HTTP请求

### 4. 条件分支 (condition)
根据条件判断执行路径

## 数据模型

### 工作流配置示例 (nodes JSON)

```json
[
  {
    "id": "trigger_1",
    "type": "trigger",
    "name": "定时触发器",
    "config": {
      "type": "cron",
      "expression": "0 9 * * *",
      "timezone": "Asia/Shanghai"
    }
  },
  {
    "id": "ai_1",
    "type": "ai_task",
    "name": "生成周报",
    "config": {
      "model": "gpt-4o-mini",
      "prompt": "请根据以下数据生成周报：{{input}}",
      "temperature": 0.7
    }
  },
  {
    "id": "feishu_1",
    "type": "tool",
    "name": "发送飞书消息",
    "config": {
      "tool_type": "feishu_message",
      "receive_id": "oc_xxx",
      "receive_id_type": "chat_id",
      "text": "{{ai_1.result}}"
    }
  }
]
```

## 开发指南

### 添加新的节点类型

1. 在 `execution_service.py` 的 `execute_workflow` 函数中添加节点类型处理逻辑
2. 在对应 service 文件中实现具体执行逻辑
3. 在前端添加对应的节点配置UI

### 添加新的工具集成

1. 创建新的 service 文件（如 `notion_service.py`）
2. 在 `execution_service.py` 的工具节点处理中添加分支
3. 添加对应的API路由（如需要）

## License

MIT
