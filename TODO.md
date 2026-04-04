# TODO.md - AI自动化工作流 待办事项

## 项目状态
- **状态**：开发中
- **当前阶段**：前后端集成 + 飞书集成
- **最后更新**：2026-03-28（飞书集成完成）

---

## ✅ 已完成

### 产品
- [x] 市场调研
- [x] 项目分析
- [x] 核心功能确认
- [x] PRD 文档
- [x] 技术方案
- [x] 竞品差异化分析

### 后端
- [x] 项目初始化（FastAPI + SQLAlchemy）
- [x] 用户认证 API（注册/登录/JWT）
- [x] 工作流 CRUD API
- [x] 执行日志 API
- [x] 工作流执行引擎
- [x] AI 任务节点（OpenAI GPT）
- [x] HTTP 请求工具节点
- [x] 飞书服务（消息发送/文档创建/读取）
- [x] 飞书机器人 Webhook 接入
- [x] 飞书消息触发器
- [x] 飞书日历事件触发器
- [x] 执行结果推送回飞书
- [x] 单元测试

### 前端
- [x] 项目初始化（React + Vite + TypeScript）
- [x] 登录/注册页面
- [x] 工作流列表页面
- [x] 工作流设计器（可视化拖拽）
- [x] 执行日志页面
- [x] 执行详情页面
- [x] 设置页面

### 测试
- [x] 后端 API 单元测试
- [x] 飞书集成测试
- [x] AI 服务层单元测试（变量替换、API 调用）
- [x] HTTP 服务层单元测试
- [x] 条件表达式求值单元测试
- [x] 端到端集成测试（认证→执行完整链路）

---

## 🔄 进行中

### 前端
- [x] 前后端 API 联调（登录/注册/工作流CRUD）
  - ✅ 修复 LoginResponse 类型（access_token vs token）
  - ✅ 修复 authStore token 字段映射
  - ✅ 修复 user.id 类型（string vs number）
  - ✅ 修复 executionStore loadLogs 空workflowId问题
- [x] 工作流设计器（可视化拖拽节点编辑）
- [x] 执行日志页面（实时加载）
- [x] 执行详情页面（节点执行详情）

### 后端
- [x] Webhook 事件 -> 工作流触发 完整链路打通

---

## 📋 待处理

### 飞书集成
- [ ] 飞书应用权限申请与配置（App ID / App Secret / Verification Token）
- [ ] 飞书事件订阅配置（需要公网可访问的 Webhook URL）
- [ ] WebSocket 长连接支持（可选，用于实时推送）

### 工作流设计器
- [ ] 节点配置面板完善
- [ ] 节点连接线样式优化
- [ ] 工作流保存/发布功能对接
- [ ] 触发器节点配置 UI

### AI 任务节点
- [ ] 模型选择 UI
- [ ] 提示词模板变量解析
- [ ] 上下文管理（多轮对话）

### 工具节点
- [ ] 飞书文档读取结果解析
- [ ] HTTP 请求响应展示优化

### 部署
- [x] Docker 容器化
- [x] 生产环境配置
- [x] 部署指南文档（环境配置、Nginx配置、Docker Compose部署）
- [x] Docker Compose 本地部署验证
- [ ] 数据库迁移（Alembic）

### GitHub 开源
- [x] 编写项目 README.md（项目介绍、功能特性、技术栈、快速开始、API文档、项目结构、贡献指南）
- [x] 整理 LICENSE 文件（MIT License，2026-04-04）
- [x] 创建 .gitignore 文件（2026-04-04）
- [x] 关联 GitHub 远程仓库并推送（2026-04-04）
- [x] GitHub 仓库状态检查（2026-04-04 21:15）：远程origin✅/本地同步✅/README.md✅/LICENSE✅/docker-compose.yml✅(backend/)

### 监控
- [ ] 执行日志保留策略（定时清理）
- [ ] 错误告警（邮件/飞书通知）

---

## 🎯 优先级排序

### P0 - 必须完成（MVP）
1. [x] 前后端 API 联调完成
2. [x] 工作流设计器完整功能
3. [ ] 飞书 Webhook 实际对接（需要公网 URL）
4. [x] Docker 部署
5. [x] Docker Compose 本地部署验证

### P1 - 重要
1. [ ] AI 任务节点完善（提示词模板、上下文）
2. [ ] 定时触发器（CRON）实现
3. [ ] 执行日志查看器优化

### P2 - 增强
1. [ ] 监控告警
2. [ ] 更多工具集成（Slack、Notion）
3. [ ] 多模型切换

---

## 📝 备注

### 飞书集成注意事项
- 需要公网可访问的 Webhook URL（可使用 ngrok 进行本地开发测试）
- 需要在飞书开放平台创建企业自建应用
- 需要配置事件订阅权限：接收消息 im:message
- 测试时可使用飞书测试企业自建应用

### 环境变量配置
```env
# 飞书配置
FEISHU_APP_ID=cli_xxxx
FEISHU_APP_SECRET=xxxx
FEISHU_VERIFICATION_TOKEN=xxxx
FEISHU_ENCRYPT_KEY=xxxx

# OpenAI 配置
OPENAI_API_KEY=sk-xxxx
```
