"""
仓储基类模块

提供数据访问层的基类，封装通用的 CRUD 操作
"""

from typing import Any, Generic, TypeVar, Type

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.base_model import BaseModel

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    仓储基类
    
    封装数据访问层的通用 CRUD 操作
    
    使用示例:
        class UserRepository(BaseRepository[User]):
            model = User
    """
    
    model: Type[ModelType]
    
    def __init__(self, db: AsyncSession):
        """
        初始化仓储
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
    
    async def get_by_id(
        self,
        id: int,
        include_deleted: bool = False,
    ) -> ModelType | None:
        """
        根据 ID 获取单条记录
        
        Args:
            id: 记录 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            模型实例或 None
        """
        query = select(self.model).where(self.model.id == id)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_ids(
        self,
        ids: list[int],
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """
        根据 ID 列表获取多条记录
        
        Args:
            ids: ID 列表
            include_deleted: 是否包含已删除记录
        
        Returns:
            模型实例列表
        """
        if not ids:
            return []
        
        query = select(self.model).where(self.model.id.in_(ids))
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> list[ModelType]:
        """
        获取记录列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            order_by: 排序字段
            include_deleted: 是否包含已删除记录
            **filters: 过滤条件
        
        Returns:
            模型实例列表
        """
        query = select(self.model)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        # 应用过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        # 排序
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(self.model.id.desc())
        
        # 分页
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        """
        统计记录数量
        
        Args:
            include_deleted: 是否包含已删除记录
            **filters: 过滤条件
        
        Returns:
            记录数量
        """
        query = select(func.count(self.model.id))
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        # 应用过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, data: dict[str, Any]) -> ModelType:
        """
        创建记录
        
        Args:
            data: 创建数据字典
        
        Returns:
            创建的模型实例
        """
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def create_many(self, data_list: list[dict[str, Any]]) -> list[ModelType]:
        """
        批量创建记录
        
        Args:
            data_list: 创建数据字典列表
        
        Returns:
            创建的模型实例列表
        """
        instances = [self.model(**data) for data in data_list]
        self.db.add_all(instances)
        await self.db.flush()
        for instance in instances:
            await self.db.refresh(instance)
        return instances
    
    async def update(
        self,
        id: int,
        data: dict[str, Any],
    ) -> ModelType | None:
        """
        更新记录
        
        Args:
            id: 记录 ID
            data: 更新数据字典
        
        Returns:
            更新后的模型实例或 None
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        
        instance.update_from_dict(data)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def update_many(
        self,
        ids: list[int],
        data: dict[str, Any],
    ) -> int:
        """
        批量更新记录
        
        Args:
            ids: ID 列表
            data: 更新数据字典
        
        Returns:
            更新的记录数量
        """
        if not ids:
            return 0
        
        stmt = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .where(self.model.is_deleted == False)
            .values(**data)
        )
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete(
        self,
        id: int,
        soft: bool = True,
    ) -> bool:
        """
        删除记录
        
        Args:
            id: 记录 ID
            soft: 是否软删除（默认 True）
        
        Returns:
            是否删除成功
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        
        if soft:
            instance.soft_delete()
        else:
            await self.db.delete(instance)
        
        await self.db.flush()
        return True
    
    async def delete_many(
        self,
        ids: list[int],
        soft: bool = True,
    ) -> int:
        """
        批量删除记录
        
        Args:
            ids: ID 列表
            soft: 是否软删除（默认 True）
        
        Returns:
            删除的记录数量
        """
        if not ids:
            return 0
        
        if soft:
            stmt = (
                update(self.model)
                .where(self.model.id.in_(ids))
                .where(self.model.is_deleted == False)
                .values(is_deleted=True)
            )
        else:
            stmt = delete(self.model).where(self.model.id.in_(ids))
        
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def exists(
        self,
        id: int,
        include_deleted: bool = False,
    ) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录 ID
            include_deleted: 是否包含已删除记录
        
        Returns:
            是否存在
        """
        query = select(func.count(self.model.id)).where(self.model.id == id)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0
    
    async def get_one_by(
        self,
        include_deleted: bool = False,
        **filters: Any,
    ) -> ModelType | None:
        """
        根据条件获取单条记录
        
        Args:
            include_deleted: 是否包含已删除记录
            **filters: 过滤条件
        
        Returns:
            模型实例或 None
        """
        query = select(self.model)
        
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class TenantRepository(BaseRepository[ModelType]):
    """
    租户级仓储基类
    
    自动在查询中添加 tenant_id 过滤
    """
    
    def __init__(self, db: AsyncSession, tenant_id: int):
        """
        初始化租户仓储
        
        Args:
            db: 异步数据库会话
            tenant_id: 租户 ID
        """
        super().__init__(db)
        self.tenant_id = tenant_id
    
    async def get_list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> list[ModelType]:
        """获取租户级记录列表"""
        filters["tenant_id"] = self.tenant_id
        return await super().get_list(
            skip=skip,
            limit=limit,
            order_by=order_by,
            include_deleted=include_deleted,
            **filters,
        )
    
    async def count(
        self,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        """统计租户级记录数量"""
        filters["tenant_id"] = self.tenant_id
        return await super().count(include_deleted=include_deleted, **filters)
    
    async def create(self, data: dict[str, Any]) -> ModelType:
        """创建租户级记录"""
        data["tenant_id"] = self.tenant_id
        return await super().create(data)
    
    async def get_by_id(
        self,
        id: int,
        include_deleted: bool = False,
    ) -> ModelType | None:
        """根据 ID 获取租户级记录"""
        instance = await super().get_by_id(id, include_deleted)
        # 验证租户归属
        if instance and hasattr(instance, "tenant_id"):
            if instance.tenant_id != self.tenant_id:
                return None
        return instance


# 导出
__all__ = ["BaseRepository", "TenantRepository"]
