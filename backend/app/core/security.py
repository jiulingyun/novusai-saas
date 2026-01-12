"""
安全模块

提供 JWT Token 生成/验证、密码哈希等安全相关功能
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Token 类型常量
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    创建 Access Token
    
    Args:
        subject: Token 主体（通常是用户 ID）
        expires_delta: 过期时间增量
        extra_claims: 额外的 claims
        
    Returns:
        编码后的 JWT Token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TOKEN_TYPE_ACCESS,
    }
    
    if extra_claims:
        to_encode.update(extra_claims)
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建 Refresh Token
    
    Args:
        subject: Token 主体（通常是用户 ID）
        expires_delta: 过期时间增量
        
    Returns:
        编码后的 JWT Token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TOKEN_TYPE_REFRESH,
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """
    解码并验证 Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        解码后的 payload，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = TOKEN_TYPE_ACCESS) -> str | None:
    """
    验证 Token 并返回 subject
    
    Args:
        token: JWT Token 字符串
        token_type: 期望的 Token 类型
        
    Returns:
        Token 的 subject（用户 ID），验证失败返回 None
    """
    payload = decode_token(token)
    if payload is None:
        return None
    
    # 检查 Token 类型
    if payload.get("type") != token_type:
        return None
    
    return payload.get("sub")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否正确
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希后的密码
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def create_token_pair(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    创建 Token 对（access_token + refresh_token）
    
    Args:
        subject: Token 主体
        extra_claims: 额外的 claims（仅添加到 access_token）
        
    Returns:
        包含 access_token 和 refresh_token 的字典
    """
    return {
        "access_token": create_access_token(subject, extra_claims=extra_claims),
        "refresh_token": create_refresh_token(subject),
        "token_type": "bearer",
    }


__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "verify_password",
    "get_password_hash",
    "create_token_pair",
    "TOKEN_TYPE_ACCESS",
    "TOKEN_TYPE_REFRESH",
]
