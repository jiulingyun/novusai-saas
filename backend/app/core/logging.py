"""
日志管理模块

提供按模块独立的日志文件和统一的日志格式
"""

import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Literal

from app.core.config import settings


# 日志格式
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DETAILED_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
)
JSON_FORMAT = (
    '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
    '"file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}'
)

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class LogManager:
    """
    日志管理器
    
    提供按模块独立的日志配置
    """
    
    _initialized: bool = False
    _log_dir: Path | None = None
    _loggers: dict[str, logging.Logger] = {}
    
    @classmethod
    def init(
        cls,
        log_dir: str | None = None,
        log_level: str | None = None,
        enable_console: bool = True,
        enable_file: bool = True,
    ) -> None:
        """
        初始化日志系统
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
        """
        if cls._initialized:
            return
        
        # 设置日志目录
        cls._log_dir = Path(log_dir or settings.LOG_DIR)
        cls._log_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取日志级别
        level = LOG_LEVELS.get(
            (log_level or settings.LOG_LEVEL).upper(),
            logging.INFO
        )
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除已有处理器
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        if enable_console:
            console_handler = cls._create_console_handler(level)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if enable_file:
            # 主日志文件
            file_handler = cls._create_file_handler("app", level)
            root_logger.addHandler(file_handler)
            
            # 错误日志单独文件
            error_handler = cls._create_file_handler(
                "error", logging.ERROR, max_bytes=50 * 1024 * 1024
            )
            root_logger.addHandler(error_handler)
        
        # 调整第三方库日志级别
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(
            logging.INFO if settings.DEBUG else logging.WARNING
        )
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        
        cls._initialized = True
    
    @classmethod
    def _create_console_handler(cls, level: int) -> logging.StreamHandler:
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # 开发环境使用详细格式
        fmt = DETAILED_FORMAT if settings.DEBUG else DEFAULT_FORMAT
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        
        return handler
    
    @classmethod
    def _create_file_handler(
        cls,
        name: str,
        level: int,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> RotatingFileHandler:
        """
        创建文件处理器（按大小轮转）
        
        Args:
            name: 日志文件名（不含扩展名）
            level: 日志级别
            max_bytes: 单个文件最大字节数
            backup_count: 保留备份文件数
        """
        if cls._log_dir is None:
            raise RuntimeError("LogManager not initialized")
        
        log_file = cls._log_dir / f"{name}.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setLevel(level)
        
        formatter = logging.Formatter(DETAILED_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        
        return handler
    
    @classmethod
    def _create_timed_handler(
        cls,
        name: str,
        level: int,
        when: Literal["midnight", "D", "H", "M"] = "midnight",
        backup_count: int = 30,
    ) -> TimedRotatingFileHandler:
        """
        创建文件处理器（按时间轮转）
        
        Args:
            name: 日志文件名
            level: 日志级别
            when: 轮转时机
            backup_count: 保留备份数
        """
        if cls._log_dir is None:
            raise RuntimeError("LogManager not initialized")
        
        log_file = cls._log_dir / f"{name}.log"
        handler = TimedRotatingFileHandler(
            log_file,
            when=when,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setLevel(level)
        
        formatter = logging.Formatter(DETAILED_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        
        return handler
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        *,
        separate_file: bool = False,
        level: int | None = None,
    ) -> logging.Logger:
        """
        获取模块日志器
        
        Args:
            name: 日志器名称（通常为模块名）
            separate_file: 是否使用独立日志文件
            level: 日志级别（可选）
            
        Returns:
            配置好的日志器
            
        Example:
            logger = LogManager.get_logger(__name__)
            logger.info("Hello")
            
            # 独立日志文件
            audit_logger = LogManager.get_logger("audit", separate_file=True)
        """
        # 确保已初始化
        if not cls._initialized:
            cls.init()
        
        # 检查缓存
        cache_key = f"{name}:{separate_file}"
        if cache_key in cls._loggers:
            return cls._loggers[cache_key]
        
        logger = logging.getLogger(name)
        
        # 设置级别
        if level is not None:
            logger.setLevel(level)
        
        # 添加独立文件处理器
        if separate_file and cls._log_dir:
            # 使用简化的文件名
            file_name = name.split(".")[-1]
            handler = cls._create_file_handler(file_name, logger.level or logging.INFO)
            logger.addHandler(handler)
        
        cls._loggers[cache_key] = logger
        return logger


def get_logger(name: str, *, separate_file: bool = False) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称
        separate_file: 是否使用独立日志文件
        
    Returns:
        logging.Logger
        
    Example:
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Processing request")
    """
    return LogManager.get_logger(name, separate_file=separate_file)


def init_logging() -> None:
    """初始化日志系统"""
    LogManager.init()


__all__ = [
    "LogManager",
    "get_logger",
    "init_logging",
]
