"""
数据库连接模块

提供异步数据库连接、会话管理和依赖注入
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.base_model import Base


# ============================================
# 异步数据库引擎
# ============================================

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境打印 SQL
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,  # 连接前检查
)

# 异步会话工厂
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ============================================
# 同步数据库引擎（用于 Alembic 迁移）
# ============================================

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

sync_session_factory = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


# ============================================
# 依赖注入
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（FastAPI 依赖注入）
    
    使用示例:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（上下文管理器）
    
    使用示例:
        async with get_db_context() as db:
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================
# 数据库管理函数
# ============================================

async def check_database_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        连接是否成功
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def create_database_if_not_exists() -> bool:
    """
    检查数据库是否存在，如果不存在则创建
    
    Returns:
        是否成功
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import ProgrammingError
    
    # 连接到 postgres 默认数据库来创建目标数据库
    admin_url = (
        f"postgresql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/postgres"
    )
    
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    try:
        with admin_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(
                text(
                    "SELECT 1 FROM pg_database WHERE datname = :dbname"
                ),
                {"dbname": settings.DATABASE_NAME}
            )
            exists = result.scalar() is not None
            
            if not exists:
                print(f"📦 数据库 '{settings.DATABASE_NAME}' 不存在，正在创建...")
                conn.execute(
                    text(f'CREATE DATABASE "{settings.DATABASE_NAME}"')
                )
                print(f"✅ 数据库 '{settings.DATABASE_NAME}' 创建成功")
            else:
                print(f"✅ 数据库 '{settings.DATABASE_NAME}' 已存在")
        
        return True
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        return False
    finally:
        admin_engine.dispose()


def run_migrations() -> bool:
    """
    运行数据库迁移（同步方式，用于启动时）
    
    Returns:
        是否成功
    """
    import os
    from pathlib import Path
    
    try:
        from alembic.config import Config
        from alembic import command
        
        # 获取 alembic.ini 路径
        backend_dir = Path(__file__).parent.parent.parent
        alembic_ini = backend_dir / "alembic.ini"
        
        if not alembic_ini.exists():
            print("⚠️  alembic.ini 不存在，跳过迁移")
            return True
        
        # 检查是否有迁移文件
        migrations_dir = backend_dir / "migrations" / "versions"
        if not migrations_dir.exists() or not any(migrations_dir.glob("*.py")):
            print("⚠️  没有迁移文件，跳过迁移")
            return True
        
        print("🔄 正在运行数据库迁移...")
        
        # 创建 Alembic 配置
        alembic_cfg = Config(str(alembic_ini))
        
        # 设置数据库 URL
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)
        
        # 运行迁移
        command.upgrade(alembic_cfg, "head")
        
        print("✅ 数据库迁移完成")
        return True
    except ImportError:
        print("⚠️  Alembic 未安装，跳过迁移")
        return True
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False


async def init_database() -> bool:
    """
    初始化数据库（启动时调用）
    
    1. 检查/创建数据库
    2. 运行迁移
    3. 验证连接
    
    Returns:
        是否成功
    """
    print("🔧 正在初始化数据库...")
    
    # 1. 检查/创建数据库
    if not await asyncio.to_thread(create_database_if_not_exists):
        return False
    
    # 2. 运行迁移
    if not await asyncio.to_thread(run_migrations):
        return False
    
    # 3. 验证连接
    if not await check_database_connection():
        return False
    
    print("✅ 数据库初始化完成")
    return True


async def close_database() -> None:
    """
    关闭数据库连接（关闭时调用）
    """
    await async_engine.dispose()
    sync_engine.dispose()
    print("✅ 数据库连接已关闭")


# 导出
__all__ = [
    "async_engine",
    "async_session_factory",
    "sync_engine",
    "sync_session_factory",
    "get_db",
    "get_db_context",
    "check_database_connection",
    "create_database_if_not_exists",
    "run_migrations",
    "init_database",
    "close_database",
    "Base",
]
