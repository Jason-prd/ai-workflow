# V2EX 推广内容

> 运营负责人：Sam  
> 创建日期：2026-04-05  
> 发布平台：v2ex.com/?tab=develop

---

## 资源分享帖（推荐首发）

**标题：**
```
[开源] AI 自动化工作流 — 拖拽设计 GPT 工作流，支持飞书集成，已支持 Docker 部署
```

**正文：**

```
大家好，分享一个我最近做的开源项目：AI 自动化工作流

GitHub：https://github.com/Jason-prd/ai-workflow
Stars：正在努力从 0 开始 (；′⌒`)

## 这个项目做什么

低代码可视化 AI 驱动自动化工作流平台——通过拖拽节点，创建 GPT 自动化工作流，无需编程。

## 核心功能

🤖 AI 任务节点
  - 支持 GPT-4o / GPT-4o-mini
  - Prompt 模板支持 {{variable}} 变量占位符
  - Temperature / Max Tokens 灵活配置

🔔 触发方式
  - 手动触发（点击按钮执行）
  - CRON 定时触发（支持任意 cron 表达式）

📤 工具节点
  - 飞书消息（文本/卡片，推送到群或个人）
  - 飞书文档（自动创建/读取飞书云文档）
  - HTTP 请求（集成任意 RESTful API）

🔀 条件分支
  - If / Else 逻辑判断，决定工作流执行分支

📋 执行日志
  - 节点级输入/输出日志
  - 执行状态实时追踪（Pending → Running → Success/Failed）
  - 失败节点自动重试（1次）

## 差异化亮点

🇨🇳 国内首个飞书深度集成的开源 AI 工作流平台
  - 飞书消息触发器（关键词/群 ID 匹配）
  - 飞书日历触发器（提前 N 分钟提醒）
  - 执行结果推送（卡片消息到群）
  - 自动创建/读取飞书云文档

## 快速开始

一行命令启动：
$ git clone https://github.com/Jason-prd/ai-workflow.git
$ cd ai-workflow/backend
$ docker compose up -d

然后访问 http://localhost 即可

## 技术栈

后端：FastAPI + SQLAlchemy + Pydantic v2 + JWT
前端：React 18 + TypeScript + @xyflow/react + Ant Design + TailwindCSS
部署：Docker Compose（开箱即用）

## 适用场景

📊 运营自动化 — 自动生成周报/月报，数据汇总分析
📝 HR 工作流 — 简历初筛、面试安排提醒
🌐 跨境电商 — 商品 listing 多语言优化、多平台发布
🔧 个人效率 — 跨系统 API 集成、定时任务自动化
👥 团队协作 — 工作流自动化、审批流程

## 开源生态

✅ MIT License
✅ CONTRIBUTING.md（贡献指南）
✅ SECURITY.md（安全漏洞报告政策）
✅ .github/ISSUE_TEMPLATE.md（Bug Report / Feature Request 模板）
✅ GitHub Actions CI/CD

## 求 Star 互助

如果你觉得这个项目有意思，求给个 ⭐ 支持一下！
你的 Star 是我持续更新的最大动力 🙏

也欢迎提 Issue 和 PR，一起完善这个项目！

有什么问题评论区见～
```

---

## 求 Star 互助帖（可选）

**标题：**
```
[开源] AI Workflow 求 Star，互助 Star 来吗？🙋
```

**正文：**

```
大家好，我的开源项目 AI 自动化工作流刚发布一周，目前 Stars: 0 (；′⌒`)

项目地址：https://github.com/Jason-prd/ai-workflow

功能已经比较完整（拖拽设计器 + GPT 节点 + 飞书集成 + Docker 部署），欢迎来玩！

本贴互助规则：
- 你给我 Star，我给你回 Star（回必回）
- 评论区留下你的 GitHub 地址和项目简介
- 我 Star 完之后会 @ 你确认

希望和大家互相支持，一起成长 💪

（纯互助非营销，项目是真的好用，信我）
```

---

## 注意事项

1. **V2EX 社区重视真实反馈**，避免纯营销语气，帖子要体现真实使用感受
2. **不要刷屏发帖**，同一内容间隔至少 1 周
3. **及时回复评论**，解答技术问题，建立信任
4. **更新进度**，有新的 Release 或功能更新时在帖子下更新
