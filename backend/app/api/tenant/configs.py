"""
租户配置管理 API

提供租户级配置管理接口（租户管理员专用）
"""

from fastapi import HTTPException, Request, status

from app.configs.service import ConfigService
from app.configs.registry import config_registry
from app.core.base_controller import TenantController
from app.core.deps import DbSession, ActiveTenantAdmin
from app.core.i18n import _
from app.core.response import success
from app.enums.config import ConfigScope
from app.enums.rbac import PermissionScope
from app.rbac.decorators import (
    permission_resource,
    MenuConfig,
    action_read,
    action_update,
)
from app.schemas.system.config import (
    ConfigGroupResponse,
    ConfigGroupListResponse,
    ConfigItemResponse,
    ConfigUpdateRequest,
)


@permission_resource(
    resource="tenant_config",
    name="menu.tenant.tenant_config",  # i18n key
    scope=PermissionScope.TENANT,
    menu=MenuConfig(
        icon="lucide:sliders-horizontal",
        path="/system/configs",
        component="system/configs/List",
        parent="system",  # 父菜单: 系统管理
        sort_order=40,
    ),
)
class TenantConfigController(TenantController):
    """
    租户配置管理控制器
    
    提供租户级配置的查看和修改接口
    """
    
    prefix = "/configs"
    tags = ["租户配置"]
    
    def _register_routes(self) -> None:
        """注册路由"""
        router = self.router
        
        @router.get("/groups", summary="获取配置分组列表")
        @action_read("action.tenant_config.groups")
        async def list_config_groups(
            request: Request,
            db: DbSession,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取租户配置分组列表
            
            返回所有租户级配置分组（不含具体配置项）
            
            权限: tenant_config:groups
            """
            groups = config_registry.get_groups_by_scope(ConfigScope.TENANT)
            
            result = []
            for group in groups:
                if not group.is_active:
                    continue
                
                # 计算可见配置项数量
                visible_count = sum(
                    1 for c in group.configs if c.is_visible
                )
                
                result.append(ConfigGroupListResponse(
                    code=group.code,
                    name_key=group.name_key,
                    description_key=group.description_key,
                    icon=group.icon,
                    sort_order=group.sort_order,
                    config_count=visible_count,
                ))
            
            return success(
                data=sorted(result, key=lambda x: x.sort_order),
                message=_("common.success"),
            )
        
        @router.get("/groups/{group_code}", summary="获取分组配置项")
        @action_read("action.tenant_config.detail")
        async def get_group_configs(
            request: Request,
            db: DbSession,
            group_code: str,
            current_admin: ActiveTenantAdmin,
        ):
            """
            获取指定分组的配置项列表（含当前值）
            
            权限: tenant_config:detail
            """
            # 验证分组存在
            group = config_registry.get_group(group_code)
            if not group or group.scope != ConfigScope.TENANT:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("config.group_not_found"),
                )
            
            # 获取配置值
            config_service = ConfigService(db)
            groups_with_configs = await config_service.get_groups_with_configs(
                scope=ConfigScope.TENANT,
                tenant_id=current_admin.tenant_id,
            )
            
            # 找到目标分组
            target_group = None
            for g in groups_with_configs:
                if g["code"] == group_code:
                    target_group = g
                    break
            
            if not target_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("config.group_not_found"),
                )
            
            # 转换响应
            configs = [
                ConfigItemResponse(
                    key=c["key"],
                    name_key=c["name_key"],
                    description_key=c.get("description_key"),
                    value_type=c["value_type"],
                    value=c["value"],
                    default_value=c["default_value"],
                    options=c.get("options", []),
                    validation_rules=c.get("validation_rules", []),
                    is_required=c["is_required"],
                    is_encrypted=c["is_encrypted"],
                    sort_order=c["sort_order"],
                )
                for c in target_group["configs"]
            ]
            
            return success(
                data=ConfigGroupResponse(
                    code=target_group["code"],
                    name_key=target_group["name_key"],
                    description_key=target_group.get("description_key"),
                    icon=target_group.get("icon"),
                    sort_order=target_group["sort_order"],
                    configs=configs,
                ),
                message=_("common.success"),
            )
        
        @router.put("/groups/{group_code}", summary="更新分组配置")
        @action_update("action.tenant_config.update")
        async def update_group_configs(
            request: Request,
            db: DbSession,
            group_code: str,
            data: ConfigUpdateRequest,
            current_admin: ActiveTenantAdmin,
        ):
            """
            批量更新分组下的配置项
            
            权限: tenant_config:update
            """
            # 验证分组存在
            group = config_registry.get_group(group_code)
            if not group or group.scope != ConfigScope.TENANT:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_("config.group_not_found"),
                )
            
            # 获取分组下的配置键列表
            valid_keys = {c.key for c in group.configs}
            
            # 验证传入的配置键
            invalid_keys = set(data.configs.keys()) - valid_keys
            if invalid_keys:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_("config.invalid_keys", keys=", ".join(invalid_keys)),
                )
            
            # 更新配置
            config_service = ConfigService(db)
            for key, value in data.configs.items():
                await config_service.set_tenant_config(
                    tenant_id=current_admin.tenant_id,
                    key=key,
                    value=value,
                )
            
            await db.commit()
            
            # 返回更新后的配置
            groups_with_configs = await config_service.get_groups_with_configs(
                scope=ConfigScope.TENANT,
                tenant_id=current_admin.tenant_id,
            )
            
            target_group = None
            for g in groups_with_configs:
                if g["code"] == group_code:
                    target_group = g
                    break
            
            configs = [
                ConfigItemResponse(
                    key=c["key"],
                    name_key=c["name_key"],
                    description_key=c.get("description_key"),
                    value_type=c["value_type"],
                    value=c["value"],
                    default_value=c["default_value"],
                    options=c.get("options", []),
                    validation_rules=c.get("validation_rules", []),
                    is_required=c["is_required"],
                    is_encrypted=c["is_encrypted"],
                    sort_order=c["sort_order"],
                )
                for c in target_group["configs"]
            ] if target_group else []
            
            return success(
                data=ConfigGroupResponse(
                    code=group_code,
                    name_key=group.name_key,
                    description_key=group.description_key,
                    icon=group.icon,
                    sort_order=group.sort_order,
                    configs=configs,
                ),
                message=_("config.updated"),
            )


# 导出路由
router = TenantConfigController.get_router()


__all__ = [
    "router",
    "TenantConfigController",
]
