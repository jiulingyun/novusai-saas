"""
配置分组定义

定义平台级和租户级的配置分组
"""

from app.configs.meta import ConfigGroupMeta
from app.enums.config import ConfigScope


# ==========================================
# 平台配置分组
# ==========================================

# 通用设置分组
PLATFORM_GENERAL_GROUP = ConfigGroupMeta(
    code="platform_general",
    name_key="config.group.platform_general",
    description_key="config.group.platform_general.desc",
    scope=ConfigScope.PLATFORM,
    icon="settings",
    sort_order=10,
)

# 安全设置分组
PLATFORM_SECURITY_GROUP = ConfigGroupMeta(
    code="platform_security",
    name_key="config.group.platform_security",
    description_key="config.group.platform_security.desc",
    scope=ConfigScope.PLATFORM,
    icon="shield",
    sort_order=20,
)

# 邮件设置分组
PLATFORM_EMAIL_GROUP = ConfigGroupMeta(
    code="platform_email",
    name_key="config.group.platform_email",
    description_key="config.group.platform_email.desc",
    scope=ConfigScope.PLATFORM,
    icon="mail",
    sort_order=30,
)

# 存储设置分组
PLATFORM_STORAGE_GROUP = ConfigGroupMeta(
    code="platform_storage",
    name_key="config.group.platform_storage",
    description_key="config.group.platform_storage.desc",
    scope=ConfigScope.PLATFORM,
    icon="database",
    sort_order=40,
)


# ==========================================
# 租户配置分组（后续 T6 任务使用）
# ==========================================

# 租户基础设置分组
TENANT_GENERAL_GROUP = ConfigGroupMeta(
    code="tenant_general",
    name_key="config.group.tenant_general",
    description_key="config.group.tenant_general.desc",
    scope=ConfigScope.TENANT,
    icon="building",
    sort_order=10,
)

# 租户外观设置分组
TENANT_APPEARANCE_GROUP = ConfigGroupMeta(
    code="tenant_appearance",
    name_key="config.group.tenant_appearance",
    description_key="config.group.tenant_appearance.desc",
    scope=ConfigScope.TENANT,
    icon="palette",
    sort_order=20,
)

# 租户功能设置分组
TENANT_FEATURES_GROUP = ConfigGroupMeta(
    code="tenant_features",
    name_key="config.group.tenant_features",
    description_key="config.group.tenant_features.desc",
    scope=ConfigScope.TENANT,
    icon="puzzle",
    sort_order=30,
)


# ==========================================
# 分组列表
# ==========================================

# 所有平台配置分组
PLATFORM_CONFIG_GROUPS = [
    PLATFORM_GENERAL_GROUP,
    PLATFORM_SECURITY_GROUP,
    PLATFORM_EMAIL_GROUP,
    PLATFORM_STORAGE_GROUP,
]

# 所有租户配置分组
TENANT_CONFIG_GROUPS = [
    TENANT_GENERAL_GROUP,
    TENANT_APPEARANCE_GROUP,
    TENANT_FEATURES_GROUP,
]

# 所有配置分组
ALL_CONFIG_GROUPS = PLATFORM_CONFIG_GROUPS + TENANT_CONFIG_GROUPS


__all__ = [
    # 平台分组
    "PLATFORM_GENERAL_GROUP",
    "PLATFORM_SECURITY_GROUP",
    "PLATFORM_EMAIL_GROUP",
    "PLATFORM_STORAGE_GROUP",
    "PLATFORM_CONFIG_GROUPS",
    # 租户分组
    "TENANT_GENERAL_GROUP",
    "TENANT_APPEARANCE_GROUP",
    "TENANT_FEATURES_GROUP",
    "TENANT_CONFIG_GROUPS",
    # 全部
    "ALL_CONFIG_GROUPS",
]
