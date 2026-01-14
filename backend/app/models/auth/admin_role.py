"""
平台管理员角色模型

平台级别的角色，用于平台管理员权限控制，支持多级角色层级结构
"""

from typing import TYPE_CHECKING

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
    - 支持多级角色层级结构（父子关系）
    - 子角色自动继承父角色的权限
    """
    
    __tablename__ = "admin_roles"
    
    # 角色名称
    name: Mapped[str] = mapped_column(
        String(50), comment="角色名称"
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
    
    # ========== 层级结构字段 ==========
    # 父角色 ID
    parent_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("admin_roles.id", ondelete="SET NULL"),
        nullable=True, 
        index=True,
        comment="父角色 ID"
    )
    
    # 层级路径（物化路径，如 /1/3/7/）
    path: Mapped[str | None] = mapped_column(
        String(500), 
        nullable=True, 
        index=True,
        comment="层级路径"
    )
    
    # 层级深度（根节点为 1）
    level: Mapped[int] = mapped_column(
        Integer, 
        default=1, 
        comment="层级深度"
    )
    
    # ========== 关联关系 ==========
    # 父角色关系（自引用）
    parent: Mapped["AdminRole | None"] = relationship(
        "AdminRole",
        remote_side="AdminRole.id",
        back_populates="children",
        lazy="selectin",
    )
    
    # 子角色关系（自引用）
    children: Mapped[list["AdminRole"]] = relationship(
        "AdminRole",
        back_populates="parent",
        lazy="selectin",
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
        return f"<AdminRole(id={self.id}, code={self.code}, level={self.level})>"
    
    @property
    def children_count(self) -> int:
        """获取子角色数量"""
        return len([c for c in self.children if not c.is_deleted])
    
    @property
    def has_children(self) -> bool:
        """是否有子角色"""
        return self.children_count > 0
    
    @property
    def has_admins(self) -> bool:
        """是否有关联的管理员"""
        return len([a for a in self.admins if not a.is_deleted]) > 0
    
    def has_permission(self, permission_code: str) -> bool:
        """
        检查角色是否拥有指定权限（仅检查自身权限，不含继承）
        
        Args:
            permission_code: 权限代码
        
        Returns:
            是否拥有该权限
        """
        return any(p.code == permission_code for p in self.permissions)
    
    def get_ancestor_ids(self) -> list[int]:
        """
        从 path 中解析所有祖先角色 ID
        
        Returns:
            祖先角色 ID 列表（不含自身）
        """
        if not self.path:
            return []
        # path 格式为 /1/3/7/，解析出 [1, 3, 7]
        parts = [p for p in self.path.strip('/').split('/') if p]
        # 排除自身 ID
        return [int(p) for p in parts if int(p) != self.id]


# 需要导入用于类型注解
from app.models.auth.permission import Permission
if TYPE_CHECKING:
    from app.models.system.admin import Admin


__all__ = ["AdminRole", "admin_role_permissions"]
