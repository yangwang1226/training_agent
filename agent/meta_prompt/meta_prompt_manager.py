"""
元提示词管理器
"""

import logging
from typing import Optional
from .base_template import BaseMetaPromptTemplate
from .sales_template import SalesMetaPromptTemplate
from .service_template import ServiceMetaPromptTemplate


class MetaPromptManager:
    """元提示词管理器"""
    
    def __init__(self):
        self.templates = {
            "sales": SalesMetaPromptTemplate(),
            "service": ServiceMetaPromptTemplate()
        }
        self.logger = logging.getLogger(__name__)
    
    def generate_meta_prompt(
        self, 
        scene_type: str, 
        scene_data: dict
    ) -> str:
        """
        根据场景类型生成元提示词
        
        Args:
            scene_type: 场景类型（sales/service）
            scene_data: 场景数据字典
            
        Returns:
            生成的元提示词
            
        Raises:
            ValueError: 不支持的场景类型
        """
        template = self.templates.get(scene_type)
        if not template:
            raise ValueError(f"不支持的场景类型: {scene_type}")
        
        self.logger.info(f"正在生成{scene_type}场景的元提示词...")
        return template.generate(scene_data)
    
    def add_template(self, scene_type: str, template: BaseMetaPromptTemplate):
        """添加新的场景模板（扩展用）"""
        self.templates[scene_type] = template
        self.logger.info(f"已添加新场景模板: {scene_type}")
    
    def get_supported_scene_types(self) -> list:
        """获取支持的场景类型列表"""
        return list(self.templates.keys())