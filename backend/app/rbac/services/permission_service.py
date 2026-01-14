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
from app.repositories.system.admin_role_repository import AdminRoleRepository
from app.repositories.tenant.tenant_role_repository import TenantRoleRepository


class PermissionService:
    """
    权限检查服务
    
    提供：
    - 获取用户权限列表
    - 检查用户是否拥有指定权限
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_admin_permissions(
        self, 
        admin: Admin, 
        include_inherited: bool = True,
    ) -> set[str]:
        """
        获取平台管理员的权限集合
        
        Args:
            admin: 平台管理员
            include_inherited: 是否包含继承的权限（来自祖先角色）
        
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
        
        permissions: set[str] = {
            p.code for p in role.permissions 
            if p.is_enabled and not p.is_deleted
        }
        
        # 获取继承的权限（来自祖先角色）
        if include_inherited:
            repo = AdminRoleRepository(self.db)
            ancestors = await repo.get_ancestors(admin.role_id)
            for ancestor in ancestors:
                if ancestor.is_active:
                    # 需要加载权限关联
                    result = await self.db.execute(
                        select(AdminRole)
                        .where(AdminRole.id == ancestor.id)
                        .options(selectinload(AdminRole.permissions))
                    )
                    ancestor_with_perms = result.scalar_one_or_none()
                    if ancestor_with_perms:
                        for p in ancestor_with_perms.permissions:
                            if p.is_enabled and not p.is_deleted:
                                permissions.add(p.code)
        
        return permissions
    
    async def get_admin_effective_permission_ids(self, admin: Admin) -> set[int]:
        """
        获取平台管理员的有效权限 ID 集合（含继承）
        
        Args:
            admin: 平台管理员
        
        Returns:
            权限 ID 集合
        """
        # 超级管理员拥有所有权限
        if admin.is_super:
            result = await self.db.execute(
                select(Permission.id).where(
                    Permission.is_enabled == True,
                    Permission.is_deleted == False,
                )
            )
            return set(result.scalars().all())
        
        # 无角色则无权限
        if admin.role_id is None:
            return set()
        
        permission_ids: set[int] = set()
        
        # 获取当前角色的权限
        result = await self.db.execute(
            select(AdminRole)
            .where(AdminRole.id == admin.role_id)
            .options(selectinload(AdminRole.permissions))
        )
        role = result.scalar_one_or_none()
        
        if role and role.is_active:
            for p in role.permissions:
                if p.is_enabled and not p.is_deleted:
                    permission_ids.add(p.id)
        
        # 获取祖先角色的权限
        repo = AdminRoleRepository(self.db)
        ancestors = await repo.get_ancestors(admin.role_id)
        for ancestor in ancestors:
            if ancestor.is_active:
                result = await self.db.execute(
                    select(AdminRole)
                    .where(AdminRole.id == ancestor.id)
                    .options(selectinload(AdminRole.permissions))
                )
                ancestor_with_perms = result.scalar_one_or_none()
                if ancestor_with_perms:
                    for p in ancestor_with_perms.permissions:
                        if p.is_enabled and not p.is_deleted:
                            permission_ids.add(p.id)
        
        return permission_ids
    
    async def get_admin_manageable_role_ids(self, admin: Admin) -> set[int]:
        """
        获取平台管理员可管理的角色 ID 集合
        
        可管理的角色 = 自身角色的所有后代角色（不含自身）
        
        Args:
            admin: 平台管理员
        
        Returns:
            角色 ID 集合
        """
        # 超级管理员可以管理所有角色
        if admin.is_super:
            result = await self.db.execute(
                select(AdminRole.id).where(AdminRole.is_deleted == False)
            )
            return set(result.scalars().all())
        
        # 无角色则无法管理任何角色
        if admin.role_id is None:
            return set()
        
        # 获取后代角色（不含自身）
        repo = AdminRoleRepository(self.db)
        descendant_ids = await repo.get_descendant_ids(admin.role_id)
        return set(descendant_ids)
    
    async def get_admin_visible_role_ids(self, admin: Admin) -> set[int]:
        """
        获取平台管理员可见的角色 ID 集合
        
        可见的角色 = 自身角色 + 所有后代角色
        
        Args:
            admin: 平台管理员
        
        Returns:
            角色 ID 集合
        """
        # 超级管理员可以看到所有角色
        if admin.is_super:
            result = await self.db.execute(
                select(AdminRole.id).where(AdminRole.is_deleted == False)
            )
            return set(result.scalars().all())
        
        # 无角色则无法看到任何角色
        if admin.role_id is None:
            return set()
        
        # 自身角色 + 后代角色
        visible_ids = {admin.role_id}
        repo = AdminRoleRepository(self.db)
        descendant_ids = await repo.get_descendant_ids(admin.role_id)
        visible_ids.update(descendant_ids)
        
        return visible_ids
    
    async def get_tenant_admin_permissions(
        self, 
        tenant_admin: TenantAdmin,
        include_inherited: bool = True,
    ) -> set[str]:
        """
        获取租户管理员的权限集合
        
        Args:
            tenant_admin: 租户管理员
            include_inherited: 是否包含继承的权限
        
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
        
        permissions: set[str] = {
            p.code for p in role.permissions 
            if p.is_enabled and not p.is_deleted
        }
        
        # 获取继承的权限
        if include_inherited:
            repo = TenantRoleRepository(self.db, tenant_admin.tenant_id)
            ancestors = await repo.get_ancestors(tenant_admin.role_id)
            for ancestor in ancestors:
                if ancestor.is_active:
                    result = await self.db.execute(
                        select(TenantAdminRole)
                        .where(TenantAdminRole.id == ancestor.id)
                        .options(selectinload(TenantAdminRole.permissions))
                    )
                    ancestor_with_perms = result.scalar_one_or_none()
                    if ancestor_with_perms:
                        for p in ancestor_with_perms.permissions:
                            if p.is_enabled and not p.is_deleted:
                                permissions.add(p.code)
        
        return permissions
    
    async def get_tenant_admin_effective_permission_ids(
        self, 
        tenant_admin: TenantAdmin,
    ) -> set[int]:
        """
        获取租户管理员的有效权限 ID 集合（含继承）
        
        Args:
            tenant_admin: 租户管理员
        
        Returns:
            权限 ID 集合
        """
        # 租户所有者拥有所有权限
        if tenant_admin.is_owner:
            result = await self.db.execute(
                select(Permission.id).where(
                    Permission.is_enabled == True,
                    Permission.is_deleted == False,
                )
            )
            return set(result.scalars().all())
        
        # 无角色则无权限
        if tenant_admin.role_id is None:
            return set()
        
        permission_ids: set[int] = set()
        
        # 获取当前角色的权限
        result = await self.db.execute(
            select(TenantAdminRole)
            .where(TenantAdminRole.id == tenant_admin.role_id)
            .options(selectinload(TenantAdminRole.permissions))
        )
        role = result.scalar_one_or_none()
        
        if role and role.is_active:
            for p in role.permissions:
                if p.is_enabled and not p.is_deleted:
                    permission_ids.add(p.id)
        
        # 获取祖先角色的权限
        repo = TenantRoleRepository(self.db, tenant_admin.tenant_id)
        ancestors = await repo.get_ancestors(tenant_admin.role_id)
        for ancestor in ancestors:
            if ancestor.is_active:
                result = await self.db.execute(
                    select(TenantAdminRole)
                    .where(TenantAdminRole.id == ancestor.id)
                    .options(selectinload(TenantAdminRole.permissions))
                )
                ancestor_with_perms = result.scalar_one_or_none()
                if ancestor_with_perms:
                    for p in ancestor_with_perms.permissions:
                        if p.is_enabled and not p.is_deleted:
                            permission_ids.add(p.id)
        
        return permission_ids
    
    async def get_tenant_admin_manageable_role_ids(
        self, 
        tenant_admin: TenantAdmin,
    ) -> set[int]:
        """
        获取租户管理员可管理的角色 ID 集合
        
        Args:
            tenant_admin: 租户管理员
        
        Returns:
            角色 ID 集合
        """
        # 租户所有者可以管理所有角色
        if tenant_admin.is_owner:
            result = await self.db.execute(
                select(TenantAdminRole.id).where(
                    TenantAdminRole.tenant_id == tenant_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
            )
            return set(result.scalars().all())
        
        # 无角色则无法管理
        if tenant_admin.role_id is None:
            return set()
        
        # 获取后代角色
        repo = TenantRoleRepository(self.db, tenant_admin.tenant_id)
        descendant_ids = await repo.get_descendant_ids(tenant_admin.role_id)
        return set(descendant_ids)
    
    async def get_tenant_admin_visible_role_ids(
        self, 
        tenant_admin: TenantAdmin,
    ) -> set[int]:
        """
        获取租户管理员可见的角色 ID 集合
        
        Args:
            tenant_admin: 租户管理员
        
        Returns:
            角色 ID 集合
        """
        # 租户所有者可以看到所有角色
        if tenant_admin.is_owner:
            result = await self.db.execute(
                select(TenantAdminRole.id).where(
                    TenantAdminRole.tenant_id == tenant_admin.tenant_id,
                    TenantAdminRole.is_deleted == False,
                )
            )
            return set(result.scalars().all())
        
        # 无角色则无法看到
        if tenant_admin.role_id is None:
            return set()
        
        # 自身角色 + 后代角色
        visible_ids = {tenant_admin.role_id}
        repo = TenantRoleRepository(self.db, tenant_admin.tenant_id)
        descendant_ids = await repo.get_descendant_ids(tenant_admin.role_id)
        visible_ids.update(descendant_ids)
        
        return visible_ids
    
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
