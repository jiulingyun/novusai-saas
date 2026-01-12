"""
租户管理员服务

提供租户管理员的业务逻辑（租户隔离）
"""

from typing import Any

from app.core.base_service import TenantService
from app.core.i18n import _
from app.core.security import get_password_hash, verify_password
from app.exceptions import BusinessException, NotFoundException
from app.models.tenant.tenant_admin import TenantAdmin
from app.repositories.tenant.tenant_admin_repository import TenantAdminRepository


class TenantAdminService(TenantService[TenantAdmin, TenantAdminRepository]):
    """
    租户管理员服务
    
    提供租户管理员特有的业务方法，自动注入租户隔离
    """
    
    model = TenantAdmin
    repository_class = TenantAdminRepository
    
    async def get_by_username(self, username: str) -> TenantAdmin | None:
        """
        根据用户名获取管理员
        
        Args:
            username: 用户名
        
        Returns:
            管理员实例或 None
        """
        return await self.repo.get_by_username(username)
    
    async def get_by_email(self, email: str) -> TenantAdmin | None:
        """
        根据邮箱获取管理员
        
        Args:
            email: 邮箱
        
        Returns:
            管理员实例或 None
        """
        return await self.repo.get_by_email(email)
    
    async def get_by_username_or_email(
        self,
        username_or_email: str,
    ) -> TenantAdmin | None:
        """
        根据用户名或邮箱获取管理员（用于登录）
        
        Args:
            username_or_email: 用户名或邮箱
        
        Returns:
            管理员实例或 None
        """
        return await self.repo.get_by_username_or_email(username_or_email)
    
    async def create_admin(
        self,
        username: str,
        email: str,
        password: str,
        phone: str | None = None,
        nickname: str | None = None,
        is_active: bool = True,
        is_owner: bool = False,
        role_id: int | None = None,
    ) -> TenantAdmin:
        """
        创建租户管理员
        
        Args:
            username: 用户名
            email: 邮箱
            password: 明文密码
            phone: 手机号
            nickname: 昵称
            is_active: 是否激活
            is_owner: 是否租户所有者
            role_id: 角色 ID
        
        Returns:
            创建的管理员
        
        Raises:
            BusinessException: 用户名/邮箱/手机号已存在
        """
        # 检查用户名是否已存在（租户内唯一）
        if await self.repo.username_exists(username):
            raise BusinessException(
                message=_("tenant_admin.username_exists"),
                code=4001,
            )
        
        # 检查邮箱是否已存在（租户内唯一）
        if await self.repo.email_exists(email):
            raise BusinessException(
                message=_("tenant_admin.email_exists"),
                code=4002,
            )
        
        # 检查手机号是否已存在（租户内唯一）
        if phone and await self.repo.phone_exists(phone):
            raise BusinessException(
                message=_("tenant_admin.phone_exists"),
                code=4003,
            )
        
        # 创建管理员（tenant_id 由 TenantService 自动注入）
        data = {
            "username": username,
            "email": email,
            "password_hash": get_password_hash(password),
            "phone": phone,
            "nickname": nickname,
            "is_active": is_active,
            "is_owner": is_owner,
            "role_id": role_id,
        }
        
        return await self.create(data)
    
    async def update_admin(
        self,
        admin_id: int,
        data: dict[str, Any],
    ) -> TenantAdmin:
        """
        更新租户管理员
        
        Args:
            admin_id: 管理员 ID
            data: 更新数据（不含密码）
        
        Returns:
            更新后的管理员
        
        Raises:
            NotFoundException: 管理员不存在
            BusinessException: 邮箱/手机号已存在
        """
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise NotFoundException(
                message=_("tenant_admin.not_found"),
            )
        
        # 检查邮箱是否已被其他管理员使用
        if "email" in data and data["email"]:
            if await self.repo.email_exists(data["email"], exclude_id=admin_id):
                raise BusinessException(
                    message=_("tenant_admin.email_exists"),
                    code=4002,
                )
        
        # 检查手机号是否已被其他管理员使用
        if "phone" in data and data["phone"]:
            if await self.repo.phone_exists(data["phone"], exclude_id=admin_id):
                raise BusinessException(
                    message=_("tenant_admin.phone_exists"),
                    code=4003,
                )
        
        # 移除不允许直接更新的字段
        data.pop("password", None)
        data.pop("password_hash", None)
        data.pop("username", None)  # 用户名不允许修改
        data.pop("tenant_id", None)  # 租户 ID 不允许修改
        
        result = await self.update(admin_id, data)
        if not result:
            raise NotFoundException(message=_("tenant_admin.not_found"))
        return result
    
    async def change_password(
        self,
        admin_id: int,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        修改密码（管理员自己操作）
        
        Args:
            admin_id: 管理员 ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            是否成功
        
        Raises:
            NotFoundException: 管理员不存在
            BusinessException: 旧密码错误
        """
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise NotFoundException(
                message=_("tenant_admin.not_found"),
            )
        
        # 验证旧密码
        if not verify_password(old_password, admin.password_hash):
            raise BusinessException(
                message=_("tenant_admin.password_incorrect"),
                code=4004,
            )
        
        # 更新密码
        await self.update(admin_id, {
            "password_hash": get_password_hash(new_password),
        })
        
        return True
    
    async def reset_password(
        self,
        admin_id: int,
        new_password: str,
    ) -> bool:
        """
        重置密码（租户所有者操作）
        
        Args:
            admin_id: 管理员 ID
            new_password: 新密码
        
        Returns:
            是否成功
        
        Raises:
            NotFoundException: 管理员不存在
        """
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise NotFoundException(
                message=_("tenant_admin.not_found"),
            )
        
        # 更新密码
        await self.update(admin_id, {
            "password_hash": get_password_hash(new_password),
        })
        
        return True
    
    async def toggle_status(self, admin_id: int, is_active: bool) -> TenantAdmin:
        """
        切换管理员状态
        
        Args:
            admin_id: 管理员 ID
            is_active: 是否激活
        
        Returns:
            更新后的管理员
        
        Raises:
            NotFoundException: 管理员不存在
        """
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise NotFoundException(
                message=_("tenant_admin.not_found"),
            )
        
        result = await self.update(admin_id, {"is_active": is_active})
        if not result:
            raise NotFoundException(message=_("tenant_admin.not_found"))
        return result


__all__ = ["TenantAdminService"]
