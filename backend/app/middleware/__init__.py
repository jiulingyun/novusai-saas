"""
中间件模块
"""

from app.middleware.i18n import I18nMiddleware
from app.middleware.permission import PermissionMiddleware
from app.middleware.access_control import AccessControlMiddleware

__all__ = ["I18nMiddleware", "PermissionMiddleware", "AccessControlMiddleware"]
