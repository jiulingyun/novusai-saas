"""
租户管理后台 API 路由模块

聚合所有租户管理后台的 API 路由
"""

from fastapi import APIRouter

from app.api.tenant.auth import router as auth_router

# 创建租户管理后台路由器
tenant_router = APIRouter()

# 注册子路由
tenant_router.include_router(auth_router)


__all__ = ["tenant_router"]
