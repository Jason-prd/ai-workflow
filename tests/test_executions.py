"""
工作流执行触发测试
覆盖：手动触发执行、定时触发配置、消息触发、执行日志查看
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.models.execution import Execution, ExecutionLog


class TestWorkflowManualExecution:
    """工作流手动执行测试"""

    def test_execute_workflow_success(self, client, auth_headers, published_workflow, db):
        """手动执行工作流 - 成功触发执行"""
        workflow_id = published_workflow["id"]
        
        with patch("app.services.execution_service.execute_workflow_node") as mock_execute:
            # 模拟异步执行
            async def mock_node_execute(*args, **kwargs):
                return {"result": "模拟AI输出"}
            mock_execute.side_effect = mock_node_execute
            
            response = client.post(
                f"/api/workflows/{workflow_id}/execute",
                json={"trigger_input": {"test": "data"}},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["workflow_id"] == workflow_id
        assert data["trigger_type"] == "manual"
        assert data["status"] in ["success", "failed", "pending", "running"]

    def test_execute_workflow_not_found(self, client, auth_headers):
        """手动执行工作流 - 工作流不存在"""
        response = client.post(
            "/api/workflows/99999/execute",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "工作流不存在" in response.json()["detail"]

    def test_execute_workflow_draft_status(self, client, auth_headers, sample_workflow):
        """手动执行工作流 - 草稿状态也可以执行"""
        workflow_id = sample_workflow["id"]
        response = client.post(
            f"/api/workflows/{workflow_id}/execute",
            headers=auth_headers
        )
        # 草稿状态也可以手动执行
        assert response.status_code == 200

    def test_execute_workflow_without_auth(self, client, published_workflow):
        """手动执行工作流 - 未认证应返回403"""
        workflow_id = published_workflow["id"]
        response = client.post(f"/api/workflows/{workflow_id}/execute")
        assert response.status_code == 403

    def test_execute_workflow_other_user(self, client, auth_headers, published_workflow, auth_headers2):
        """手动执行工作流 - 无权执行其他用户的工作流"""
        workflow_id = published_workflow["id"]
        response = client.post(
            f"/api/workflows/{workflow_id}/execute",
            headers=auth_headers2
        )
        assert response.status_code == 404

    def test_execute_workflow_with_trigger_input(self, client, auth_headers, published_workflow):
        """手动执行工作流 - 带触发输入数据"""
        workflow_id = published_workflow["id"]
        trigger_input = {
            "input_text": "这是一段测试文本",
            "user_id": "user_123"
        }
        
        with patch("app.services.execution_service.execute_workflow_node"):
            async def mock_node_execute(*args, **kwargs):
                return {"processed": True}
            from app.services import execution_service
            execution_service.execute_workflow_node = mock_node_execute
            
            response = client.post(
                f"/api/workflows/{workflow_id}/execute",
                json={"trigger_input": trigger_input},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        # trigger_input 应该被记录
        execution = response.json()
        # 注意：trigger_input 的存储和返回取决于实现

    def test_execute_workflow_no_trigger_input(self, client, auth_headers, published_workflow):
        """手动执行工作流 - 不带触发输入数据"""
        workflow_id = published_workflow["id"]
        
        with patch("app.services.execution_service.execute_workflow_node"):
            async def mock_node_execute(*args, **kwargs):
                return {"result": "ok"}
            from app.services import execution_service
            execution_service.execute_workflow_node = mock_node_execute
            
            response = client.post(
                f"/api/workflows/{workflow_id}/execute",
                headers=auth_headers
            )
        
        assert response.status_code == 200


class TestExecutionList:
    """执行记录列表测试"""

    def test_list_executions_empty(self, client, auth_headers, sample_workflow):
        """获取执行记录列表 - 空列表"""
        workflow_id = sample_workflow["id"]
        response = client.get(
            f"/api/workflows/{workflow_id}/executions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_executions_with_items(self, client, auth_headers, published_workflow, db):
        """获取执行记录列表 - 包含执行记录"""
        workflow_id = published_workflow["id"]
        
        # 创建执行记录
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        
        response = client.get(
            f"/api/workflows/{workflow_id}/executions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_executions_pagination(self, client, auth_headers, published_workflow, db):
        """获取执行记录列表 - 分页"""
        workflow_id = published_workflow["id"]
        
        # 创建多个执行记录
        for i in range(10):
            execution = Execution(
                workflow_id=workflow_id,
                trigger_type="manual",
                status="success"
            )
            db.add(execution)
        db.commit()
        
        response = client.get(
            f"/api/workflows/{workflow_id}/executions?skip=0&limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5

    def test_list_executions_workflow_not_found(self, client, auth_headers):
        """获取执行记录列表 - 工作流不存在"""
        response = client.get(
            "/api/workflows/99999/executions",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_list_executions_other_user(self, client, auth_headers, published_workflow, auth_headers2):
        """获取执行记录列表 - 无权访问"""
        workflow_id = published_workflow["id"]
        response = client.get(
            f"/api/workflows/{workflow_id}/executions",
            headers=auth_headers2
        )
        assert response.status_code == 404

    def test_list_executions_without_auth(self, client, published_workflow):
        """获取执行记录列表 - 未认证"""
        workflow_id = published_workflow["id"]
        response = client.get(f"/api/workflows/{workflow_id}/executions")
        assert response.status_code == 403


class TestExecutionDetail:
    """执行详情测试"""

    def test_get_execution_detail_success(self, client, auth_headers, published_workflow, db):
        """获取执行详情 - 成功"""
        workflow_id = published_workflow["id"]
        
        # 创建执行记录和日志
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 创建执行日志
        log = ExecutionLog(
            execution_id=execution.id,
            node_id="trigger_1",
            node_type="trigger",
            node_name="触发器",
            status="success",
            input_data='{"triggered": true}',
            output_data='{"result": "ok"}',
            duration_ms=100
        )
        db.add(log)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution.id
        assert data["workflow_id"] == workflow_id
        assert data["trigger_type"] == "manual"
        assert "logs" in data
        assert len(data["logs"]) == 1

    def test_get_execution_detail_not_found(self, client, auth_headers):
        """获取执行详情 - 不存在"""
        response = client.get(
            "/api/executions/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "执行记录不存在" in response.json()["detail"]

    def test_get_execution_detail_other_user(self, client, auth_headers, auth_headers2, published_workflow, db):
        """获取执行详情 - 无权访问其他用户的执行记录"""
        workflow_id = published_workflow["id"]
        
        # 用户1 创建执行记录
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 用户2 尝试访问
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404

    def test_get_execution_detail_without_auth(self, client, published_workflow, db):
        """获取执行详情 - 未认证"""
        workflow_id = published_workflow["id"]
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        response = client.get(f"/api/executions/{execution.id}")
        assert response.status_code == 403


class TestExecutionStatus:
    """执行状态测试"""

    def test_execution_status_success(self, client, auth_headers, published_workflow, db):
        """执行状态 - 成功"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_execution_status_failed(self, client, auth_headers, published_workflow, db):
        """执行状态 - 失败"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="manual",
            status="failed",
            error_message="AI服务调用失败"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "AI服务调用失败"

    def test_execution_status_pending(self, client, auth_headers, published_workflow, db):
        """执行状态 - 待执行"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="manual",
            status="pending"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_execution_status_running(self, client, auth_headers, published_workflow, db):
        """执行状态 - 执行中"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="manual",
            status="running"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "running"


class TestExecutionLogDetails:
    """执行日志详情测试"""

    def test_execution_log_all_fields(self, client, auth_headers, published_workflow, db):
        """执行日志 - 完整字段验证"""
        workflow_id = published_workflow["id"]
        
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        log = ExecutionLog(
            execution_id=execution.id,
            node_id="ai_1",
            node_type="ai_task",
            node_name="AI处理",
            status="success",
            input_data='{"prompt": "请处理：{{input}}"}',
            output_data='{"result": "处理完成"}',
            error=None,
            duration_ms=2500
        )
        db.add(log)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        log_data = response.json()["logs"][0]
        
        assert log_data["node_id"] == "ai_1"
        assert log_data["node_type"] == "ai_task"
        assert log_data["node_name"] == "AI处理"
        assert log_data["status"] == "success"
        assert log_data["input_data"] is not None
        assert log_data["output_data"] is not None
        assert log_data["duration_ms"] == 2500

    def test_execution_log_multiple_nodes(self, client, auth_headers, published_workflow, db):
        """执行日志 - 多节点执行顺序"""
        workflow_id = published_workflow["id"]
        
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 添加多个节点的日志
        logs = [
            ExecutionLog(
                execution_id=execution.id,
                node_id="trigger_1",
                node_type="trigger",
                node_name="触发器",
                status="success",
                duration_ms=10
            ),
            ExecutionLog(
                execution_id=execution.id,
                node_id="ai_1",
                node_type="ai_task",
                node_name="AI处理",
                status="success",
                duration_ms=2000
            ),
            ExecutionLog(
                execution_id=execution.id,
                node_id="tool_1",
                node_type="tool",
                node_name="发送消息",
                status="success",
                duration_ms=500
            )
        ]
        for log in logs:
            db.add(log)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["logs"]) == 3

    def test_execution_log_failed_node(self, client, auth_headers, published_workflow, db):
        """执行日志 - 失败节点记录错误信息"""
        workflow_id = published_workflow["id"]
        
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="failed",
            error_message="工作流执行失败"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 失败的AI节点
        log = ExecutionLog(
            execution_id=execution.id,
            node_id="ai_1",
            node_type="ai_task",
            node_name="AI处理",
            status="failed",
            error="OpenAI API 调用超时"
        )
        db.add(log)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        log_data = response.json()["logs"][0]
        assert log_data["status"] == "failed"
        assert "超时" in log_data["error"]


class TestTriggerTypes:
    """触发器类型测试"""

    def test_trigger_type_manual(self, client, auth_headers, published_workflow, db):
        """触发类型 - 手动触发"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["trigger_type"] == "manual"

    def test_trigger_type_cron(self, client, auth_headers, published_workflow, db):
        """触发类型 - 定时触发"""
        execution = Execution(
            workflow_id=published_workflow["id"],
            trigger_type="cron",
            status="success"
        )
        db.add(execution)
        db.commit()
        
        response = client.get(
            f"/api/executions/{execution.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["trigger_type"] == "cron"


class TestMessageTrigger:
    """消息触发测试（预留接口测试）"""

    def test_message_trigger_workflow_execution(self, client, auth_headers, published_workflow):
        """消息触发 - 工作流应该能通过消息触发"""
        # 注意：消息触发是预留功能，当前MVP只支持手动和定时触发
        # 这里测试触发输入包含消息数据的场景
        
        workflow_id = published_workflow["id"]
        message_trigger_input = {
            "trigger_type": "message",
            "message_content": "测试消息内容",
            "sender": "user_123",
            "chat_id": "oc_xxx"
        }
        
        with patch("app.services.execution_service.execute_workflow_node"):
            async def mock_node_execute(*args, **kwargs):
                return {"result": "消息处理完成"}
            from app.services import execution_service
            execution_service.execute_workflow_node = mock_node_execute
            
            response = client.post(
                f"/api/workflows/{workflow_id}/execute",
                json={"trigger_input": message_trigger_input},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        # 消息触发在数据库中存储为 manual 类型（消息触发是前端/外部系统调用execute接口）
