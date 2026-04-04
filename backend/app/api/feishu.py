"""
飞书集成 API 路由
发送消息、创建文档等
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services import feishu_service

router = APIRouter(prefix="/api/integrations/feishu", tags=["飞书集成"])


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    receive_id: str
    receive_id_type: str = "chat_id"  # open_id / chat_id
    text: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class CreateDocRequest(BaseModel):
    """创建文档请求"""
    title: str
    content: Optional[str] = None


class ReadDocRequest(BaseModel):
    """读取文档请求"""
    document_id: str


@router.post("/send-message")
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送飞书消息
    """
    if not request.text and not request.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 text 或 content 参数"
        )
    
    try:
        result = await feishu_service.send_message(
            receive_id=request.receive_id,
            receive_id_type=request.receive_id_type,
            text=request.text,
            content=request.content
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )


@router.post("/create-doc")
async def create_document(
    request: CreateDocRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建飞书云文档
    """
    try:
        result = await feishu_service.create_document(
            title=request.title,
            content=request.content
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文档失败: {str(e)}"
        )


@router.post("/read-doc")
async def read_document(
    request: ReadDocRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    读取飞书云文档内容
    """
    try:
        result = await feishu_service.read_document(
            document_id=request.document_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取文档失败: {str(e)}"
        )
