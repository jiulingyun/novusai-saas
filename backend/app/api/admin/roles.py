"""
平台管理员角色 API

提供平台端角色 CRUD、权限分配等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.i18n import _
from app.core.response import success
from app.models import Admin, Permission
from app.models.auth.admin_role import AdminRole
from app.rbac import require_admin_permissions
from app.schemas.system import (
    AdminRoleResponse,
    AdminRoleDetailResponse,
    AdminRoleCreateRequest,
    AdminRoleUpdateRequest,
    AdminRolePermissionsRequest,
)


router = APIRouter(prefix="/roles", tags=["平台角色管理"])


@router.get("", summary="获取角色列表")
async def list_roles(
    db: DbSession,
    current_admin: Admin = Depends(require_admin_permissions("role:read")),
):
    """
    获取所有平台角色
    
    权限: role:read
    """
    result = await db.execute(
        select(AdminRole)
        .where(AdminRole.is_deleted == False)
        .order_by(AdminRole.sort_order)
    )
    roles = result.scalars().all()
    
    return success(
        data=[AdminRoleResponse.model_validate(r, from_attributes=True) for r in roles],
        message=_("common.success"),
    )


@router.get("/{role_id}", summary="获取角色详情")
async def get_role(
    db: DbSession,
    role_id: int,
    current_admin: Admin = Depends(require_admin_permissions("role:read")),
):
    """
    获取角色详情（含权限列表）
    
    权限: role:read
    """
    result = await db.execute(
        select(AdminRole)
        .where(AdminRole.id == role_id, AdminRole.is_deleted == False)
        .options(selectinload(AdminRole.permissions))
    )
    role = result.scalar_one_or_none()
    
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("role.not_found"),
        )
    
    return success(
        data=AdminRoleDetailResponse(
            id=role.id,
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
async def create_role(
    db: DbSession,
    data: AdminRoleCreateRequest,
    current_admin: Admin = Depends(require_admin_permissions("role:create")),
):
    """
    创建平台角色
    
    权限: role:create
    """
    # 检查代码是否已存在
    result = await db.execute(
        select(AdminRole).where(
            AdminRole.code == data.code,
            AdminRole.is_deleted == False,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("role.code_exists"),
        )
    
    # 创建角色
    role = AdminRole(
        code=data.code,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        sort_order=data.sort_order,
        is_system=False,
    )
    
    # 关联权限
    if data.permission_ids:
        perm_result = await db.execute(
            select(Permission).where(
                Permission.id.in_(data.permission_ids),
                Permission.is_enabled == True,
                Permission.is_deleted == False,
            )
        )
        role.permissions = list(perm_result.scalars().all())
    
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return success(
        data=AdminRoleResponse.model_validate(role, from_attributes=True),
        message=_("role.created"),
    )


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    db: DbSession,
    role_id: int,
    data: AdminRoleUpdateRequest,
    current_admin: Admin = Depends(require_admin_permissions("role:update")),
):
    """
    更新平台角色
    
    权限: role:update
    """
    result = await db.execute(
        select(AdminRole)
        .where(AdminRole.id == role_id, AdminRole.is_deleted == False)
        .options(selectinload(AdminRole.permissions))
    )
    role = result.scalar_one_or_none()
    
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("role.not_found"),
        )
    
    # 系统内置角色不可修改代码
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
            )
        )
        role.permissions = list(perm_result.scalars().all())
    
    await db.commit()
    await db.refresh(role)
    
    return success(
        data=AdminRoleResponse.model_validate(role, from_attributes=True),
        message=_("role.updated"),
    )


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    db: DbSession,
    role_id: int,
    current_admin: Admin = Depends(require_admin_permissions("role:delete")),
):
    """
    删除平台角色（软删除）
    
    权限: role:delete
    """
    result = await db.execute(
        select(AdminRole).where(AdminRole.id == role_id, AdminRole.is_deleted == False)
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
async def assign_permissions(
    db: DbSession,
    role_id: int,
    data: AdminRolePermissionsRequest,
    current_admin: Admin = Depends(require_admin_permissions("role:update")),
):
    """
    分配角色权限
    
    权限: role:update
    """
    result = await db.execute(
        select(AdminRole)
        .where(AdminRole.id == role_id, AdminRole.is_deleted == False)
        .options(selectinload(AdminRole.permissions))
    )
    role = result.scalar_one_or_none()
    
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("role.not_found"),
        )
    
    # 获取权限
    perm_result = await db.execute(
        select(Permission).where(
            Permission.id.in_(data.permission_ids),
            Permission.is_enabled == True,
            Permission.is_deleted == False,
        )
    )
    role.permissions = list(perm_result.scalars().all())
    
    await db.commit()
    
    return success(
        message=_("role.permissions_updated"),
    )


__all__ = ["router"]
