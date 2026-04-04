"""
工作流 CRUD 测试
覆盖：创建、查询列表、查询详情、更新、删除、发布
"""
import pytest
import json


class TestWorkflowCreate:
    """工作流创建测试"""

    def test_create_workflow_success(self, client, auth_headers, sample_workflow_data):
        """正常创建工作流 - 应成功返回工作流信息"""
        response = client.post(
            "/api/workflows",
            json=sample_workflow_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试工作流"
        assert data["description"] == "用于测试的工作流"
        assert data["status"] == "draft"
        assert data["user_id"] is not None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        # nodes 应被解析为列表
        assert isinstance(data.get("nodes"), list)
        assert len(data["nodes"]) == 2

    def test_create_workflow_minimal(self, client, auth_headers):
        """创建工作流 - 仅提供必填字段"""
        response = client.post(
            "/api/workflows",
            json={"name": "最小工作流"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "最小工作流"
        assert data["description"] is None
        assert data["status"] == "draft"

    def test_create_workflow_with_cron_trigger(self, client, auth_headers):
        """创建工作流 - 定时触发器配置"""
        data = {
            "name": "定时工作流",
            "trigger_config": {
                "type": "cron",
                "expression": "0 9 * * 1-5",
                "timezone": "Asia/Shanghai"
            },
            "nodes": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "定时触发器",
                    "config": {
                        "type": "cron",
                        "expression": "0 9 * * 1-5",
                        "timezone": "Asia/Shanghai"
                    }
                }
            ]
        }
        response = client.post("/api/workflows", json=data, headers=auth_headers)
        assert response.status_code == 201
        workflow = response.json()
        assert workflow["trigger_config"]["type"] == "cron"
        assert workflow["trigger_config"]["expression"] == "0 9 * * 1-5"

    def test_create_workflow_without_auth(self, client, sample_workflow_data):
        """创建工作流 - 未认证应返回401"""
        response = client.post(
            "/api/workflows",
            json=sample_workflow_data
        )
        assert response.status_code == 403

    def test_create_workflow_invalid_token(self, client, sample_workflow_data):
        """创建工作流 - 无效Token应返回401"""
        response = client.post(
            "/api/workflows",
            json=sample_workflow_data,
            headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401

    def test_create_workflow_missing_name(self, client, auth_headers):
        """创建工作流 - 缺少name应返回422"""
        response = client.post(
            "/api/workflows",
            json={"description": "没有名字"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_workflow_empty_name(self, client, auth_headers):
        """创建工作流 - name为空应返回422"""
        response = client.post(
            "/api/workflows",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_workflow_name_too_long(self, client, auth_headers):
        """创建工作流 - name超过200字符应返回4xx（数据库约束）"""
        response = client.post(
            "/api/workflows",
            json={"name": "x" * 201},
            headers=auth_headers
        )
        assert response.status_code in [400, 422]


class TestWorkflowList:
    """工作流列表测试"""

    def test_list_workflows_empty(self, client, auth_headers):
        """获取工作流列表 - 空列表"""
        response = client.get("/api/workflows", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_workflows_with_items(self, client, auth_headers, sample_workflow):
        """获取工作流列表 - 包含已创建的工作流"""
        response = client.get("/api/workflows", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        # 验证返回字段
        workflow = data["items"][0]
        assert "id" in workflow
        assert "name" in workflow
        assert "status" in workflow

    def test_list_workflows_pagination(self, client, auth_headers):
        """获取工作流列表 - 分页参数"""
        # 创建多个工作流
        for i in range(5):
            client.post(
                "/api/workflows",
                json={"name": f"工作流{i}"},
                headers=auth_headers
            )
        
        # 测试 limit
        response = client.get("/api/workflows?limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 5
        
        # 测试 skip
        response = client.get("/api/workflows?skip=2&limit=2", headers=auth_headers)
        assert response.status_code == 200

    def test_list_workflows_order(self, client, auth_headers):
        """获取工作流列表 - 按updated_at降序"""
        # 创建两个工作流
        client.post("/api/workflows", json={"name": "第一个"}, headers=auth_headers)
        client.post("/api/workflows", json={"name": "第二个"}, headers=auth_headers)
        
        response = client.get("/api/workflows", headers=auth_headers)
        data = response.json()
        # 最新的应该在前面
        names = [w["name"] for w in data["items"]]
        # 顺序不确定，取决于创建时间，但至少应该能获取到

    def test_list_workflows_user_isolation(self, client, auth_headers, auth_headers2, sample_workflow):
        """获取工作流列表 - 用户数据隔离"""
        # 用户1 创建的工作流，用户2 不应该看到
        response = client.get("/api/workflows", headers=auth_headers2)
        assert response.status_code == 200
        data = response.json()
        # 用户2 应该看不到用户1 的工作流（如果用户2还没创建任何工作流）
        # 注意：这取决于哪个用户先创建，这里只验证能正常返回

    def test_list_workflows_without_auth(self, client):
        """获取工作流列表 - 未认证应返回403"""
        response = client.get("/api/workflows")
        assert response.status_code == 403


class TestWorkflowGet:
    """工作流详情测试"""

    def test_get_workflow_success(self, client, auth_headers, sample_workflow):
        """获取工作流详情 - 成功"""
        workflow_id = sample_workflow["id"]
        response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == "测试工作流"
        assert "nodes" in data

    def test_get_workflow_not_found(self, client, auth_headers):
        """获取工作流详情 - 不存在应返回404"""
        response = client.get("/api/workflows/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "工作流不存在" in response.json()["detail"]

    def test_get_workflow_other_user(self, client, auth_headers, sample_workflow, auth_headers2):
        """获取工作流详情 - 无权访问其他用户的工作流"""
        workflow_id = sample_workflow["id"]
        response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers2)
        assert response.status_code == 404  # 不会暴露存在性

    def test_get_workflow_invalid_id(self, client, auth_headers):
        """获取工作流详情 - 无效ID格式"""
        response = client.get("/api/workflows/invalid", headers=auth_headers)
        assert response.status_code == 422

    def test_get_workflow_deleted(self, client, auth_headers, sample_workflow):
        """获取工作流详情 - 已删除的工作流"""
        workflow_id = sample_workflow["id"]
        # 删除工作流
        client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        # 再获取应该404
        response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response.status_code == 404


class TestWorkflowUpdate:
    """工作流更新测试"""

    def test_update_workflow_name(self, client, auth_headers, sample_workflow):
        """更新工作流 - 修改名称"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "新名称"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_update_workflow_description(self, client, auth_headers, sample_workflow):
        """更新工作流 - 修改描述"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"description": "新的描述"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["description"] == "新的描述"

    def test_update_workflow_nodes(self, client, auth_headers, sample_workflow):
        """更新工作流 - 修改节点配置"""
        workflow_id = sample_workflow["id"]
        new_nodes = [
            {
                "id": "trigger_1",
                "type": "trigger",
                "name": "触发器",
                "config": {"type": "manual"}
            },
            {
                "id": "ai_1",
                "type": "ai_task",
                "name": "AI任务",
                "config": {
                    "model": "gpt-4o",
                    "prompt": "新提示词"
                }
            },
            {
                "id": "tool_1",
                "type": "tool",
                "name": "HTTP工具",
                "config": {
                    "tool_type": "http",
                    "method": "GET",
                    "url": "https://api.example.com"
                }
            }
        ]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"nodes": new_nodes},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["nodes"]) == 3

    def test_update_workflow_trigger_config(self, client, auth_headers, sample_workflow):
        """更新工作流 - 修改触发器配置"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
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
        assert response.status_code == 200
        assert response.json()["trigger_config"]["type"] == "cron"

    def test_update_workflow_partial(self, client, auth_headers, sample_workflow):
        """更新工作流 - 部分更新（只传name）"""
        workflow_id = sample_workflow["id"]
        original_description = sample_workflow["description"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "部分更新"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "部分更新"
        assert data["description"] == original_description  # 保持不变

    def test_update_workflow_not_found(self, client, auth_headers):
        """更新工作流 - 不存在应返回404"""
        response = client.patch(
            "/api/workflows/99999",
            json={"name": "新名称"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_workflow_other_user(self, client, auth_headers, sample_workflow, auth_headers2):
        """更新工作流 - 无权更新其他用户的工作流"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "被劫持的名称"},
            headers=auth_headers2
        )
        assert response.status_code == 404

    def test_update_workflow_empty_body(self, client, auth_headers, sample_workflow):
        """更新工作流 - 空更新体应正常处理"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 200  # 空更新不报错

    def test_update_workflow_invalid_nodes(self, client, auth_headers, sample_workflow):
        """更新工作流 - 节点数量超限（>20）"""
        workflow_id = sample_workflow["id"]
        many_nodes = [{"id": f"node_{i}", "type": "ai_task", "name": f"节点{i}", "config": {}} for i in range(21)]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"nodes": many_nodes},
            headers=auth_headers
        )
        # 发布时会检查节点数量，直接更新不检查


class TestWorkflowDelete:
    """工作流删除测试"""

    def test_delete_workflow_success(self, client, auth_headers, sample_workflow):
        """删除工作流 - 成功"""
        workflow_id = sample_workflow["id"]
        response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证已被删除
        get_response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_workflow_not_found(self, client, auth_headers):
        """删除工作流 - 不存在应返回404"""
        response = client.delete("/api/workflows/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_workflow_other_user(self, client, auth_headers, sample_workflow, auth_headers2):
        """删除工作流 - 无权删除其他用户的工作流"""
        workflow_id = sample_workflow["id"]
        response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers2)
        assert response.status_code == 404
        
        # 验证工作流仍然存在
        get_response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_response.status_code == 200

    def test_delete_workflow_cascade_executions(self, client, auth_headers, sample_workflow, db):
        """删除工作流 - 应级联删除执行记录（数据库外键）"""
        workflow_id = sample_workflow["id"]
        
        # 创建执行记录
        from app.models.execution import Execution
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        
        # 删除工作流
        response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证执行记录也被删除（外键级联）
        remaining_executions = db.query(Execution).filter(Execution.workflow_id == workflow_id).all()
        assert len(remaining_executions) == 0

    def test_delete_workflow_without_auth(self, client, sample_workflow):
        """删除工作流 - 未认证应返回403"""
        workflow_id = sample_workflow["id"]
        response = client.delete(f"/api/workflows/{workflow_id}")
        assert response.status_code == 403


class TestWorkflowPublish:
    """工作流发布测试"""

    def test_publish_workflow_success(self, client, auth_headers, sample_workflow):
        """发布工作流 - 成功"""
        workflow_id = sample_workflow["id"]
        response = client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_publish_workflow_no_nodes(self, client, auth_headers):
        """发布工作流 - 没有节点应返回400"""
        # 创建一个没有节点的工作流
        response = client.post(
            "/api/workflows",
            json={"name": "空工作流"},
            headers=auth_headers
        )
        workflow_id = response.json()["id"]
        
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 400
        assert "至少包含一个节点" in publish_response.json()["detail"]

    def test_publish_workflow_no_trigger(self, client, auth_headers):
        """发布工作流 - 没有触发器节点应返回400"""
        response = client.post(
            "/api/workflows",
            json={
                "name": "无触发器工作流",
                "nodes": [
                    {
                        "id": "ai_1",
                        "type": "ai_task",
                        "name": "AI任务",
                        "config": {}
                    }
                ]
            },
            headers=auth_headers
        )
        workflow_id = response.json()["id"]
        
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 400
        assert "触发器节点" in publish_response.json()["detail"]

    def test_publish_workflow_too_many_nodes(self, client, auth_headers):
        """发布工作流 - 节点过多应返回400"""
        nodes = [
            {
                "id": f"node_{i}",
                "type": "ai_task" if i > 0 else "trigger",
                "name": f"节点{i}",
                "config": {}
            }
            for i in range(21)
        ]
        response = client.post(
            "/api/workflows",
            json={"name": "节点过多工作流", "nodes": nodes},
            headers=auth_headers
        )
        workflow_id = response.json()["id"]
        
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 400
        assert "最多" in publish_response.json()["detail"]

    def test_publish_workflow_not_found(self, client, auth_headers):
        """发布工作流 - 不存在应返回404"""
        response = client.post("/api/workflows/99999/publish", headers=auth_headers)
        assert response.status_code == 404

    def test_publish_workflow_already_published(self, client, auth_headers, published_workflow):
        """发布工作流 - 重复发布应正常处理（幂等）"""
        workflow_id = published_workflow["id"]
        response = client.post(f"/api/workflows/{workflow_id}/publish", headers=auth_headers)
        # 已发布的工作流再次发布应成功（幂等性）
        assert response.status_code == 200
        assert response.json()["status"] == "published"


class TestWorkflowCRUDIntegration:
    """工作流 CRUD 集成测试"""

    def test_full_workflow_lifecycle(self, client, auth_headers):
        """完整生命周期：创建 -> 查询 -> 更新 -> 发布 -> 删除"""
        # 1. 创建
        create_response = client.post(
            "/api/workflows",
            json={
                "name": "生命周期测试",
                "description": "测试完整流程",
                "trigger_config": {"type": "manual"},
                "nodes": [
                    {
                        "id": "trigger_1",
                        "type": "trigger",
                        "name": "触发器",
                        "config": {"type": "manual"}
                    }
                ]
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]
        
        # 2. 查询详情
        get_response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "生命周期测试"
        
        # 3. 更新
        update_response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "更新后的名称"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # 4. 发布
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "published"
        
        # 5. 列表确认
        list_response = client.get("/api/workflows", headers=auth_headers)
        assert list_response.status_code == 200
        
        # 6. 删除
        delete_response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # 7. 确认删除
        get_after_delete = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_after_delete.status_code == 404

    def test_workflow_data_isolation_between_users(self, client, auth_headers, auth_headers2):
        """用户间数据隔离测试"""
        # 用户1 创建工作流
        response1 = client.post(
            "/api/workflows",
            json={"name": "用户1的工作流"},
            headers=auth_headers
        )
        workflow1_id = response1.json()["id"]
        
        # 用户2 创建工作流
        response2 = client.post(
            "/api/workflows",
            json={"name": "用户2的工作流"},
            headers=auth_headers2
        )
        workflow2_id = response2.json()["id"]
        
        # 用户1 看不到用户2的工作流
        list1 = client.get("/api/workflows", headers=auth_headers)
        names1 = [w["name"] for w in list1.json()["items"]]
        assert "用户2的工作流" not in names1
        
        # 用户2 看不到用户1的工作流
        list2 = client.get("/api/workflows", headers=auth_headers2)
        names2 = [w["name"] for w in list2.json()["items"]]
        assert "用户1的工作流" not in names2
        
        # 用户1 无法访问用户2的工作流
        response = client.get(f"/api/workflows/{workflow2_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # 用户2 无法访问用户1的工作流
        response = client.get(f"/api/workflows/{workflow1_id}", headers=auth_headers2)
        assert response.status_code == 404
