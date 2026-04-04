"""
工作流 API 路由
工作流的 CRUD 操作和执行
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse
)
from app.schemas.execution import ExecutionResponse
from app.services.auth_service import get_current_user
from app.services import workflow_service, execution_service
from app.config import settings

router = APIRouter(prefix="/api/workflows", tags=["工作流"])


class WorkflowValidationError(BaseModel):
    """工作流验证错误"""
    field: str  # name / nodes / trigger_config
    message: str
    node_id: Optional[str] = None  # 如与特定节点相关


class WorkflowValidationResponse(BaseModel):
    """工作流验证结果"""
    valid: bool
    errors: List[WorkflowValidationError] = []


# 支持的节点类型
VALID_NODE_TYPES = {"trigger", "ai_task", "tool", "condition"}
VALID_TOOL_TYPES = {"feishu_message", "feishu_doc", "http_request"}
VALID_TRIGGER_TYPES = {"manual", "cron"}


def _parse_workflow_json(workflow: Workflow) -> dict:
    """将工作流的JSON字符串字段解析为Python对象"""
    data = {
        "id": workflow.id,
        "user_id": workflow.user_id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }
    
    # 解析 trigger_config
    if workflow.trigger_config:
        try:
            data["trigger_config"] = json.loads(workflow.trigger_config)
        except (json.JSONDecodeError, TypeError):
            data["trigger_config"] = None
    else:
        data["trigger_config"] = None
    
    # 解析 nodes
    if workflow.nodes:
        try:
            data["nodes"] = json.loads(workflow.nodes)
        except (json.JSONDecodeError, TypeError):
            data["nodes"] = None
    else:
        data["nodes"] = None
    
    return data


@router.post("/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证工作流配置（不保存）
    用于工作流设计器保存前检查配置的合法性
    """
    errors: List[WorkflowValidationError] = []
    
    # 1. 验证名称
    if not workflow_data.name or not workflow_data.name.strip():
        errors.append(WorkflowValidationError(
            field="name",
            message="工作流名称不能为空"
        ))
    elif len(workflow_data.name) > 200:
        errors.append(WorkflowValidationError(
            field="name",
            message="工作流名称不能超过200个字符"
        ))
    
    # 2. 验证描述长度
    if workflow_data.description and len(workflow_data.description) > 2000:
        errors.append(WorkflowValidationError(
            field="description",
            message="工作流描述不能超过2000个字符"
        ))
    
    # 3. 验证节点
    nodes = workflow_data.nodes or []
    
    if not nodes:
        errors.append(WorkflowValidationError(
            field="nodes",
            message="工作流必须包含至少一个节点"
        ))
    else:
        # 检查节点数量
        if len(nodes) > settings.MAX_NODES_PER_WORKFLOW:
            errors.append(WorkflowValidationError(
                field="nodes",
                message=f"工作流最多包含 {settings.MAX_NODES_PER_WORKFLOW} 个节点"
            ))
        
        # 检查是否有重复ID
        node_ids = [n.get("id") for n in nodes if n.get("id")]
        if len(node_ids) != len(set(node_ids)):
            errors.append(WorkflowValidationError(
                field="nodes",
                message="存在重复的节点ID"
            ))
        
        # 验证每个节点
        for i, node in enumerate(nodes):
            node_id = node.get("id", f"index_{i}")
            node_type = node.get("type")
            
            # 节点类型验证
            if not node_type:
                errors.append(WorkflowValidationError(
                    field="nodes",
                    message=f"节点 {node_id} 缺少 type 字段",
                    node_id=node_id
                ))
            elif node_type not in VALID_NODE_TYPES:
                errors.append(WorkflowValidationError(
                    field="nodes",
                    message=f"节点 {node_id} 的类型 '{node_type}' 不支持",
                    node_id=node_id
                ))
            
            # 节点名称验证
            if not node.get("name"):
                errors.append(WorkflowValidationError(
                    field="nodes",
                    message=f"节点 {node_id} 缺少 name 字段",
                    node_id=node_id
                ))
            
            # 触发器节点检查
            if node_type == "trigger":
                trigger_cfg = node.get("config", {})
                trigger_type = trigger_cfg.get("type", "manual")
                if trigger_type not in VALID_TRIGGER_TYPES:
                    errors.append(WorkflowValidationError(
                        field="nodes",
                        message=f"触发器 {node_id} 的类型 '{trigger_type}' 不支持",
                        node_id=node_id
                    ))
                if trigger_type == "cron" and not trigger_cfg.get("cron_expression"):
                    errors.append(WorkflowValidationError(
                        field="nodes",
                        message=f"触发器 {node_id} 设置为定时触发但未提供 Cron 表达式",
                        node_id=node_id
                    ))
            
            # 工具节点检查
            if node_type == "tool":
                tool_cfg = node.get("config", {})
                tool_type = tool_cfg.get("tool_type")
                if tool_type and tool_type not in VALID_TOOL_TYPES:
                    errors.append(WorkflowValidationError(
                        field="nodes",
                        message=f"工具节点 {node_id} 的工具类型 '{tool_type}' 不支持",
                        node_id=node_id
                    ))
    
    # 4. 验证触发器配置
    trigger_cfg = workflow_data.trigger_config
    if trigger_cfg:
        trigger_type = trigger_cfg.get("type")
        if trigger_type and trigger_type not in VALID_TRIGGER_TYPES:
            errors.append(WorkflowValidationError(
                field="trigger_config",
                message=f"触发器类型 '{trigger_type}' 不支持"
            ))
        if trigger_type == "cron" and not trigger_cfg.get("expression"):
            errors.append(WorkflowValidationError(
                field="trigger_config",
                message="定时触发器未提供 Cron 表达式"
            ))
    
    return WorkflowValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新工作流
    """
    result = workflow_service.create_workflow(db, current_user, workflow_data)
    return _parse_workflow_json(result)


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的工作流列表
    """
    workflows = workflow_service.get_workflows(db, current_user.id, skip, limit)
    total = workflow_service.count_workflows(db, current_user.id)
    items = [_parse_workflow_json(w) for w in workflows]
    return {"items": items, "total": total}


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定工作流详情
    """
    workflow = workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    return _parse_workflow_json(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新工作流
    """
    result = workflow_service.update_workflow(db, workflow_id, current_user.id, workflow_data)
    return _parse_workflow_json(result)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除工作流
    """
    workflow_service.delete_workflow(db, workflow_id, current_user.id)
    return None


@router.post("/{workflow_id}/publish", response_model=WorkflowResponse)
async def publish_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发布工作流
    发布后工作流可以被定时触发执行
    """
    result = workflow_service.publish_workflow(db, workflow_id, current_user.id)
    return _parse_workflow_json(result)


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_workflow(
    workflow_id: int,
    trigger_input: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动执行工作流
    这是一个异步操作，立即返回执行记录ID，状态为 'running'
    轮询 /api/executions/{id}/status 可获取实时进度
    """
    workflow = workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    if workflow.status != "published" and workflow.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流状态为 {workflow.status}，无法执行"
        )
    
    if not workflow.nodes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流没有配置节点"
        )
    
    # 执行工作流（异步）
    execution = await execution_service.execute_workflow(
        db=db,
        workflow=workflow,
        trigger_type="manual",
        trigger_input=trigger_input
    )
    
    # 解析执行记录的JSON字段
    import json as _json
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
    
    if execution.trigger_input:
        try:
            data["trigger_input"] = _json.loads(execution.trigger_input)
        except:
            data["trigger_input"] = None
    else:
        data["trigger_input"] = None
    
    return ExecutionResponse(**data)
