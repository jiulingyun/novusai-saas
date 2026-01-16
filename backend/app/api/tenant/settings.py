"""
租户设置管理 API

提供租户设置和自定义域名管理接口
"""

from fastapi import HTTPException, Request, status

from app.core.base_controller import TenantController
from app.core.deps import DbSession, ActiveTenantAdmin
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.exceptions import BusinessException, NotFoundException
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
from app.services.tenant import TenantSettingsService


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
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                settings_data = await service.get_settings()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            return success(
                data=TenantSettingsResponse(**settings_data),
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
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                settings_data = await service.update_settings(data.model_dump(exclude_none=True))
                await db.commit()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            return success(
                data=TenantSettingsResponse(**settings_data),
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
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                tenant = await service.get_tenant()
                domains = await service.list_domains()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            cname_target = service.get_cname_target(tenant)
            
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
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                tenant = await service.get_tenant()
                domain = await service.add_domain(
                    domain=data.domain,
                    is_primary=data.is_primary,
                    remark=data.remark,
                )
                await db.commit()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            except BusinessException as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e.message),
                )
            
            cname_target = service.get_cname_target(tenant)
            
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
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                tenant = await service.get_tenant()
                domain = await service.get_domain(domain_id)
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            cname_target = service.get_cname_target(tenant)
            
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
            
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                tenant = await service.get_tenant()
                domain = await service.update_domain(
                    domain_id=domain_id,
                    is_primary=data.is_primary,
                    remark=data.remark,
                )
                await db.commit()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            cname_target = service.get_cname_target(tenant)
            
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
            
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                await service.delete_domain(domain_id)
                await db.commit()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
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
            service = TenantSettingsService(db, current_admin.tenant_id)
            
            try:
                tenant = await service.get_tenant()
                domain = await service.verify_domain(domain_id)
                await db.commit()
            except NotFoundException as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e.message),
                )
            
            cname_target = service.get_cname_target(tenant)
            
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
