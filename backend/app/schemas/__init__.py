"""
Schema 模块

按模块分层组织，统一导出所有 Pydantic Schema

目录结构:
- common/: 公共 Schema（三端共用）
- system/: 平台管理后台 Schema
- tenant/: 租户相关 Schema
"""

# Common
from app.schemas.common import (
    TokenResponse,
    RefreshTokenRequest,
)

# System
from app.schemas.system import (
    AdminLoginRequest,
    AdminResponse,
    AdminCreateRequest,
    AdminUpdateRequest,
    AdminChangePasswordRequest,
)

# Tenant
from app.schemas.tenant import (
    TenantAdminLoginRequest,
    TenantAdminResponse,
    TenantAdminCreateRequest,
    TenantAdminUpdateRequest,
    TenantAdminChangePasswordRequest,
    TenantUserLoginRequest,
    TenantUserResponse,
    TenantUserCreateRequest,
    TenantUserUpdateRequest,
    TenantUserChangePasswordRequest,
)

__all__ = [
    # Common
    "TokenResponse",
    "RefreshTokenRequest",
    # System - Admin
    "AdminLoginRequest",
    "AdminResponse",
    "AdminCreateRequest",
    "AdminUpdateRequest",
    "AdminChangePasswordRequest",
    # Tenant - Admin
    "TenantAdminLoginRequest",
    "TenantAdminResponse",
    "TenantAdminCreateRequest",
    "TenantAdminUpdateRequest",
    "TenantAdminChangePasswordRequest",
    # Tenant - User
    "TenantUserLoginRequest",
    "TenantUserResponse",
    "TenantUserCreateRequest",
    "TenantUserUpdateRequest",
    "TenantUserChangePasswordRequest",
]
