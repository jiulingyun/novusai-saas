"""
权限装饰器

通过装饰器在控制器上声明式定义权限，应用启动时自动扫描并同步到数据库
"""

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, TypeVar

from app.enums.rbac import PermissionType, PermissionScope

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MenuConfig:
    """菜单配置"""
    
    icon: str | None = None
    path: str | None = None
    component: str | None = None
    parent: str | None = None  # 父菜单资源标识
    sort_order: int = 0
    hidden: bool = False  # 是否隐藏菜单（仅做权限控制）


@dataclass
class PermissionMeta:
    """权限元信息"""
    
    code: str
    name: str
    type: PermissionType
    scope: PermissionScope
    resource: str
    action: str
    description: str = ""
    # 菜单专用
    icon: str | None = None
    path: str | None = None
    component: str | None = None
    parent_code: str | None = None
    sort_order: int = 0
    hidden: bool = False


def permission_resource(
    resource: str,
    name: str,
    scope: PermissionScope = PermissionScope.TENANT,
    menu: MenuConfig | None = None,
    description: str = "",
) -> Callable[[type], type]:
    """
    资源权限装饰器（用于控制器类）
    
    自动注册：
    1. 菜单权限（如果提供了 menu 配置）
    2. 操作权限（通过 @action_* 装饰器自动扫描）
    
    Args:
        resource: 资源标识，如 "user", "order"
        name: 资源名称，如 "用户管理"
        scope: 权限作用域
        menu: 菜单配置（可选）
        description: 描述
    
    Example:
        @permission_resource(
            resource="user",
            name="用户管理",
            scope=PermissionScope.TENANT,
            menu=MenuConfig(icon="user", path="/users", component="user/List")
        )
        class UserController:
            # 操作权限通过 @action_read 等装饰器自动注册
            @action_read("查看用户")
            async def list_users(self, ...):
                ...
    """
    # 延迟导入避免循环引用
    from app.rbac.registry import permission_registry
    
    def decorator(cls: type) -> type:
        # 保存资源元信息到类属性
        cls._permission_resource = resource  # type: ignore
        cls._permission_name = name  # type: ignore
        cls._permission_scope = scope  # type: ignore
        
        # 注册菜单权限
        if menu:
            scope_prefix = "admin" if scope == PermissionScope.ADMIN else "tenant"
            menu_code = f"menu:{scope_prefix}.{resource}"
            parent_code = None
            if menu.parent:
                parent_code = f"menu:{scope_prefix}.{menu.parent}"
            
            menu_perm = PermissionMeta(
                code=menu_code,
                name=name,
                type=PermissionType.MENU,
                scope=scope,
                resource="menu",
                action=f"{scope_prefix}.{resource}",
                description=description,
                icon=menu.icon,
                path=menu.path,
                component=menu.component,
                parent_code=parent_code,
                sort_order=menu.sort_order,
                hidden=menu.hidden,
            )
            permission_registry.register(menu_perm)
        
        return cls
    
    return decorator


def permission_action(
    action: str,
    name: str,
    description: str = "",
    auto_check: bool = True,
) -> Callable[[F], F]:
    """
    操作权限装饰器（用于控制器方法）
    
    在路由注册时自动将操作权限注册到 permission_registry。
    
    Args:
        action: 操作标识，如 "create", "read", "update", "delete"
        name: 操作名称，如 "创建用户"
        description: 描述
        auto_check: 是否自动检查权限（默认 True，由依赖注入处理）
    
    Example:
        @action_read("查看用户列表")
        async def list_users(...):
            ...
    """
    def decorator(func: F) -> F:
        # 保存操作元信息到函数属性
        func._permission_action = {  # type: ignore
            "action": action,
            "name": name,
            "description": description,
            "auto_check": auto_check,
        }
        
        # 标记需要的权限（用于依赖注入检查）
        func._required_permission_action = action  # type: ignore
        
        return func
    
    return decorator


# ==================== 快捷装饰器 ====================

def action_read(name: str = "查看", **kwargs: Any) -> Callable[[F], F]:
    """查看权限快捷装饰器"""
    return permission_action("read", name, **kwargs)


def action_create(name: str = "创建", **kwargs: Any) -> Callable[[F], F]:
    """创建权限快捷装饰器"""
    return permission_action("create", name, **kwargs)


def action_update(name: str = "编辑", **kwargs: Any) -> Callable[[F], F]:
    """编辑权限快捷装饰器"""
    return permission_action("update", name, **kwargs)


def action_delete(name: str = "删除", **kwargs: Any) -> Callable[[F], F]:
    """删除权限快捷装饰器"""
    return permission_action("delete", name, **kwargs)


def action_export(name: str = "导出", **kwargs: Any) -> Callable[[F], F]:
    """导出权限快捷装饰器"""
    return permission_action("export", name, **kwargs)


def action_import(name: str = "导入", **kwargs: Any) -> Callable[[F], F]:
    """导入权限快捷装饰器"""
    return permission_action("import", name, **kwargs)


# ==================== 操作权限自动注册 ====================

def register_action_permissions(controller_cls: type, router: Any) -> None:
    """
    扫描路由器上的路由，自动注册操作权限
    
    在控制器的 _register_routes 执行后调用，扫描路由器上所有带有
    _permission_action 属性的路由处理函数，并注册到 permission_registry。
    
    Args:
        controller_cls: 控制器类（带有 _permission_resource 等属性）
        router: FastAPI APIRouter 实例
    """
    from app.rbac.registry import permission_registry
    
    # 获取控制器的资源信息
    resource = getattr(controller_cls, "_permission_resource", None)
    scope = getattr(controller_cls, "_permission_scope", None)
    
    if not resource or not scope:
        return
    
    # 已注册的操作（避免重复）
    registered_actions: set[str] = set()
    
    # 扫描路由器上的所有路由
    for route in router.routes:
        # 获取路由的 endpoint 函数
        endpoint = getattr(route, "endpoint", None)
        if not endpoint:
            continue
        
        # 检查是否有 _permission_action 属性
        action_info = getattr(endpoint, "_permission_action", None)
        if not action_info:
            continue
        
        action = action_info["action"]
        
        # 避免重复注册
        if action in registered_actions:
            continue
        registered_actions.add(action)
        
        # 注册操作权限
        action_perm = PermissionMeta(
            code=f"{resource}:{action}",
            name=action_info["name"],
            type=PermissionType.OPERATION,
            scope=scope,
            resource=resource,
            action=action,
            description=action_info.get("description", ""),
        )
        permission_registry.register(action_perm)


__all__ = [
    "MenuConfig",
    "PermissionMeta",
    "permission_resource",
    "permission_action",
    "action_read",
    "action_create",
    "action_update",
    "action_delete",
    "action_export",
    "action_import",
    # 用于手动注册操作权限
    "register_action_permissions",
]
