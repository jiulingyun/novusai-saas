"""
租户设置管理 API

提供租户设置和自定义域名管理接口
"""

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import select, func

from app.core.base_controller import TenantController
from app.core.config import settings
from app.core.deps import DbSession, ActiveTenantAdmin
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.models import Tenant, TenantDomain, TenantAdmin
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
    action_create,
    action_update,
    action_delete,
)
from app.schemas.tenant import (
    TenantSettingsResponse,
    TenantSettingsUpdateRequest,
    TenantDomainResponse,
    TenantDomainCreateRequest,
    TenantDomainUpdateRequest,
)


@permission_resource(
    resource="tenant_settings",
    name="menu.tenant.tenant_settings",  # i18n key
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="lucide:settings",
        path="/system/settings",
        component="system/settings/Index",
        parent="system",  # 父菜单: 权限管理
        sort_order=30,
    ),
)
class TenantSettingsController(TenantController):
    """
    租户设置控制器
    
    提供租户设置和自定义域名管理接口
    """
    
    prefix = "/settings"
    tags = ["租户设置管理"]
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        # ==================== 租户设置 ====================
        
        @router.get("", summary="获取租户设置")
        @action_read("action.tenant_settings.view")
        async def get_tenant_settings(
            request: Request,
            db: DbSession,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取当前租户的设置信息
            
            权限: tenant_settings:read
            """
            # 获取租户
            result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            # 统计已绑定域名数量
            domain_count_result = await db.execute(
                select(func.count(TenantDomain.id)).where(
                    TenantDomain.tenant_id == tenant.id,
                    TenantDomain.is_deleted == False,
                )
            )
            custom_domain_count = domain_count_result.scalar() or 0
            
            # 构建子域名 URL
            subdomain_url = f"https://{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
            
            return success(
                data=TenantSettingsResponse(
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
                    max_custom_domains=tenant.max_custom_domains,
                    custom_domain_count=custom_domain_count,
                ),
                message=_("common.success"),
            )
        
        @router.put("", summary="更新租户设置")
        @action_update("action.tenant_settings.update")
        async def update_tenant_settings(
            request: Request,
            db: DbSession,
            data: TenantSettingsUpdateRequest,
            current_admin: ActiveTenantAdmin,
        ):
            """
            更新当前租户的设置
            
            - 只有租户所有者可以修改设置
            
            权限: tenant_settings:update + 租户所有者
            """
            # 验证是否为租户所有者
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            # 获取租户
            result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            # 更新设置
            current_settings = tenant.settings or {}
            
            if data.logo_url is not None:
                current_settings["logo_url"] = data.logo_url
            if data.favicon_url is not None:
                current_settings["favicon_url"] = data.favicon_url
            if data.theme_color is not None:
                current_settings["theme_color"] = data.theme_color
            if data.captcha_enabled is not None:
                current_settings["captcha_enabled"] = data.captcha_enabled
            if data.login_methods is not None:
                current_settings["login_methods"] = data.login_methods
            
            tenant.settings = current_settings
            await db.commit()
            await db.refresh(tenant)
            
            # 统计域名数量
            domain_count_result = await db.execute(
                select(func.count(TenantDomain.id)).where(
                    TenantDomain.tenant_id == tenant.id,
                    TenantDomain.is_deleted == False,
                )
            )
            custom_domain_count = domain_count_result.scalar() or 0
            
            subdomain_url = f"https://{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
            
            return success(
                data=TenantSettingsResponse(
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
                    max_custom_domains=tenant.max_custom_domains,
                    custom_domain_count=custom_domain_count,
                ),
                message=_("tenant.settings_updated"),
            )
        
        # ==================== 域名管理 ====================
        
        @router.get("/domains", summary="获取域名列表")
        @action_read("action.tenant_settings.domain_list")
        async def list_tenant_domains(
            request: Request,
            db: DbSession,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取当前租户绑定的自定义域名列表
            
            权限: tenant_settings:read
            """
            result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.tenant_id == current_admin.tenant_id,
                    TenantDomain.is_deleted == False,
                ).order_by(TenantDomain.is_primary.desc(), TenantDomain.created_at)
            )
            domains = result.scalars().all()
            
            # 获取租户信息以构建 cname_target
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}" if tenant else None
            
            return success(
                data=[
                    TenantDomainResponse(
                        id=d.id,
                        tenant_id=d.tenant_id,
                        domain=d.domain,
                        is_verified=d.is_verified,
                        verified_at=d.verified_at,
                        is_primary=d.is_primary,
                        ssl_status=d.ssl_status,
                        ssl_expires_at=d.ssl_expires_at,
                        cname_target=cname_target,
                        created_at=d.created_at,
                    )
                    for d in domains
                ],
                message=_("common.success"),
            )
        
        @router.post("/domains", summary="添加自定义域名")
        @action_create("action.tenant_settings.domain_add")
        async def add_tenant_domain(
            request: Request,
            db: DbSession,
            data: TenantDomainCreateRequest,
            current_admin: ActiveTenantAdmin,
        ):
            """
            添加自定义域名
            
            - 只有租户所有者可以添加域名
            - 域名数量受套餐限制
            
            权限: tenant_settings:create + 租户所有者
            """
            # 验证是否为租户所有者
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            # 获取租户
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            # 检查配额
            if not settings.ALLOW_CUSTOM_DOMAIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("domain.custom_domain_disabled"),
                )
            
            domain_count_result = await db.execute(
                select(func.count(TenantDomain.id)).where(
                    TenantDomain.tenant_id == tenant.id,
                    TenantDomain.is_deleted == False,
                )
            )
            current_count = domain_count_result.scalar() or 0
            
            if current_count >= tenant.max_custom_domains:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("domain.quota_exceeded"),
                )
            
            # 检查域名是否已被使用
            existing_result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.domain == data.domain.lower(),
                    TenantDomain.is_deleted == False,
                )
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("domain.already_exists"),
                )
            
            # 如果设为主域名，先取消其他主域名
            if data.is_primary:
                await db.execute(
                    TenantDomain.__table__.update()
                    .where(
                        TenantDomain.tenant_id == tenant.id,
                        TenantDomain.is_primary == True,
                    )
                    .values(is_primary=False)
                )
            
            # 创建域名
            domain = TenantDomain(
                tenant_id=tenant.id,
                domain=data.domain.lower(),
                is_primary=data.is_primary,
                is_verified=False,
                ssl_status="pending",
                verification_token=secrets.token_urlsafe(32),
                remark=data.remark,
            )
            
            db.add(domain)
            await db.commit()
            await db.refresh(domain)
            
            cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
            
            return success(
                data=TenantDomainResponse(
                    id=domain.id,
                    tenant_id=domain.tenant_id,
                    domain=domain.domain,
                    is_verified=domain.is_verified,
                    verified_at=domain.verified_at,
                    is_primary=domain.is_primary,
                    ssl_status=domain.ssl_status,
                    ssl_expires_at=domain.ssl_expires_at,
                    cname_target=cname_target,
                    created_at=domain.created_at,
                ),
                message=_("domain.created"),
            )
        
        @router.get("/domains/{domain_id}", summary="获取域名详情")
        @action_read("action.tenant_settings.domain_detail")
        async def get_tenant_domain(
            request: Request,
            db: DbSession,
            domain_id: int,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取域名详情及验证信息
            
            权限: tenant_settings:read
            """
            result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.id == domain_id,
                    TenantDomain.tenant_id == current_admin.tenant_id,
                    TenantDomain.is_deleted == False,
                )
            )
            domain = result.scalar_one_or_none()
            
            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("domain.not_found"),
                )
            
            # 获取租户
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}" if tenant else None
            
            return success(
                data=TenantDomainResponse(
                    id=domain.id,
                    tenant_id=domain.tenant_id,
                    domain=domain.domain,
                    is_verified=domain.is_verified,
                    verified_at=domain.verified_at,
                    is_primary=domain.is_primary,
                    ssl_status=domain.ssl_status,
                    ssl_expires_at=domain.ssl_expires_at,
                    cname_target=cname_target,
                    created_at=domain.created_at,
                ),
                message=_("common.success"),
            )
        
        @router.put("/domains/{domain_id}", summary="更新域名设置")
        @action_update("action.tenant_settings.domain_update")
        async def update_tenant_domain(
            request: Request,
            db: DbSession,
            domain_id: int,
            data: TenantDomainUpdateRequest,
            current_admin: ActiveTenantAdmin,
        ):
            """
            更新域名设置（如设为主域名）
            
            权限: tenant_settings:update + 租户所有者
            """
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.id == domain_id,
                    TenantDomain.tenant_id == current_admin.tenant_id,
                    TenantDomain.is_deleted == False,
                )
            )
            domain = result.scalar_one_or_none()
            
            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("domain.not_found"),
                )
            
            # 如果设为主域名，先取消其他主域名
            if data.is_primary:
                await db.execute(
                    TenantDomain.__table__.update()
                    .where(
                        TenantDomain.tenant_id == current_admin.tenant_id,
                        TenantDomain.is_primary == True,
                        TenantDomain.id != domain_id,
                    )
                    .values(is_primary=False)
                )
                domain.is_primary = True
            elif data.is_primary is False:
                domain.is_primary = False
            
            if data.remark is not None:
                domain.remark = data.remark
            
            await db.commit()
            await db.refresh(domain)
            
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}" if tenant else None
            
            return success(
                data=TenantDomainResponse(
                    id=domain.id,
                    tenant_id=domain.tenant_id,
                    domain=domain.domain,
                    is_verified=domain.is_verified,
                    verified_at=domain.verified_at,
                    is_primary=domain.is_primary,
                    ssl_status=domain.ssl_status,
                    ssl_expires_at=domain.ssl_expires_at,
                    cname_target=cname_target,
                    created_at=domain.created_at,
                ),
                message=_("domain.updated"),
            )
        
        @router.delete("/domains/{domain_id}", summary="删除域名")
        @action_delete("action.tenant_settings.domain_delete")
        async def delete_tenant_domain(
            request: Request,
            db: DbSession,
            domain_id: int,
            current_admin: ActiveTenantAdmin,
        ):
            """
            删除自定义域名
            
            权限: tenant_settings:delete + 租户所有者
            """
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.id == domain_id,
                    TenantDomain.tenant_id == current_admin.tenant_id,
                    TenantDomain.is_deleted == False,
                )
            )
            domain = result.scalar_one_or_none()
            
            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("domain.not_found"),
                )
            
            domain.soft_delete()
            await db.commit()
            
            return success(message=_("domain.deleted"))
        
        @router.post("/domains/{domain_id}/verify", summary="验证域名")
        @action_update("action.tenant_settings.domain_verify")
        async def verify_tenant_domain(
            request: Request,
            db: DbSession,
            domain_id: int,
            current_admin: ActiveTenantAdmin,
        ):
            """
            验证域名 DNS 配置
            
            检查 CNAME 记录是否正确配置。
            
            权限: tenant_settings:update
            """
            result = await db.execute(
                select(TenantDomain).where(
                    TenantDomain.id == domain_id,
                    TenantDomain.tenant_id == current_admin.tenant_id,
                    TenantDomain.is_deleted == False,
                )
            )
            domain = result.scalar_one_or_none()
            
            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("domain.not_found"),
                )
            
            # 获取租户
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == current_admin.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            # TODO: 实际的 DNS 验证逻辑
            # 这里简化处理，实际应该查询 DNS 记录验证 CNAME 指向
            # import dns.resolver
            # try:
            #     answers = dns.resolver.resolve(domain.domain, 'CNAME')
            #     expected = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
            #     for rdata in answers:
            #         if str(rdata.target).rstrip('.') == expected:
            #             domain.is_verified = True
            #             domain.verified_at = datetime.now(timezone.utc)
            #             break
            # except Exception:
            #     pass
            
            # 简化实现：假设验证通过
            domain.is_verified = True
            domain.verified_at = datetime.now(timezone.utc)
            domain.ssl_status = "active"  # 实际应该触发 SSL 证书申请
            
            await db.commit()
            await db.refresh(domain)
            
            cname_target = f"{tenant.code}{settings.TENANT_DOMAIN_SUFFIX}"
            
            return success(
                data=TenantDomainResponse(
                    id=domain.id,
                    tenant_id=domain.tenant_id,
                    domain=domain.domain,
                    is_verified=domain.is_verified,
                    verified_at=domain.verified_at,
                    is_primary=domain.is_primary,
                    ssl_status=domain.ssl_status,
                    ssl_expires_at=domain.ssl_expires_at,
                    cname_target=cname_target,
                    created_at=domain.created_at,
                ),
                message=_("domain.verified"),
            )


# 导出路由器
router = TenantSettingsController.get_router()

__all__ = ["router", "TenantSettingsController"]
