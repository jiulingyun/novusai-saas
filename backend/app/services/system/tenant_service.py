"""
租户服务

提供租户的业务逻辑
"""

from datetime import datetime
from typing import Any

from app.core.base_service import GlobalService
from app.core.i18n import _
from app.exceptions import BusinessException, NotFoundException
from app.models.tenant.tenant import Tenant
from app.repositories.system.tenant_repository import TenantRepository


class TenantService(GlobalService[Tenant, TenantRepository]):
    """
    租户服务
    
    提供租户特有的业务方法（全局级别，由平台管理员操作）
    """
    
    model = Tenant
    repository_class = TenantRepository
    
    async def get_by_code(self, code: str) -> Tenant | None:
        """
        根据编码获取租户
        
        Args:
            code: 租户编码
        
        Returns:
            租户实例或 None
        """
        return await self.repo.get_by_code(code)
    
    async def create_tenant(
        self,
        code: str,
        name: str,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        plan: str = "free",
        quota: dict | None = None,
        expires_at: datetime | None = None,
        remark: str | None = None,
    ) -> Tenant:
        """
        创建租户
        
        Args:
            code: 租户编码
            name: 租户名称
            contact_name: 联系人姓名
            contact_phone: 联系人电话
            contact_email: 联系人邮箱
            plan: 套餐类型
            quota: 配额配置
            expires_at: 到期时间
            remark: 备注
        
        Returns:
            创建的租户
        
        Raises:
            BusinessException: 编码已存在
        """
        # 检查编码是否已存在
        if await self.repo.code_exists(code):
            raise BusinessException(
                message=_("tenant.code_exists"),
                code=4001,
            )
        
        # 创建租户
        data = {
            "code": code,
            "name": name,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "plan": plan,
            "quota": quota,
            "expires_at": expires_at,
            "remark": remark,
            "is_active": True,
        }
        
        return await self.create(data)
    
    async def update_tenant(
        self,
        tenant_id: int,
        data: dict[str, Any],
    ) -> Tenant:
        """
        更新租户
        
        Args:
            tenant_id: 租户 ID
            data: 更新数据
        
        Returns:
            更新后的租户
        
        Raises:
            NotFoundException: 租户不存在
            BusinessException: 编码已存在
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundException(
                message=_("tenant.not_found"),
            )
        
        # 如果要更新编码，检查是否已被占用
        if "code" in data and data["code"]:
            if data["code"] != tenant.code:
                if await self.repo.code_exists(data["code"], exclude_id=tenant_id):
                    raise BusinessException(
                        message=_("tenant.code_exists"),
                        code=4001,
                    )
        
        result = await self.update(tenant_id, data)
        if not result:
            raise NotFoundException(message=_("tenant.not_found"))
        return result
    
    async def enable_tenant(self, tenant_id: int) -> Tenant:
        """
        启用租户
        
        Args:
            tenant_id: 租户 ID
        
        Returns:
            更新后的租户
        
        Raises:
            NotFoundException: 租户不存在
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundException(
                message=_("tenant.not_found"),
            )
        
        result = await self.update(tenant_id, {"is_active": True})
        if not result:
            raise NotFoundException(message=_("tenant.not_found"))
        return result
    
    async def disable_tenant(self, tenant_id: int) -> Tenant:
        """
        禁用租户
        
        Args:
            tenant_id: 租户 ID
        
        Returns:
            更新后的租户
        
        Raises:
            NotFoundException: 租户不存在
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundException(
                message=_("tenant.not_found"),
            )
        
        result = await self.update(tenant_id, {"is_active": False})
        if not result:
            raise NotFoundException(message=_("tenant.not_found"))
        return result
    
    async def toggle_status(self, tenant_id: int, is_active: bool) -> Tenant:
        """
        切换租户状态
        
        Args:
            tenant_id: 租户 ID
            is_active: 是否启用
        
        Returns:
            更新后的租户
        
        Raises:
            NotFoundException: 租户不存在
        """
        if is_active:
            return await self.enable_tenant(tenant_id)
        else:
            return await self.disable_tenant(tenant_id)


__all__ = ["TenantService"]
