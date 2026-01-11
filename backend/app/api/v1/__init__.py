"""
API v1 路由模块

聚合所有 v1 版本的 API 路由
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

# 创建 v1 路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth_router)


__all__ = ["api_router"]
