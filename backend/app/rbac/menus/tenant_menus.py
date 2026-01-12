"""
租户管理端菜单定义

定义租户管理后台的目录型菜单结构，叶子菜单通过控制器装饰器声明。

菜单层级示例:
- 仪表板 (dashboard)
- 权限管理 (system)
  ├── 用户管理 (tenant_user) - 由控制器声明
  └── 角色管理 (role) - 由控制器声明
- 业务管理 (business) - 预留，具体子菜单由业务控制器声明
"""

from app.enums.rbac import PermissionType, PermissionScope
from app.rbac.decorators import PermissionMeta


# 租户管理端目录菜单
TENANT_DIRECTORY_MENUS: list[PermissionMeta] = [
    # ========================================
    # 仪表板（首页，叶子菜单）
    # ========================================
    PermissionMeta(
        code="menu:tenant.dashboard",
        name="仪表板",
        type=PermissionType.MENU,
        scope=PermissionScope.TENANT,
        resource="menu",
        action="tenant.dashboard",
        icon="dashboard",
        path="/dashboard",
        component="dashboard/Index",
        sort_order=0,
    ),
    
    # ========================================
    # 权限管理（目录）
    # ========================================
    PermissionMeta(
        code="menu:tenant.system",
        name="权限管理",
        type=PermissionType.MENU,
        scope=PermissionScope.TENANT,
        resource="menu",
        action="tenant.system",
        icon="setting",
        path="/system",
        sort_order=10,
    ),
    # 子菜单由控制器声明:
    # - menu:tenant.tenant_user (用户管理)
    # - menu:tenant.permission (权限管理) - 可选，一般隐藏
    # - menu:tenant.role (角色管理)
    
    # ========================================
    # 业务管理（目录，预留）
    # ========================================
    # PermissionMeta(
    #     code="menu:tenant.business",
    #     name="业务管理",
    #     type=PermissionType.MENU,
    #     scope=PermissionScope.TENANT,
    #     resource="menu",
    #     action="tenant.business",
    #     icon="appstore",
    #     path="/business",
    #     sort_order=20,
    # ),
]


__all__ = ["TENANT_DIRECTORY_MENUS"]
