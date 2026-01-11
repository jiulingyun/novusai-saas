"""
核心模块

包含应用配置、基类、依赖注入等核心组件
"""

# 配置
from app.core.config import settings

# 国际化
from app.core.i18n import _, translate, get_locale, set_locale

# 基类 - Model
from app.core.base_model import Base, BaseModel, TenantModel

# 基类 - Schema
from app.core.base_schema import (
    BaseSchema,
    BaseCreateSchema,
    BaseUpdateSchema,
    BaseResponseSchema,
    TenantResponseSchema,
    PageParams,
    PageResponse,
)

# 基类 - Repository
from app.core.base_repository import BaseRepository, TenantRepository

# 基类 - Service
from app.core.base_service import BaseService, TenantService, GlobalService

# 基类 - Controller
from app.core.base_controller import BaseController, TenantController, GlobalController

__all__ = [
    # 配置
    "settings",
    # 国际化
    "_",
    "translate",
    "get_locale",
    "set_locale",
    # Model
    "Base",
    "BaseModel",
    "TenantModel",
    # Schema
    "BaseSchema",
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseResponseSchema",
    "TenantResponseSchema",
    "PageParams",
    "PageResponse",
    # Repository
    "BaseRepository",
    "TenantRepository",
    # Service
    "BaseService",
    "TenantService",
    "GlobalService",
    # Controller
    "BaseController",
    "TenantController",
    "GlobalController",
]
