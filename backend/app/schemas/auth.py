"""
认证相关 Schema

定义认证 API 的请求和响应数据结构
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.base_schema import BaseSchema


class TokenResponse(BaseSchema):
    """Token 响应"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class RefreshTokenRequest(BaseSchema):
    """刷新 Token 请求"""
    
    refresh_token: str = Field(..., description="刷新令牌")


class LoginRequest(BaseSchema):
    """登录请求（JSON 格式）"""
    
    username: str = Field(..., min_length=1, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="密码")


class UserResponse(BaseSchema):
    """用户信息响应"""
    
    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    phone: str | None = Field(None, description="手机号")
    nickname: str | None = Field(None, description="昵称")
    avatar: str | None = Field(None, description="头像 URL")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级管理员")
    tenant_id: int | None = Field(None, description="租户 ID")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")


class ChangePasswordRequest(BaseSchema):
    """修改密码请求"""
    
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


__all__ = [
    "TokenResponse",
    "RefreshTokenRequest",
    "LoginRequest",
    "UserResponse",
    "ChangePasswordRequest",
]
