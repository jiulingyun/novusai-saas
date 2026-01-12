"""
租户公开配置 Schema

定义登录前可获取的租户公开信息
"""

from pydantic import Field

from app.core.base_schema import BaseSchema


class TenantPublicConfig(BaseSchema):
    """
    租户公开配置
    
    登录页面可获取的租户信息（无需认证）
    """
    
    # 基本信息
    tenant_id: int = Field(..., description="租户 ID")
    tenant_code: str = Field(..., description="租户代码")
    tenant_name: str = Field(..., description="租户名称")
    
    # 品牌设置
    logo_url: str | None = Field(None, description="Logo URL")
    favicon_url: str | None = Field(None, description="Favicon URL")
    theme_color: str | None = Field(None, description="主题色")
    
    # 登录设置
    captcha_enabled: bool = Field(False, description="是否启用验证码")
    login_methods: list[str] = Field(
        default_factory=lambda: ["password"],
        description="支持的登录方式",
    )
    
    # 域名信息
    subdomain: str = Field(..., description="租户子域名")
    subdomain_url: str = Field(..., description="子域名完整 URL")


class DomainVerificationInfo(BaseSchema):
    """
    域名验证信息
    
    用于指导用户配置 DNS 记录
    """
    
    # 要验证的域名
    domain: str = Field(..., description="待验证域名")
    
    # CNAME 配置
    cname_target: str = Field(..., description="CNAME 解析目标")
    cname_name: str = Field(
        "@",
        description="CNAME 记录名称（通常为 @ 或子域名）",
    )
    
    # TXT 验证记录（可选，用于验证域名所有权）
    txt_name: str | None = Field(None, description="TXT 记录名称")
    txt_value: str | None = Field(None, description="TXT 记录值")
    
    # 验证状态
    is_verified: bool = Field(False, description="是否已验证")
    
    # 配置说明
    instructions: str = Field(
        "",
        description="配置说明",
    )


__all__ = [
    "TenantPublicConfig",
    "DomainVerificationInfo",
]
