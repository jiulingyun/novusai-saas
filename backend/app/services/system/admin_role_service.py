"""
平台管理员角色服务

提供平台角色的业务逻辑，支持层级结构和权限继承
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_service import GlobalService
from app.core.i18n import _
from app.exceptions import BusinessException, NotFoundException
from app.models.auth.admin_role import AdminRole
from app.models.auth.permission import Permission
from app.repositories.system.admin_role_repository import AdminRoleRepository
from app.services.common.role_tree_mixin import RoleTreeMixin, MAX_ROLE_DEPTH


class AdminRoleService(GlobalService[AdminRole, AdminRoleRepository], RoleTreeMixin[AdminRole]):
    """
    平台管理员角色服务
    
    提供角色的 CRUD 操作和层级结构管理
    """
    
    model = AdminRole
    repository_class = AdminRoleRepository
    
    async def get_by_code(self, code: str) -> AdminRole | None:
        """
        根据代码获取角色
        
        Args:
            code: 角色代码
        
        Returns:
            角色实例或 None
        """
        return await self.repo.get_by_code(code)
    
    async def create_role(
        self,
        name: str,
        code: str,
        description: str | None = None,
        is_system: bool = False,
        is_active: bool = True,
        sort_order: int = 0,
        parent_id: int | None = None,
    ) -> AdminRole:
        """
        创建角色
        
        Args:
            name: 角色名称
            code: 角色代码（唯一）
            description: 角色描述
            is_system: 是否系统内置
            is_active: 是否启用
            sort_order: 排序
            parent_id: 父角色 ID
        
        Returns:
            创建的角色
        
        Raises:
            BusinessException: 代码已存在或父角色无效
        """
        # 检查代码是否已存在
        if await self.repo.code_exists(code):
            raise BusinessException(
                message=_("role.code_exists"),
                code=4001,
            )
        
        # 验证父角色并获取 path 和 level
        parent_path, parent_level = await self.validate_parent(parent_id)
        
        # 检查深度限制
        new_level = self._calculate_level(parent_level)
        if new_level > MAX_ROLE_DEPTH:
            raise BusinessException(
                message=_("role.max_depth_exceeded"),
                code=4103,
            )
        
        # 创建角色（先不设置 path，需要先获取 ID）
        data = {
            "name": name,
            "code": code,
            "description": description,
            "is_system": is_system,
            "is_active": is_active,
            "sort_order": sort_order,
            "parent_id": parent_id,
            "level": new_level,
        }
        
        role = await self.repo.create(data)
        
        # 更新 path（需要角色 ID）
        path = self._build_path(parent_path, role.id)
        await self.repo.update(role.id, {"path": path})
        
        # 刷新角色
        return await self.repo.get_by_id(role.id)
    
    async def update_role(
        self,
        role_id: int,
        data: dict[str, Any],
    ) -> AdminRole:
        """
        更新角色
        
        Args:
            role_id: 角色 ID
            data: 更新数据
        
        Returns:
            更新后的角色
        
        Raises:
            NotFoundException: 角色不存在
            BusinessException: 代码已存在或父角色无效
        """
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise NotFoundException(message=_("role.not_found"))
        
        # 系统角色不可修改父级关系
        if role.is_system and "parent_id" in data:
            raise BusinessException(
                message=_("role.system_role_cannot_change_parent"),
                code=4104,
            )
        
        # 检查代码是否已被其他角色使用
        if "code" in data and data["code"]:
            if await self.repo.code_exists(data["code"], exclude_id=role_id):
                raise BusinessException(
                    message=_("role.code_exists"),
                    code=4001,
                )
        
        # 如果更新了父角色，需要验证并更新 path/level
        if "parent_id" in data and data["parent_id"] != role.parent_id:
            new_parent_id = data["parent_id"]
            parent_path, parent_level = await self.validate_parent(new_parent_id, exclude_id=role_id)
            
            new_level = self._calculate_level(parent_level)
            
            # 检查深度限制（含子树）
            max_descendant_depth = await self._get_max_descendant_depth(role_id)
            if new_level + max_descendant_depth > MAX_ROLE_DEPTH:
                raise BusinessException(
                    message=_("role.max_depth_exceeded"),
                    code=4103,
                )
            
            # 计算新 path
            new_path = self._build_path(parent_path, role_id)
            old_path = role.path or f"/{role_id}/"
            
            data["path"] = new_path
            data["level"] = new_level
            
            # 更新角色
            result = await self.repo.update(role_id, data)
            
            # 更新所有后代的 path 和 level
            await self._update_descendants_path(role_id, old_path, new_path, new_level)
            
            return await self.repo.get_by_id(role_id)
        
        # 普通更新（不涉及父级变更）
        result = await self.repo.update(role_id, data)
        if not result:
            raise NotFoundException(message=_("role.not_found"))
        
        return result
    
    async def delete_role(self, role_id: int) -> bool:
        """
        删除角色
        
        Args:
            role_id: 角色 ID
        
        Returns:
            是否删除成功
        
        Raises:
            NotFoundException: 角色不存在
            BusinessException: 有子角色或关联用户
        """
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise NotFoundException(message=_("role.not_found"))
        
        # 系统角色不可删除
        if role.is_system:
            raise BusinessException(
                message=_("role.system_role_cannot_delete"),
                code=4105,
            )
        
        # 检查是否有子角色（使用 repository 方法避免 lazy-load 问题）
        if await self.repo.has_children(role_id):
            raise BusinessException(
                message=_("role.has_children"),
                code=4106,
            )
        
        # 检查是否有关联的管理员（使用 repository 方法避免 lazy-load 问题）
        if await self.repo.has_admins(role_id):
            raise BusinessException(
                message=_("role.has_users"),
                code=4107,
            )
        
        return await self.repo.delete(role_id)
    
    async def assign_permissions(
        self,
        role_id: int,
        permission_ids: list[int],
    ) -> AdminRole:
        """
        分配权限给角色
        
        Args:
            role_id: 角色 ID
            permission_ids: 权限 ID 列表
        
        Returns:
            更新后的角色
        
        Raises:
            NotFoundException: 角色不存在
        """
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise NotFoundException(message=_("role.not_found"))
        
        # 查询权限
        query = select(Permission).where(
            Permission.id.in_(permission_ids),
            Permission.is_deleted == False,
        )
        result = await self.db.execute(query)
        permissions = list(result.scalars().all())
        
        # 更新角色权限
        role.permissions = permissions
        await self.db.flush()
        await self.db.refresh(role)
        
        return role
    
    async def get_root_roles(self) -> list[AdminRole]:
        """
        获取所有顶级角色
        
        Returns:
            顶级角色列表
        """
        return await self.repo.get_root_roles()


__all__ = ["AdminRoleService"]
