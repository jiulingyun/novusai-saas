"""
RBAC 权限相关枚举

定义权限类型、作用域等枚举
"""

from app.enums.base import StrEnum


class PermissionType(StrEnum):
    """权限类型"""
    
    MENU = ("menu", "enum.permission_type.menu")
    OPERATION = ("operation", "enum.permission_type.operation")


class PermissionScope(StrEnum):
    """权限作用域"""
    
    ADMIN = ("admin", "enum.permission_scope.admin")
    TENANT = ("tenant", "enum.permission_scope.tenant")
    BOTH = ("both", "enum.permission_scope.both")


__all__ = [
    "PermissionType",
    "PermissionScope",
]
