"""
租户相关 Schema

定义租户 API 的请求和响应数据结构
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.base_schema import BaseSchema


class TenantResponse(BaseSchema):
    """租户信息响应"""
    
    id: int = Field(..., description="租户 ID")
    code: str = Field(..., description="租户编码")
    name: str = Field(..., description="租户名称")
    contact_name: str | None = Field(None, description="联系人姓名")
    contact_phone: str | None = Field(None, description="联系人电话")
    contact_email: str | None = Field(None, description="联系人邮箱")
    is_active: bool = Field(..., description="是否启用")
    plan: str = Field(..., description="套餐类型")
    quota: dict[str, Any] | None = Field(None, description="配额配置")
    expires_at: datetime | None = Field(None, description="到期时间")
    remark: str | None = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TenantCreateRequest(BaseSchema):
    """创建租户请求"""
    
    code: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        pattern=r"^[a-z][a-z0-9_-]*$",
        description="租户编码（唯一标识，小写字母开头，只能包含小写字母、数字、下划线、中划线）"
    )
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    contact_name: str | None = Field(None, max_length=50, description="联系人姓名")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    contact_email: str | None = Field(None, description="联系人邮箱")
    plan: str = Field("free", description="套餐类型")
    quota: dict[str, Any] | None = Field(None, description="配额配置")
    expires_at: datetime | None = Field(None, description="到期时间")
    remark: str | None = Field(None, max_length=500, description="备注")


class TenantUpdateRequest(BaseSchema):
    """更新租户请求"""
    
    name: str | None = Field(None, min_length=1, max_length=100, description="租户名称")
    contact_name: str | None = Field(None, max_length=50, description="联系人姓名")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    contact_email: str | None = Field(None, description="联系人邮箱")
    plan: str | None = Field(None, description="套餐类型")
    quota: dict[str, Any] | None = Field(None, description="配额配置")
    expires_at: datetime | None = Field(None, description="到期时间")
    remark: str | None = Field(None, max_length=500, description="备注")


class TenantStatusRequest(BaseSchema):
    """租户状态切换请求"""
    
    is_active: bool = Field(..., description="是否启用")


class TenantImpersonateRequest(BaseSchema):
    """一键登录租户后台请求"""
    
    role_id: int | None = Field(None, description="目标角色 ID（可选）")


class TenantImpersonateResponse(BaseSchema):
    """一键登录租户后台响应"""
    
    impersonate_token: str = Field(..., description="一键登录 Token（60秒有效，一次性）")
    tenant_code: str = Field(..., description="租户编码")
    tenant_name: str = Field(..., description="租户名称")
    expires_in: int = Field(60, description="Token 有效期（秒）")


__all__ = [
    "TenantResponse",
    "TenantCreateRequest",
    "TenantUpdateRequest",
    "TenantStatusRequest",
    "TenantImpersonateRequest",
    "TenantImpersonateResponse",
]
