"""
Schema 模块

导出所有 Pydantic Schema
"""

from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    LoginRequest,
    UserResponse,
    ChangePasswordRequest,
)
from app.schemas.admin import (
    AdminLoginRequest,
    AdminResponse,
    AdminCreateRequest,
    AdminUpdateRequest,
    AdminChangePasswordRequest,
)
from app.schemas.tenant_admin import (
    TenantAdminLoginRequest,
    TenantAdminResponse,
    TenantAdminCreateRequest,
    TenantAdminUpdateRequest,
    TenantAdminChangePasswordRequest,
)

__all__ = [
    # Auth
    "TokenResponse",
    "RefreshTokenRequest",
    "LoginRequest",
    "UserResponse",
    "ChangePasswordRequest",
    # Admin
    "AdminLoginRequest",
    "AdminResponse",
    "AdminCreateRequest",
    "AdminUpdateRequest",
    "AdminChangePasswordRequest",
    # TenantAdmin
    "TenantAdminLoginRequest",
    "TenantAdminResponse",
    "TenantAdminCreateRequest",
    "TenantAdminUpdateRequest",
    "TenantAdminChangePasswordRequest",
]
