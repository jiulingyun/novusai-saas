"""
认证服务

提供平台管理员、租户管理员、租户用户的认证逻辑
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n import _
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    verify_token_with_scope,
    verify_impersonate_token,
    TOKEN_TYPE_REFRESH,
    TOKEN_SCOPE_ADMIN,
    TOKEN_SCOPE_TENANT_ADMIN,
    TOKEN_SCOPE_TENANT_USER,
)
from app.exceptions import AuthenticationException, BusinessException, NotFoundException
from app.models import Admin, TenantAdmin, TenantUser, Tenant


class AuthService:
    """
    认证服务
    
    提供：
    - 平台管理员认证 (Admin)
    - 租户管理员认证 (TenantAdmin)
    - 租户用户认证 (TenantUser)
    - Token 刷新
    - 密码修改
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
    
    # ==================== 平台管理员认证 ====================
    
    async def authenticate_admin(
        self,
        username: str,
        password: str,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        平台管理员认证
        
        Args:
            username: 用户名或邮箱
            password: 密码
            client_ip: 客户端 IP
        
        Returns:
            包含 tokens 的字典
        
        Raises:
            AuthenticationException: 认证失败
        """
        # 查询管理员
        result = await self.db.execute(
            select(Admin).where(
                or_(Admin.username == username, Admin.email == username)
            )
        )
        admin = result.scalar_one_or_none()
        
        # 验证管理员和密码
        if admin is None or not verify_password(password, admin.password_hash):
            raise AuthenticationException(message=_("auth.credentials_invalid"))
        
        # 检查状态
        if not admin.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        # 更新登录信息
        admin.last_login_at = datetime.now(timezone.utc)
        admin.last_login_ip = client_ip
        
        # 生成 Token
        tokens = create_token_pair(admin.id, scope=TOKEN_SCOPE_ADMIN)
        
        return tokens
    
    async def refresh_admin_token(self, refresh_token: str) -> dict[str, Any]:
        """
        刷新平台管理员 Token
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的 tokens
        
        Raises:
            AuthenticationException: Token 无效
        """
        admin_id, scope = verify_token_with_scope(
            refresh_token, TOKEN_SCOPE_ADMIN, TOKEN_TYPE_REFRESH
        )
        if admin_id is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        # 查询管理员
        result = await self.db.execute(
            select(Admin).where(Admin.id == int(admin_id))
        )
        admin = result.scalar_one_or_none()
        
        if admin is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        if not admin.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        return create_token_pair(admin.id, scope=TOKEN_SCOPE_ADMIN)
    
    async def change_admin_password(
        self,
        admin: Admin,
        old_password: str,
        new_password: str,
    ) -> None:
        """
        修改平台管理员密码
        
        Args:
            admin: 管理员实例
            old_password: 旧密码
            new_password: 新密码
        
        Raises:
            BusinessException: 旧密码不正确
        """
        if not verify_password(old_password, admin.password_hash):
            raise BusinessException(message=_("auth.password_mismatch"))
        
        admin.password_hash = get_password_hash(new_password)
    
    # ==================== 租户管理员认证 ====================
    
    async def authenticate_tenant_admin(
        self,
        username: str,
        password: str,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        租户管理员认证
        
        Args:
            username: 用户名或邮箱
            password: 密码
            client_ip: 客户端 IP
        
        Returns:
            包含 tokens 的字典
        
        Raises:
            AuthenticationException: 认证失败
        """
        # 查询租户管理员
        result = await self.db.execute(
            select(TenantAdmin).where(
                or_(
                    TenantAdmin.username == username,
                    TenantAdmin.email == username,
                )
            )
        )
        tenant_admin = result.scalar_one_or_none()
        
        # 验证管理员和密码
        if tenant_admin is None or not verify_password(password, tenant_admin.password_hash):
            raise AuthenticationException(message=_("auth.credentials_invalid"))
        
        # 检查管理员状态
        if not tenant_admin.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        # 检查租户状态
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_admin.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if tenant is None or not tenant.is_active:
            raise AuthenticationException(message=_("tenant.disabled"))
        
        # 更新登录信息
        tenant_admin.last_login_at = datetime.now(timezone.utc)
        tenant_admin.last_login_ip = client_ip
        
        # 生成 Token
        tokens = create_token_pair(
            tenant_admin.id,
            scope=TOKEN_SCOPE_TENANT_ADMIN,
            extra_claims={"tenant_id": tenant_admin.tenant_id},
        )
        
        return tokens
    
    async def refresh_tenant_admin_token(self, refresh_token: str) -> dict[str, Any]:
        """
        刷新租户管理员 Token
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的 tokens
        
        Raises:
            AuthenticationException: Token 无效
        """
        admin_id, scope = verify_token_with_scope(
            refresh_token, TOKEN_SCOPE_TENANT_ADMIN, TOKEN_TYPE_REFRESH
        )
        if admin_id is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        # 查询租户管理员
        result = await self.db.execute(
            select(TenantAdmin).where(TenantAdmin.id == int(admin_id))
        )
        tenant_admin = result.scalar_one_or_none()
        
        if tenant_admin is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        if not tenant_admin.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        return create_token_pair(
            tenant_admin.id,
            scope=TOKEN_SCOPE_TENANT_ADMIN,
            extra_claims={"tenant_id": tenant_admin.tenant_id},
        )
    
    async def change_tenant_admin_password(
        self,
        tenant_admin: TenantAdmin,
        old_password: str,
        new_password: str,
    ) -> None:
        """
        修改租户管理员密码
        
        Args:
            tenant_admin: 租户管理员实例
            old_password: 旧密码
            new_password: 新密码
        
        Raises:
            BusinessException: 旧密码不正确
        """
        if not verify_password(old_password, tenant_admin.password_hash):
            raise BusinessException(message=_("auth.password_mismatch"))
        
        tenant_admin.password_hash = get_password_hash(new_password)
    
    async def impersonate_tenant_admin(
        self,
        impersonate_token: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        验证平台管理员的 impersonate token 并换取正式 Token
        
        Args:
            impersonate_token: 一键登录令牌
        
        Returns:
            (tokens, audit_info) 元组
        
        Raises:
            AuthenticationException: Token 无效
            NotFoundException: 租户或所有者不存在
        """
        # 验证 impersonate token
        payload = verify_impersonate_token(impersonate_token, TOKEN_SCOPE_TENANT_ADMIN)
        
        if payload is None:
            raise AuthenticationException(message=_("auth.impersonate_token_invalid"))
        
        admin_id = payload.get("admin_id")
        target_tenant_id = payload.get("target_tenant_id")
        target_role_id = payload.get("target_role_id")
        
        # 验证租户状态
        tenant_result = await self.db.execute(
            select(Tenant).where(
                Tenant.id == target_tenant_id,
                Tenant.is_deleted == False,
            )
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if tenant is None or not tenant.is_active:
            raise AuthenticationException(message=_("tenant.disabled"))
        
        # 获取租户的所有者信息
        owner_result = await self.db.execute(
            select(TenantAdmin).where(
                TenantAdmin.tenant_id == target_tenant_id,
                TenantAdmin.is_owner == True,
                TenantAdmin.is_deleted == False,
            )
        )
        tenant_owner = owner_result.scalar_one_or_none()
        
        if tenant_owner is None:
            raise NotFoundException(message=_("tenant.owner_not_found"))
        
        # 获取执行 impersonate 的平台管理员信息
        platform_admin_result = await self.db.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        platform_admin = platform_admin_result.scalar_one_or_none()
        platform_admin_username = platform_admin.username if platform_admin else "unknown"
        
        # 生成正式 Token
        extra_claims = {
            "tenant_id": target_tenant_id,
            "impersonated_by": admin_id,
        }
        
        if target_role_id:
            extra_claims["impersonate_role_id"] = target_role_id
        
        tokens = create_token_pair(
            tenant_owner.id,
            scope=TOKEN_SCOPE_TENANT_ADMIN,
            extra_claims=extra_claims,
        )
        
        # 返回审计信息
        audit_info = {
            "admin_id": admin_id,
            "admin_username": platform_admin_username,
            "target_tenant_id": target_tenant_id,
            "target_tenant_code": tenant.code,
            "tenant_owner_id": tenant_owner.id,
            "target_role_id": target_role_id,
        }
        
        return tokens, audit_info
    
    # ==================== 租户用户认证 ====================
    
    async def authenticate_tenant_user(
        self,
        username: str,
        password: str,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        租户用户认证
        
        Args:
            username: 用户名、邮箱或手机号
            password: 密码
            client_ip: 客户端 IP
        
        Returns:
            包含 tokens 的字典
        
        Raises:
            AuthenticationException: 认证失败
        """
        # 查询用户
        result = await self.db.execute(
            select(TenantUser).where(
                or_(
                    TenantUser.username == username,
                    TenantUser.email == username,
                    TenantUser.phone == username,
                )
            )
        )
        user = result.scalar_one_or_none()
        
        # 验证用户和密码
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationException(message=_("auth.credentials_invalid"))
        
        # 检查用户状态
        if not user.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        # 更新登录信息
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = client_ip
        
        # 生成 Token
        tokens = create_token_pair(
            user.id,
            scope=TOKEN_SCOPE_TENANT_USER,
            extra_claims={"tenant_id": user.tenant_id},
        )
        
        return tokens
    
    async def refresh_tenant_user_token(self, refresh_token: str) -> dict[str, Any]:
        """
        刷新租户用户 Token
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的 tokens
        
        Raises:
            AuthenticationException: Token 无效
        """
        user_id, scope = verify_token_with_scope(
            refresh_token, TOKEN_SCOPE_TENANT_USER, TOKEN_TYPE_REFRESH
        )
        if user_id is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        # 查询用户
        result = await self.db.execute(
            select(TenantUser).where(TenantUser.id == int(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise AuthenticationException(message=_("auth.refresh_token_invalid"))
        
        if not user.is_active:
            raise AuthenticationException(message=_("auth.account_disabled"))
        
        return create_token_pair(
            user.id,
            scope=TOKEN_SCOPE_TENANT_USER,
            extra_claims={"tenant_id": user.tenant_id},
        )
    
    async def change_tenant_user_password(
        self,
        user: TenantUser,
        old_password: str,
        new_password: str,
    ) -> None:
        """
        修改租户用户密码
        
        Args:
            user: 用户实例
            old_password: 旧密码
            new_password: 新密码
        
        Raises:
            BusinessException: 旧密码不正确
        """
        if not verify_password(old_password, user.password_hash):
            raise BusinessException(message=_("auth.password_mismatch"))
        
        user.password_hash = get_password_hash(new_password)


__all__ = ["AuthService"]
