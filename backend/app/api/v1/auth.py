"""
认证 API 路由

提供用户登录、登出、Token 刷新等认证相关接口
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DbSession, ActiveUser
from app.core.i18n import _
from app.core.response import success, error
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    verify_token,
    TOKEN_TYPE_REFRESH,
)
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    LoginRequest,
    UserResponse,
    ChangePasswordRequest,
)


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="用户登录（OAuth2 表单）")
async def login_oauth2(
    db: DbSession,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 密码模式登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查询用户（支持用户名或邮箱登录）
    result = await db.execute(
        select(User).where(
            or_(User.username == form_data.username, User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    # 验证用户和密码
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.credentials_invalid"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 更新登录信息
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None
    await db.commit()
    
    # 生成 Token
    tokens = create_token_pair(user.id)
    
    return success(
        data=TokenResponse(**tokens),
        message=_("auth.login_success"),
    )


@router.post("/login/json", summary="用户登录（JSON 格式）")
async def login_json(
    db: DbSession,
    request: Request,
    login_data: LoginRequest,
):
    """
    JSON 格式登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查询用户
    result = await db.execute(
        select(User).where(
            or_(User.username == login_data.username, User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    # 验证用户和密码
    if user is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.credentials_invalid"),
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 更新登录信息
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None
    await db.commit()
    
    # 生成 Token
    tokens = create_token_pair(user.id)
    
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
    # 验证 Refresh Token
    user_id = verify_token(refresh_data.refresh_token, TOKEN_TYPE_REFRESH)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("auth.refresh_token_invalid"),
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("auth.account_disabled"),
        )
    
    # 生成新的 Token 对
    tokens = create_token_pair(user.id)
    
    return success(
        data=TokenResponse(**tokens),
        message=_("common.success"),
    )


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: ActiveUser,
):
    """
    用户登出
    
    注意：JWT 是无状态的，登出只是客户端行为。
    如需服务端黑名单机制，请使用 Redis 存储已失效的 Token。
    """
    return success(
        message=_("auth.logout_success"),
    )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: ActiveUser,
):
    """
    获取当前登录用户的详细信息
    """
    return success(
        data=UserResponse.model_validate(current_user, from_attributes=True),
        message=_("common.success"),
    )


@router.put("/password", summary="修改密码")
async def change_password(
    db: DbSession,
    current_user: ActiveUser,
    password_data: ChangePasswordRequest,
):
    """
    修改当前用户密码
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("auth.password_mismatch"),
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return success(
        message=_("auth.password_changed"),
    )


__all__ = ["router"]
