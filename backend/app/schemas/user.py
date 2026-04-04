"""
Pydantic schemas for User
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """用户创建Schema"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """用户登录Schema - 支持邮箱登录"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """用户响应Schema"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    """用户简要信息（用于登录响应）"""
    id: int
    name: str
    email: str


class Token(BaseModel):
    """JWT Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[UserBrief] = None


class TokenData(BaseModel):
    """Token中包含的用户数据"""
    user_id: Optional[int] = None


class TokenRefreshRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str
