"""
平台管理员管理 API

提供平台管理员 CRUD 接口
"""

from fastapi import Depends, Query
from pydantic import Field

from app.core.base_controller import GlobalController
from app.core.base_schema import BaseSchema, PageParams
from app.core.deps import DbSession, ActiveAdmin
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
    AdminResponse,
    AdminCreateRequest,
    AdminUpdateRequest,
)
from app.services.system import AdminService


class AdminResetPasswordRequest(BaseSchema):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


@permission_resource(
    resource="admin_user",
    name="menu.admin.admin_user",  # i18n key
    scope=PermissionScope.ADMIN,
    menu=MenuConfig(
        icon="user",
        path="/system/admins",
        component="system/admin/List",
        parent="system",  # 父菜单: 权限管理
        sort_order=5,
    ),
)
class AdminAdminController(GlobalController):
    """
    平台管理员控制器
    
    提供管理员 CRUD、状态切换、密码重置等接口
    """
    
    prefix = "/admins"
    tags = ["平台管理员管理"]
    service_class = AdminService
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("", summary="获取管理员列表")
        @action_read("查看管理员列表")
        async def list_admins(
            db: DbSession,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:read")),
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="每页数量"),
            is_active: bool | None = Query(None, description="是否激活"),
        ):
            """
            获取所有平台管理员列表
            
            - 支持分页
            - 支持按激活状态过滤
            
            权限: admin_user:read
            """
            service = AdminService(db)
            page_params = PageParams(page=page, page_size=page_size)
            
            # 构建过滤条件
            filters = {}
            if is_active is not None:
                filters["is_active"] = is_active
            
            # 获取分页数据
            page_result = await service.get_paginated(page_params, **filters)
            
            return success(
                data={
                    "items": [AdminResponse.model_validate(item, from_attributes=True) for item in page_result.items],
                    "total": page_result.total,
                    "page": page_result.page,
                    "page_size": page_result.page_size,
                    "pages": page_result.pages,
                },
                message=_("common.success"),
            )
        
        @router.get("/{admin_id}", summary="获取管理员详情")
        @action_read("查看管理员详情")
        async def get_admin(
            db: DbSession,
            admin_id: int,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:read")),
        ):
            """
            获取管理员详情
            
            权限: admin_user:read
            """
            service = AdminService(db)
            admin = await service.get_by_id(admin_id)
            
            if admin is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("admin.not_found"),
                )
            
            return success(
                data=AdminResponse.model_validate(admin, from_attributes=True),
                message=_("common.success"),
            )
        
        @router.post("", summary="创建管理员")
        @action_create("创建管理员")
        async def create_admin(
            db: DbSession,
            data: AdminCreateRequest,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:create")),
        ):
            """
            创建平台管理员
            
            权限: admin_user:create
            """
            service = AdminService(db)
            admin = await service.create_admin(
                username=data.username,
                email=data.email,
                password=data.password,
                phone=data.phone,
                nickname=data.nickname,
                is_active=data.is_active,
                is_super=data.is_super,
                role_id=data.role_id,
            )
            await db.commit()
            
            return success(
                data=AdminResponse.model_validate(admin, from_attributes=True),
                message=_("admin.created"),
            )
        
        @router.put("/{admin_id}", summary="更新管理员")
        @action_update("更新管理员")
        async def update_admin(
            db: DbSession,
            admin_id: int,
            data: AdminUpdateRequest,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:update")),
        ):
            """
            更新平台管理员信息
            
            - 不能修改用户名
            - 密码通过专门接口修改
            
            权限: admin_user:update
            """
            service = AdminService(db)
            
            # 移除 None 值
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            
            admin = await service.update_admin(admin_id, update_data)
            await db.commit()
            
            return success(
                data=AdminResponse.model_validate(admin, from_attributes=True),
                message=_("admin.updated"),
            )
        
        @router.delete("/{admin_id}", summary="删除管理员")
        @action_delete("删除管理员")
        async def delete_admin(
            db: DbSession,
            admin_id: int,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:delete")),
        ):
            """
            删除平台管理员（软删除）
            
            - 不能删除自己
            - 不能删除超级管理员（除非自己也是超管）
            
            权限: admin_user:delete
            """
            # 不能删除自己
            if admin_id == current_admin.id:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("admin.cannot_delete_self"),
                )
            
            service = AdminService(db)
            
            # 检查目标管理员
            target_admin = await service.get_by_id(admin_id)
            if target_admin is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("admin.not_found"),
                )
            
            # 非超管不能删除超管
            if target_admin.is_super and not current_admin.is_super:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("admin.cannot_delete_super"),
                )
            
            await service.delete(admin_id)
            await db.commit()
            
            return success(message=_("admin.deleted"))
        
        @router.put("/{admin_id}/reset-password", summary="重置密码")
        @action_update("重置管理员密码")
        async def reset_password(
            db: DbSession,
            admin_id: int,
            data: AdminResetPasswordRequest,
            current_admin: Admin = Depends(require_admin_permissions("admin_user:update")),
        ):
            """
            重置管理员密码（超管操作）
            
            - 只有超级管理员可以重置其他管理员的密码
            
            权限: admin_user:update + 超级管理员
            """
            # 验证当前用户是超级管理员
            if not current_admin.is_super:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("admin.super_admin_required"),
                )
            
            service = AdminService(db)
            await service.reset_password(admin_id, data.new_password)
            await db.commit()
            
            return success(message=_("admin.password_reset"))
        
        @router.put("/{admin_id}/status", summary="切换管理员状态")
        @action_update("切换管理员状态")
        async def toggle_admin_status(
            db: DbSession,
            admin_id: int,
            is_active: bool = Query(..., description="是否激活"),
            current_admin: Admin = Depends(require_admin_permissions("admin_user:update")),
        ):
            """
            启用或禁用管理员
            
            - 不能禁用自己
            - 非超管不能操作超管
            
            权限: admin_user:update
            """
            # 不能禁用自己
            if admin_id == current_admin.id:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("admin.cannot_disable_self"),
                )
            
            service = AdminService(db)
            
            # 检查目标管理员
            target_admin = await service.get_by_id(admin_id)
            if target_admin is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("admin.not_found"),
                )
            
            # 非超管不能操作超管
            if target_admin.is_super and not current_admin.is_super:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_("admin.cannot_modify_super"),
                )
            
            admin = await service.toggle_status(admin_id, is_active)
            await db.commit()
            
            return success(
                data=AdminResponse.model_validate(admin, from_attributes=True),
                message=_("admin.status_updated"),
            )


# 导出路由器
router = AdminAdminController.get_router()

__all__ = ["router", "AdminAdminController"]
