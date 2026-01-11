"""
数据模型模块

导出所有数据库模型

目录结构:
- system/: 平台级模型 (Admin)
- tenant/: 租户级模型 (Tenant, TenantAdmin, TenantUser)
- auth/: 认证授权模型 (Role, Permission)
"""

# 平台级模型
from app.models.system import Admin

# 租户级模型
from app.models.tenant import Tenant, TenantAdmin, TenantUser

# 认证授权模型 (TODO: M2-T2)
# from app.models.auth import Role, Permission

__all__ = [
    # 平台级
    "Admin",
    # 租户级
    "Tenant",
    "TenantAdmin",
    "TenantUser",
]
