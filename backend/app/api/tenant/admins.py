"""
租户管理员管理 API

提供租户内管理员 CRUD 接口
"""

from fastapi import Depends, HTTPException, Query, status
from pydantic import Field

from app.core.base_controller import TenantController
from app.core.base_schema import BaseSchema, PageParams
from app.core.deps import DbSession
from app.core.i18n import _
from app.core.response import success
from app.enums.rbac import PermissionScope
from app.models import TenantAdmin
from app.rbac import require_tenant_admin_permissions
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
    action_create,
    action_update,
    action_delete,
)
from app.schemas.tenant import (
    TenantAdminResponse,
    TenantAdminCreateRequest,
    TenantAdminUpdateRequest,
)
from app.services.tenant import TenantAdminService


class TenantAdminResetPasswordRequest(BaseSchema):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


@permission_resource(
    resource="tenant_user",
    name="menu.tenant.tenant_user",  # i18n key
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="user",
        path="/system/admins",
        component="system/admin/List",
        parent="system",  # 父菜单: 权限管理
        sort_order=10,
    ),
)
class TenantAdminController(TenantController):
    """
    租户管理员控制器
    
    提供租户内管理员 CRUD、状态切换、密码重置等接口
    """
    
    prefix = "/admins"
    tags = ["租户管理员管理"]
    service_class = TenantAdminService
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("", summary="获取管理员列表")
        @action_read("action.admin.list")
        async def list_admins(
            db: DbSession,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:read")),
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="每页数量"),
            is_active: bool | None = Query(None, description="是否激活"),
        ):
            """
            获取当前租户的所有管理员列表
            
            - 支持分页
            - 支持按激活状态过滤
            - 自动过滤当前租户数据
            
            权限: tenant_user:read
            """
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            page_params = PageParams(page=page, page_size=page_size)
            
            # 构建过滤条件
            filters = {}
            if is_active is not None:
                filters["is_active"] = is_active
            
            # 获取分页数据
            page_result = await service.get_paginated(page_params, **filters)
            
            return success(
                data={
                    "items": [TenantAdminResponse.from_model(item) for item in page_result.items],
                    "total": page_result.total,
                    "page": page_result.page,
                    "page_size": page_result.page_size,
                    "pages": page_result.pages,
                },
                message=_("common.success"),
            )
        
        @router.get("/{admin_id}", summary="获取管理员详情")
        @action_read("action.admin.detail")
        async def get_admin(
            db: DbSession,
            admin_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:read")),
        ):
            """
            获取管理员详情
            
            权限: tenant_user:read
            """
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            admin = await service.get_by_id(admin_id)
            
            if admin is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant_admin.not_found"),
                )
            
            return success(
                data=TenantAdminResponse.from_model(admin),
                message=_("common.success"),
            )
        
        @router.post("", summary="创建管理员")
        @action_create("action.admin.create")
        async def create_admin(
            db: DbSession,
            data: TenantAdminCreateRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:create")),
        ):
            """
            创建租户管理员
            
            权限: tenant_user:create
            """
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            admin = await service.create_admin(
                username=data.username,
                email=data.email,
                password=data.password,
                phone=data.phone,
                nickname=data.nickname,
                is_active=data.is_active,
                is_owner=data.is_owner,
                role_id=data.role_id,
            )
            await db.commit()
            
            return success(
                data=TenantAdminResponse.from_model(admin),
                message=_("tenant_admin.created"),
            )
        
        @router.put("/{admin_id}", summary="更新管理员")
        @action_update("action.admin.update")
        async def update_admin(
            db: DbSession,
            admin_id: int,
            data: TenantAdminUpdateRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:update")),
        ):
            """
            更新租户管理员信息
            
            - 不能修改用户名
            - 密码通过专门接口修改
            
            权限: tenant_user:update
            """
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            
            # 移除 None 值
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            
            admin = await service.update_admin(admin_id, update_data)
            await db.commit()
            
            return success(
                data=TenantAdminResponse.from_model(admin),
                message=_("tenant_admin.updated"),
            )
        
        @router.delete("/{admin_id}", summary="删除管理员")
        @action_delete("action.admin.delete")
        async def delete_admin(
            db: DbSession,
            admin_id: int,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:delete")),
        ):
            """
            删除租户管理员（软删除）
            
            - 不能删除自己
            - 不能删除租户所有者（除非自己也是所有者）
            
            权限: tenant_user:delete
            """
            # 不能删除自己
            if admin_id == current_admin.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("tenant_admin.cannot_delete_self"),
                )
            
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            
            # 检查目标管理员
            target_admin = await service.get_by_id(admin_id)
            if target_admin is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant_admin.not_found"),
                )
            
            # 非所有者不能删除所有者
            if target_admin.is_owner and not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.cannot_delete_owner"),
                )
            
            await service.delete(admin_id)
            await db.commit()
            
            return success(message=_("tenant_admin.deleted"))
        
        @router.put("/{admin_id}/reset-password", summary="重置密码")
        @action_update("action.admin.reset_password")
        async def reset_password(
            db: DbSession,
            admin_id: int,
            data: TenantAdminResetPasswordRequest,
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:update")),
        ):
            """
            重置管理员密码（租户所有者操作）
            
            - 只有租户所有者可以重置其他管理员的密码
            
            权限: tenant_user:update + 租户所有者
            """
            # 验证当前用户是租户所有者
            if not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.owner_required"),
                )
            
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            await service.reset_password(admin_id, data.new_password)
            await db.commit()
            
            return success(message=_("tenant_admin.password_reset"))
        
        @router.put("/{admin_id}/status", summary="切换管理员状态")
        @action_update("action.admin.toggle_status")
        async def toggle_admin_status(
            db: DbSession,
            admin_id: int,
            is_active: bool = Query(..., description="是否激活"),
            current_admin: TenantAdmin = Depends(require_tenant_admin_permissions("tenant_user:update")),
        ):
            """
            启用或禁用管理员
            
            - 不能禁用自己
            - 非所有者不能操作所有者
            
            权限: tenant_user:update
            """
            # 不能禁用自己
            if admin_id == current_admin.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("tenant_admin.cannot_disable_self"),
                )
            
            service = TenantAdminService(db, tenant_id=current_admin.tenant_id)
            
            # 检查目标管理员
            target_admin = await service.get_by_id(admin_id)
            if target_admin is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("tenant_admin.not_found"),
                )
            
            # 非所有者不能操作所有者
            if target_admin.is_owner and not current_admin.is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("tenant_admin.cannot_modify_owner"),
                )
            
            admin = await service.toggle_status(admin_id, is_active)
            await db.commit()
            
            return success(
                data=TenantAdminResponse.from_model(admin),
                message=_("tenant_admin.status_updated"),
            )


# 导出路由器
router = TenantAdminController.get_router()

__all__ = ["router", "TenantAdminController"]
