"""
端到端集成测试
测试完整工作流：认证 → 创建 → 配置 → 执行 → 日志
不依赖外部网络（AI/HTTP/飞书均 Mock）
"""
import pytest
import json
from unittest.mock import patch, AsyncMock


class TestAuthToExecutionE2E:
    """认证到执行完整流程 E2E 测试"""

    def test_full_user_journey_register_login_create_workflow(
        self, client, db
    ):
        """完整用户旅程：注册 → 登录 → 创建工作流"""
        # 1. 注册
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "e2e_user",
                "email": "e2e@example.com",
                "password": "SecurePass123"
            }
        )
        assert register_response.status_code == 201
        assert register_response.json()["username"] == "e2e_user"

        # 2. 登录
        login_response = client.post(
            "/api/auth/login",
            json={"username": "e2e_user", "password": "SecurePass123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 创建工作流
        workflow_response = client.post(
            "/api/workflows",
            json={
                "name": "E2E测试工作流",
                "description": "端到端测试",
                "trigger_config": {"type": "manual"},
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {"id": "a1", "type": "ai_task", "name": "AI任务", "config": {
                        "model": "gpt-4o-mini",
                        "prompt": "总结：{{input}}",
                        "temperature": 0.7
                    }}
                ]
            },
            headers=headers
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # 4. 验证工作流已创建
        get_response = client.get(f"/api/workflows/{workflow_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "E2E测试工作流"

    def test_workflow_publish_and_execute_e2e(
        self, client, auth_headers, db
    ):
        """工作流发布并执行 E2E"""
        # 创建并发布工作流
        create_response = client.post(
            "/api/workflows",
            json={
                "name": "执行测试工作流",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {"id": "a1", "type": "ai_task", "name": "AI", "config": {
                        "model": "gpt-4o-mini",
                        "prompt": "hello {{input}}"
                    }}
                ]
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]

        # 发布
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "published"

        # 执行（Mock AI 服务）
        with patch("app.services.execution_service.ai_service.execute_ai_task", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"result": "Mock AI response", "model": "gpt-4o-mini", "usage": {}}

            execute_response = client.post(
                f"/api/workflows/{workflow_id}/execute",
                json={"trigger_input": {"input": "world"}},
                headers=auth_headers
            )
            assert execute_response.status_code == 201
            execution_data = execute_response.json()
            assert execution_data["workflow_id"] == workflow_id
            assert execution_data["trigger_type"] == "manual"
            execution_id = execution_data["id"]

            # 获取执行详情
            detail_response = client.get(
                f"/api/executions/{execution_id}",
                headers=auth_headers
            )
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["id"] == execution_id
            assert "logs" in detail

    def test_workflow_update_and_publish_e2e(
        self, client, auth_headers, db
    ):
        """工作流更新并发布 E2E"""
        # 创建空节点工作流（初始状态不可发布）
        create_response = client.post(
            "/api/workflows",
            json={"name": "待完善工作流"},
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]

        # 尝试发布 - 应该失败（没有节点）
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 400

        # 添加节点
        update_response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}}
                ]
            },
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # 再次发布 - 应该成功
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 200

    def test_workflow_lifecycle_with_executions(
        self, client, auth_headers, db
    ):
        """工作流完整生命周期 + 执行记录"""
        from app.models.execution import Execution

        # 创建
        create_response = client.post(
            "/api/workflows",
            json={
                "name": "生命周期测试",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}}
                ]
            },
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]

        # 发布
        client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)

        # 多次执行
        for i in range(3):
            with patch("app.services.execution_service.ai_service.execute_ai_task", new_callable=AsyncMock):
                mock_ai.return_value = {"result": f"run {i}"}
                client.post(
                    f"/api/workflows/{workflow_id}/execute",
                    headers=auth_headers
                )

        # 列出执行记录
        list_response = client.get(
            f"/api/workflows/{workflow_id}/executions",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 3

        # 更新工作流名称
        update_response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "生命周期测试_已更新"},
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # 删除
        delete_response = client.delete(
            f"/api/workflows/{workflow_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 204

        # 确认删除后执行记录也被清理
        list_response = client.get(
            f"/api/workflows/{workflow_id}/executions",
            headers=auth_headers
        )
        assert list_response.status_code == 404


class TestWorkflowNodeExecutionE2E:
    """工作流节点执行 E2E 测试"""

    @pytest.mark.asyncio
    async def test_ai_task_node_substitutes_variables(self, db, client, auth_headers):
        """AI 任务节点正确替换变量"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        # 创建工作流
        create_response = client.post(
            "/api/workflows",
            json={
                "name": "变量替换测试",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {
                        "id": "a1",
                        "type": "ai_task",
                        "name": "AI任务",
                        "config": {
                            "model": "gpt-4o-mini",
                            "prompt": "请总结：{{input_text}}"
                        }
                    }
                ]
            },
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        captured_prompts = []

        async def capture_prompt(*args, **kwargs):
            captured_prompts.append(kwargs.get("prompt") or args[0])
            return {"result": "done", "model": "gpt-4o-mini", "usage": {}}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock:
            mock.side_effect = capture_prompt

            execution = await execution_service.execute_workflow(
                db=db,
                workflow=workflow,
                trigger_type="manual",
                trigger_input={"input_text": "这是测试文本内容"}
            )

            assert execution.status == "success"
            assert len(captured_prompts) == 1
            assert "这是测试文本内容" in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_http_tool_node_executes_get(self, db, client, auth_headers):
        """HTTP 工具节点执行 GET 请求"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        create_response = client.post(
            "/api/workflows",
            json={
                "name": "HTTP工具测试",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {
                        "id": "http1",
                        "type": "tool",
                        "name": "HTTP请求",
                        "config": {
                            "tool_type": "http_request",
                            "method": "GET",
                            "url": "https://api.example.com/data"
                        }
                    }
                ]
            },
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = '{"status": "ok"}'
            mock_get.return_value = mock_response

            execution = await execution_service.execute_workflow(
                db=db, workflow=workflow, trigger_type="manual", trigger_input={}
            )

            assert execution.status == "success"
            mock_get.assert_called()

    @pytest.mark.asyncio
    async def test_workflow_node_execution_order(self, db, client, auth_headers):
        """工作流节点按顺序执行"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        create_response = client.post(
            "/api/workflows",
            json={
                "name": "顺序测试",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {"id": "a1", "type": "ai_task", "name": "AI-1", "config": {
                        "model": "gpt-4o-mini", "prompt": "step1"
                    }},
                    {"id": "a2", "type": "ai_task", "name": "AI-2", "config": {
                        "model": "gpt-4o-mini", "prompt": "step2"
                    }}
                ]
            },
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        execution_order = []

        async def track_execution(*args, **kwargs):
            prompt = kwargs.get("prompt", args[0] if args else "")
            execution_order.append(prompt)
            return {"result": f"done: {prompt}", "model": "gpt-4o-mini", "usage": {}}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock:
            mock.side_effect = track_execution

            execution = await execution_service.execute_workflow(
                db=db, workflow=workflow, trigger_type="manual", trigger_input={}
            )

            assert execution.status == "success"
            # 2 个 AI 节点都执行了
            assert len(execution_order) == 2


class TestSchedulerE2E:
    """定时触发器 E2E 测试"""

    def test_cron_trigger_workflow_flow(
        self, client, auth_headers, db
    ):
        """定时触发工作流配置流程"""
        # 创建带 CRON 触发器的工作流
        create_response = client.post(
            "/api/workflows",
            json={
                "name": "定时工作流",
                "trigger_config": {
                    "type": "cron",
                    "expression": "0 9 * * 1-5",
                    "timezone": "Asia/Shanghai"
                },
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {
                        "type": "cron",
                        "expression": "0 9 * * 1-5",
                        "timezone": "Asia/Shanghai"
                    }}
                ]
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]

        # 发布
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 200

        # 更新触发配置
        update_response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={
                "trigger_config": {
                    "type": "cron",
                    "expression": "0 */2 * * *",
                    "timezone": "Asia/Shanghai"
                }
            },
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["trigger_config"]["expression"] == "0 */2 * * *"


class TestDataIsolationE2E:
    """数据隔离 E2E 测试"""

    def test_multi_user_workflow_isolation(
        self, client, auth_headers, auth_headers2, db
    ):
        """多用户工作流数据完全隔离"""
        # 用户1 创建工作流
        u1_response = client.post(
            "/api/workflows",
            json={"name": "用户1的工作流"},
            headers=auth_headers
        )
        u1_workflow_id = u1_response.json()["id"]

        # 用户2 创建工作流
        u2_response = client.post(
            "/api/workflows",
            json={"name": "用户2的工作流"},
            headers=auth_headers2
        )
        u2_workflow_id = u2_response.json()["id"]

        # 用户1 列出工作流 - 只能看到自己的
        u1_list = client.get("/api/workflows", headers=auth_headers)
        u1_names = [w["name"] for w in u1_list.json()["items"]]
        assert "用户1的工作流" in u1_names
        assert "用户2的工作流" not in u1_names

        # 用户2 列出工作流 - 只能看到自己的
        u2_list = client.get("/api/workflows", headers=auth_headers2)
        u2_names = [w["name"] for w in u2_list.json()["items"]]
        assert "用户2的工作流" in u2_names
        assert "用户1的工作流" not in u2_names

        # 用户1 无法访问用户2的工作流
        cross_access = client.get(f"/api/workflows/{u2_workflow_id}", headers=auth_headers)
        assert cross_access.status_code == 404

        # 用户2 无法访问用户1的工作流
        cross_access = client.get(f"/api/workflows/{u1_workflow_id}", headers=auth_headers2)
        assert cross_access.status_code == 404


class TestErrorRecoveryE2E:
    """错误恢复 E2E 测试"""

    @pytest.mark.asyncio
    async def test_workflow_continues_after_ai_failure(
        self, client, auth_headers, db
    ):
        """AI 节点失败时工作流标记为失败"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        create_response = client.post(
            "/api/workflows",
            json={
                "name": "AI失败测试",
                "nodes": [
                    {"id": "t1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
                    {"id": "a1", "type": "ai_task", "name": "AI任务", "config": {
                        "model": "gpt-4o-mini", "prompt": "fail"
                    }}
                ]
            },
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        # Mock AI 服务抛出异常
        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock:
            import httpx
            mock.side_effect = httpx.HTTPStatusError(
                "API Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )

            execution = await execution_service.execute_workflow(
                db=db, workflow=workflow, trigger_type="manual", trigger_input={}
            )

            assert execution.status == "failed"
            assert execution.error_message is not None
            assert "500" in execution.error_message or "API" in execution.error_message

    @pytest.mark.asyncio
    async def test_workflow_empty_nodes_handling(
        self, client, auth_headers, db
    ):
        """空节点工作流执行失败"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        create_response = client.post(
            "/api/workflows",
            json={"name": "空节点工作流", "nodes": []},
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        execution = await execution_service.execute_workflow(
            db=db, workflow=workflow, trigger_type="manual", trigger_input={}
        )

        assert execution.status == "failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
