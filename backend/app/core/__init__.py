"""
核心模块

包含应用配置、基类、依赖注入等核心组件
"""

from app.core.config import settings
from app.core.i18n import _, translate, get_locale, set_locale

__all__ = ["settings", "_", "translate", "get_locale", "set_locale"]
