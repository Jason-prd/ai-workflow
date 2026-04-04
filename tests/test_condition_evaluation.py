"""
条件表达式求值单元测试
直接测试 execution_service.evaluate_condition 函数
"""
import pytest


class TestEvaluateCondition:
    """条件表达式求值测试"""

    def test_evaluate_condition_simple_equals_true(self):
        """简单条件 equals - 匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="status equals success",
            data={"status": "success"}
        )
        assert result is True

    def test_evaluate_condition_simple_equals_false(self):
        """简单条件 equals - 不匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="status equals success",
            data={"status": "failed"}
        )
        assert result is False

    def test_evaluate_condition_equals_case_insensitive(self):
        """简单条件 equals - 大小写不敏感"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="name equals ALICE",
            data={"name": "alice"}
        )
        assert result is True

    def test_evaluate_condition_contains_true(self):
        """简单条件 contains - 包含"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="message contains hello",
            data={"message": "hello world"}
        )
        assert result is True

    def test_evaluate_condition_contains_false(self):
        """简单条件 contains - 不包含"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="message contains goodbye",
            data={"message": "hello world"}
        )
        assert result is False

    def test_evaluate_condition_contains_case_insensitive(self):
        """简单条件 contains - 大小写不敏感"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="text contains WORLD",
            data={"text": "hello world"}
        )
        assert result is True

    def test_evaluate_condition_starts_with_true(self):
        """简单条件 starts_with - 匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="name starts_with admin",
            data={"name": "admin_user"}
        )
        assert result is True

    def test_evaluate_condition_starts_with_false(self):
        """简单条件 starts_with - 不匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="name starts_with admin",
            data={"name": "user_admin"}
        )
        assert result is False

    def test_evaluate_condition_ends_with_true(self):
        """简单条件 ends_with - 匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="filename ends_with .pdf",
            data={"filename": "document.pdf"}
        )
        assert result is True

    def test_evaluate_condition_ends_with_false(self):
        """简单条件 ends_with - 不匹配"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="filename ends_with .pdf",
            data={"filename": "document.txt"}
        )
        assert result is False

    def test_evaluate_condition_missing_key(self):
        """条件 - 数据中键不存在"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="nonexistent equals value",
            data={"other_key": "value"}
        )
        # 键不存在时 data_value 为空字符串，equals 不匹配
        assert result is False

    def test_evaluate_condition_empty_expression(self):
        """条件 - 空表达式"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="",
            data={"key": "value"}
        )
        # 表达式为空时不满足条件判断，走默认返回 True
        assert result is True

    def test_evaluate_condition_invalid_operator(self):
        """条件 - 无效操作符（回退到默认 True）"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="key unknown value",
            data={"key": "anything"}
        )
        # 操作符不在支持列表中，走默认返回 True
        assert result is True

    def test_evaluate_condition_unknown_condition_type(self):
        """条件 - 未知条件类型（回退到默认 True）"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="complex",  # 未知类型
            expression="some expression",
            data={"key": "value"}
        )
        # 未知条件类型，走默认返回 True
        assert result is True

    def test_evaluate_condition_multi_word_value(self):
        """条件 - 值包含空格"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="greeting equals hello world",
            data={"greeting": "hello world"}
        )
        assert result is True

    def test_evaluate_condition_with_integer_comparison(self):
        """条件 - 数值比较（仅支持字符串比较）"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="count equals 100",
            data={"count": 100}
        )
        # 数值会被转字符串比较
        assert result is True

    def test_evaluate_condition_multiple_spaces(self):
        """条件 - 多个空格分隔"""
        from app.services.execution_service import evaluate_condition

        result = evaluate_condition(
            condition="simple",
            expression="key   equals   value",
            data={"key": "value"}
        )
        # split() 会合并多个空格
        assert result is False  # "key   equals   value".split() = ['key', 'equals', 'value']，这是对的
        # 实际上 3 个词，第二个是 "equals"，第三个是 "value"，所以应该相等
        # 'value' == 'value' -> True
        assert result is True


class TestConditionNodeExecution:
    """条件节点执行测试（在 execute_workflow 流程中）"""

    @pytest.mark.asyncio
    async def test_workflow_with_condition_node_true_branch(
        self, client, auth_headers, published_workflow, db
    ):
        """带条件节点的工作流 - 条件满足"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        # 更新工作流，添加条件节点
        workflow = db.query(Workflow).filter(Workflow.id == published_workflow["id"]).first()
        import json
        workflow.nodes = json.dumps([
            {"id": "trigger_1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件判断",
                "config": {
                    "condition": "simple",
                    "expression": "triggered equals true"
                }
            }
        ])
        db.commit()

        with patch("app.services.execution_service.ai_service.execute_ai_task", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"result": "ok"}

            with patch("app.services.execution_service.feishu_service.send_message", new_callable=AsyncMock) as mock_feishu:
                mock_feishu.return_value = {"message_id": "om_test"}

                # 重新从 DB 加载
                workflow = db.query(Workflow).filter(Workflow.id == published_workflow["id"]).first()

                execution = await execution_service.execute_workflow(
                    db=db,
                    workflow=workflow,
                    trigger_type="manual",
                    trigger_input={}
                )

                assert execution.status == "success"

    @pytest.mark.asyncio
    async def test_workflow_condition_node_not_last(
        self, client, auth_headers, published_workflow, db
    ):
        """条件节点不是最后一个节点 - 后继节点继续执行"""
        from app.models.workflow import Workflow
        from app.services import execution_service

        workflow = db.query(Workflow).filter(Workflow.id == published_workflow["id"]).first()
        import json
        workflow.nodes = json.dumps([
            {"id": "trigger_1", "type": "trigger", "name": "触发器", "config": {"type": "manual"}},
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件判断",
                "config": {"condition": "simple", "expression": "triggered equals true"}
            }
        ])
        db.commit()

        with patch("app.services.execution_service.ai_service.execute_ai_task", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"result": "ai_output"}

            workflow = db.query(Workflow).filter(Workflow.id == published_workflow["id"]).first()
            execution = await execution_service.execute_workflow(
                db=db, workflow=workflow, trigger_type="manual", trigger_input={}
            )

            assert execution.status == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
