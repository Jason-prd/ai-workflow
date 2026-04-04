# AI 自动化工作流

[English](#english) | 中文

---

<p align="center">
  <img src="frontend/src/assets/hero.png" alt="AI自动化工作流" width="600"/>
</p>

<p align="center">
  <strong>低代码 · 可视化 · AI 驱动</strong><br>
  无需编程，通过拖拽即可创建由 AI 驱动的自动化工作流
</p>

<p align="center">
  <a href="https://github.com/Jason-prd/ai-workflow/stargazers">
    <img src="https://img.shields.io/github/stars/Jason-prd/ai-workflow?style=flat-square" alt="Stars"/>
  </a>
  <a href="https://github.com/Jason-prd/ai-workflow/network/members">
    <img src="https://img.shields.io/github/forks/Jason-prd/ai-workflow?style=flat-square" alt="Forks"/>
  </a>
  <a href="https://github.com/Jason-prd/ai-workflow/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Jason-prd/ai-workflow?style=flat-square" alt="License"/>
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square" alt="Python"/>
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.110+-green?style=flat-square" alt="FastAPI"/>
  </a>
  <a href="https://react.dev/">
    <img src="https://img.shields.io/badge/React-18-blue?style=flat-square" alt="React"/>
  </a>
  <a href="https://github.com/Jason-prd/ai-workflow/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Jason-prd/ai-workflow/ci.yml?branch=main&style=flat-square" alt="Build"/>
  </a>
  <a href="https://github.com/Jason-prd/ai-workflow/releases">
    <img src="https://img.shields.io/github/v/release/Jason-prd/ai-workflow?style=flat-square" alt="Release"/>
  </a>
</p>

---

## 📖 项目介绍

**AI 自动化工作流**是一款面向企业和个人用户的低代码 AI 自动化平台。通过可视化拖拽方式，用户无需编程即可创建由 AI 驱动的自动化工作流，解决重复性工作效率低下、跨系统数据孤岛等问题。

### 核心价值

| 价值点 | 说明 |
|--------|------|
| **低门槛** | 可视化拖拽设计，无需编码即可创建 AI 工作流 |
| **高效率** | 自动化执行重复任务，释放人力投入高价值工作 |
| **可扩展** | 预置主流工具连接器，支持 API 自定义扩展 |
| **可追溯** | 完整执行日志，实时监控运行状态 |

### 典型使用场景

- 📊 **运营自动化** — 自动生成周报/月报，数据汇总分析
- 📝 **HR 工作流** — 简历初筛、面试安排提醒
- 🌐 **跨境电商** — 商品 listing 多语言优化、多平台发布
- 🔧 **个人效率** — 个人效率工具、跨系统 API 集成
- 👥 **团队协作** — 团队工作流自动化、审批流程

---

## ✨ 功能特性

### 🎨 可视化工作流设计器
- 基于 React Flow 的无限画布，支持缩放、平移
- 拖拽式节点添加，连线即连接
- 节点配置面板，实时预览配置效果

### 🤖 AI 任务节点
- 支持 OpenAI GPT 系列（GPT-4o、GPT-4o-mini）
- 提示词模板，支持 `{{variable}}` 变量占位符
- Temperature、Max Tokens 灵活配置

### ⚡ 灵活的触发方式
- **手动触发** — 点击按钮立即执行
- **定时触发** — 支持 CRON 表达式，精准控制执行时间

### 🔧 丰富的工具集成
- **飞书消息** — 发送文本/卡片消息到群聊或个人
- **飞书文档** — 自动创建/读取飞书云文档
- **HTTP 请求** — 集成任意 RESTful API

### 🔀 条件分支
- 支持条件表达式判断，决定工作流执行分支

### 📊 执行监控
- 完整执行日志，每个节点的输入/输出清晰可见
- 执行状态实时追踪（Pending → Running → Success/Failed）
- 失败节点自动重试（1次）

### 🐳 Docker 部署
- 一键 Docker Compose 部署，开箱即用
- 生产级 Nginx 反向代理配置

---

## 🛠 技术栈

### 后端

| 技术 | 说明 |
|------|------|
| **FastAPI 0.110+** | 现代高性能 Web 框架 |
| **SQLAlchemy 2.0** | Python ORM（SQLite for MVP） |
| **Pydantic v2** | 数据验证与_settings |
| **JWT** | 用户认证（python-jose + passlib） |
| **httpx** | 异步 HTTP 客户端 |
| **APScheduler** | 定时任务调度 |
| **Uvicorn** | ASGI 服务器 |

### 前端

| 技术 | 说明 |
|------|------|
| **React 18** | UI 框架 |
| **TypeScript** | 类型安全 |
| **Vite** | 构建工具 |
| **@xyflow/react** | 可视化工作流设计器（React Flow） |
| **Ant Design 6** | 企业级 UI 组件库 |
| **TailwindCSS 4** | 原子化 CSS |
| **Zustand** | 轻量级状态管理 |
| **React Router 6** | 客户端路由 |
| **Axios** | HTTP 客户端 |

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose（用于容器部署）

### 方式一：Docker Compose 一键部署（推荐）

```bash
# 克隆项目
git clone https://github.com/Jason-prd/ai-workflow.git
cd ai-workflow/backend

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置（参考下方环境变量说明）

# 启动服务
docker-compose up -d

# 访问应用
# 前端：http://localhost
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 方式二：本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 环境变量配置（`.env`）

```env
# ========== 认证配置 ==========
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ========== OpenAI 配置 ==========
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# ========== 飞书配置（可选） ==========
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=your-feishu-app-secret
FEISHU_VERIFICATION_TOKEN=your-verification-token
FEISHU_ENCRYPT_KEY=your-encrypt-key
FEISHU_CALENDAR_POLL_INTERVAL_SECONDS=60
FEISHU_CALENDAR_REMIND_MINUTES=5

# ========== 系统配置 ==========
MAX_NODES_PER_WORKFLOW=20
MAX_CONCURRENT_EXECUTIONS=5
EXECUTION_TIMEOUT_SECONDS=60
MAX_EXECUTION_LOGS=100
LOG_RETENTION_DAYS=7
```

---

## 📐 项目结构

```
ai-workflow/
├── backend/                      # 后端（FastAPI）
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── workflows.py      # 工作流接口
│   │   │   ├── executions.py     # 执行记录接口
│   │   │   ├── feishu.py         # 飞书集成接口
│   │   │   └── nodes.py          # 节点类型元数据接口
│   │   ├── models/              # SQLAlchemy 数据模型
│   │   ├── schemas/             # Pydantic 数据模型
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── auth_service.py      # 认证服务
│   │   │   ├── workflow_service.py   # 工作流服务
│   │   │   ├── execution_service.py  # 执行引擎
│   │   │   ├── ai_service.py         # OpenAI 调用
│   │   │   ├── feishu_service.py      # 飞书 API
│   │   │   └── http_service.py        # HTTP 请求
│   │   ├── integrations/        # 飞书集成
│   │   │   ├── feishu_bot.py            # 飞书机器人 Webhook
│   │   │   ├── feishu_trigger.py        # 飞书消息触发器
│   │   │   ├── feishu_calendar_trigger.py  # 飞书日历触发器
│   │   │   ├── feishu_event_handler.py   # 事件处理器
│   │   │   └── feishu_notification.py     # 执行结果推送
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库配置
│   │   └── main.py              # 应用入口
│   ├── docs/                    # 后端文档
│   │   ├── API接口文档.md
│   │   └── 前端集成指南.md
│   ├── data/                    # 数据存储目录（SQLite）
│   ├── Dockerfile               # Docker 镜像构建
│   ├── docker-compose.yml       # Docker Compose 配置
│   ├── nginx.conf               # Nginx 配置
│   ├── requirements.txt         # Python 依赖
│   └── .env.example             # 环境变量示例
│
├── frontend/                    # 前端（React + Vite + TypeScript）
│   ├── src/
│   │   ├── components/          # 公共组件
│   │   │   ├── layout/          # 布局组件
│   │   │   ├── nodes/           # 自定义流程节点
│   │   │   ├── NodeConfigPanel.tsx   # 节点配置面板
│   │   │   └── WorkflowCard.tsx      # 工作流卡片
│   │   ├── pages/              # 页面组件
│   │   │   ├── LoginPage.tsx         # 登录页
│   │   │   ├── RegisterPage.tsx     # 注册页
│   │   │   ├── WorkflowListPage.tsx  # 工作流列表页
│   │   │   ├── WorkflowDesignerPage.tsx  # 工作流设计器
│   │   │   ├── ExecutionLogsPage.tsx     # 执行日志页
│   │   │   ├── ExecutionDetailPage.tsx   # 执行详情页
│   │   │   └── SettingsPage.tsx           # 设置页
│   │   ├── services/            # API 服务层
│   │   │   └── api.ts
│   │   ├── stores/              # Zustand 状态管理
│   │   │   ├── authStore.ts          # 认证状态
│   │   │   ├── workflowStore.ts       # 工作流状态
│   │   │   └── executionStore.ts      # 执行状态
│   │   ├── types/               # TypeScript 类型定义
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/                 # 静态资源
│   ├── dist/                    # 构建产物
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── tests/                      # 测试代码（pytest）
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_workflows.py
│   ├── test_executions.py
│   ├── test_ai_service.py
│   ├── test_feishu_integration.py
│   ├── test_http_service.py
│   ├── test_condition_evaluation.py
│   ├── test_exceptions.py
│   └── test_integration.py
│
├── docs/                       # 项目文档
│   ├── PRD.md                  # 产品需求文档
│   ├── 项目分析.md
│   ├── 核心功能确认.md
│   ├── 竞品差异化分析.md
│   ├── 部署指南.md
│   └── 生产环境部署检查清单.md
│
├── PROGRESS.md                 # 项目进度跟踪
├── TODO.md                     # 待办事项
└── README.md
```

---

## 📡 API 文档

启动服务后访问 **http://localhost:8000/docs** 查看交互式 Swagger API 文档。

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
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
| POST | `/api/workflows/validate` | 验证工作流配置 |

### 执行记录接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workflows/{id}/executions` | 获取执行记录列表 |
| GET | `/api/executions/{id}` | 获取执行详情（含节点日志） |
| GET | `/api/executions/{id}/status` | 获取执行状态（轮询） |
| GET | `/api/executions/{id}/logs` | 获取节点执行日志列表 |

### 节点类型接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/node-types` | 获取所有节点类型元数据 |
| GET | `/api/node-types/{type}` | 获取指定节点类型定义 |

### 飞书集成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integrations/feishu/webhook` | 飞书 Webhook URL 验证 |
| POST | `/api/integrations/feishu/webhook` | 接收飞书事件 |
| POST | `/api/integrations/feishu/send-message` | 发送飞书消息 |

### 工作流节点类型

| 节点类型 | 说明 | 典型用途 |
|----------|------|----------|
| `trigger` | 触发器 | 手动触发 / 定时触发（CRON） |
| `ai_task` | AI 任务 | 调用 GPT 处理内容 |
| `tool` | 工具 | 飞书消息、飞书文档、HTTP 请求 |
| `condition` | 条件分支 | 根据条件决定执行路径 |

---

## 🔧 工作流配置示例

```json
{
  "name": "日报自动生成器",
  "description": "每天早上自动生成并发送日报",
  "trigger_config": {
    "type": "cron",
    "expression": "0 9 * * 1-5",
    "timezone": "Asia/Shanghai"
  },
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "name": "定时触发",
      "config": {
        "type": "cron",
        "cron_expression": "0 9 * * 1-5",
        "timezone": "Asia/Shanghai"
      },
      "position": { "x": 100, "y": 200 }
    },
    {
      "id": "ai_1",
      "type": "ai_task",
      "name": "生成日报",
      "config": {
        "model": "gpt-4o-mini",
        "prompt": "请根据以下数据生成今日工作日报：\n{{input}}",
        "temperature": 0.7,
        "max_tokens": 2000
      },
      "position": { "x": 350, "y": 200 }
    },
    {
      "id": "feishu_1",
      "type": "tool",
      "name": "发送飞书消息",
      "config": {
        "tool_type": "feishu_message",
        "receive_id": "oc_xxxxxxxxxx",
        "receive_id_type": "chat_id",
        "text": "📋 今日日报：\n{{ai_result}}"
      },
      "position": { "x": 600, "y": 200 }
    }
  ]
}
```

---

## 🐳 Docker 部署详解

### docker-compose.yml 结构

```yaml
services:
  api:           # FastAPI 后端服务
  nginx:         # Nginx 反向代理（同时托管前端静态文件）
```

### 生产环境部署步骤

```bash
# 1. 克隆代码
git clone https://github.com/Jason-prd/ai-workflow.git
cd ai-workflow/backend

# 2. 配置环境变量
cp .env.example .env.production
# 重要：修改 SECRET_KEY、OPENAI_API_KEY、飞书配置

# 3. 构建并启动
docker-compose -f docker-compose.yml --env-file .env.production up -d --build

# 4. 验证部署
docker-compose ps
curl http://localhost:8000/api/health

# 5. 查看日志
docker-compose logs -f api
```

### 前端构建（独立部署）

如果需要单独部署前端：

```bash
cd frontend
npm install
npm run build
# 构建产物在 dist/ 目录
# 复制到 backend/frontend-dist/ 后重启 nginx
```

---

## 🧪 测试

```bash
cd tests

# 安装测试依赖
pip install -r requirements-test.txt

# 运行所有测试
pytest -v

# 运行指定测试
pytest -v tests/test_ai_service.py
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. **Fork** 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交改动：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 **Pull Request**

### 开发规范

- 后端代码遵循 PEP 8，使用 Black 格式化
- 前端代码使用 ESLint + Prettier
- 提交信息使用中文，格式：`类型: 描述`（如 `feat: 添加新节点类型`）
- 所有新功能需附带测试用例

### Commit 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) — 高性能 Web 框架
- [React Flow](https://reactflow.dev/) — 可视化流程图组件库
- [Ant Design](https://ant.design/) — 企业级 UI 组件库
- [飞书开放平台](https://open.feishu.cn/) — 强大的企业协作工具
- [OpenAI](https://openai.com/) — GPT 大语言模型

---

<p align="center">
  用 ❤️ 构建 · MIT License
</p>

---

## English

# AI Workflow Automation

A low-code visual workflow automation platform powered by AI. Create AI-driven workflows through drag-and-drop — no coding required.

### Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, JWT, APScheduler
- **Frontend**: React 18, TypeScript, Vite, React Flow, Ant Design, TailwindCSS, Zustand
- **Deployment**: Docker, Docker Compose, Nginx

### Quick Start

```bash
# Clone and start with Docker
git clone https://github.com/Jason-prd/ai-workflow.git
cd ai-workflow/backend
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d

# Access
# Frontend: http://localhost
# API Docs: http://localhost:8000/docs
```

### Features

- 🎨 Visual workflow designer (React Flow)
- 🤖 AI task nodes (GPT-4o, GPT-4o-mini)
- ⚡ Manual & CRON triggers
- 🔧 Feishu integration (messages, docs)
- 🌐 HTTP requests to any REST API
- 📊 Execution logs & monitoring
- 🐳 Docker-ready deployment
