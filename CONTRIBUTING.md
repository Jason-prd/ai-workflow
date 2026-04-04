# 🤝 贡献指南

感谢你有意为 AI 自动化工作流 项目做出贡献！本文档将帮助你了解如何参与项目贡献。

---

## 📋 贡献方式

### 🐛 报告 Bug
- 前往 [Issue 页面](https://github.com/Jason-prd/ai-workflow/issues)
- 选择 **Bug Report** 模板
- 提供详细的复现步骤、环境信息和建议

### 💡 提出功能建议
- 前往 [Issue 页面](https://github.com/Jason-prd/ai-workflow/issues)
- 选择 **Feature Request** 模板
- 清晰描述功能需求和使用场景

### 🔧 提交代码
- Fork 仓库
- 创建特性分支
- 提交 Pull Request

---

## 🔨 开发环境搭建

### 前置条件

| 工具 | 版本要求 |
|------|----------|
| Python | 3.11+ |
| Node.js | 18+ |
| Git | 最新版 |
| Docker | 24+（可选） |

### 后端开发

```bash
# 克隆你的 Fork
git clone https://github.com/YOUR_USERNAME/ai-workflow.git
cd ai-workflow

# 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
cd backend
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入实际配置

# 启动开发服务器（热重载）
python -m uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 访问 http://localhost:5173
```

### 运行测试

```bash
# 后端测试
cd backend
pip install -r requirements.txt        # 确保测试依赖已安装
pytest -v                              # 运行所有测试
pytest -v tests/test_ai_service.py     # 运行指定测试

# 前端测试
cd frontend
npm run test
```

---

## 📐 代码规范

### Commit 格式

```
<type>: <描述>

可选的详细说明
```

**Type 类型：**

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加飞书日历触发器` |
| `fix` | Bug 修复 | `fix: 修复 AI 任务节点超时问题` |
| `docs` | 文档更新 | `docs: 更新 API 文档` |
| `style` | 代码格式（不影响功能） | `style: 格式化 import 语句` |
| `refactor` | 重构 | `refactor: 重构执行引擎结构` |
| `test` | 测试相关 | `test: 添加执行引擎集成测试` |
| `chore` | 构建/工具相关 | `chore: 升级 pytest 版本` |

### Python 代码规范

- 遵循 **PEP 8**
- 使用 **Black** 格式化代码：`black app/`
- 使用 **isort** 排序 import：`isort app/`
- 类型注解：所有公共函数应包含类型注解

```python
# Good
def execute_workflow(workflow_id: int, trigger_input: dict) -> ExecutionResponse:
    ...

# Bad
def execute_workflow(workflow_id, trigger_input):
    ...
```

### 前端代码规范

- 遵循项目 ESLint + Prettier 配置
- 使用 **TypeScript** 进行类型安全开发
- 组件文件使用 PascalCase：`WorkflowCard.tsx`
- Hooks 使用 camelCase 以 `use` 开头：`useWorkflowStore.ts`

---

## 🔀 分支管理

```
main          # 稳定版本，用于发布
├── develop   # 开发主分支（可选）
├── feature/  # 功能开发分支
├── fix/      # Bug 修复分支
└── docs/     # 文档更新分支
```

**命名规范：**
- `feature/ai-task-node` — 新功能
- `fix/execution-timeout` — Bug 修复
- `docs/api-readme` — 文档更新

---

## 🔍 Pull Request 流程

1. **Fork 仓库**（如果还没有）

2. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **开发并测试**
   ```bash
   # 开发你的功能
   # 编写/更新测试
   pytest -v  # 确保所有测试通过
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m 'feat: 添加 xxx 功能'
   git push origin feature/your-feature-name
   ```

5. **创建 Pull Request**
   - 前往 GitHub 仓库页面
   - 点击 **New Pull Request**
   - 选择你的分支，描述你的改动
   - 关联相关 Issue（如果有）

6. **等待 Review**
   - 维护者会 Review 你的代码
   - 可能需要做一些修改
   - 合并后你的代码将被纳入主分支

---

## 🧪 测试要求

所有新功能**必须**包含测试：

- **后端**：使用 `pytest`，覆盖率不应低于 80%
- **前端**：使用 React Testing Library 或 Vitest

```python
# tests/test_your_feature.py
import pytest
from app.services.your_service import your_function

def test_your_feature():
    result = your_function(input_data)
    assert result == expected_output
```

---

## 📖 文档要求

新增功能请同步更新文档：

- API 变更 → 更新 `docs/API接口文档.md`
- 新增配置项 → 更新 `.env.example` 和 README
- 新增节点类型 → 更新 README 中的节点类型说明

---

## ❓ 常见问题

**Q: 开发时遇到依赖安装失败？**
```bash
# 确保使用 Python 3.11+
python --version

# 尝试使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: 前端无法启动？**
```bash
# 清除 node_modules 重新安装
cd frontend
rm -rf node_modules
npm install
npm run dev
```

**Q: 测试失败？**
```bash
# 查看详细错误
pytest -v --tb=long

# 运行单个测试文件
pytest tests/test_xxx.py -v
```

---

## 📬 联系方式

- GitHub Issues: https://github.com/Jason-prd/ai-workflow/issues
- 仓库地址: https://github.com/Jason-prd/ai-workflow

---

再次感谢你的贡献！ 🎉
