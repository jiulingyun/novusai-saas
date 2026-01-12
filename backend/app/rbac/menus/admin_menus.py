"""
平台管理端菜单定义

定义平台管理后台的目录型菜单结构，叶子菜单通过控制器装饰器声明。

菜单层级示例:
- 仪表板 (dashboard)
- 权限管理 (system)
  ├── 用户管理 (admin_user) - 由控制器声明
  └── 角色管理 (role) - 由控制器声明
- 租户管理 (tenant_mgmt)
  └── 租户列表 (tenant) - 由控制器声明
"""

from app.enums.rbac import PermissionType, PermissionScope
from app.rbac.decorators import PermissionMeta


# 平台管理端目录菜单
ADMIN_DIRECTORY_MENUS: list[PermissionMeta] = [
    # ========================================
    # 仪表板（首页，叶子菜单）
    # ========================================
    PermissionMeta(
        code="menu:admin.dashboard",
        name="仪表板",
        type=PermissionType.MENU,
        scope=PermissionScope.ADMIN,
        resource="menu",
        action="admin.dashboard",
        icon="dashboard",
        path="/dashboard",
        component="dashboard/Index",
        sort_order=0,
    ),
    
    # ========================================
    # 权限管理（目录）
    # ========================================
    PermissionMeta(
        code="menu:admin.system",
        name="权限管理",
        type=PermissionType.MENU,
        scope=PermissionScope.ADMIN,
        resource="menu",
        action="admin.system",
        icon="setting",
        path="/system",
        sort_order=10,
    ),
    # 子菜单由控制器声明:
    # - menu:admin.admin_user (用户管理)
    # - menu:admin.permission (权限管理) - 可选，一般隐藏
    # - menu:admin.role (角色管理)
    
    # ========================================
    # 租户管理（目录）
    # ========================================
    PermissionMeta(
        code="menu:admin.tenant_mgmt",
        name="租户管理",
        type=PermissionType.MENU,
        scope=PermissionScope.ADMIN,
        resource="menu",
        action="admin.tenant_mgmt",
        icon="apartment",
        path="/tenant",
        sort_order=20,
    ),
    # 子菜单由控制器声明:
    # - menu:admin.tenant (租户列表)
]


__all__ = ["ADMIN_DIRECTORY_MENUS"]
