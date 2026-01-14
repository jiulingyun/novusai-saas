"""
租户管理员角色 API

提供租户端角色 CRUD、权限分配、层级管理等接口
"""

from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.base_controller import TenantController
from app.core.deps import DbSession
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.exceptions import BusinessException, NotFoundException
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
    TenantAdminRoleTreeNode,
    TenantAdminRoleCreateRequest,
    TenantAdminRoleUpdateRequest,
    TenantAdminRolePermissionsRequest,
    TenantAdminRoleMoveRequest,
)
from app.schemas.common import PermissionResponse
from app.services.tenant.tenant_admin_role_service import TenantAdminRoleService
from app.services.common.role_hierarchy_validator import TenantAdminRoleHierarchyValidator


@permission_resource(
    resource="role",
    name="menu.tenant.role",  # i18n key
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="users",
        path="/system/roles",
        component="system/role/List",
        parent="system",  # 父菜单: 权限管理
        sort_order=20,
    ),
)
class TenantRoleController(TenantController):
    """
    租户角色控制器
    
    提供角色 CRUD、权限分配、层级管理等接口
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
            获取租户角色列表
            
            层级权限控制：
            - 租户所有者可以看到所有角色
            - 普通管理员只能看到自己的角色及其下级角色
            
            权限: role:read
            """
            # 获取可见角色 ID
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            visible_ids = await validator.get_visible_role_ids()
            
            if not visible_ids:
                return success(data=[], message=_("common.success"))
            
            # 查询可见角色
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                    TenantAdminRole.id.in_(visible_ids),
                )
                .options(
                    selectinload(TenantAdminRole.children),
                    selectinload(TenantAdminRole.admins),
                )
                .order_by(TenantAdminRole.sort_order)
            )
            roles = result.scalars().all()
            
            return success(
                data=[TenantAdminRoleResponse.model_validate(r, from_attributes=True) for r in roles],
                message=_("common.success"),
            )
        
        @router.get("/tree", summary="获取角色树")
        @action_read("查看角色树")
        async def get_role_tree(
            db: DbSession,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取角色树形结构
            
            层级权限控制：
            - 租户所有者可以看到完整角色树
            - 普通管理员只能看到以自己角色为根的子树
            
            权限: role:read
            """
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            # 租户所有者可以看到完整树
            if current_admin.is_owner:
                tree = await service.get_tree()
                return success(data=tree, message=_("common.success"))
            
            # 普通管理员只能看到以自己角色为根的子树
            if current_admin.role_id is None:
                return success(data=[], message=_("common.success"))
            
            tree = await service.get_tree(parent_id=current_admin.role_id)
            return success(data=tree, message=_("common.success"))
        
        @router.get("/{role_id}", summary="获取角色详情")
        @action_read("查看角色详情")
        async def get_role(
            db: DbSession,
            role_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取角色详情（含权限列表）
            
            层级权限控制：只能查看可见角色的详情
            
            权限: role:read
            """
            # 先查询角色是否存在
            result = await db.execute(
                select(TenantAdminRole)
                .where(
                    TenantAdminRole.id == role_id,
                    TenantAdminRole.tenant_id == current_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
                .options(
                    selectinload(TenantAdminRole.permissions),
                    selectinload(TenantAdminRole.children),
                    selectinload(TenantAdminRole.admins),
                )
            )
            role = result.scalar_one_or_none()
            
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            # 校验角色可见性
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            if not await validator.can_view_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_view"),
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
                    parent_id=role.parent_id,
                    path=role.path,
                    level=role.level,
                    children_count=role.children_count,
                    has_children=role.has_children,
                    created_at=role.created_at,
                    permission_ids=[p.id for p in role.permissions],
                    permission_codes=[p.code for p in role.permissions],
                ),
                message=_("common.success"),
            )
        
        @router.get("/{role_id}/children", summary="获取子角色")
        @action_read("查看子角色")
        async def get_role_children(
            db: DbSession,
            role_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取指定角色的直接子角色
            
            层级权限控制：只能查看可见角色的子角色
            
            权限: role:read
            """
            # 校验角色可见性
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            if not await validator.can_view_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_view"),
                )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            children = await service.get_children(role_id)
            
            # 加载关联以确保 property 可访问
            if children:
                role_ids = [c.id for c in children]
                result = await db.execute(
                    select(TenantAdminRole)
                    .where(TenantAdminRole.id.in_(role_ids))
                    .options(
                        selectinload(TenantAdminRole.children),
                        selectinload(TenantAdminRole.admins),
                    )
                )
                children = result.scalars().all()
            
            return success(
                data=[TenantAdminRoleResponse.model_validate(r, from_attributes=True) for r in children],
                message=_("common.success"),
            )
        
        @router.get("/{role_id}/permissions/effective", summary="获取有效权限")
        @action_read("查看有效权限")
        async def get_effective_permissions(
            db: DbSession,
            role_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:read")),
        ):
            """
            获取角色的有效权限（含继承的权限）
            
            层级权限控制：只能查看可见角色的有效权限
            
            权限: role:read
            """
            # 校验角色可见性
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            if not await validator.can_view_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_view"),
                )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            try:
                permissions = await service.get_effective_permissions(role_id)
            except NotFoundException:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            return success(
                data=[PermissionResponse.model_validate(p, from_attributes=True) for p in permissions],
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
            
            层级权限控制：
            - 租户所有者可以在任何位置创建角色
            - 普通管理员只能在自己角色或其下级角色下创建
            - 只能分配自己已拥有的权限
            
            权限: role:create
            """
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            
            # 校验父角色
            if not await validator.can_create_under_parent(data.parent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.parent_must_be_visible"),
                )
            
            # 校验权限分配
            if data.permission_ids:
                unassignable = await validator.get_unassignable_permissions(data.permission_ids)
                if unassignable:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=_("role.cannot_assign_permission"),
                    )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            try:
                role = await service.create_role(
                    name=data.name,
                    description=data.description,
                    is_active=data.is_active,
                    sort_order=data.sort_order,
                    parent_id=data.parent_id,
                )
                
                # 分配权限（只能分配租户端权限，且必须是自己拥有的）
                if data.permission_ids:
                    # 过滤只保留租户端权限
                    perm_result = await db.execute(
                        select(Permission.id).where(
                            Permission.id.in_(data.permission_ids),
                            Permission.scope.in_(["tenant", "both"]),
                            Permission.is_enabled == True,
                            Permission.is_deleted == False,
                        )
                    )
                    valid_perm_ids = [p for p in perm_result.scalars().all()]
                    if valid_perm_ids:
                        role = await service.assign_permissions(role.id, valid_perm_ids)
                
                await db.commit()
                
                # 重新加载角色以获取完整关联
                result = await db.execute(
                    select(TenantAdminRole)
                    .where(TenantAdminRole.id == role.id)
                    .options(
                        selectinload(TenantAdminRole.children),
                        selectinload(TenantAdminRole.admins),
                    )
                )
                role = result.scalar_one()
                
                return success(
                    data=TenantAdminRoleResponse.model_validate(role, from_attributes=True),
                    message=_("role.created"),
                )
                
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            except BusinessException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e.message),
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
            
            层级权限控制：
            - 只能更新自己的下级角色
            - 只能分配自己已拥有的权限
            
            权限: role:update
            """
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            
            # 校验角色可管理性
            if not await validator.can_manage_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_manage"),
                )
            
            # 如果更新父角色，校验新父角色
            if data.parent_id is not None:
                if not await validator.can_create_under_parent(data.parent_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=_("role.parent_must_be_visible"),
                    )
            
            # 校验权限分配
            if data.permission_ids is not None:
                unassignable = await validator.get_unassignable_permissions(data.permission_ids)
                if unassignable:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=_("role.cannot_assign_permission"),
                    )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            try:
                # 构建更新数据
                update_data = {}
                if data.name is not None:
                    update_data["name"] = data.name
                if data.description is not None:
                    update_data["description"] = data.description
                if data.is_active is not None:
                    update_data["is_active"] = data.is_active
                if data.sort_order is not None:
                    update_data["sort_order"] = data.sort_order
                if data.parent_id is not None:
                    update_data["parent_id"] = data.parent_id
                
                role = await service.update_role(role_id, update_data)
                
                # 更新权限（只能分配租户端权限，且必须是自己拥有的）
                if data.permission_ids is not None:
                    perm_result = await db.execute(
                        select(Permission.id).where(
                            Permission.id.in_(data.permission_ids),
                            Permission.scope.in_(["tenant", "both"]),
                            Permission.is_enabled == True,
                            Permission.is_deleted == False,
                        )
                    )
                    valid_perm_ids = [p for p in perm_result.scalars().all()]
                    role = await service.assign_permissions(role_id, valid_perm_ids)
                
                await db.commit()
                
                # 重新加载角色以获取完整关联
                result = await db.execute(
                    select(TenantAdminRole)
                    .where(TenantAdminRole.id == role.id)
                    .options(
                        selectinload(TenantAdminRole.children),
                        selectinload(TenantAdminRole.admins),
                    )
                )
                role = result.scalar_one()
                
                return success(
                    data=TenantAdminRoleResponse.model_validate(role, from_attributes=True),
                    message=_("role.updated"),
                )
                
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            except BusinessException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e.message),
                )
        
        @router.put("/{role_id}/move", summary="移动角色")
        @action_update("移动角色")
        async def move_role(
            db: DbSession,
            role_id: int,
            data: TenantAdminRoleMoveRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("role:update")),
        ):
            """
            移动角色到新的父节点
            
            层级权限控制：
            - 只能移动自己的下级角色
            - 目标父角色必须是自己的角色或其下级
            
            权限: role:update
            """
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            
            # 校验角色可管理性
            if not await validator.can_manage_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_manage"),
                )
            
            # 校验目标父角色
            if data.new_parent_id is not None:
                if not await validator.can_create_under_parent(data.new_parent_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=_("role.parent_must_be_visible"),
                    )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            try:
                role = await service.move_node(role_id, data.new_parent_id)
                await db.commit()
                
                # 重新加载角色以获取完整关联
                result = await db.execute(
                    select(TenantAdminRole)
                    .where(TenantAdminRole.id == role.id)
                    .options(
                        selectinload(TenantAdminRole.children),
                        selectinload(TenantAdminRole.admins),
                    )
                )
                role = result.scalar_one()
                
                return success(
                    data=TenantAdminRoleResponse.model_validate(role, from_attributes=True),
                    message=_("role.moved"),
                )
                
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            except BusinessException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e.message),
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
            
            层级权限控制：只能删除自己的下级角色
            
            删除前检查：
            - 系统内置角色不可删除
            - 有子角色的角色不可删除
            - 有关联用户的角色不可删除
            
            权限: role:delete
            """
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            # 先检查角色是否存在
            role = await service.repo.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("role.not_found"),
                )
            
            # 校验角色可管理性
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            if not await validator.can_manage_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_manage"),
                )
            
            try:
                await service.delete_role(role_id)
                await db.commit()
                
                return success(
                    message=_("role.deleted"),
                )
                
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            except BusinessException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e.message),
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
            
            层级权限控制：
            - 只能给自己的下级角色分配权限
            - 只能分配自己已拥有的权限
            
            权限: role:update
            """
            validator = TenantAdminRoleHierarchyValidator(db, current_admin)
            
            # 校验角色可管理性
            if not await validator.can_manage_role(role_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("role.no_permission_to_manage"),
                )
            
            # 校验权限分配
            if data.permission_ids:
                unassignable = await validator.get_unassignable_permissions(data.permission_ids)
                if unassignable:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=_("role.cannot_assign_permission"),
                    )
            
            service = TenantAdminRoleService(db, current_admin.tenant_id)
            
            try:
                # 过滤只保留租户端权限
                perm_result = await db.execute(
                    select(Permission.id).where(
                        Permission.id.in_(data.permission_ids),
                        Permission.scope.in_(["tenant", "both"]),
                        Permission.is_enabled == True,
                        Permission.is_deleted == False,
                    )
                )
                valid_perm_ids = [p for p in perm_result.scalars().all()]
                
                await service.assign_permissions(role_id, valid_perm_ids)
                await db.commit()
                
                return success(
                    message=_("role.permissions_updated"),
                )
                
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )


# 导出路由器
router = TenantRoleController.get_router()

__all__ = ["router", "TenantRoleController"]
