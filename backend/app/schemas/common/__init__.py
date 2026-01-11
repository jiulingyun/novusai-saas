"""
公共 Schema 模块

导出三端共用的 Schema
"""

from app.schemas.common.auth import (
    TokenResponse,
    RefreshTokenRequest,
)

__all__ = [
    "TokenResponse",
    "RefreshTokenRequest",
]
