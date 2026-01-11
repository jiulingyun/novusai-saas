"""
用户模型模块

定义用户相关的数据库模型
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantModel

if TYPE_CHECKING:
    pass


class User(TenantModel):
    """
    用户模型
    
    存储用户基本信息和认证数据
    """
    
    __tablename__ = "users"
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, comment="邮箱"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, nullable=True, comment="手机号"
    )
    
    # 认证信息
    password_hash: Mapped[str] = mapped_column(
        String(255), comment="密码哈希"
    )
    
    # 用户状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否激活"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否超级管理员"
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
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


__all__ = ["User"]
