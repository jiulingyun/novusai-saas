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
]
