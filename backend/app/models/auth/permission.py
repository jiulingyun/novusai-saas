"""
权限模型

定义系统中的所有权限点
"""

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Permission(BaseModel):
    """
    权限模型
    
    - 定义系统中的权限点
    - 权限按模块分组
    - 权限代码全局唯一
    """
    
    __tablename__ = "permissions"
    
    # 权限代码（唯一标识）
    code: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, comment="权限代码（如：admin:user:create）"
    )
    
    # 权限名称
    name: Mapped[str] = mapped_column(
        String(100), comment="权限名称"
    )
    
    # 权限描述
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="权限描述"
    )
    
    # 权限分组（用于前端展示分组）
    group: Mapped[str] = mapped_column(
        String(50), index=True, comment="权限分组（如：system, tenant, user）"
    )
    
    # 排序
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="排序（同组内排序）"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code})>"


__all__ = ["Permission"]
