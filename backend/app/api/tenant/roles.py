"""
租户管理员角色 API

提供租户端角色 CRUD、权限分配等接口
"""

from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.base_controller import TenantController
from app.core.deps import DbSession
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.models import TenantAdmin, Permission
from app.models.auth.tenant_admin_role import TenantAdminRole
from app.rbac import require_tenant_admin_permissions
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
    action_create,
    action_update,
    action_delete,
)
from app.schemas.tenant import (
    TenantAdminRoleResponse,
    TenantAdminRoleDetailResponse,
    TenantAdminRoleCreateRequest,
    TenantAdminRoleUpdateRequest,
    TenantAdminRolePermissionsRequest,
)


@permission_resource(
    resource="role",
    name="角色管理",
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="users",
        path="/system/roles",
        component="system/role/List",
        parent="system",  # 父菜单: 权限管理
        sort_order=20,
    ),
    description="租户角色管理",
)
class TenantRoleController(TenantController):
    """
    租户角色控制器
    
    提供角色 CRUD、权限分配等接口
    """
    
    prefix = "/roles"
    tags = ["租户角色管理"]
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("", summary="获取角色列表")
        @action_read("查看角色列表")
        async def list_roles(
            db: DbSession,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取当前租户的所有角色
            
            权限: role:read
            """
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
                .order_by(TenantAdminRole.sort_order)
            )
            roles = result.scalars().all()
            
            return success(
                data=[TenantAdminRoleResponse.model_validate(r, from_attributes=True) for r in roles],
                message=_("common.success"),
            )
        
        @router.get("/{role_id}", summary="获取角色详情")
        @action_read("查看角色详情")
        async def get_role(
            db: DbSession,
            role_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取角色详情（含权限列表）
            
            权限: role:read
            """
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.id == role_id,
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
                .options(selectinload(TenantAdminRole.permissions))
            )
            role = result.scalar_one_or_none()
            
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            return success(
                data=TenantAdminRoleDetailResponse(
                    id=role.id,
                    tenant_id=role.tenant_id,
                    code=role.code,
                    name=role.name,
                    description=role.description,
                    is_system=role.is_system,
                    is_active=role.is_active,
                    sort_order=role.sort_order,
                    created_at=role.created_at,
                    permission_ids=[p.id for p in role.permissions],
                    permission_codes=[p.code for p in role.permissions],
                ),
                message=_("common.success"),
            )
        
        @router.post("", summary="创建角色")
        @action_create("创建角色")
        async def create_role(
            db: DbSession,
            data: TenantAdminRoleCreateRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:create")),
        ):
            """
            创建租户角色
            
            权限: role:create
            """
            # 检查代码是否已存在（租户内唯一）
            result = await db.execute(
                select(TenantAdminRole).where(
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.code == data.code,
                    TenantAdminRole.is_deleted == False,
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("role.code_exists"),
                )
            
            # 创建角色
            role = TenantAdminRole(
                tenant_id=current_admin.tenant_id,
                code=data.code,
                name=data.name,
                description=data.description,
                is_active=data.is_active,
                sort_order=data.sort_order,
                is_system=False,
            )
            
            # 关联权限（只能关联租户端权限）
            if data.permission_ids:
                perm_result = await db.execute(
                    select(Permission).where(
                        Permission.id.in_(data.permission_ids),
                        Permission.is_enabled == True,
                        Permission.is_deleted == False,
                        Permission.scope.in_(["tenant", "both"]),
                    )
                )
                role.permissions = list(perm_result.scalars().all())
            
            db.add(role)
            await db.commit()
            await db.refresh(role)
            
            return success(
                data=TenantAdminRoleResponse.model_validate(role, from_attributes=True),
                message=_("role.created"),
            )
        
        @router.put("/{role_id}", summary="更新角色")
        @action_update("更新角色")
        async def update_role(
            db: DbSession,
            role_id: int,
            data: TenantAdminRoleUpdateRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:update")),
        ):
            """
            更新租户角色
            
            权限: role:update
            """
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.id == role_id,
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
                .options(selectinload(TenantAdminRole.permissions))
            )
            role = result.scalar_one_or_none()
            
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            # 系统内置角色不可修改
            if role.is_system:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("role.system_role_cannot_modify"),
                )
            
            # 更新字段
            if data.name is not None:
                role.name = data.name
            if data.description is not None:
                role.description = data.description
            if data.is_active is not None:
                role.is_active = data.is_active
            if data.sort_order is not None:
                role.sort_order = data.sort_order
            
            # 更新权限
            if data.permission_ids is not None:
                perm_result = await db.execute(
                    select(Permission).where(
                        Permission.id.in_(data.permission_ids),
                        Permission.is_enabled == True,
                        Permission.is_deleted == False,
                        Permission.scope.in_(["tenant", "both"]),
                    )
                )
                role.permissions = list(perm_result.scalars().all())
            
            await db.commit()
            await db.refresh(role)
            
            return success(
                data=TenantAdminRoleResponse.model_validate(role, from_attributes=True),
                message=_("role.updated"),
            )
        
        @router.delete("/{role_id}", summary="删除角色")
        @action_delete("删除角色")
        async def delete_role(
            db: DbSession,
            role_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:delete")),
        ):
            """
            删除租户角色（软删除）
            
            权限: role:delete
            """
            result = await db.execute(
                select(TenantAdminRole).where(
                    TenantAdminRole.id == role_id,
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
            )
            role = result.scalar_one_or_none()
            
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            # 系统内置角色不可删除
            if role.is_system:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("role.system_role_cannot_delete"),
                )
            
            role.soft_delete()
            await db.commit()
            
            return success(
                message=_("role.deleted"),
            )
        
        @router.put("/{role_id}/permissions", summary="分配角色权限")
        @action_update("分配角色权限")
        async def assign_permissions(
            db: DbSession,
            role_id: int,
            data: TenantAdminRolePermissionsRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:update")),
        ):
            """
            分配角色权限
            
            权限: role:update
            """
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.id == role_id,
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
                .options(selectinload(TenantAdminRole.permissions))
            )
            role = result.scalar_one_or_none()
            
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            # 获取权限（只能分配租户端权限）
            perm_result = await db.execute(
                select(Permission).where(
                    Permission.id.in_(data.permission_ids),
                    Permission.is_enabled == True,
                    Permission.is_deleted == False,
                    Permission.scope.in_(["tenant", "both"]),
                )
            )
            role.permissions = list(perm_result.scalars().all())
            
            await db.commit()
            
            return success(
                message=_("role.permissions_updated"),
            )


# 导出路由器
router = TenantRoleController.get_router()

__all__ = ["router", "TenantRoleController"]
