"""
中间件模块
"""

from app.middleware.i18n import I18nMiddleware
from app.middleware.permission import PermissionMiddleware

__all__ = ["I18nMiddleware", "PermissionMiddleware"]
