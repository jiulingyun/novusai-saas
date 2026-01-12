"""
租户角色仓储

提供租户角色的数据访问操作（租户隔离）
"""

from sqlalchemy import select

from app.core.base_repository import TenantRepository
from app.models.auth.tenant_admin_role import TenantAdminRole


class TenantRoleRepository(TenantRepository[TenantAdminRole]):
    """
    租户角色仓储
    
    提供租户角色特有的数据访问方法，自动过滤租户 ID
    """
    
    model = TenantAdminRole
    
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


__all__ = ["TenantRoleRepository"]
