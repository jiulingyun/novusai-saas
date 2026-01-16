"""
租户模型

多租户 SaaS 的租户实体
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class Tenant(BaseModel):
    """
    租户模型
    
    - 每个租户是一个独立的商户/组织
    - 租户数据完全隔离
    """
    
    __tablename__ = "tenants"
    
    # 允许前端筛选的字段
    __filterable__ = {
        "id": "id",
        "name": "name",
        "code": "code",
        "contact_name": "contact_name",
        "contact_phone": "contact_phone",
        "contact_email": "contact_email",
        "is_active": "is_active",
        "plan": "plan",
        "expires_at": "expires_at",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    
    # 下拉选项配置
    __selectable__ = {
        "label": "name",
        "value": "id",
        "search": ["name", "code"],
        "extra": ["code"],
    }
    
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
    
    # 租户设置（JSON 格式）
    # @deprecated: 已废弃，请使用 ConfigService.get_tenant_config() 获取配置
    # 数据已迁移到 system_config_values 表
    # 保留字段以兼容旧数据，但不再使用
    settings: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="租户设置(已废弃)"
    )
    
    # ==================== 关系 ====================
    
    # 租户绑定的域名列表
    domains = relationship(
        "TenantDomain",
        back_populates="tenant",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    # ==================== 辅助属性 ====================
    
    @property
    def subdomain(self) -> str:
        """获取租户子域名"""
        return self.code
    
    # 以下属性已废弃，请使用 ConfigService.get_tenant_config() 代替
    # - logo_url -> tenant_logo
    # - favicon_url -> tenant_favicon  
    # - theme_color -> tenant_primary_color
    # - captcha_enabled -> tenant_captcha_enabled
    # - login_methods -> tenant_login_methods
    
    @property
    def max_custom_domains(self) -> int:
        """获取最大自定义域名数量（由套餐决定）"""
        # 从 quota 或 settings 中获取，默认为 0
        if self.quota:
            return self.quota.get("max_custom_domains", 0)
        return 0
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name})>"


__all__ = ["Tenant"]
