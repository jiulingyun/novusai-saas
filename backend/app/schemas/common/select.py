"""
通用下拉选项 Schema

提供前端远程下拉组件的统一响应格式
"""

from typing import Any

from pydantic import BaseModel


class SelectOption(BaseModel):
    """
    下拉选项
    
    统一的下拉选项数据结构，适用于所有远程下拉组件
    """
    
    label: str
    """显示文本"""
    
    value: int | str
    """选中值"""
    
    extra: dict[str, Any] | None = None
    """额外数据（如 code、icon、color 等）"""
    
    disabled: bool = False
    """是否禁用"""


class SelectResponse(BaseModel):
    """
    下拉选项列表响应
    """
    
    items: list[SelectOption]
    """选项列表"""


__all__ = ["SelectOption", "SelectResponse"]
