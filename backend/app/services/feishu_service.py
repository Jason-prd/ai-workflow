"""
飞书服务
飞书开放平台 API 调用（消息发送、文档操作）
"""
import httpx
from typing import Optional, Dict, Any
from app.config import settings


class FeishuService:
    """飞书服务类"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or settings.FEISHU_APP_ID
        self.app_secret = app_secret or settings.FEISHU_APP_SECRET
        self.api_base = "https://open.feishu.cn/open-apis"
        self._tenant_access_token: Optional[str] = None
    
    async def get_tenant_access_token(self) -> str:
        """
        获取 tenant_access_token
        """
        if self._tenant_access_token:
            return self._tenant_access_token
        
        url = f"{self.api_base}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取飞书访问令牌失败: {result.get('msg')}")
            
            self._tenant_access_token = result.get("tenant_access_token")
            return self._tenant_access_token
    
    async def send_message(
        self,
        receive_id_type: str,
        receive_id: str,
        msg_type: str = "text",
        content: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送飞书消息
        
        Args:
            receive_id_type: 接收者类型（open_id / chat_id）
            receive_id: 接收者ID
            msg_type: 消息类型（text / post / interactive）
            content: 消息内容（JSON格式）
            text: 文本内容（简化模式）
        
        Returns:
            发送结果
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置未完成")
        
        token = await self.get_tenant_access_token()
        url = f"{self.api_base}/im/v1/messages?receive_id_type={receive_id_type}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 处理消息内容
        if text is not None:
            message_content = {"text": text}
        elif content is not None:
            message_content = content
        else:
            raise ValueError("必须提供 text 或 content 参数")
        
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": message_content if isinstance(message_content, str) else message_content
        }
        
        # 转换content为字符串
        if isinstance(payload["content"], dict):
            payload["content"] = str(payload["content"])
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"发送飞书消息失败: {result.get('msg')}")
            
            return {
                "message_id": result.get("data", {}).get("message_id"),
                "status": "success"
            }
    
    async def create_document(
        self,
        title: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建飞书云文档
        
        Args:
            title: 文档标题
            content: 文档内容（Markdown格式，可选）
        
        Returns:
            创建的文档信息
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置未完成")
        
        token = await self.get_tenant_access_token()
        url = f"{self.api_base}/docx/v1/documents"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "title": title
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"创建飞书文档失败: {result.get('msg')}")
            
            document = result.get("data", {}).get("document", {})
            doc_token = document.get("document_id")
            
            return {
                "document_id": doc_token,
                "title": title,
                "url": f"https://.feishu.cn/document/{doc_token}"
            }
    
    async def read_document(self, document_id: str) -> Dict[str, Any]:
        """
        读取飞书云文档内容
        
        Args:
            document_id: 文档ID
        
        Returns:
            文档内容
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置未完成")
        
        token = await self.get_tenant_access_token()
        url = f"{self.api_base}/docx/v1/documents/{document_id}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"读取飞书文档失败: {result.get('msg')}")
            
            document = result.get("data", {}).get("document", {})
            return {
                "document_id": document_id,
                "title": document.get("title"),
                "content": document  # 实际内容需要额外API获取
            }
    
    async def get_calendar_events(
        self,
        start_time: str,
        end_time: str,
        calendar_id: Optional[str] = None
    ) -> list:
        """
        获取日历事件列表
        
        Args:
            start_time: 开始时间（ISO 8601 格式，带时区）
            end_time: 结束时间（ISO 8601 格式，带时区）
            calendar_id: 日历ID，None 表示主日历
        
        Returns:
            日历事件列表
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置未完成")
        
        token = await self.get_tenant_access_token()
        target_calendar_id = calendar_id or "primary"
        url = f"{self.api_base}/calendar/v4/calendars/{target_calendar_id}/events"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "page_size": 50
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取日历事件失败: {result.get('msg')}")
            
            return result.get("data", {}).get("items", [])
    
    async def get_primary_calendar_id(self) -> str:
        """
        获取主日历ID
        
        Returns:
            主日历ID
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置未完成")
        
        token = await self.get_tenant_access_token()
        url = f"{self.api_base}/calendar/v4/calendars/primary"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取主日历失败: {result.get('msg')}")
            
            return result.get("data", {}).get("calendar", {}).get("calendar_id", "primary")


# 全局飞书服务实例
feishu_service = FeishuService()


async def send_feishu_message(
    receive_id: str,
    receive_id_type: str = "chat_id",
    text: Optional[str] = None,
    content: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """发送飞书消息的便捷函数"""
    return await feishu_service.send_message(
        receive_id_type=receive_id_type,
        receive_id=receive_id,
        text=text,
        content=content
    )


async def create_feishu_doc(
    title: str,
    content: Optional[str] = None
) -> Dict[str, Any]:
    """创建飞书文档的便捷函数"""
    return await feishu_service.create_document(title=title, content=content)
