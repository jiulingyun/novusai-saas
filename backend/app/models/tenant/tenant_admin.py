"""
租户管理员模型

租户后台管理人员，区别于租户业务用户
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantModel


class TenantAdmin(TenantModel):
    """
    租户管理员模型
    
    - 属于特定租户
    - 管理租户后台
    - 可管理租户内的用户、配置等
    - 独立于业务用户（TenantUser）
    """
    
    __tablename__ = "tenant_admins"
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), index=True, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(255), index=True, comment="邮箱"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), index=True, nullable=True, comment="手机号"
    )
    
    # 认证信息
    password_hash: Mapped[str] = mapped_column(
        String(255), comment="密码哈希"
    )
    
    # 管理员状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否激活"
    )
    is_owner: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否租户所有者（最高权限）"
    )
    
    # 个人资料
    nickname: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="昵称"
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像 URL"
    )
    
    # 登录信息
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="最后登录 IP"
    )
    
    # 角色关联（租户内角色）
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenant_admin_roles.id"), nullable=True, comment="角色 ID"
    )
    
    def __repr__(self) -> str:
        return f"<TenantAdmin(id={self.id}, tenant_id={self.tenant_id}, username={self.username})>"


__all__ = ["TenantAdmin"]
