"""
平台管理员认证 API

提供平台管理员的登录、登出、Token 刷新等接口
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import select, or_

from app.core.deps import DbSession, ActiveAdmin
from app.core.i18n import _
from app.core.response import success
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    verify_token_with_scope,
    TOKEN_TYPE_REFRESH,
    TOKEN_SCOPE_ADMIN,
)
from app.models import Admin
from app.rbac.decorators import public, auth_only
from app.schemas.common import TokenResponse, RefreshTokenRequest
from app.schemas.system import (
    AdminLoginRequest,
    AdminResponse,
    AdminChangePasswordRequest,
)


router = APIRouter(prefix="/auth", tags=["平台管理员认证"])


@router.post("/login", summary="管理员登录")
@public
async def admin_login(
    db: DbSession,
    request: Request,
    login_data: AdminLoginRequest,
):
    """
    平台管理员登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查询管理员
    result = await db.execute(
        select(Admin).where(
            or_(Admin.username == login_data.username, Admin.email == login_data.username)
        )
    )
    admin = result.scalar_one_or_none()
    
    # 验证管理员和密码
    if admin is None or not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.credentials_invalid"),
        )
    
    # 检查状态
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 更新登录信息
    admin.last_login_at = datetime.now(timezone.utc)
    admin.last_login_ip = request.client.host if request.client else None
    await db.commit()
    
    # 生成 Token
    tokens = create_token_pair(admin.id, scope=TOKEN_SCOPE_ADMIN)
    
    return success(
        data=TokenResponse(**tokens),
        message=_("auth.login_success"),
    )


@router.post("/refresh", summary="刷新 Token")
@public
async def refresh_token(
    db: DbSession,
    refresh_data: RefreshTokenRequest,
):
    """
    使用 Refresh Token 获取新的 Token 对
    """
    # 验证 Refresh Token 并检查 scope
    admin_id, scope = verify_token_with_scope(
        refresh_data.refresh_token, TOKEN_SCOPE_ADMIN, TOKEN_TYPE_REFRESH
    )
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 查询管理员
    result = await db.execute(
        select(Admin).where(Admin.id == int(admin_id))
    )
    admin = result.scalar_one_or_none()
    
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 检查状态
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 生成新的 Token 对
    tokens = create_token_pair(admin.id, scope=TOKEN_SCOPE_ADMIN)
    
    return success(
        data=TokenResponse(**tokens),
        message=_("common.success"),
    )


@router.post("/logout", summary="管理员登出")
@auth_only
async def admin_logout(
    current_admin: ActiveAdmin,
):
    """
    管理员登出
    """
    return success(
        message=_("auth.logout_success"),
    )


@router.get("/me", summary="获取当前管理员信息")
@auth_only
async def get_current_admin_info(
    current_admin: ActiveAdmin,
):
    """
    获取当前登录管理员的详细信息
    """
    return success(
        data=AdminResponse.model_validate(current_admin, from_attributes=True),
        message=_("common.success"),
    )


@router.put("/password", summary="修改密码")
@auth_only
async def change_password(
    db: DbSession,
    current_admin: ActiveAdmin,
    password_data: AdminChangePasswordRequest,
):
    """
    修改当前管理员密码
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


__all__ = ["router"]
