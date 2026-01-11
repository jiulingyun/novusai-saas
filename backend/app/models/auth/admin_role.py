"""
平台管理员角色模型

平台级别的角色，用于平台管理员权限控制
"""

from sqlalchemy import Boolean, String, Integer, Text, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel, Base


# 角色-权限关联表（多对多）
admin_role_permissions = Table(
    "admin_role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("admin_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class AdminRole(BaseModel):
    """
    平台管理员角色模型
    
    - 用于平台管理员的权限控制
    - 与 Permission 多对多关联
    - is_super 标记的角色拥有所有权限
    """
    
    __tablename__ = "admin_roles"
    
    # 角色名称
    name: Mapped[str] = mapped_column(
        String(50), unique=True, comment="角色名称"
    )
    
    # 角色代码（唯一标识）
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="角色代码"
    )
    
    # 角色描述
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="角色描述"
    )
    
    # 是否系统内置（内置角色不可删除）
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否系统内置"
    )
    
    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    
    # 排序
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="排序"
    )
    
    # 关联权限（多对多）
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=admin_role_permissions,
        lazy="selectin",
    )
    
    # 关联管理员（一对多）
    admins: Mapped[list["Admin"]] = relationship(
        "Admin",
        back_populates="role",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<AdminRole(id={self.id}, code={self.code})>"
    
    def has_permission(self, permission_code: str) -> bool:
        """
        检查角色是否拥有指定权限
        
        Args:
            permission_code: 权限代码
        
        Returns:
            是否拥有该权限
        """
        return any(p.code == permission_code for p in self.permissions)


# 需要导入用于类型注解
from app.models.auth.permission import Permission
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.system.admin import Admin


__all__ = ["AdminRole", "admin_role_permissions"]
