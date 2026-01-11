"""
租户模型

多租户 SaaS 的租户实体
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Tenant(BaseModel):
    """
    租户模型
    
    - 每个租户是一个独立的商户/组织
    - 租户数据完全隔离
    """
    
    __tablename__ = "tenants"
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), index=True, comment="租户名称"
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="租户编码（唯一标识）"
    )
    
    # 联系信息
    contact_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="联系人姓名"
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="联系人电话"
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="联系人邮箱"
    )
    
    # 租户状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    
    # 套餐/配额
    plan: Mapped[str] = mapped_column(
        String(50), default="free", comment="套餐类型"
    )
    quota: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="配额配置"
    )
    
    # 有效期
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="到期时间"
    )
    
    # 备注
    remark: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name})>"


__all__ = ["Tenant"]
