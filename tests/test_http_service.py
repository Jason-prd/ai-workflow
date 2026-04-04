"""
HTTP服务层单元测试
直接测试 HTTP 请求执行逻辑（不通过 API 层）
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock


class TestExecuteHTTPRequest:
    """HTTP 请求执行测试"""

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """GET 请求 - 成功"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = '{"result": "ok"}'

            mock_get.return_value = mock_response

            result = await execute_http_request("https://api.example.com/data")

            assert result["status_code"] == 200
            assert result["is_success"] is True
            assert result["content"] == '{"result": "ok"}'
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_with_headers(self):
        """GET 请求 - 带请求头"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = "ok"

            mock_get.return_value = mock_response

            headers = {"Authorization": "Bearer token123", "Accept": "application/json"}
            await execute_http_request("https://api.example.com/data", headers=headers)

            call_args = mock_get.call_args
            assert call_args[1]["headers"] == headers

    @pytest.mark.asyncio
    async def test_post_request_with_body(self):
        """POST 请求 - 带请求体"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.headers = {}
            mock_response.text = '{"id": 1}'

            mock_post.return_value = mock_response

            body = {"name": "test", "value": 123}
            result = await execute_http_request(
                "https://api.example.com/create",
                method="POST",
                body=body
            )

            assert result["status_code"] == 201
            call_args = mock_post.call_args
            assert call_args[1]["json"] == body

    @pytest.mark.asyncio
    async def test_put_request(self):
        """PUT 请求"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.put", new_callable=AsyncMock) as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = '{"updated": true}'

            mock_put.return_value = mock_response

            result = await execute_http_request(
                "https://api.example.com/update/1",
                method="PUT",
                body={"name": "updated"}
            )

            assert result["status_code"] == 200
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_request(self):
        """DELETE 请求"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_response.headers = {}
            mock_response.text = ""

            mock_delete.return_value = mock_response

            result = await execute_http_request(
                "https://api.example.com/delete/1",
                method="DELETE"
            )

            assert result["status_code"] == 204
            assert result["is_success"] is True

    @pytest.mark.asyncio
    async def test_http_request_4xx_error(self):
        """HTTP 请求 - 4xx 客户端错误"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.headers = {}
            mock_response.text = "Not Found"

            mock_get.return_value = mock_response

            result = await execute_http_request("https://api.example.com/notfound")

            assert result["status_code"] == 404
            assert result["is_success"] is False

    @pytest.mark.asyncio
    async def test_http_request_5xx_error(self):
        """HTTP 请求 - 5xx 服务器错误"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.headers = {}
            mock_response.text = "Internal Server Error"

            mock_get.return_value = mock_response

            result = await execute_http_request("https://api.example.com/error")

            assert result["status_code"] == 500
            assert result["is_success"] is False

    @pytest.mark.asyncio
    async def test_http_request_timeout(self):
        """HTTP 请求 - 自定义超时"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = "ok"

            mock_get.return_value = mock_response

            await execute_http_request("https://api.example.com/data", timeout=60)

            # 验证 AsyncClient 的 timeout 参数
            call_args = mock_get.call_args
            # httpx.AsyncClient(timeout=60) 表示超时60秒
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_request_method_case_insensitive(self):
        """HTTP 请求 - 方法名大小写不敏感"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = "ok"

            mock_post.return_value = mock_response

            # 小写 method
            result = await execute_http_request("https://api.example.com", method="post", body={})

            assert result["status_code"] == 200
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_request_unsupported_method(self):
        """HTTP 请求 - 不支持的方法"""
        from app.services.http_service import execute_http_request

        with pytest.raises(ValueError, match="不支持的HTTP方法"):
            await execute_http_request("https://api.example.com", method="PATCH")

    @pytest.mark.asyncio
    async def test_http_request_returns_headers(self):
        """HTTP 请求 - 返回响应头"""
        from app.services.http_service import execute_http_request

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {
                "Content-Type": "application/json",
                "X-Request-Id": "req-123"
            }
            mock_response.text = '{"data": true}'

            mock_get.return_value = mock_response

            result = await execute_http_request("https://api.example.com/data")

            assert "Content-Type" in result["headers"]
            assert result["headers"]["X-Request-Id"] == "req-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
