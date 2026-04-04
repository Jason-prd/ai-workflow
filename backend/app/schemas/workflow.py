"""
Pydantic schemas for Workflow
"""
import json
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Any, Dict


class TriggerConfig(BaseModel):
    """触发器配置"""
    type: str  # "manual" 或 "cron"
    expression: Optional[str] = None  # CRON表达式，如 "0 9 * * *"
    timezone: Optional[str] = "Asia/Shanghai"


class NodeConfig(BaseModel):
    """节点配置"""
    id: str
    type: str  # "trigger" / "ai_task" / "tool" / "condition"
    name: str
    config: Dict[str, Any] = {}
    position: Optional[Dict[str, float]] = None  # {"x": 100, "y": 200}


class WorkflowCreate(BaseModel):
    """工作流创建Schema"""
    name: str
    description: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    nodes: Optional[List[Dict[str, Any]]] = None


class WorkflowUpdate(BaseModel):
    """工作流更新Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    """工作流响应Schema"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    trigger_config: Optional[Dict[str, Any]] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, values):
        """将数据库JSON字符串字段解析为Python对象"""
        # values 可能是 ORM 对象（with_attributes）或字典
        # 统一转换为字典处理
        if hasattr(values, '__dict__'):
            # ORM 对象 -> 字典
            values = {k: v for k, v in values.__dict__.items() if not k.startswith('_')}
        if not isinstance(values, dict):
            return values
        
        # trigger_config 可能是JSON字符串或已经解析的dict
        tc = values.get("trigger_config")
        if isinstance(tc, str) and tc:
            try:
                values["trigger_config"] = json.loads(tc)
            except (json.JSONDecodeError, TypeError):
                values["trigger_config"] = None
        # nodes 可能是JSON字符串或已经解析的list
        nodes = values.get("nodes")
        if isinstance(nodes, str) and nodes:
            try:
                values["nodes"] = json.loads(nodes)
            except (json.JSONDecodeError, TypeError):
                values["nodes"] = None
        return values

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    items: List[WorkflowResponse]
    total: int
