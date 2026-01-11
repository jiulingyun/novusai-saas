"""
租户 Schema 模块

导出租户相关的 Schema
"""

from app.schemas.tenant.admin import (
    TenantAdminLoginRequest,
    TenantAdminResponse,
    TenantAdminCreateRequest,
    TenantAdminUpdateRequest,
    TenantAdminChangePasswordRequest,
)
from app.schemas.tenant.user import (
    TenantUserLoginRequest,
    TenantUserResponse,
    TenantUserCreateRequest,
    TenantUserUpdateRequest,
    TenantUserChangePasswordRequest,
)

__all__ = [
    # TenantAdmin
    "TenantAdminLoginRequest",
    "TenantAdminResponse",
    "TenantAdminCreateRequest",
    "TenantAdminUpdateRequest",
    "TenantAdminChangePasswordRequest",
    # TenantUser
    "TenantUserLoginRequest",
    "TenantUserResponse",
    "TenantUserCreateRequest",
    "TenantUserUpdateRequest",
    "TenantUserChangePasswordRequest",
]
