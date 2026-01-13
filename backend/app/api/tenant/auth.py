"""
租户管理员认证 API

提供租户管理员的登录、登出、Token 刷新等接口
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import select, or_

from app.core.deps import DbSession, ActiveTenantAdmin
from app.core.i18n import _
from app.core.logging import get_logger
from app.core.response import success
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    verify_token_with_scope,
    verify_impersonate_token,
    TOKEN_TYPE_REFRESH,
    TOKEN_SCOPE_TENANT_ADMIN,
)
from app.models import TenantAdmin, Tenant, Admin
from app.schemas.common import TokenResponse, RefreshTokenRequest, ImpersonateTokenRequest
from app.schemas.tenant import (
    TenantAdminLoginRequest,
    TenantAdminResponse,
    TenantAdminChangePasswordRequest,
)

# 审计日志
audit_logger = get_logger("impersonate", separate_file=True)


router = APIRouter(prefix="/auth", tags=["租户管理员认证"])


@router.post("/login", summary="租户管理员登录")
async def tenant_admin_login(
    db: DbSession,
    request: Request,
    login_data: TenantAdminLoginRequest,
):
    """
    租户管理员登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查询租户管理员（支持用户名或邮箱登录）
    result = await db.execute(
        select(TenantAdmin).where(
            or_(
                TenantAdmin.username == login_data.username,
                TenantAdmin.email == login_data.username,
            )
        )
    )
    tenant_admin = result.scalar_one_or_none()
    
    # 验证管理员和密码
    if tenant_admin is None or not verify_password(login_data.password, tenant_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.credentials_invalid"),
        )
    
    # 检查管理员状态
    if not tenant_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 检查租户状态
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_admin.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    
    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("tenant.disabled"),
        )
    
    # 更新登录信息
    tenant_admin.last_login_at = datetime.now(timezone.utc)
    tenant_admin.last_login_ip = request.client.host if request.client else None
    await db.commit()
    
    # 生成 Token（包含 tenant_id 信息）
    tokens = create_token_pair(
        tenant_admin.id,
        scope=TOKEN_SCOPE_TENANT_ADMIN,
        extra_claims={"tenant_id": tenant_admin.tenant_id},
    )
    
    return success(
        data=TokenResponse(**tokens),
        message=_("auth.login_success"),
    )


@router.post("/refresh", summary="刷新 Token")
async def refresh_token(
    db: DbSession,
    refresh_data: RefreshTokenRequest,
):
    """
    使用 Refresh Token 获取新的 Token 对
    """
    # 验证 Refresh Token 并检查 scope
    admin_id, scope = verify_token_with_scope(
        refresh_data.refresh_token, TOKEN_SCOPE_TENANT_ADMIN, TOKEN_TYPE_REFRESH
    )
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 查询租户管理员
    result = await db.execute(
        select(TenantAdmin).where(TenantAdmin.id == int(admin_id))
    )
    tenant_admin = result.scalar_one_or_none()
    
    if tenant_admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 检查状态
    if not tenant_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 生成新的 Token 对
    tokens = create_token_pair(
        tenant_admin.id,
        scope=TOKEN_SCOPE_TENANT_ADMIN,
        extra_claims={"tenant_id": tenant_admin.tenant_id},
    )
    
    return success(
        data=TokenResponse(**tokens),
        message=_("common.success"),
    )


@router.post("/logout", summary="租户管理员登出")
async def tenant_admin_logout(
    current_admin: ActiveTenantAdmin,
):
    """
    租户管理员登出
    """
    return success(
        message=_("auth.logout_success"),
    )


@router.get("/me", summary="获取当前租户管理员信息")
async def get_current_tenant_admin_info(
    current_admin: ActiveTenantAdmin,
):
    """
    获取当前登录租户管理员的详细信息
    """
    return success(
        data=TenantAdminResponse.model_validate(current_admin, from_attributes=True),
        message=_("common.success"),
    )


@router.put("/password", summary="修改密码")
async def change_password(
    db: DbSession,
    current_admin: ActiveTenantAdmin,
    password_data: TenantAdminChangePasswordRequest,
):
    """
    修改当前租户管理员密码
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("auth.password_mismatch"),
        )
    
    # 更新密码
    current_admin.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return success(
        message=_("auth.password_changed"),
    )


@router.post("/impersonate", summary="平台管理员一键登录")
async def impersonate_login(
    db: DbSession,
    request: Request,
    data: ImpersonateTokenRequest,
):
    """
    验证平台管理员的 impersonate token 并换取正式 Token
    
    - Token 60 秒过期，一次性使用
    - 返回标准的 access_token 和 refresh_token
    """
    # 验证 impersonate token
    payload = verify_impersonate_token(data.impersonate_token, TOKEN_SCOPE_TENANT_ADMIN)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.impersonate_token_invalid"),
        )
    
    admin_id = payload.get("admin_id")
    target_tenant_id = payload.get("target_tenant_id")
    target_role_id = payload.get("target_role_id")
    
    # 验证租户状态
    tenant_result = await db.execute(
        select(Tenant).where(
            Tenant.id == target_tenant_id,
            Tenant.is_deleted == False,
        )
    )
    tenant = tenant_result.scalar_one_or_none()
    
    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("tenant.disabled"),
        )
    
    # 获取租户的所有者信息（作为登录身份）
    owner_result = await db.execute(
        select(TenantAdmin).where(
            TenantAdmin.tenant_id == target_tenant_id,
            TenantAdmin.is_owner == True,
            TenantAdmin.is_deleted == False,
        )
    )
    tenant_owner = owner_result.scalar_one_or_none()
    
    if tenant_owner is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("tenant.owner_not_found"),
        )
    
    # 获取执行 impersonate 的平台管理员信息（用于审计日志）
    platform_admin_result = await db.execute(
        select(Admin).where(Admin.id == admin_id)
    )
    platform_admin = platform_admin_result.scalar_one_or_none()
    platform_admin_username = platform_admin.username if platform_admin else "unknown"
    
    # 生成正式 Token
    extra_claims = {
        "tenant_id": target_tenant_id,
        "impersonated_by": admin_id,  # 标记是平台管理员代登录
    }
    
    # 如果指定了角色，加入 claims
    if target_role_id:
        extra_claims["impersonate_role_id"] = target_role_id
    
    tokens = create_token_pair(
        tenant_owner.id,
        scope=TOKEN_SCOPE_TENANT_ADMIN,
        extra_claims=extra_claims,
    )
    
    # 记录审计日志
    audit_logger.info(
        "Admin impersonate completed | admin_id=%s | admin_username=%s | "
        "target_tenant_id=%s | target_tenant_code=%s | tenant_owner_id=%s | "
        "target_role_id=%s | client_ip=%s",
        admin_id,
        platform_admin_username,
        target_tenant_id,
        tenant.code,
        tenant_owner.id,
        target_role_id,
        request.client.host if request.client else None,
    )
    
    return success(
        data=TokenResponse(**tokens),
        message=_("auth.impersonate_success"),
    )


__all__ = ["router"]
