"""
租户管理 API

提供租户 CRUD 接口（平台管理员专用）
"""

from fastapi import Depends, Query

from app.core.base_controller import GlobalController
from app.core.base_schema import PageParams
from app.core.deps import DbSession
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.models import Admin
from app.rbac import require_admin_permissions
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
    action_create,
    action_update,
    action_delete,
)
from app.schemas.system import (
    TenantResponse,
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantStatusRequest,
)
from app.services.system import TenantService


@permission_resource(
    resource="tenant",
    name="menu.admin.tenant",  # i18n key
    scope=PermissionScope.ADMIN,
    menu=MenuConfig(
        icon="shop",
        path="/tenant/list",
        component="tenant/List",
        parent="tenant_mgmt",  # 父菜单: 租户管理
        sort_order=10,
    ),
)
class AdminTenantController(GlobalController):
    """
    租户管理控制器
    
    提供租户 CRUD、状态切换等接口
    """
    
    prefix = "/tenants"
    tags = ["租户管理"]
    service_class = TenantService
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("", summary="获取租户列表")
        @action_read("查看租户列表")
        async def list_tenants(
            db: DbSession,
            current_admin: Admin = Depends(require_admin_permissions("tenant:read")),
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="每页数量"),
            is_active: bool | None = Query(None, description="是否启用"),
            plan: str | None = Query(None, description="套餐类型"),
        ):
            """
            获取所有租户列表
            
            - 支持分页
            - 支持按状态、套餐过滤
            
            权限: tenant:read
            """
            service = TenantService(db)
            page_params = PageParams(page=page, page_size=page_size)
            
            # 构建过滤条件
            filters = {}
            if is_active is not None:
                filters["is_active"] = is_active
            if plan is not None:
                filters["plan"] = plan
            
            # 获取分页数据
            page_result = await service.get_paginated(page_params, **filters)
            
            return success(
                data={
                    "items": [TenantResponse.model_validate(item, from_attributes=True) for item in page_result.items],
                    "total": page_result.total,
                    "page": page_result.page,
                    "page_size": page_result.page_size,
                    "pages": page_result.pages,
                },
                message=_("common.success"),
            )
        
        @router.get("/{tenant_id}", summary="获取租户详情")
        @action_read("查看租户详情")
        async def get_tenant(
            db: DbSession,
            tenant_id: int,
            current_admin: Admin = Depends(require_admin_permissions("tenant:read")),
        ):
            """
            获取租户详情
            
            权限: tenant:read
            """
            service = TenantService(db)
            tenant = await service.get_by_id(tenant_id)
            
            if tenant is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            return success(
                data=TenantResponse.model_validate(tenant, from_attributes=True),
                message=_("common.success"),
            )
        
        @router.post("", summary="创建租户")
        @action_create("创建租户")
        async def create_tenant(
            db: DbSession,
            data: TenantCreateRequest,
            current_admin: Admin = Depends(require_admin_permissions("tenant:create")),
        ):
            """
            创建租户
            
            权限: tenant:create
            """
            service = TenantService(db)
            tenant = await service.create_tenant(
                code=data.code,
                name=data.name,
                contact_name=data.contact_name,
                contact_phone=data.contact_phone,
                contact_email=data.contact_email,
                plan=data.plan,
                quota=data.quota,
                expires_at=data.expires_at,
                remark=data.remark,
            )
            await db.commit()
            
            return success(
                data=TenantResponse.model_validate(tenant, from_attributes=True),
                message=_("tenant.created"),
            )
        
        @router.put("/{tenant_id}", summary="更新租户")
        @action_update("更新租户")
        async def update_tenant(
            db: DbSession,
            tenant_id: int,
            data: TenantUpdateRequest,
            current_admin: Admin = Depends(require_admin_permissions("tenant:update")),
        ):
            """
            更新租户信息
            
            权限: tenant:update
            """
            service = TenantService(db)
            
            # 移除 None 值
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            
            tenant = await service.update_tenant(tenant_id, update_data)
            await db.commit()
            
            return success(
                data=TenantResponse.model_validate(tenant, from_attributes=True),
                message=_("tenant.updated"),
            )
        
        @router.delete("/{tenant_id}", summary="删除租户")
        @action_delete("删除租户")
        async def delete_tenant(
            db: DbSession,
            tenant_id: int,
            current_admin: Admin = Depends(require_admin_permissions("tenant:delete")),
        ):
            """
            删除租户（软删除）
            
            **注意**: 删除租户会导致该租户下所有数据不可访问
            
            权限: tenant:delete
            """
            service = TenantService(db)
            
            # 检查租户是否存在
            tenant = await service.get_by_id(tenant_id)
            if tenant is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant.not_found"),
                )
            
            await service.delete(tenant_id)
            await db.commit()
            
            return success(message=_("tenant.deleted"))
        
        @router.put("/{tenant_id}/status", summary="切换租户状态")
        @action_update("切换租户状态")
        async def toggle_tenant_status(
            db: DbSession,
            tenant_id: int,
            data: TenantStatusRequest,
            current_admin: Admin = Depends(require_admin_permissions("tenant:update")),
        ):
            """
            启用或禁用租户
            
            - 禁用后租户下所有用户无法登录
            
            权限: tenant:update
            """
            service = TenantService(db)
            tenant = await service.toggle_status(tenant_id, data.is_active)
            await db.commit()
            
            return success(
                data=TenantResponse.model_validate(tenant, from_attributes=True),
                message=_("tenant.status_updated"),
            )


# 导出路由器
router = AdminTenantController.get_router()

__all__ = ["router", "AdminTenantController"]
