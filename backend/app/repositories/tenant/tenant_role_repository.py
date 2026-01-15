"""
租户角色仓储

提供租户角色的数据访问操作（租户隔离），支持层级查询
"""

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.base_repository import TenantRepository
from app.models.auth.tenant_admin_role import TenantAdminRole


class TenantRoleRepository(TenantRepository[TenantAdminRole]):
    """
    租户角色仓储
    
    提供租户角色特有的数据访问方法，自动过滤租户 ID，包含层级结构查询
    """
    
    model = TenantAdminRole
    
    # 按 scope 限制可过滤字段
    _scope_fields = {
        # 平台管理员查看租户角色
        "admin": {
            "id", "tenant_id", "name", "code", "is_system", "is_active",
            "parent_id", "level", "type", "leader_id",
            "created_at", "updated_at",
        },
        # 租户管理员查看本租户角色
        "tenant": {
            "id", "name", "code", "is_system", "is_active",
            "parent_id", "level", "type", "leader_id",
            "created_at", "updated_at",
        },
    }
    
    async def get_by_code(self, code: str) -> TenantAdminRole | None:
        """
        根据代码获取角色（租户内）
        
        Args:
            code: 角色代码
        
        Returns:
            角色实例或 None
        """
        return await self.get_one_by(code=code, tenant_id=self.tenant_id)
    
    async def code_exists(
        self,
        code: str,
        exclude_id: int | None = None,
    ) -> bool:
        """
        检查角色代码是否已存在（租户内唯一）
        
        Args:
            code: 角色代码
            exclude_id: 排除的 ID
        
        Returns:
            是否存在
        """
        query = select(self.model.id).where(
            self.model.tenant_id == self.tenant_id,
            self.model.code == code,
            self.model.is_deleted == False,
        )
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ========== 层级查询方法 ==========
    
    async def get_children(
        self,
        parent_id: int | None,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取直接子角色列表（租户内）
        
        Args:
            parent_id: 父角色 ID，None 表示获取顶级角色
            include_deleted: 是否包含已删除记录
        
        Returns:
            子角色列表
        """
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.parent_id == parent_id if parent_id else self.model.parent_id.is_(None),
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.order_by(self.model.sort_order.asc(), self.model.id.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_ancestors(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取所有祖先角色（从根到父，不含自身）
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            祖先角色列表（按层级从上到下排序）
        """
        # 先获取当前角色的 path（需要验证租户归属）
        role = await self.get_by_id(role_id, include_deleted=include_deleted)
        if not role or not role.path:
            return []
        
        # 解析 path 获取祖先 ID 列表
        ancestor_ids = role.get_ancestor_ids()
        if not ancestor_ids:
            return []
        
        # 查询祖先角色（同一租户内）
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.id.in_(ancestor_ids),
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.order_by(self.model.level.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_descendants(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取所有后代角色（不含自身）
        
        使用 path 字段的 LIKE 查询实现
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            后代角色列表（按层级从上到下排序）
        """
        # 先获取当前角色（需要验证租户归属）
        role = await self.get_by_id(role_id, include_deleted=include_deleted)
        if not role:
            return []
        
        # 构建 path 前缀模式
        path_prefix = role.path or f"/{role_id}/"
        
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.path.like(f"{path_prefix}%"),
            self.model.id != role_id,  # 排除自身
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.order_by(self.model.level.asc(), self.model.sort_order.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_descendant_ids(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> list[int]:
        """
        获取所有后代角色 ID（不含自身）
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            后代角色 ID 列表
        """
        descendants = await self.get_descendants(role_id, include_deleted)
        return [d.id for d in descendants]
    
    async def get_tree(
        self,
        parent_id: int | None = None,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取角色树（指定节点下的所有角色，租户内）
        
        Args:
            parent_id: 父角色 ID，None 表示从根节点开始
            include_deleted: 是否包含已删除记录
        
        Returns:
            角色列表（平铺，按层级和排序字段排序）
        """
        if parent_id is None:
            # 获取租户内所有角色
            query = select(self.model).where(
                self.model.tenant_id == self.tenant_id
            )
        else:
            # 获取指定节点及其后代（需要验证租户归属）
            role = await self.get_by_id(parent_id, include_deleted=include_deleted)
            if not role:
                return []
            
            path_prefix = role.path or f"/{parent_id}/"
            query = select(self.model).where(
                self.model.tenant_id == self.tenant_id,
                self.model.path.like(f"{path_prefix}%"),
            )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        # 加载子角色和管理员关联，支持 children_count/has_children/has_admins 属性
        query = query.options(
            selectinload(self.model.children),
            selectinload(self.model.admins),
        )
        query = query.order_by(self.model.level.asc(), self.model.sort_order.asc(), self.model.id.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def has_children(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> bool:
        """
        检查角色是否有子角色（租户内）
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            是否有子角色
        """
        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == self.tenant_id,
            self.model.parent_id == role_id,
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0
    
    async def count_children(
        self,
        parent_id: int | None,
        include_deleted: bool = False,
    ) -> int:
        """
        统计直接子角色数量（租户内）
        
        Args:
            parent_id: 父角色 ID，None 表示统计顶级角色
            include_deleted: 是否包含已删除记录
        
        Returns:
            子角色数量
        """
        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == self.tenant_id,
            self.model.parent_id == parent_id if parent_id else self.model.parent_id.is_(None),
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_root_roles(
        self,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取所有顶级角色（租户内，无父角色）
        
        Args:
            include_deleted: 是否包含已删除记录
        
        Returns:
            顶级角色列表
        """
        return await self.get_children(parent_id=None, include_deleted=include_deleted)
    
    async def has_admins(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> bool:
        """
        检查角色是否有关联的管理员（租户内）
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            是否有关联管理员
        """
        from app.models.tenant.tenant_admin import TenantAdmin
        
        query = select(func.count(TenantAdmin.id)).where(
            TenantAdmin.tenant_id == self.tenant_id,
            TenantAdmin.role_id == role_id,
        )
        
        if not include_deleted:
            query = query.where(TenantAdmin.is_deleted == False)
        
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0
    
    # ========== 组织架构查询方法 ==========
    
    async def get_by_type(
        self,
        role_type: str,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        根据节点类型获取角色列表（租户内）
        
        Args:
            role_type: 节点类型 (department/position/role)
            include_deleted: 是否包含已删除记录
        
        Returns:
            角色列表
        """
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.type == role_type,
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.order_by(self.model.sort_order.asc(), self.model.id.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_departments(
        self,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取所有部门节点（租户内）
        
        Args:
            include_deleted: 是否包含已删除记录
        
        Returns:
            部门列表
        """
        return await self.get_by_type("department", include_deleted)
    
    async def get_members(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> list:
        """
        获取节点成员列表（租户内）
        
        Args:
            role_id: 角色/节点 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            成员列表 (TenantAdmin)
        """
        from app.models.tenant.tenant_admin import TenantAdmin
        
        query = select(TenantAdmin).where(
            TenantAdmin.tenant_id == self.tenant_id,
            TenantAdmin.role_id == role_id,
        )
        
        if not include_deleted:
            query = query.where(TenantAdmin.is_deleted == False)
        
        query = query.order_by(TenantAdmin.id.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_members(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> int:
        """
        统计节点成员数量（租户内）
        
        Args:
            role_id: 角色/节点 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            成员数量
        """
        from app.models.tenant.tenant_admin import TenantAdmin
        
        query = select(func.count(TenantAdmin.id)).where(
            TenantAdmin.tenant_id == self.tenant_id,
            TenantAdmin.role_id == role_id,
        )
        
        if not include_deleted:
            query = query.where(TenantAdmin.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_with_members(
        self,
        role_id: int,
        include_deleted: bool = False,
    ) -> TenantAdminRole | None:
        """
        获取角色并加载成员关系（租户内）
        
        Args:
            role_id: 角色 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            角色实例（含成员列表）
        """
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.id == role_id,
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        query = query.options(
            selectinload(self.model.admins),
            selectinload(self.model.leader),
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_organization_tree(
        self,
        include_deleted: bool = False,
    ) -> list[TenantAdminRole]:
        """
        获取组织架构树（含成员信息，租户内）
        
        Args:
            include_deleted: 是否包含已删除记录
        
        Returns:
            角色列表（平铺，按层级排序，含成员列表）
        """
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id
        )
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        # 加载关联数据
        query = query.options(
            selectinload(self.model.children),
            selectinload(self.model.admins),
            selectinload(self.model.leader),
        )
        query = query.order_by(
            self.model.level.asc(),
            self.model.sort_order.asc(),
            self.model.id.asc(),
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


__all__ = ["TenantRoleRepository"]
