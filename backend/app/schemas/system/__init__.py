"""
平台管理后台 Schema 模块

导出平台管理相关的 Schema
"""

from app.schemas.system.admin import (
    AdminLoginRequest,
    AdminResponse,
    AdminCreateRequest,
    AdminUpdateRequest,
    AdminChangePasswordRequest,
)
from app.schemas.system.role import (
    AdminRoleResponse,
    AdminRoleDetailResponse,
    AdminRoleCreateRequest,
    AdminRoleUpdateRequest,
    AdminRolePermissionsRequest,
)

__all__ = [
    # Admin
    "AdminLoginRequest",
    "AdminResponse",
    "AdminCreateRequest",
    "AdminUpdateRequest",
    "AdminChangePasswordRequest",
    # Role
    "AdminRoleResponse",
    "AdminRoleDetailResponse",
    "AdminRoleCreateRequest",
    "AdminRoleUpdateRequest",
    "AdminRolePermissionsRequest",
]
