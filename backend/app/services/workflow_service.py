"""
工作流服务
工作流的 CRUD 操作
"""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.workflow import Workflow, WorkflowStatus
from app.models.user import User
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.config import settings


def get_workflow(db: Session, workflow_id: int, user_id: int) -> Optional[Workflow]:
    """获取工作流（验证所有权）"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == user_id
    ).first()
    return workflow


def get_workflows(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Workflow]:
    """获取用户的所有工作流"""
    return db.query(Workflow).filter(
        Workflow.user_id == user_id
    ).order_by(Workflow.updated_at.desc()).offset(skip).limit(limit).all()


def count_workflows(db: Session, user_id: int) -> int:
    """统计用户的工作流数量"""
    return db.query(Workflow).filter(Workflow.user_id == user_id).count()


def create_workflow(db: Session, user: User, workflow_data: WorkflowCreate) -> Workflow:
    """创建工作流"""
    # 检查工作流数量限制
    current_count = count_workflows(db, user.id)
    # 如果有数量限制，可以在这里检查
    # 目前MVP不限制数量
    
    workflow = Workflow(
        user_id=user.id,
        name=workflow_data.name,
        description=workflow_data.description,
        trigger_config=json.dumps(workflow_data.trigger_config) if workflow_data.trigger_config else None,
        nodes=json.dumps(workflow_data.nodes) if workflow_data.nodes else None,
        status=WorkflowStatus.DRAFT.value
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def update_workflow(
    db: Session, 
    workflow_id: int, 
    user_id: int, 
    workflow_data: WorkflowUpdate
) -> Workflow:
    """更新工作流"""
    workflow = get_workflow(db, workflow_id, user_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 更新字段
    update_data = workflow_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "trigger_config" and value is not None:
            setattr(workflow, field, json.dumps(value))
        elif field == "nodes" and value is not None:
            setattr(workflow, field, json.dumps(value))
        else:
            setattr(workflow, field, value)
    
    db.commit()
    db.refresh(workflow)
    return workflow


def delete_workflow(db: Session, workflow_id: int, user_id: int) -> bool:
    """删除工作流"""
    workflow = get_workflow(db, workflow_id, user_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    db.delete(workflow)
    db.commit()
    return True


def publish_workflow(db: Session, workflow_id: int, user_id: int) -> Workflow:
    """发布工作流"""
    workflow = get_workflow(db, workflow_id, user_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 验证工作流配置
    if not workflow.nodes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流必须包含至少一个节点"
        )
    
    # 检查节点数量
    nodes = json.loads(workflow.nodes) if workflow.nodes else []
    if len(nodes) > settings.MAX_NODES_PER_WORKFLOW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流最多包含 {settings.MAX_NODES_PER_WORKFLOW} 个节点"
        )
    
    # 检查是否有触发器节点
    has_trigger = any(node.get("type") == "trigger" for node in nodes)
    if not has_trigger:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流必须包含触发器节点"
        )
    
    workflow.status = WorkflowStatus.PUBLISHED.value
    db.commit()
    db.refresh(workflow)
    return workflow
