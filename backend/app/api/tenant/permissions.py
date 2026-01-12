"""
租户管理员权限 API

提供租户端权限树、菜单等接口
"""

from fastapi import Depends

from sqlalchemy import select

from app.core.base_controller import TenantController
from app.core.deps import DbSession, ActiveTenantAdmin
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.models import Permission, TenantAdmin
from app.rbac import require_tenant_admin_permissions
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
)
from app.rbac.services import PermissionService
from app.schemas.common import PermissionTreeResponse, MenuResponse


def _translate_name(name: str) -> str:
    """翻译权限/菜单名称"""
    # 如果 name 是 i18n key 格式（包含点号），则翻译
    if name and "." in name:
        translated = _(name)
        # 如果翻译失败（返回原 key），尝试返回最后一段作为默认名称
        if translated == name:
            return name.split(".")[-1]
        return translated
    return name or ""


def build_permission_tree(
    permissions: list[Permission], 
    parent_id: int | None = None,
) -> list[PermissionTreeResponse]:
    """构建权限树"""
    tree = []
    for perm in permissions:
        if perm.parent_id == parent_id:
            children = build_permission_tree(permissions, perm.id)
            tree.append(PermissionTreeResponse(
                id=perm.id,
                code=perm.code,
                name=_translate_name(perm.name),
                description=perm.description,
                type=perm.type,
                scope=perm.scope,
                resource=perm.resource,
                action=perm.action,
                parent_id=perm.parent_id,
                sort_order=perm.sort_order,
                icon=perm.icon,
                path=perm.path,
                component=perm.component,
                hidden=perm.hidden,
                children=children,
            ))
    return sorted(tree, key=lambda x: x.sort_order)


def build_menu_tree(
    permissions: list[Permission],
    parent_id: int | None = None,
) -> list[MenuResponse]:
    """构建菜单树"""
    tree = []
    for perm in permissions:
        if perm.parent_id == parent_id and perm.type == "menu":
            children = build_menu_tree(permissions, perm.id)
            tree.append(MenuResponse(
                id=perm.id,
                code=perm.code,
                name=_translate_name(perm.name),
                icon=perm.icon,
                path=perm.path,
                component=perm.component,
                hidden=perm.hidden,
                sort_order=perm.sort_order,
                children=children,
            ))
    return sorted(tree, key=lambda x: x.sort_order)


@permission_resource(
    resource="permission",
    name="menu.tenant.permission",  # i18n key
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="key",
        path="/system/permissions",
        component="system/permission/List",
        parent="system",  # 父菜单: 权限管理
        sort_order=10,
        hidden=True,  # 一般隐藏，仅租户所有者可见
    ),
)
class TenantPermissionController(TenantController):
    """
    租户权限控制器
    
    提供权限树、菜单树等查询接口
    """
    
    prefix = "/permissions"
    tags = ["租户权限管理"]
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("", summary="获取权限树")
        @action_read("查看权限树")
        async def get_permission_tree(
            db: DbSession,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("permission:read")),
        ):
            """
            获取租户端所有可分配权限（树形结构）
            
            用于角色权限配置页面
            
            权限: permission:read
            """
            perm_service = PermissionService(db)
            permissions = await perm_service.get_enabled_permissions_by_scope("tenant")
            tree = build_permission_tree(permissions)
            
            return success(
                data=tree,
                message=_("common.success"),
            )
        
        @router.get("/menus", summary="获取当前用户菜单")
        async def get_current_user_menus(
            db: DbSession,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取当前租户管理员的菜单列表
            
            根据角色权限过滤，用于前端动态渲染菜单
            """
            perm_service = PermissionService(db)
            
            # 租户所有者获取所有菜单
            if current_admin.is_owner:
                all_permissions = await perm_service.get_enabled_permissions_by_scope("tenant")
                menus = build_menu_tree(all_permissions)
                return success(data=menus, message=_("common.success"))
            
            # 获取用户权限
            user_perms = await perm_service.get_tenant_admin_permissions(current_admin)
            
            # 获取所有菜单权限
            result = await db.execute(
                select(Permission)
                .where(
                    Permission.is_enabled == True,
                    Permission.is_deleted == False,
                    Permission.type == "menu",
                    Permission.scope.in_(["tenant", "both"]),
                )
                .order_by(Permission.sort_order)
            )
            all_menus = list(result.scalars().all())
            
            # 过滤出用户有权限的菜单
            user_menu_codes = {p for p in user_perms if p.startswith("menu:")}
            filtered_menus = [m for m in all_menus if m.code in user_menu_codes]
            
            # 补充父级菜单（确保树形结构完整）
            filtered_ids = {m.id for m in filtered_menus}
            for menu in all_menus:
                if menu.id not in filtered_ids:
                    has_child = any(m.parent_id == menu.id for m in filtered_menus)
                    if has_child:
                        filtered_menus.append(menu)
                        filtered_ids.add(menu.id)
            
            menus = build_menu_tree(filtered_menus)
            
            return success(
                data=menus,
                message=_("common.success"),
            )
        
        @router.get("/list", summary="获取权限列表（平铺）")
        @action_read("查看权限列表")
        async def get_permission_list(
            db: DbSession,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("permission:read")),
            type: str | None = None,
        ):
            """
            获取权限列表（非树形）
            
            - type: 可选过滤，menu/operation
            
            权限: permission:read
            """
            query = select(Permission).where(
                Permission.is_enabled == True,
                Permission.is_deleted == False,
                Permission.scope.in_(["tenant", "both"]),
            )
            
            if type:
                query = query.where(Permission.type == type)
            
            query = query.order_by(Permission.sort_order)
            
            result = await db.execute(query)
            permissions = result.scalars().all()
            
            return success(
                data=[PermissionTreeResponse.model_validate(p, from_attributes=True) for p in permissions],
                message=_("common.success"),
            )


# 导出路由器
router = TenantPermissionController.get_router()

__all__ = ["router", "TenantPermissionController"]
