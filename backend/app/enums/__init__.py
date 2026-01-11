"""
枚举模块

提供应用的枚举类定义
"""

from app.enums.base import BaseEnum, IntEnum, StrEnum
from app.enums.common import (
    StatusEnum,
    BoolEnum,
    GenderEnum,
    AuditStatusEnum,
    SortOrderEnum,
    OperationTypeEnum,
    PriorityEnum,
)
from app.enums.rbac import (
    PermissionType,
    PermissionScope,
)

__all__ = [
    # 基类
    "BaseEnum",
    "IntEnum",
    "StrEnum",
    # 通用枚举
    "StatusEnum",
    "BoolEnum",
    "GenderEnum",
    "AuditStatusEnum",
    "SortOrderEnum",
    "OperationTypeEnum",
    "PriorityEnum",
    # RBAC
    "PermissionType",
    "PermissionScope",
]
