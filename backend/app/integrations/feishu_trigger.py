"""
飞书消息触发器
基于飞书消息事件触发工作流执行
"""
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from app.services.feishu_service import FeishuService


@dataclass
class TriggerEvent:
    """触发器事件"""
    trigger_type: str  # feishu_message / feishu_calendar
    event_id: str  # 事件唯一ID
    timestamp: str  # 事件时间
    data: Dict[str, Any]  # 事件数据
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "data": self.data
        }


class BaseTrigger(ABC):
    """触发器基类"""
    
    @abstractmethod
    async def check(self) -> List[TriggerEvent]:
        """检查是否有新的触发事件"""
        pass
    
    @abstractmethod
    async def execute(self, workflow_id: int, event: TriggerEvent):
        """执行指定工作流"""
        pass


class FeishuMessageTriggerConfig:
    """飞书消息触发器配置"""
    
    def __init__(
        self,
        keywords: Optional[List[str]] = None,
        chat_ids: Optional[List[str]] = None,  # 监听特定群，None 表示监听所有
        chat_types: Optional[List[str]] = None,  # ["p2p", "group"]
        exclude_keywords: Optional[List[str]] = None,
    ):
        self.keywords = keywords or []  # 触发关键词列表
        self.chat_ids = chat_ids or []  # 监听群ID列表
        self.chat_types = chat_types or ["p2p", "group"]  # 默认监听所有类型
        self.exclude_keywords = exclude_keywords or []  # 排除关键词
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "FeishuMessageTriggerConfig":
        """从工作流节点配置创建"""
        trigger_config = config.get("trigger_config", {})
        return cls(
            keywords=trigger_config.get("keywords", []),
            chat_ids=trigger_config.get("chat_ids", []),
            chat_types=trigger_config.get("chat_types", ["p2p", "group"]),
            exclude_keywords=trigger_config.get("exclude_keywords", []),
        )
    
    def match(self, message: Dict[str, Any]) -> bool:
        """
        检查消息是否匹配触发条件
        
        Args:
            message: 统一格式的消息对象
        
        Returns:
            是否匹配
        """
        # 检查聊天类型
        chat_type = message.get("chat_type", "")
        if chat_type not in self.chat_types:
            return False
        
        # 检查群ID白名单
        if self.chat_ids and message.get("chat_id") not in self.chat_ids:
            return False
        
        text = message.get("text", "")
        
        # 检查排除关键词
        for exclude_kw in self.exclude_keywords:
            if exclude_kw in text:
                return False
        
        # 检查触发关键词（为空表示无需关键词匹配）
        if not self.keywords:
            return True
        
        # 检查是否包含任意一个关键词
        for keyword in self.keywords:
            if keyword in text:
                return True
        
        return False


class FeishuMessageTrigger(BaseTrigger):
    """飞书消息触发器"""
    
    def __init__(self, config: FeishuMessageTriggerConfig):
        self.config = config
        # 已处理的消息ID集合（避免重复触发）
        self._processed_ids: set = set()
    
    @property
    def trigger_type(self) -> str:
        return "feishu_message"
    
    async def check(self, message: Dict[str, Any]) -> List[TriggerEvent]:
        """
        检查消息是否匹配触发条件
        
        Args:
            message: 统一格式的消息对象
        
        Returns:
            匹配的触发事件列表
        """
        message_id = message.get("message_id", "")
        
        # 避免重复处理
        if message_id in self._processed_ids:
            return []
        
        # 检查是否匹配
        if not self.config.match(message):
            return []
        
        # 标记为已处理
        self._processed_ids.add(message_id)
        
        # 构建触发事件
        event = TriggerEvent(
            trigger_type="feishu_message",
            event_id=message_id,
            timestamp=message.get("create_time", datetime.utcnow().isoformat()),
            data={
                "chat_id": message.get("chat_id"),
                "chat_type": message.get("chat_type"),
                "sender_id": message.get("sender_id"),
                "message_type": message.get("message_type"),
                "text": message.get("text", ""),
                "raw_content": message.get("raw_content"),
            }
        )
        
        return [event]
    
    async def execute(self, workflow_id: int, event: TriggerEvent, db=None):
        """
        执行指定工作流
        
        Args:
            workflow_id: 工作流ID
            event: 触发事件
            db: 数据库会话
        """
        # 延迟导入避免循环依赖
        from app.services.execution_service import execute_workflow
        from app.models.workflow import Workflow
        from sqlalchemy.orm import Session
        
        if db is None:
            from app.database import SessionLocal
            db = SessionLocal()
        
        try:
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # 触发工作流执行
            execution = await execute_workflow(
                db=db,
                workflow=workflow,
                trigger_type="feishu_message",
                trigger_input=event.data
            )
            
            return execution
        finally:
            if db:
                db.close()


# ==================== 消息事件缓存 ====================


class FeishuMessageEventBus:
    """飞书消息事件总线 - 收集待处理的消息事件"""
    
    def __init__(self):
        self._pending_events: List[Dict[str, Any]] = []
        self._lock = False  # 简单锁，防止并发问题
    
    def add_message(self, message: Dict[str, Any]):
        """添加新消息到事件总线"""
        self._pending_events.append(message)
    
    def get_pending_events(self) -> List[Dict[str, Any]]:
        """获取所有待处理的消息"""
        events = self._pending_events
        self._pending_events = []
        return events
    
    def clear(self):
        """清空事件队列"""
        self._pending_events = []


# 全局事件总线实例
feishu_message_event_bus = FeishuMessageEventBus()
