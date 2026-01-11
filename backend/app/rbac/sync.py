"""
权限同步服务

应用启动时调用，将装饰器定义的权限同步到数据库
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LogManager
from app.models.auth.permission import Permission
from app.rbac.decorators import PermissionMeta
from app.rbac.registry import permission_registry

logger = LogManager.get_logger(__name__)


class PermissionSyncService:
    """
    权限同步服务
    
    应用启动时调用，将装饰器定义的权限同步到数据库
    
    策略：
    - 新权限：创建
    - 已存在：更新名称、描述等（code 不变）
    - 数据库中多余的：标记为禁用（不删除，保留历史）
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_permissions(self) -> dict[str, int]:
        """
        同步权限到数据库
        
        Returns:
            {"created": n, "updated": n, "disabled": n}
        """
        registered_permissions = permission_registry.get_all()
        registered_codes = {p.code for p in registered_permissions}
        
        # 获取数据库中现有权限
        result = await self.db.execute(select(Permission))
        existing_permissions = result.scalars().all()
        existing_codes = {p.code for p in existing_permissions}
        existing_map = {p.code: p for p in existing_permissions}
        
        created_count = 0
        updated_count = 0
        disabled_count = 0
        
        # 处理父级权限映射（用于菜单层级）
        parent_map: dict[str, int] = {}  # code -> id
        
        # 第一轮：创建/更新权限（先处理无父级的）
        sorted_permissions = sorted(
            registered_permissions, 
            key=lambda x: x.parent_code or ""
        )
        
        for perm_meta in sorted_permissions:
            if perm_meta.code in existing_codes:
                # 更新
                db_perm = existing_map[perm_meta.code]
                db_perm.name = perm_meta.name
                db_perm.description = perm_meta.description
                db_perm.type = perm_meta.type.value
                db_perm.scope = perm_meta.scope.value
                db_perm.resource = perm_meta.resource
                db_perm.action = perm_meta.action
                db_perm.icon = perm_meta.icon
                db_perm.path = perm_meta.path
                db_perm.component = perm_meta.component
                db_perm.sort_order = perm_meta.sort_order
                db_perm.hidden = perm_meta.hidden
                db_perm.is_enabled = True
                
                # 更新父级
                if perm_meta.parent_code and perm_meta.parent_code in parent_map:
                    db_perm.parent_id = parent_map[perm_meta.parent_code]
                
                parent_map[perm_meta.code] = db_perm.id
                updated_count += 1
            else:
                # 创建
                parent_id = None
                if perm_meta.parent_code and perm_meta.parent_code in parent_map:
                    parent_id = parent_map[perm_meta.parent_code]
                
                db_perm = Permission(
                    code=perm_meta.code,
                    name=perm_meta.name,
                    description=perm_meta.description,
                    type=perm_meta.type.value,
                    scope=perm_meta.scope.value,
                    resource=perm_meta.resource,
                    action=perm_meta.action,
                    parent_id=parent_id,
                    sort_order=perm_meta.sort_order,
                    icon=perm_meta.icon,
                    path=perm_meta.path,
                    component=perm_meta.component,
                    hidden=perm_meta.hidden,
                    is_enabled=True,
                )
                self.db.add(db_perm)
                await self.db.flush()  # 获取 ID
                parent_map[perm_meta.code] = db_perm.id
                created_count += 1
        
        # 禁用数据库中多余的权限（代码中已删除的）
        orphan_codes = existing_codes - registered_codes
        for code in orphan_codes:
            db_perm = existing_map[code]
            if db_perm.is_enabled:
                db_perm.is_enabled = False
                disabled_count += 1
        
        await self.db.commit()
        
        logger.info(
            f"权限同步完成: 新增 {created_count}, 更新 {updated_count}, 禁用 {disabled_count}"
        )
        
        return {
            "created": created_count,
            "updated": updated_count,
            "disabled": disabled_count,
        }


async def sync_permissions_on_startup(db: AsyncSession) -> dict[str, int]:
    """
    启动时同步权限
    
    Args:
        db: 数据库会话
    
    Returns:
        同步结果统计
    """
    sync_service = PermissionSyncService(db)
    return await sync_service.sync_permissions()


__all__ = [
    "PermissionSyncService",
    "sync_permissions_on_startup",
]
