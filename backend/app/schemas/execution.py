"""
Pydantic schemas for Execution
"""
import json
from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional, List, Dict, Any


class ExecutionLogResponse(BaseModel):
    """执行日志响应"""
    id: int
    execution_id: int
    node_id: str
    node_type: str
    node_name: Optional[str]
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime
    
    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, values):
        """将数据库JSON字符串字段解析为Python对象"""
        if hasattr(values, '__dict__'):
            values = {k: v for k, v in values.__dict__.items() if not k.startswith('_')}
        if not isinstance(values, dict):
            return values
        
        # input_data 可能是JSON字符串或已经解析的dict
        for field in ("input_data", "output_data"):
            val = values.get(field)
            if isinstance(val, str) and val:
                try:
                    values[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    values[field] = None
            elif val is None:
                values[field] = None
        
        return values

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """执行记录响应"""
    id: int
    workflow_id: int
    trigger_type: str
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    error_message: Optional[str]
    trigger_input: Optional[Dict[str, Any]] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, values):
        """将数据库JSON字符串字段解析为Python对象"""
        if hasattr(values, '__dict__'):
            values = {k: v for k, v in values.__dict__.items() if not k.startswith('_')}
        if not isinstance(values, dict):
            return values
        
        # trigger_input 可能是JSON字符串或已经解析的dict
        ti = values.get("trigger_input")
        if isinstance(ti, str) and ti:
            try:
                values["trigger_input"] = json.loads(ti)
            except (json.JSONDecodeError, TypeError):
                values["trigger_input"] = None
        elif ti is None:
            values["trigger_input"] = None
        
        return values

    class Config:
        from_attributes = True


class ExecutionDetailResponse(ExecutionResponse):
    """执行详情响应（包含日志）"""
    logs: List[ExecutionLogResponse] = []
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """执行记录列表响应"""
    items: List[ExecutionResponse]
    total: int


class ExecutionStatusResponse(BaseModel):
    """执行状态响应（用于轮询）"""
    id: int
    workflow_id: int
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    error_message: Optional[str]
    # 当前正在执行的节点（如果有）
    current_node_id: Optional[str] = None
    current_node_name: Optional[str] = None
    # 完成百分比（估算）
    progress_percent: int = 0
    created_at: datetime
