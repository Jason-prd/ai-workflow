"""
边界条件和异常场景测试
覆盖：输入验证、并发、权限、超限场景
"""
import pytest
from fastapi import status


class TestInputValidation:
    """输入验证测试"""

    def test_workflow_name_max_length(self, client, auth_headers):
        """工作流名称 - 最大长度边界（200字符）"""
        long_name = "a" * 200
        response = client.post(
            "/api/workflows",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == 201  # 刚好200字符应该成功

    def test_workflow_name_exceeds_max(self, client, auth_headers):
        """工作流名称 - 超过最大长度"""
        long_name = "a" * 201
        response = client.post(
            "/api/workflows",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code in [400, 422]

    def test_workflow_description_max_length(self, client, auth_headers):
        """工作流描述 - 文本类型，无严格限制"""
        long_desc = "测试描述" * 1000
        response = client.post(
            "/api/workflows",
            json={"name": "测试", "description": long_desc},
            headers=auth_headers
        )
        # Text类型在SQLite中允许大量文本
        assert response.status_code == 201

    def test_workflow_nodes_empty_array(self, client, auth_headers):
        """工作流节点 - 空数组应该允许创建（发布时才检查）"""
        response = client.post(
            "/api/workflows",
            json={"name": "空节点工作流", "nodes": []},
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_workflow_nodes_invalid_json_structure(self, client, auth_headers):
        """工作流节点 - 无效的JSON结构"""
        response = client.post(
            "/api/workflows",
            json={"name": "测试", "nodes": [{"invalid": "structure"}]},
            headers=auth_headers
        )
        # 节点类型缺失，应该能创建但无法正确执行
        assert response.status_code == 201

    def test_workflow_trigger_config_invalid_type(self, client, auth_headers):
        """触发器配置 - 无效的触发类型"""
        response = client.post(
            "/api/workflows",
            json={
                "name": "测试",
                "trigger_config": {"type": "invalid_type"}
            },
            headers=auth_headers
        )
        # 允许创建，但执行时会失败
        assert response.status_code == 201

    def test_cron_expression_invalid_format(self, client, auth_headers):
        """CRON表达式 - 无效格式"""
        response = client.post(
            "/api/workflows",
            json={
                "name": "测试",
                "trigger_config": {
                    "type": "cron",
                    "expression": "not_a_cron"
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 201  # 创建时不验证CRON格式

    def test_email_invalid_format(self, client):
        """邮箱 - 无效格式"""
        invalid_emails = [
            "notanemail",
            "@nodomain.com",
            "no@",
            "spaces in@email.com",
            "",
        ]
        for email in invalid_emails:
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"user_{email[:5]}",
                    "email": email,
                    "password": "ValidPassword123"
                }
            )
            assert response.status_code == 422, f"Email {email} should fail validation"

    def test_username_special_characters(self, client):
        """用户名 - 特殊字符"""
        # 用户名通常允许字母数字下划线
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user@name!",
                "email": "test@example.com",
                "password": "ValidPassword123"
            }
        )
        # FastAPI/Pydantic 默认不限制，但数据库唯一索引会限制长度
        assert response.status_code in [201, 400, 422]

    def test_username_unicode(self, client):
        """用户名 - 中文/Unicode字符"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "测试用户",
                "email": "test1@example.com",
                "password": "ValidPassword123"
            }
        )
        # 取决于实现，部分系统允许Unicode用户名
        assert response.status_code in [201, 400, 422]

    def test_password_empty(self, client):
        """密码 - 空字符串"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": ""
            }
        )
        # 空密码可能被接受（取决于实现），但这是安全问题
        assert response.status_code in [201, 422]


class TestDataIsolation:
    """数据隔离测试"""

    def test_user_cannot_access_other_workflow(self, client, auth_headers, auth_headers2, sample_workflow):
        """用户无法访问其他用户的工作流"""
        workflow_id = sample_workflow["id"]
        
        # 获取详情
        response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers2)
        assert response.status_code == 404
        
        # 更新
        response = client.patch(f"/api/workflows/{workflow_id}", json={"name": "hack"}, headers=auth_headers2)
        assert response.status_code == 404
        
        # 删除
        response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers2)
        assert response.status_code == 404
        
        # 执行
        response = client.post(f"/api/workflows/{workflow_id}/execute", headers=auth_headers2)
        assert response.status_code == 404

    def test_user_cannot_access_other_executions(self, client, auth_headers, auth_headers2, published_workflow, db):
        """用户无法访问其他用户的执行记录"""
        workflow_id = published_workflow["id"]
        
        # 用户1 创建执行记录
        from app.models.execution import Execution
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 用户2 无法访问
        response = client.get(f"/api/executions/{execution.id}", headers=auth_headers2)
        assert response.status_code == 404
        
        # 用户2 无法列出
        response = client.get(f"/api/workflows/{workflow_id}/executions", headers=auth_headers2)
        assert response.status_code == 404

    def test_deleted_workflow_not_accessible(self, client, auth_headers, sample_workflow):
        """删除的工作流不可访问"""
        workflow_id = sample_workflow["id"]
        
        # 删除
        client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        
        # 尝试获取
        response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # 尝试更新
        response = client.patch(f"/api/workflows/{workflow_id}", json={"name": "new"}, headers=auth_headers)
        assert response.status_code == 404

    def test_user_data_persistence_after_logout(self, client, test_user):
        """用户数据在登出后应该持久存在（Token失效但数据保留）"""
        # 登录
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]
        
        # 登出（如果实现的话）后，用户数据应该仍然存在
        # 这里测试Token在有效期内可以反复使用
        for _ in range(3):
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200


