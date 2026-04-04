"""
AI服务层单元测试
直接测试 AI Service 的变量替换和调用逻辑（不通过 HTTP API）
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock


class TestVariableSubstitution:
    """提示词变量替换测试"""

    def test_substitute_simple_variable(self):
        """简单变量替换 - {{variable}}"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "请处理：{{input}}"
        variables = {"input": "测试数据"}

        result = service.substitute_variables(template, variables)
        assert result == "请处理：测试数据"

    def test_substitute_nested_variable(self):
        """嵌套变量替换 - {{object.field}}"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "用户{{user.name}}的数据是{{user.value}}"
        variables = {"user": {"name": "张三", "value": "12345"}}

        result = service.substitute_variables(template, variables)
        assert result == "用户张三的数据是12345"

    def test_substitute_multiple_variables(self):
        """多变量替换"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "{{greeting}}，{{name}}！今天是{{date}}。"
        variables = {"greeting": "你好", "name": "小明", "date": "2026-03-28"}

        result = service.substitute_variables(template, variables)
        assert result == "你好，小明！今天是2026-03-28。"

    def test_substitute_missing_variable(self):
        """缺失变量 - 替换为空字符串"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "Hello {{name}}, your score is {{score}}"
        variables = {"name": "Alice"}  # score 缺失

        result = service.substitute_variables(template, variables)
        assert result == "Hello Alice, your score is "

    def test_substitute_no_variables(self):
        """无变量模板 - 保持不变"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "这是一段固定的提示词，不含变量。"
        variables = {"name": "test"}

        result = service.substitute_variables(template, variables)
        assert result == "这是一段固定的提示词，不含变量。"

    def test_substitute_empty_template(self):
        """空模板"""
        from app.services.ai_service import AIService

        service = AIService()
        result = service.substitute_variables("", {"key": "value"})
        assert result == ""

    def test_substitute_with_whitespace(self):
        """带空白的变量名"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "{{ input }}"
        variables = {"input": "data"}

        result = service.substitute_variables(template, variables)
        assert result == "data"

    def test_substitute_nested_deep(self):
        """深度嵌套变量"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "值：{{a.b.c.d}}"
        variables = {"a": {"b": {"c": {"d": "deep_value"}}}}

        result = service.substitute_variables(template, variables)
        assert result == "值：deep_value"

    def test_substitute_nested_partial_path(self):
        """嵌套变量，部分路径不存在"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "{{a.b.c}}"
        variables = {"a": {"b": {}}}  # c 不存在

        result = service.substitute_variables(template, variables)
        assert result == ""

    def test_substitute_with_integer_value(self):
        """整数类型变量值"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "分数：{{score}}"
        variables = {"score": 95}

        result = service.substitute_variables(template, variables)
        assert result == "分数：95"

    def test_substitute_with_float_value(self):
        """浮点数类型变量值"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "温度：{{temp}}度"
        variables = {"temp": 36.6}

        result = service.substitute_variables(template, variables)
        assert result == "温度：36.6度"

    def test_substitute_with_list_value(self):
        """列表类型变量值（转为字符串）"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "项目：{{projects}}"
        variables = {"projects": ["A", "B", "C"]}

        result = service.substitute_variables(template, variables)
        assert result == "项目：['A', 'B', 'C']"

    def test_substitute_mixed_braces(self):
        """混合花括号边界"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "公式：{{x}} + {{y}} = {{z}}"
        variables = {"x": 1, "y": 2, "z": 3}

        result = service.substitute_variables(template, variables)
        assert result == "公式：1 + 2 = 3"

    def test_substitute_dupplicate_vars(self):
        """同一变量出现多次"""
        from app.services.ai_service import AIService

        service = AIService()
        template = "{{name}}说：{{name}}你好！{{name}}再见！"
        variables = {"name": "小李"}

        result = service.substitute_variables(template, variables)
        assert result == "小李说：小李你好！小李再见！"


class TestExecuteAITask:
    """execute_ai_task 函数测试"""

    @pytest.mark.asyncio
    async def test_execute_ai_task_with_mock(self):
        """AI任务执行 - Mock OpenAI API"""
        from app.services.ai_service import execute_ai_task

        node_config = {
            "model": "gpt-4o-mini",
            "prompt": "请总结：{{input}}",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        input_data = {"input": "这是一段需要总结的长文本。"}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "这是总结后的内容。",
                "model": "gpt-4o-mini",
                "usage": {"prompt_tokens": 50, "completion_tokens": 20}
            }

            result = await execute_ai_task(node_config, input_data)

            assert result["result"] == "这是总结后的内容。"
            assert result["model"] == "gpt-4o-mini"
            assert "usage" in result
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_ai_task_variable_substitution(self):
        """AI任务执行 - 变量替换"""
        from app.services.ai_service import execute_ai_task

        node_config = {
            "model": "gpt-4o-mini",
            "prompt": "{{content}}",
        }
        input_data = {"content": "Hello World"}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"content": "响应", "model": "gpt-4o-mini", "usage": {}}

            await execute_ai_task(node_config, input_data)

            # 验证传入的 prompt 已被替换
            call_args = mock_call.call_args
            assert call_args[1]["prompt"] == "Hello World"

    @pytest.mark.asyncio
    async def test_execute_ai_task_with_system_message(self):
        """AI任务执行 - 带系统消息"""
        from app.services.ai_service import execute_ai_task

        node_config = {
            "model": "gpt-4o-mini",
            "prompt": "{{input}}",
            "system_message": "你是一个翻译助手。"
        }
        input_data = {"input": "Hello"}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"content": "你好", "model": "gpt-4o-mini", "usage": {}}

            await execute_ai_task(node_config, input_data)

            call_args = mock_call.call_args
            assert call_args[1]["system_message"] == "你是一个翻译助手。"

    @pytest.mark.asyncio
    async def test_execute_ai_task_no_model_in_config(self):
        """AI任务执行 - 配置中未指定模型（使用默认）"""
        from app.services.ai_service import execute_ai_task

        node_config = {
            "prompt": "hello",
            # 没有 model 字段
        }
        input_data = {}

        with patch("app.services.ai_service.ai_service.call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"content": "response", "model": "gpt-4o", "usage": {}}

            result = await execute_ai_task(node_config, input_data)

            # model 为 None，会使用默认模型
            call_args = mock_call.call_args
            assert call_args[1]["model"] is None  # execute_ai_task 传 None，call_openai 用默认


class TestCallOpenAI:
    """OpenAI API 调用测试"""

    @pytest.mark.asyncio
    async def test_call_openai_success(self):
        """OpenAI API - 成功调用"""
        from app.services.ai_service import AIService

        service = AIService(api_key="sk-test-key")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}],
                "model": "gpt-4o"
            }
            mock_response.raise_for_status = MagicMock()

            mock_post.return_value = mock_response

            result = await service.call_openai("Hello")

            assert result["content"] == "Test response"
            assert result["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_call_openai_no_api_key(self):
        """OpenAI API - 未配置 API Key"""
        from app.services.ai_service import AIService

        service = AIService(api_key=None)

        with pytest.raises(ValueError, match="OpenAI API密钥未配置"):
            await service.call_openai("Hello")

    @pytest.mark.asyncio
    async def test_call_openai_with_custom_params(self):
        """OpenAI API - 自定义参数"""
        from app.services.ai_service import AIService

        service = AIService(api_key="sk-test-key")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "model": "gpt-4o"
            }
            mock_response.raise_for_status = MagicMock()

            mock_post.return_value = mock_response

            await service.call_openai(
                prompt="Test",
                model="gpt-4o",
                temperature=0.5,
                max_tokens=500,
                system_message="You are a helpful assistant."
            )

            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            assert payload["model"] == "gpt-4o"
            assert payload["temperature"] == 0.5
            assert payload["max_tokens"] == 500
            assert len(payload["messages"]) == 2  # system + user

    @pytest.mark.asyncio
    async def test_call_openai_api_error(self):
        """OpenAI API - API 返回错误"""
        from app.services.ai_service import AIService
        import httpx

        service = AIService(api_key="sk-invalid")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=MagicMock()
            )
            mock_post.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await service.call_openai("Test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
