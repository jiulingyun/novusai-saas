"""
平台管理后台服务模块

提供平台管理相关的服务
"""

from app.services.system.admin_service import AdminService
from app.services.system.admin_role_service import AdminRoleService
from app.services.system.tenant_service import TenantService


__all__ = [
    "AdminService",
    "AdminRoleService",
    "TenantService",
]
