"""
工作流模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class WorkflowStatus(str, enum.Enum):
    """工作流状态枚举"""
    DRAFT = "draft"      # 草稿
    PUBLISHED = "published"  # 已发布


class Workflow(Base):
    """工作流表"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 触发器配置（JSON格式）
    # 例如：{"type": "manual"} 或 {"type": "cron", "expression": "0 9 * * *", "timezone": "Asia/Shanghai"}
    trigger_config = Column(Text, nullable=True)
    
    # 节点配置（JSON格式）
    # 包含所有节点的定义和连接关系
    # 例如：[{"id": "1", "type": "trigger", "config": {...}}, {"id": "2", "type": "ai_task", "config": {...}}]
    nodes = Column(Text, nullable=True)
    
    # 工作流状态
    status = Column(String(20), default=WorkflowStatus.DRAFT.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联：所属用户
    owner = relationship("User", back_populates="workflows")
    
    # 关联：执行记录
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
