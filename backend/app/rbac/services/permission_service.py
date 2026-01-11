"""
权限检查服务

提供权限获取和检查功能
"""

from typing import Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Admin, TenantAdmin, Permission
from app.models.auth.admin_role import AdminRole
from app.models.auth.tenant_admin_role import TenantAdminRole


class PermissionService:
    """
    权限检查服务
    
    提供：
    - 获取用户权限列表
    - 检查用户是否拥有指定权限
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_admin_permissions(self, admin: Admin) -> set[str]:
        """
        获取平台管理员的权限集合
        
        Args:
            admin: 平台管理员
        
        Returns:
            权限代码集合
        """
        # 超级管理员拥有所有权限
        if admin.is_super:
            return {"*"}
        
        # 无角色则无权限
        if admin.role_id is None:
            return set()
        
        # 查询角色及其权限
        result = await self.db.execute(
            select(AdminRole)
            .where(AdminRole.id == admin.role_id)
            .options(selectinload(AdminRole.permissions))
        )
        role = result.scalar_one_or_none()
        
        if role is None or not role.is_active:
            return set()
        
        return {
            p.code for p in role.permissions 
            if p.is_enabled and not p.is_deleted
        }
    
    async def get_tenant_admin_permissions(self, tenant_admin: TenantAdmin) -> set[str]:
        """
        获取租户管理员的权限集合
        
        Args:
            tenant_admin: 租户管理员
        
        Returns:
            权限代码集合
        """
        # 租户所有者拥有租户内所有权限
        if tenant_admin.is_owner:
            return {"*"}
        
        # 无角色则无权限
        if tenant_admin.role_id is None:
            return set()
        
        # 查询角色及其权限
        result = await self.db.execute(
            select(TenantAdminRole)
            .where(TenantAdminRole.id == tenant_admin.role_id)
            .options(selectinload(TenantAdminRole.permissions))
        )
        role = result.scalar_one_or_none()
        
        if role is None or not role.is_active:
            return set()
        
        return {
            p.code for p in role.permissions 
            if p.is_enabled and not p.is_deleted
        }
    
    def check_permission(
        self, 
        user_permissions: set[str], 
        required: str,
    ) -> bool:
        """
        检查用户是否拥有指定权限
        
        支持：
        - 精确匹配: user:create
        - 通配符: * (所有权限)
        - 资源通配符: user:* (某资源的所有操作)
        
        Args:
            user_permissions: 用户权限集合
            required: 需要的权限代码
        
        Returns:
            是否拥有权限
        """
        # 超级权限
        if "*" in user_permissions:
            return True
        
        # 精确匹配
        if required in user_permissions:
            return True
        
        # 资源通配符匹配
        if ":" in required:
            resource = required.split(":")[0]
            if f"{resource}:*" in user_permissions:
                return True
        
        return False
    
    def check_any_permission(
        self, 
        user_permissions: set[str], 
        required_permissions: list[str],
    ) -> bool:
        """
        检查用户是否拥有任意一个指定权限
        
        Args:
            user_permissions: 用户权限集合
            required_permissions: 需要的权限代码列表
        
        Returns:
            是否拥有任意一个权限
        """
        return any(
            self.check_permission(user_permissions, perm) 
            for perm in required_permissions
        )
    
    def check_all_permissions(
        self, 
        user_permissions: set[str], 
        required_permissions: list[str],
    ) -> bool:
        """
        检查用户是否拥有所有指定权限
        
        Args:
            user_permissions: 用户权限集合
            required_permissions: 需要的权限代码列表
        
        Returns:
            是否拥有所有权限
        """
        return all(
            self.check_permission(user_permissions, perm) 
            for perm in required_permissions
        )
    
    async def get_enabled_permissions_by_scope(self, scope: str) -> list[Permission]:
        """
        获取指定作用域的所有启用权限
        
        Args:
            scope: 权限作用域 (admin/tenant/both)
        
        Returns:
            权限列表
        """
        result = await self.db.execute(
            select(Permission)
            .where(
                Permission.is_enabled == True,
                Permission.is_deleted == False,
                Permission.scope.in_([scope, "both"]),
            )
            .order_by(Permission.sort_order)
        )
        return list(result.scalars().all())


__all__ = ["PermissionService"]
