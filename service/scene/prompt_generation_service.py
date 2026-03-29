"""
场景提示词生成服务
基于结构化模板静态生成，彻底实现考训分离
"""

import logging
from typing import Dict, Any
from service.scene.template_service import TemplateManager


class PromptGenerationService:
    """
    场景提示词生成服务
    仅做确定性的模板映射，不再使用大模型动态生成。
    """
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.logger = logging.getLogger(__name__)
        
    def generate_scene_prompt(self, scene_data: Dict[str, Any]) -> str:
        """
        基于前端传入的场景数据，确定性地生成对练系统提示词。
        注意：sop_checklist (考核目标) 被刻意排除在此方法之外，仅用于课后评估。
        
        Args:
            scene_data: 场景数据字典
            
        Returns:
            生成的提示词
        """
        try:
            # 确定使用的模板，目前默认统一用 training_sales
            scene_type = scene_data.get('scene_type', 'sales')
            template_name = 'training_sales' if scene_type == 'sales' else 'training_service'
            
            # 由于可能缺少 service 模板，回退到 sales 兜底
            if not self.template_manager.template_exists(template_name):
                template_name = 'training_sales'

            template_str = self.template_manager.get_template(template_name)
            
            # 1. 提取基础变量，设置防空默认值
            industry = scene_data.get('industry', '通用行业')
            ai_role = scene_data.get('ai_role', '客户')
            user_role = scene_data.get('user_role', '销售')
            scene_description = scene_data.get('scene_description', '无特殊背景设定。')
            opening_line = scene_data.get('opening_line', '无设定，由用户主动破冰。')
            
            # 2. 提取终止逻辑，无则使用默认防死循环逻辑
            termination_logic = scene_data.get('termination_logic', '') 
            if not termination_logic:
                termination_logic = "1. 用户主动提出结束。\n2. 已经完成采购决策或明确拒绝。\n3. 对话轮数超过15轮。"

            # 3. 填充模板变量 (不再包含 SOP 考核相关字段)
            final_prompt = template_str.format(
                industry=industry,
                ai_role=ai_role,
                user_role=user_role,
                scene_description=scene_description,
                termination_logic=termination_logic,
                opening_line=opening_line
            )
            
            return final_prompt
            
        except Exception as e:
            self.logger.error(f"生成场景提示词失败: {str(e)}", exc_info=True)
            return ""
