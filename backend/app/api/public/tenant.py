"""
租户公开 API

提供登录前可访问的租户公开信息接口
"""

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.core.i18n import _
from app.core.response import success
from app.middleware.tenant import get_tenant_context, get_current_tenant
from app.schemas.public import TenantPublicConfig, DomainVerificationInfo


router = APIRouter(prefix="/tenant", tags=["租户公开接口"])


@router.get("/config", summary="获取当前租户公开配置")
async def get_tenant_public_config(request: Request):
    """
    获取当前租户的公开配置
    
    根据请求的域名自动识别租户，返回该租户的公开配置信息。
    
    **域名识别规则:**
    - 子域名模式: `{tenant_code}.app.novusai.com`
    - 自定义域名模式: 用户绑定的独立域名
    
    **返回内容:**
    - 租户基本信息（名称、logo 等）
    - 登录配置（验证码、登录方式等）
    - 品牌设置（主题色等）
    
    此接口无需认证，用于前端登录页面获取租户信息。
    """
    tenant_ctx = get_tenant_context(request)
    
    if not tenant_ctx or not tenant_ctx.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("tenant.not_found"),
        )
    
    tenant = tenant_ctx.tenant
    
    # 构建子域名完整 URL
    subdomain_url = f"https://{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
    
    return success(
        data=TenantPublicConfig(
            tenant_id=tenant.id,
            tenant_code=tenant.code,
            tenant_name=tenant.name,
            logo_url=tenant.logo_url,
            favicon_url=tenant.favicon_url,
            theme_color=tenant.theme_color,
            captcha_enabled=tenant.captcha_enabled,
            login_methods=tenant.login_methods,
            subdomain=tenant.code,
            subdomain_url=subdomain_url,
        ),
        message=_("common.success"),
    )


@router.get("/domain-verification", summary="获取域名验证信息")
async def get_domain_verification_info(
    request: Request,
    domain: str,
):
    """
    获取域名验证信息
    
    用于指导用户配置 DNS 记录，将自定义域名解析到租户子域名。
    
    **参数:**
    - `domain`: 待绑定的域名（如 `app.example.com`）
    
    **返回:**
    - CNAME 解析目标
    - TXT 验证记录（可选）
    - 配置说明
    
    此接口无需认证。
    """
    tenant_ctx = get_tenant_context(request)
    
    if not tenant_ctx or not tenant_ctx.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("tenant.not_found"),
        )
    
    tenant = tenant_ctx.tenant
    
    # CNAME 目标
    cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
    
    # TXT 验证记录
    txt_name = f"{settings.DOMAIN_VERIFICATION_PREFIX}.{domain}"
    txt_value = f"novusai-verification={tenant.code}"
    
    # 配置说明
    instructions = f"""请在您的 DNS 服务商处添加以下记录：

1. CNAME 记录（必需）:
   - 主机记录: @ 或您的子域名
   - 记录类型: CNAME
   - 记录值: {cname_target}

2. TXT 记录（用于验证所有权）:
   - 主机记录: {settings.DOMAIN_VERIFICATION_PREFIX}
   - 记录类型: TXT
   - 记录值: {txt_value}

DNS 记录生效可能需要几分钟到几小时，请耐心等待。
"""
    
    return success(
        data=DomainVerificationInfo(
            domain=domain,
            cname_target=cname_target,
            cname_name="@",
            txt_name=txt_name,
            txt_value=txt_value,
            is_verified=False,
            instructions=instructions,
        ),
        message=_("common.success"),
    )


__all__ = ["router"]
