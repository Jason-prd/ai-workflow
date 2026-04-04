# AI自动化工作流 - 测试套件

## 测试文件说明

```
tests/
├── conftest.py                 # pytest 配置和共享 fixtures
├── test_auth.py                # 用户认证测试（注册/登录/JWT）
├── test_workflows.py           # 工作流 CRUD 测试
├── test_executions.py          # 工作流执行触发测试
├── test_exceptions.py          # 边界条件和异常场景测试
├── test_feishu_integration.py  # 飞书集成测试（消息/日历触发、通知推送）
├── test_ai_service.py          # AI 服务层单元测试（变量替换、API 调用）
├── test_http_service.py        # HTTP 服务层单元测试
├── test_condition_evaluation.py # 条件表达式求值单元测试
├── test_integration.py         # 端到端集成测试
├── pytest.ini                  # pytest 配置
├── requirements-test.txt       # 测试依赖
└── README.md                   # 本文件
```

## 安装测试依赖

```bash
cd backend
pip install -r ../tests/requirements-test.txt
# 或者
pip install pytest pytest-asyncio httpx
```

## 运行测试

```bash
# 运行所有测试
cd D:\openclaw_ground\PROJECTS\AI自动化工作流
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_auth.py -v

# 运行特定测试类
python -m pytest tests/test_auth.py::TestUserRegistration -v

# 运行特定测试用例
python -m pytest tests/test_auth.py::TestUserRegistration::test_register_success -v

# 生成覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html
```

## 测试覆盖范围

### 1. 认证测试 (test_auth.py)
- **用户注册**: 正常注册、重复用户名、重复邮箱、字段验证、邮箱格式
- **用户登录**: 正常登录、错误密码、用户不存在、字段验证、OAuth2表单登录
- **JWT Token验证**: Token包含user_id、过期时间验证、无效签名、过期Token、格式错误Token
- **Token刷新**: 正常刷新、无效Token、用户删除后刷新
- **获取当前用户**: 成功获取、无Token、无效Token、用户删除后

### 2. 工作流 CRUD 测试 (test_workflows.py)
- **创建**: 成功创建、最小字段、带定时触发、无认证、无效Token、字段验证
- **列表**: 空列表、有数据、分页、排序、用户数据隔离
- **详情**: 成功获取、不存在、无权访问、无效ID、已删除
- **更新**: 修改名称/描述/节点/触发器、部分更新、不存在、无权访问、空更新、节点超限
- **删除**: 成功删除、不存在、无权访问、级联删除执行记录、无认证
- **发布**: 成功发布、无节点、无触发器、节点过多、不存在、重复发布

### 3. 执行触发测试 (test_executions.py)
- **手动执行**: 成功触发、工作流不存在、草稿状态执行、无认证、无权访问、带/不带触发输入
- **执行列表**: 空列表、有数据、分页、工作流不存在、无权访问
- **执行详情**: 成功获取、不存在、无权访问
- **执行状态**: success/failed/pending/running 状态
- **执行日志**: 完整字段、多节点顺序、失败节点记录
- **触发类型**: manual/cron 类型

### 4. 飞书集成测试 (test_feishu_integration.py)
- **消息触发器配置**: 关键词匹配、排除关键词、群ID过滤、聊天类型过滤
- **日历触发器配置**: 日历事件匹配、关键词过滤
- **通知构建器**: 成功/失败卡片、带输出卡片
- **事件处理器**: 消息去重、纯文本提取
- **Webhook验证**: GET/POST 端点

### 5. AI 服务层测试 (test_ai_service.py)
- **变量替换**: 简单变量、嵌套变量、多变量、缺失变量、类型转换（int/float/list）
- **execute_ai_task**: Mock OpenAI、变量替换、系统消息
- **call_openai**: 成功调用、无API Key、自定义参数、API错误

### 6. HTTP 服务层测试 (test_http_service.py)
- **HTTP方法**: GET/POST/PUT/DELETE
- **请求参数**: Headers、Body、超时
- **响应处理**: 2xx成功、4xx客户端错误、5xx服务器错误、响应头

### 7. 条件表达式求值测试 (test_condition_evaluation.py)
- **操作符**: equals/contains/starts_with/ends_with（大小写不敏感）
- **条件类型**: simple、未知类型、缺失键、空表达式
- **条件节点执行**: 满足/不满足条件、工作流串行执行

### 8. 边界条件和异常测试 (test_exceptions.py)
- **输入验证**: 名称最大长度、描述长度、节点空数组、无效JSON、CRON格式、邮箱格式
- **数据隔离**: 跨用户访问、删除后不可访问、Token失效但数据持久
- **并发限制**: 快速创建、并发执行、节点数量限制
- **错误处理**: 无效JSON、缺失字段、无效状态、数据库故障
- **安全验证**: SQL注入、XSS、Token篡改、声明操作
- **分页限制**: 负数偏移、limit为0、超过最大限制、大偏移量
- **CRUD序列**: 先删后改、双重删除、删除后更新、完整生命周期

### 9. 端到端集成测试 (test_integration.py)
- **完整用户旅程**: 注册→登录→创建工作流
- **工作流生命周期**: 创建→发布→执行→查看日志→删除
- **节点执行**: AI变量替换、HTTP GET请求、节点执行顺序
- **定时触发**: CRON配置流程
- **多用户隔离**: 完整数据隔离验证
- **错误恢复**: AI失败时工作流标记失败、空节点处理

## 测试环境配置

测试使用独立的内存SQLite数据库，不影响开发数据库。

环境变量（自动设置）:
```python
DATABASE_URL = "sqlite:///:memory:"
SECRET_KEY = "test-secret-key-for-testing-only"
OPENAI_API_KEY = "sk-test-openai-key"  # Mocked in tests
```

## 编写新测试

```python
def test_new_feature(self, client, auth_headers):
    """测试描述"""
    response = client.post(
        "/api/endpoint",
        json={"field": "value"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "expected_field" in data
```

## 常用 Fixtures

| Fixture | 说明 |
|---------|------|
| `db` | 数据库会话 |
| `client` | FastAPI TestClient |
| `test_user` | 测试用户 |
| `test_user2` | 第二个测试用户 |
| `auth_token` | 用户1的JWT token |
| `auth_headers` | 用户1的认证请求头 |
| `auth_headers2` | 用户2的认证请求头 |
| `sample_workflow_data` | 示例工作流数据 |
| `sample_workflow` | 创建的示例工作流 |
| `published_workflow` | 已发布的工作流 |
