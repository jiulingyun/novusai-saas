"""
平台管理仓储模块

导出系统级仓储类
"""

from app.repositories.system.admin_repository import AdminRepository
from app.repositories.system.tenant_repository import TenantRepository


__all__ = [
    "AdminRepository",
    "TenantRepository",
]
