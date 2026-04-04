"""
执行记录模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败


class Execution(Base):
    """执行记录表"""
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    
    # 触发方式：manual（手动）/ cron（定时）
    trigger_type = Column(String(20), nullable=False)
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value)
    
    # 执行开始/结束时间
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # 错误信息（如有）
    error_message = Column(Text, nullable=True)
    
    # 触发时的输入数据（JSON格式）
    trigger_input = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联：所属工作流
    workflow = relationship("Workflow", back_populates="executions")
    
    # 关联：执行日志列表
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class ExecutionLog(Base):
    """执行日志表 - 记录每个节点的执行详情"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False, index=True)
    
    # 节点标识（来自nodes配置中的id）
    node_id = Column(String(50), nullable=False)
    
    # 节点类型：trigger / ai_task / tool / condition
    node_type = Column(String(50), nullable=False)
    
    # 节点名称
    node_name = Column(String(200), nullable=True)
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value)
    
    # 输入数据（JSON格式）
    input_data = Column(Text, nullable=True)
    
    # 输出数据（JSON格式）
    output_data = Column(Text, nullable=True)
    
    # 错误信息
    error = Column(Text, nullable=True)
    
    # 执行耗时（毫秒）
    duration_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联：所属执行记录
    execution = relationship("Execution", back_populates="logs")
