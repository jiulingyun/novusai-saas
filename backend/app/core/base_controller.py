"""
控制器基类模块

提供 API 控制器层的基类，包括：
- BaseController: 通用控制器基类
- TenantController: 租户级控制器基类
- GlobalController: 全局控制器基类
"""

from typing import Any, Type

from fastapi import APIRouter, Depends


class BaseController:
    """
    控制器基类
    
    提供统一的路由注册和依赖注入
    
    使用示例:
        class UserController(BaseController):
            prefix = "/users"
            tags = ["用户管理"]
            service_class = UserService
            
            def _register_routes(self):
                @self.router.get("")
                async def list_users():
                    ...
    """
    
    # 路由配置
    prefix: str = ""
    tags: list[str] = []
    dependencies: list = []
    
    # 关联的服务类
    service_class: Type | None = None
    
    def __init__(self):
        """初始化控制器，创建路由器"""
        self.router = APIRouter(
            prefix=self.prefix,
            tags=self.tags,
            dependencies=self.dependencies,
        )
        self._register_routes()
    
    def _register_routes(self) -> None:
        """
        注册路由
        
        子类必须重写此方法来注册具体的路由处理函数
        """
        pass
    
    def get_service(self, db: Any) -> Any:
        """
        获取服务实例
        
        Args:
            db: 数据库会话
        
        Returns:
            服务实例
        """
        if self.service_class:
            return self.service_class(db)
        return None
    
    # ========================================
    # 钩子方法（子类可重写）
    # ========================================
    
    def before_request(self, request: Any) -> None:
        """
        请求前钩子
        
        可用于：日志记录、权限预检等
        
        Args:
            request: 请求对象
        """
        pass
    
    def after_request(self, response: Any) -> Any:
        """
        请求后钩子
        
        可用于：响应处理、日志记录等
        
        Args:
            response: 响应对象
        
        Returns:
            处理后的响应
        """
        return response


class TenantController(BaseController):
    """
    租户级控制器基类
    
    自动注入租户上下文
    """
    
    def get_service(self, db: Any, tenant_id: int) -> Any:
        """
        获取租户级服务实例
        
        Args:
            db: 数据库会话
            tenant_id: 租户 ID
        
        Returns:
            租户服务实例
        """
        if self.service_class:
            return self.service_class(db, tenant_id)
        return None


class GlobalController(BaseController):
    """
    全局控制器基类
    
    用于超管或系统级操作，无租户隔离
    """
    pass


# 导出
__all__ = ["BaseController", "TenantController", "GlobalController"]
