"""
通用下拉选项 Schema

提供前端远程下拉组件的统一响应格式，支持列表和树型两种结构

使用示例:
    # 列表模式（默认）
    GET /api/roles/select
    -> {"items": [{"label": "角色1", "value": 1}, ...]}
    
    # 树型模式
    GET /api/roles/select?tree=true
    -> {"items": [{"label": "研发部", "value": 1, "children": [...]}]}
    
    # 懒加载模式（获取指定父节点的子节点）
    GET /api/roles/select?tree=true&parent_id=1
    -> {"items": [{"label": "前端组", "value": 2, "is_leaf": true}, ...]}
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SelectOption(BaseModel):
    """
    下拉选项（支持树型结构）
    
    统一的下拉选项数据结构，同时支持列表和树型两种模式
    
    列表模式:
        仅返回 label, value, extra, disabled 字段
    
    树型模式:
        返回所有字段，包含 children 子节点列表
    """
    
    label: str
    """显示文本"""
    
    value: int | str
    """选中值"""
    
    extra: dict[str, Any] | None = None
    """额外数据（如 code、icon、type 等）"""
    
    disabled: bool = False
    """是否禁用"""
    
    # ========== 树型扩展字段 ==========
    children: list[SelectOption] | None = Field(default=None)
    """子节点列表（仅 tree=true 时返回）"""
    
    is_leaf: bool | None = Field(default=None)
    """是否叶子节点（仅 tree=true 时返回，用于懒加载场景）"""


class SelectResponse(BaseModel):
    """
    下拉选项列表响应
    """
    
    items: list[SelectOption]
    """选项列表（列表模式或树型模式）"""


__all__ = ["SelectOption", "SelectResponse"]
