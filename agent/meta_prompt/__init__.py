"""
元提示词模块
用于根据场景类型动态生成提示词
"""

from .base_template import BaseMetaPromptTemplate
from .sales_template import SalesMetaPromptTemplate
from .service_template import ServiceMetaPromptTemplate
from .meta_prompt_manager import MetaPromptManager

__all__ = [
    'BaseMetaPromptTemplate',
    'SalesMetaPromptTemplate',
    'ServiceMetaPromptTemplate',
    'MetaPromptManager'
]