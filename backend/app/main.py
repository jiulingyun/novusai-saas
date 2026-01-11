"""
FastAPI 应用入口

配置应用实例、中间件、路由、异常处理器等
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.i18n import _
from app.core.database import init_database, close_database
from app.core.response import error, validation_error
from app.exceptions import AppException
from app.middleware.i18n import I18nMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    - startup: 应用启动时执行
    - shutdown: 应用关闭时执行
    """
    # ========== Startup ==========
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.APP_ENV}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    
    # 初始化数据库（检查/创建数据库 + 运行迁移）
    await init_database()
    
    # TODO: 初始化 Redis 连接
    # TODO: 初始化 Celery
    
    yield
    
    # ========== Shutdown ==========
    print(f"👋 Shutting down {settings.APP_NAME}")
    
    # 关闭数据库连接
    await close_database()
    
    # TODO: 关闭 Redis 连接


def create_application() -> FastAPI:
    """
    创建 FastAPI 应用实例
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="现代化 AI 集成 SaaS 开发框架",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    
    # ========================================
    # 注册中间件
    # ========================================
    
    # i18n 国际化中间件（需要在 CORS 之前注册）
    app.add_middleware(I18nMiddleware)
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========================================
    # 注册异常处理器
    # ========================================
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """应用异常处理器"""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """请求验证异常处理器"""
        errors = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        response = validation_error(errors=errors)
        return JSONResponse(
            status_code=422,
            content=response.model_dump(),
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """HTTP 异常处理器"""
        # 映射常见 HTTP 状态码到业务错误码
        status_code_map = {
            400: 4000,
            401: 4010,
            403: 4030,
            404: 4040,
            405: 4050,
            409: 4090,
            422: 4220,
            429: 4290,
            500: 5000,
            502: 5020,
            503: 5030,
        }
        code = status_code_map.get(exc.status_code, exc.status_code * 10)
        response = error(
            message=str(exc.detail) if exc.detail else None,
            code=code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """全局异常处理器 - 捕获未处理的异常"""
        # 在 DEBUG 模式下打印异常信息
        if settings.DEBUG:
            import traceback
            traceback.print_exc()
        
        response = error(message=_("common.server_error"), code=5000)
        return JSONResponse(
            status_code=500,
            content=response.model_dump(),
        )
    
    # ========================================
    # 注册路由
    # ========================================
    
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """根路由 - 健康检查"""
        return {
            "code": 0,
            "message": _("common.success"),
            "data": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "status": "healthy",
            },
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """健康检查端点"""
        return {
            "code": 0,
            "message": _("common.success"),
            "data": {
                "status": "healthy",
                "env": settings.APP_ENV,
            },
        }
    
    # TODO: 注册 API v1 路由
    # from app.api.v1 import api_router
    # app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    return app


# 创建应用实例
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
