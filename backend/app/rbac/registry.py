"""
权限注册中心

收集所有通过装饰器定义的权限，应用启动时同步到数据库
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.rbac.decorators import PermissionMeta
    from app.enums.rbac import PermissionType, PermissionScope


class PermissionRegistry:
    """
    权限注册中心（单例）
    
    收集所有通过装饰器定义的权限，应用启动时同步到数据库
    """
    
    _instance: "PermissionRegistry | None" = None
    _permissions: dict[str, "PermissionMeta"]
    
    def __new__(cls) -> "PermissionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._permissions = {}
        return cls._instance
    
    def register(self, permission: "PermissionMeta") -> None:
        """
        注册权限
        
        Args:
            permission: 权限元信息
        """
        if permission.code not in self._permissions:
            self._permissions[permission.code] = permission
    
    def get(self, code: str) -> "PermissionMeta | None":
        """
        获取权限
        
        Args:
            code: 权限代码
        
        Returns:
            权限元信息或 None
        """
        return self._permissions.get(code)
    
    def get_all(self) -> list["PermissionMeta"]:
        """获取所有权限"""
        return list(self._permissions.values())
    
    def get_by_scope(self, scope: "PermissionScope") -> list["PermissionMeta"]:
        """
        按作用域获取权限
        
        Args:
            scope: 权限作用域
        
        Returns:
            权限列表
        """
        return [p for p in self._permissions.values() if p.scope == scope]
    
    def get_by_type(self, perm_type: "PermissionType") -> list["PermissionMeta"]:
        """
        按类型获取权限
        
        Args:
            perm_type: 权限类型
        
        Returns:
            权限列表
        """
        return [p for p in self._permissions.values() if p.type == perm_type]
    
    def get_menus(self) -> list["PermissionMeta"]:
        """获取所有菜单权限"""
        from app.enums.rbac import PermissionType
        return self.get_by_type(PermissionType.MENU)
    
    def get_operations(self) -> list["PermissionMeta"]:
        """获取所有操作权限"""
        from app.enums.rbac import PermissionType
        return self.get_by_type(PermissionType.OPERATION)
    
    def clear(self) -> None:
        """清空（测试用）"""
        self._permissions.clear()
    
    def __len__(self) -> int:
        return len(self._permissions)
    
    def __contains__(self, code: str) -> bool:
        return code in self._permissions


# 全局实例
permission_registry = PermissionRegistry()


__all__ = ["PermissionRegistry", "permission_registry"]
