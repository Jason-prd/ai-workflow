"""
执行记录 API 路由
查看工作流的执行历史、详情和实时状态
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.execution import Execution, ExecutionLog, ExecutionStatus
from app.schemas.execution import (
    ExecutionResponse, ExecutionDetailResponse, ExecutionListResponse,
    ExecutionStatusResponse, ExecutionLogResponse
)
from app.services.auth_service import get_current_user
from app.services import workflow_service, execution_service

router = APIRouter(prefix="/api", tags=["执行记录"])


def _parse_execution_json(execution: Execution) -> dict:
    """将执行记录的JSON字符串字段解析为Python对象"""
    data = {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "trigger_type": execution.trigger_type,
        "status": execution.status,
        "started_at": execution.started_at,
        "ended_at": execution.ended_at,
        "error_message": execution.error_message,
        "created_at": execution.created_at,
    }
    
    # 解析 trigger_input
    if execution.trigger_input:
        try:
            data["trigger_input"] = json.loads(execution.trigger_input)
        except (json.JSONDecodeError, TypeError):
            data["trigger_input"] = None
    else:
        data["trigger_input"] = None
    
    return data


def _parse_log_json(log: ExecutionLog) -> dict:
    """将执行日志的JSON字符串字段解析为Python对象"""
    data = {
        "id": log.id,
        "execution_id": log.execution_id,
        "node_id": log.node_id,
        "node_type": log.node_type,
        "node_name": log.node_name,
        "status": log.status,
        "error": log.error,
        "duration_ms": log.duration_ms,
        "created_at": log.created_at,
    }
    
    # 解析 input_data
    if log.input_data:
        try:
            data["input_data"] = json.loads(log.input_data)
        except (json.JSONDecodeError, TypeError):
            data["input_data"] = None
    else:
        data["input_data"] = None
    
    # 解析 output_data
    if log.output_data:
        try:
            data["output_data"] = json.loads(log.output_data)
        except (json.JSONDecodeError, TypeError):
            data["output_data"] = None
    else:
        data["output_data"] = None
    
    return data


@router.get("/workflows/{workflow_id}/executions/{execution_id}", response_model=ExecutionDetailResponse)
async def get_workflow_execution_detail(
    workflow_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定工作流的执行详情（包含所有节点的执行日志）
    """
    # 验证工作流所有权
    workflow = workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    execution = db.query(Execution).filter(
        Execution.id == execution_id,
        Execution.workflow_id == workflow_id
    ).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 获取执行日志
    logs = execution_service.get_execution_logs(db, execution_id)
    parsed_logs = [_parse_log_json(log) for log in logs]
    
    # 构建详情响应
    data = _parse_execution_json(execution)
    data["logs"] = parsed_logs
    
    return ExecutionDetailResponse(**data)


@router.get("/workflows/{workflow_id}/executions", response_model=ExecutionListResponse)
async def list_workflow_executions(
    workflow_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定工作流的执行记录列表
    """
    # 验证工作流所有权
    workflow = workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    executions = db.query(Execution).filter(
        Execution.workflow_id == workflow_id
    ).order_by(Execution.created_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(Execution).filter(Execution.workflow_id == workflow_id).count()
    
    # 解析JSON字段
    items = [_parse_execution_json(e) for e in executions]
    
    return {"items": items, "total": total}


@router.get("/executions/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution_detail(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行详情（包含所有节点的执行日志）
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 验证工作流所有权
    workflow = workflow_service.get_workflow(db, execution.workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无权访问此执行记录"
        )
    
    # 获取执行日志
    logs = execution_service.get_execution_logs(db, execution_id)
    parsed_logs = [_parse_log_json(log) for log in logs]
    
    # 构建详情响应
    data = _parse_execution_json(execution)
    data["logs"] = parsed_logs
    
    return ExecutionDetailResponse(**data)


@router.get("/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行状态（用于轮询/实时更新）
    返回当前正在执行的节点和进度信息
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 验证工作流所有权
    workflow = workflow_service.get_workflow(db, execution.workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无权访问此执行记录"
        )
    
    # 计算进度
    progress_percent = 0
    current_node_id = None
    current_node_name = None
    
    if execution.status == ExecutionStatus.SUCCESS.value:
        progress_percent = 100
    elif execution.status == ExecutionStatus.RUNNING.value:
        # 获取已完成的节点数
        completed_logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution_id,
            ExecutionLog.status == ExecutionStatus.SUCCESS.value
        ).all()
        
        # 获取工作流总节点数
        nodes = json.loads(workflow.nodes) if workflow.nodes else []
        total_nodes = len(nodes)
        
        if total_nodes > 0:
            progress_percent = min(int(len(completed_logs) / total_nodes * 100), 99)
        
        # 获取当前正在执行的节点
        running_log = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution_id,
            ExecutionLog.status == ExecutionStatus.RUNNING.value
        ).first()
        
        if running_log:
            current_node_id = running_log.node_id
            current_node_name = running_log.node_name
    
    return ExecutionStatusResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        started_at=execution.started_at,
        ended_at=execution.ended_at,
        error_message=execution.error_message,
        current_node_id=current_node_id,
        current_node_name=current_node_name,
        progress_percent=progress_percent,
        created_at=execution.created_at,
    )


@router.get("/executions/{execution_id}/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行日志列表（不含执行记录详情）
    用于实时查看节点执行进度
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 验证工作流所有权
    workflow = workflow_service.get_workflow(db, execution.workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无权访问此执行记录"
        )
    
    logs = execution_service.get_execution_logs(db, execution_id)
    return [_parse_log_json(log) for log in logs]
