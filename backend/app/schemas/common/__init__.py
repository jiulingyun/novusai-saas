"""
公共 Schema 模块

导出三端共用的 Schema
"""

from app.schemas.common.auth import (
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.common.permission import (
    PermissionResponse,
    PermissionTreeResponse,
    MenuResponse,
)

__all__ = [
    "TokenResponse",
    "RefreshTokenRequest",
    "PermissionResponse",
    "PermissionTreeResponse",
    "MenuResponse",
]
