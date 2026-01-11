"""
RBAC 权限管理模块

提供基于角色的访问控制功能：
- decorators: 权限装饰器（声明式定义权限）
- registry: 权限注册中心
- sync: 权限同步服务
"""

from app.rbac.decorators import (
    permission_resource,
    permission_action,
    action_read,
    action_create,
    action_update,
    action_delete,
    MenuConfig,
    PermissionMeta,
)
from app.rbac.registry import permission_registry

__all__ = [
    # 装饰器
    "permission_resource",
    "permission_action",
    "action_read",
    "action_create",
    "action_update",
    "action_delete",
    # 配置
    "MenuConfig",
    "PermissionMeta",
    # 注册中心
    "permission_registry",
]
