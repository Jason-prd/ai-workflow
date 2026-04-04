"""
HTTP服务
通用的HTTP请求执行器
"""
import httpx
from typing import Dict, Any, Optional


async def execute_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    执行HTTP请求
    
    Args:
        url: 请求URL
        method: 请求方法（GET/POST/PUT/DELETE）
        headers: 请求头
        body: 请求体（JSON格式）
        timeout: 超时时间（秒）
    
    Returns:
        响应结果
    """
    method = method.upper()
    
    async with httpx.AsyncClient(timeout=float(timeout)) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=body)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=body)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        # 返回结果
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
            "is_success": 200 <= response.status_code < 300
        }
