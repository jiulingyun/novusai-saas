"""
平台角色相关 Schema

定义平台角色管理的请求和响应数据结构
"""

from datetime import datetime

from pydantic import Field

from app.core.base_schema import BaseSchema


class AdminRoleResponse(BaseSchema):
    """平台角色响应"""
    
    id: int = Field(..., description="角色 ID")
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    description: str | None = Field(None, description="角色描述")
    is_system: bool = Field(..., description="是否系统内置")
    is_active: bool = Field(..., description="是否启用")
    sort_order: int = Field(0, description="排序")
    created_at: datetime = Field(..., description="创建时间")


class AdminRoleDetailResponse(AdminRoleResponse):
    """平台角色详情响应（含权限）"""
    
    permission_ids: list[int] = Field(default_factory=list, description="权限 ID 列表")
    permission_codes: list[str] = Field(default_factory=list, description="权限代码列表")


class AdminRoleCreateRequest(BaseSchema):
    """创建平台角色请求"""
    
    code: str = Field(..., min_length=2, max_length=50, description="角色代码")
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")
    permission_ids: list[int] = Field(default_factory=list, description="权限 ID 列表")


class AdminRoleUpdateRequest(BaseSchema):
    """更新平台角色请求"""
    
    name: str | None = Field(None, min_length=1, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    is_active: bool | None = Field(None, description="是否启用")
    sort_order: int | None = Field(None, description="排序")
    permission_ids: list[int] | None = Field(None, description="权限 ID 列表")


class AdminRolePermissionsRequest(BaseSchema):
    """分配角色权限请求"""
    
    permission_ids: list[int] = Field(..., description="权限 ID 列表")


__all__ = [
    "AdminRoleResponse",
    "AdminRoleDetailResponse",
    "AdminRoleCreateRequest",
    "AdminRoleUpdateRequest",
    "AdminRolePermissionsRequest",
]
