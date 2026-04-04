"""
AI服务
OpenAI API 调用，提示词模板处理
"""
import re
import httpx
from typing import Dict, Any, Optional, List
from app.config import settings


class AIService:
    """AI服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    async def call_openai(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用 OpenAI API
        
        Args:
            prompt: 用户提示词
            model: 模型名称（可选，默认使用配置中的模型）
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            system_message: 系统消息（可选）
        
        Returns:
            包含响应内容的字典
        """
        if not self.api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model"),
                "usage": result.get("usage", {})
            }
    
    def substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        替换提示词模板中的变量
        支持 {{variable}} 和 {{variable.name}} 格式
        
        Args:
            template: 提示词模板
            variables: 变量字典
        
        Returns:
            替换后的字符串
        """
        result = template
        
        # 匹配 {{variable}} 或 {{variable.name}}
        pattern = r'\{\{([^}]+)\}\}'
        
        for match in re.finditer(pattern, template):
            var_path = match.group(1).strip()
            value = self._get_nested_value(variables, var_path)
            if value is not None:
                result = result.replace(match.group(0), str(value))
            else:
                # 变量不存在，替换为空字符串
                result = result.replace(match.group(0), "")
        
        return result
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        获取嵌套字典中的值
        例如：data = {"user": {"name": "张三"}}, path = "user.name" -> "张三"
        """
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


# 全局AI服务实例
ai_service = AIService()


async def execute_ai_task(
    node_config: Dict[str, Any],
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    执行AI任务节点
    
    Args:
        node_config: 节点配置，包含 model, prompt, temperature 等
        input_data: 上游节点的输出数据
    
    Returns:
        AI响应结果
    """
    # 获取配置
    model = node_config.get("model")
    prompt_template = node_config.get("prompt", "")
    temperature = node_config.get("temperature")
    max_tokens = node_config.get("max_tokens")
    system_message = node_config.get("system_message")
    
    # 替换变量
    prompt = ai_service.substitute_variables(prompt_template, input_data)
    
    # 调用OpenAI
    result = await ai_service.call_openai(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_message=system_message
    )
    
    return {
        "result": result["content"],
        "model": result.get("model"),
        "usage": result.get("usage", {})
    }
