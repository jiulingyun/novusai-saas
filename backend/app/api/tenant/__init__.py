"""
租户管理后台 API 路由模块

聚合所有租户管理后台的 API 路由
"""

from fastapi import APIRouter

from app.api.tenant.auth import router as auth_router
from app.api.tenant.permissions import router as permissions_router
from app.api.tenant.roles import router as roles_router

# 创建租户管理后台路由器
tenant_router = APIRouter()

# 注册子路由
tenant_router.include_router(auth_router)
tenant_router.include_router(permissions_router)
tenant_router.include_router(roles_router)


__all__ = ["tenant_router"]