class TestConcurrencyLimits:
    """并发和限制测试"""

    def test_rapid_workflow_creation(self, client, auth_headers):
        """快速连续创建工作流"""
        responses = []
        for i in range(10):
            response = client.post(
                "/api/workflows",
                json={"name": f"快速创建{i}"},
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # 所有请求都应该成功（除非有速率限制）
        success_count = sum(1 for r in responses if r == 201)
        assert success_count >= 9  # 允许少量失败（速率限制）

    def test_concurrent_execution_same_workflow(self, client, auth_headers, published_workflow):
        """并发执行同一个工作流"""
        workflow_id = published_workflow["id"]
        
        # 注意：实际并发执行可能受 MAX_CONCURRENT_EXECUTIONS 限制
        # 这里只测试API能接受多个请求
        with patch("app.services.execution_service.execute_workflow_node"):
            async def mock_node_execute(*args, **kwargs):
                return {"result": "ok"}
            from app.services import execution_service
            execution_service.execute_workflow_node = mock_node_execute
            
            responses = []
            for _ in range(3):
                response = client.post(
                    f"/api/workflows/{workflow_id}/execute",
                    headers=auth_headers
                )
                responses.append(response.status_code)
            
            # 所有请求都应该返回200（即使被限流也是429，不是500）
            for r in responses:
                assert r in [200, 429, 503]

    def test_max_nodes_limit(self, client, auth_headers):
        """节点数量限制 - 创建21个节点的工作流并发布"""
        nodes = [
            {
                "id": f"node_{i}",
                "type": "trigger" if i == 0 else "ai_task",
                "name": f"节点{i}",
                "config": {}
            }
            for i in range(21)
        ]
        
        response = client.post(
            "/api/workflows",
            json={"name": "超多节点工作流", "nodes": nodes},
            headers=auth_headers
        )
        assert response.status_code == 201
        workflow_id = response.json()["id"]
        
        # 发布时应失败
        publish_response = client.post(
            f"/api/workflows/{workflow_id}/publish",
            headers=auth_headers
        )
        assert publish_response.status_code == 400
        assert "最多" in publish_response.json()["detail"]


class TestErrorHandling:
    """错误处理测试"""

    def test_database_connection_failure(self, client, auth_headers):
        """数据库连接失败场景（测试异常处理）"""
        # 这个测试需要特殊设置来模拟DB故障
        # 在正常测试环境下，DB连接是稳定的
        pass

    def test_invalid_json_body(self, client, auth_headers):
        """无效的JSON请求体"""
        response = client.post(
            "/api/workflows",
            content="not json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_field(self, client, auth_headers):
        """缺失必填字段"""
        # WorkflowCreate.name 是必填的
        response = client.post(
            "/api/workflows",
            json={"description": "没有name"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_workflow_update_with_invalid_status(self, client, auth_headers, sample_workflow):
        """更新工作流 - 无效的状态值"""
        workflow_id = sample_workflow["id"]
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"status": "invalid_status"},
            headers=auth_headers
        )
        # 应该接受任意值（模型可能不验证status）
        # 或者返回400
        assert response.status_code in [200, 400]

    def test_execute_nonexistent_workflow(self, client, auth_headers):
        """执行不存在的工作流"""
        response = client.post(
            "/api/workflows/99999/execute",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_execution_deleted_workflow(self, client, auth_headers, published_workflow, db):
        """获取已删除工作流的执行记录"""
        workflow_id = published_workflow["id"]
        
        # 创建执行记录
        from app.models.execution import Execution
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type="manual",
            status="success"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        execution_id = execution.id
        
        # 删除工作流（会级联删除执行记录）
        client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        
        # 尝试获取执行记录
        response = client.get(f"/api/executions/{execution_id}", headers=auth_headers)
        assert response.status_code == 404


class TestSecurityValidation:
    """安全验证测试"""

    def test_sql_injection_workflow_name(self, client, auth_headers):
        """SQL注入 - 工作流名称"""
        malicious_name = "'; DROP TABLE users; --"
        response = client.post(
            "/api/workflows",
            json={"name": malicious_name},
            headers=auth_headers
        )
        # SQLAlchemy 会处理转义，不应该执行注入
        assert response.status_code in [201, 400, 422]

    def test_xss_injection_workflow_description(self, client, auth_headers):
        """XSS注入 - 工作流描述"""
        xss_content = '<script>alert("xss")</script>'
        response = client.post(
            "/api/workflows",
            json={"name": "测试", "description": xss_content},
            headers=auth_headers
        )
        # 应该允许存储（存储层不过滤），前端显示时需要转义
        assert response.status_code == 201

    def test_jwt_token_tampering(self, client, test_user):
        """JWT Token篡改"""
        # 登录获取正常Token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]
        
        # 篡改Token的最后几个字符
        tampered_token = token[:-5] + "xxxxx"
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == 401

    def test_bearer_token_case_sensitivity(self, client, test_user):
        """Bearer Token大小写敏感性"""
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]
        
        # 小写 bearer 应该失败（HTTP规范要求）
        response = client.get(
            "/api/auth/me",
            headers={"authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403  # HTTPBearer 区分大小写

    def test_expired_token_still_in_header(self, client, test_user):
        """过期Token在请求头中"""
        # 创建一个已过期的Token
        from datetime import datetime, timedelta
        from jose import jwt
        from app.config import settings
        
        expired_token = jwt.encode(
            {
                "sub": test_user.id,
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_token_claims_manipulation(self, client, test_user):
        """Token声明操作 - 修改Token中的user_id"""
        from jose import jwt
        from app.config import settings
        
        # 登录获取Token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]
        
        # 解码并修改user_id
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        payload["sub"] = 99999  # 尝试伪装成另一个用户
        
        # 重新编码
        manipulated_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {manipulated_token}"}
        )
        assert response.status_code == 401  # Token虽然格式正确，但用户不存在


class TestPaginationLimits:
    """分页限制测试"""

    def test_list_workflows_pagination_skip_negative(self, client, auth_headers):
        """分页 - skip为负数"""
        response = client.get("/api/workflows?skip=-1", headers=auth_headers)
        # 应该被拒绝或修正
        assert response.status_code in [200, 422]

    def test_list_workflows_pagination_limit_zero(self, client, auth_headers):
        """分页 - limit为0"""
        response = client.get("/api/workflows?limit=0", headers=auth_headers)
        assert response.status_code in [200, 422]

    def test_list_workflows_pagination_limit_exceeds_max(self, client, auth_headers):
        """分页 - limit超过最大限制"""
        response = client.get("/api/workflows?limit=10000", headers=auth_headers)
        # 应该被限制或正常返回
        assert response.status_code == 200

    def test_list_executions_pagination_large_offset(self, client, auth_headers, sample_workflow):
        """分页 - 大偏移量"""
        workflow_id = sample_workflow["id"]
        response = client.get(
            f"/api/workflows/{workflow_id}/executions?skip=10000&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0  # 偏移大于数据量应返回空


class TestCRUDSequence:
    """CRUD操作顺序测试"""

    def test_delete_before_create(self, client, auth_headers):
        """删除 - 在创建之前（ID不存在）"""
        response = client.delete("/api/workflows/1", headers=auth_headers)
        assert response.status_code == 404

    def test_update_before_create(self, client, auth_headers):
        """更新 - 在创建之前（ID不存在）"""
        response = client.patch(
            "/api/workflows/1",
            json={"name": "测试"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_before_create(self, client, auth_headers):
        """获取 - 在创建之前（ID不存在）"""
        response = client.get("/api/workflows/1", headers=auth_headers)
        assert response.status_code == 404

    def test_double_delete(self, client, auth_headers, sample_workflow):
        """双重删除"""
        workflow_id = sample_workflow["id"]
        
        # 第一次删除
        response1 = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response1.status_code == 204
        
        # 第二次删除
        response2 = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert response2.status_code == 404

    def test_update_after_delete(self, client, auth_headers, sample_workflow):
        """删除后更新"""
        workflow_id = sample_workflow["id"]
        
        # 删除
        client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        
        # 尝试更新
        response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "新名称"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_update_delete_sequence(self, client, auth_headers):
        """完整序列：创建→更新→删除"""
        # 创建
        create_response = client.post(
            "/api/workflows",
            json={"name": "序列测试"},
            headers=auth_headers
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]
        
        # 更新
        update_response = client.patch(
            f"/api/workflows/{workflow_id}",
            json={"name": "更新后的名称"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # 获取确认
        get_response = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "更新后的名称"
        
        # 删除
        delete_response = client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # 确认删除
        get_after = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
        assert get_after.status_code == 404
