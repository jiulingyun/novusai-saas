"""
仓储模块

导出所有仓储类
"""

from app.repositories.system import AdminRepository, TenantRepository


__all__ = [
    "AdminRepository",
    "TenantRepository",
]
