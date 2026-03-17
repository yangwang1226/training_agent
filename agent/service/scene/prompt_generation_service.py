"""
场景提示词生成服务
集成动态生成和静态模板两种方式
"""

import logging
import json
from typing import Optional, Dict, Any
from agent.service.dynamic_prompt_generator import DynamicPromptGenerator
from agent.service.template_manager import TemplateManager


class PromptGenerationService:
    """
    场景提示词生成服务
    根据场景类型选择合适的生成策略
    """
    
    def __init__(self):
        self.dynamic_generator = DynamicPromptGenerator()
        self.template_manager = TemplateManager()
        self.logger = logging.getLogger(__name__)
    
    def generate_scene_prompt(
        self,
        scene_type: str,
        scene_data: Dict[str, Any],
        use_dynamic: bool = True
    ) -> Optional[str]:
        """
        生成场景提示词
        
        Args:
            scene_type: 场景类型（sales/service）
            scene_data: 场景数据，包含：
                - ai_role: AI角色
                - user_role: 用户角色
                - industry: 行业
                - scene_description: 场景描述
                - background_info: 背景信息
                - main_questions: 主问题列表（从 fixed_questions 提取）
                - trigger_rules: 关联问题规则（从 related_questions 提取）
                - purchase_intent: 购买意愿（sales场景，可选）
                - problem_severity: 问题严重性（service场景，可选）
            use_dynamic: 是否使用动态生成（True=动态生成，False=静态模板）
            
        Returns:
            生成的提示词，失败返回 None
        """
        try:
            # 预处理场景数据
            processed_data = self._preprocess_scene_data(scene_data, scene_type)
            
            if use_dynamic:
                # 尝试动态生成
                self.logger.info(f"使用动态生成方式生成 {scene_type} 场景提示词...")
                prompt = self.dynamic_generator.generate_prompt(
                    scene_type=scene_type,
                    scene_data=processed_data
                )
                
                if prompt:
                    self.logger.info("动态生成成功")
                    return prompt
                else:
                    self.logger.warning("动态生成失败，降级到静态模板")
            
            # 降级到静态模板
            self.logger.info(f"使用静态模板生成 {scene_type} 场景提示词...")
            return self._generate_from_template(scene_type, processed_data)
            
        except Exception as e:
            self.logger.error(f"生成场景提示词失败: {str(e)}", exc_info=True)
            return None
    
    def _preprocess_scene_data(self, scene_data: Dict[str, Any], scene_type: str) -> Dict[str, Any]:
        """
        预处理场景数据，提取和转换必要字段
        
        Args:
            scene_data: 原始场景数据
            scene_type: 场景类型
            
        Returns:
            处理后的场景数据
        """
        processed = {
            'ai_role': scene_data.get('ai_role', '客户'),
            'user_role': scene_data.get('user_role', '销售顾问' if scene_type == 'sales' else '客服专员'),
            'industry': scene_data.get('industry', '未指定'),
            'scene_description': scene_data.get('scene_description', ''),
            'background_info': scene_data.get('background_info', '')
        }
        
        # 处理主问题列表
        main_questions = self._extract_main_questions(scene_data.get('fixed_questions'))
        processed['main_questions'] = main_questions
        
        # 处理关联问题规则
        trigger_rules = self._extract_trigger_rules(scene_data.get('related_questions'))
        processed['trigger_rules'] = trigger_rules
        
        # 场景特定参数
        if scene_type == 'sales':
            processed['purchase_intent'] = scene_data.get('purchase_intent', '一般')
        elif scene_type == 'service':
            processed['problem_severity'] = scene_data.get('problem_severity', '中等')
            processed['core_problem'] = scene_data.get('core_problem', '产品功能异常')
            processed['additional_concerns'] = scene_data.get('additional_concerns', [])
        
        return processed
    
    def _extract_main_questions(self, fixed_questions: Any) -> list:
        """
        从 fixed_questions 字段提取主问题列表
        
        Args:
            fixed_questions: JSON字符串或列表
            
        Returns:
            问题列表
        """
        if not fixed_questions:
            return []
        
        try:
            # 如果是字符串，尝试解析JSON
            if isinstance(fixed_questions, str):
                questions_data = json.loads(fixed_questions)
            else:
                questions_data = fixed_questions
            
            # 提取问题文本
            if isinstance(questions_data, list):
                questions = [
                    q.get('question', '') if isinstance(q, dict) else str(q)
                    for q in questions_data
                ]
                return [q for q in questions if q]  # 过滤空问题
            
            return []
            
        except Exception as e:
            self.logger.warning(f"提取主问题失败: {str(e)}")
            return []
    
    def _extract_trigger_rules(self, related_questions: Any) -> dict:
        """
        从 related_questions 字段提取关联问题规则
        
        Args:
            related_questions: JSON字符串或列表
            
        Returns:
            规则字典 {group_name: {keywords: [...], questions: [...]}}
        """
        if not related_questions:
            return {}
        
        try:
            # 如果是字符串，尝试解析JSON
            if isinstance(related_questions, str):
                related_data = json.loads(related_questions)
            else:
                related_data = related_questions
            
            if not isinstance(related_data, list):
                return {}
            
            # 转换为规则字典
            rules = {}
            for idx, item in enumerate(related_data):
                if not isinstance(item, dict):
                    continue
                
                group_name = item.get('group_name') or f"Group_{idx+1}"
                keywords = item.get('trigger_keywords', [])
                question = item.get('question', '')
                
                if keywords and question:
                    if group_name not in rules:
                        rules[group_name] = {
                            'keywords': [],
                            'questions': []
                        }
                    
                    rules[group_name]['keywords'].extend(keywords)
                    rules[group_name]['questions'].append(question)
            
            return rules
            
        except Exception as e:
            self.logger.warning(f"提取关联问题规则失败: {str(e)}")
            return {}
    
    def _generate_from_template(self, scene_type: str, scene_data: Dict[str, Any]) -> str:
        """
        使用静态模板生成提示词（降级方案）
        
        Args:
            scene_type: 场景类型
            scene_data: 场景数据
            
        Returns:
            生成的提示词
        """
        # 这里可以调用原有的模板生成逻辑
        # 暂时返回一个基础模板
        template_mapping = {
            'sales': 'sales_training',
            'service': 'service_training'
        }
        
        template_name = template_mapping.get(scene_type, 'sales_training')
        
        try:
            template = self.template_manager.get_template(template_name)
            
            # 填充模板
            background = scene_data.get('background_info', '')
            questions_text = '\n'.join([
                f"{i+1}. {q}" 
                for i, q in enumerate(scene_data.get('main_questions', []))
            ])
            
            # 简单的字符串替换
            filled_template = template.replace('#背景信息：', f"#背景信息：\n{background}")
            filled_template = filled_template.replace('# 待提问主列表：', f"# 待提问主列表：\n{questions_text}")
            
            return filled_template
            
        except Exception as e:
            self.logger.error(f"静态模板生成失败: {str(e)}", exc_info=True)
            # 返回一个最基础的提示词
            return self._generate_fallback_prompt(scene_type, scene_data)
    
    def _generate_fallback_prompt(self, scene_type: str, scene_data: Dict[str, Any]) -> str:
        """
        生成最基础的降级提示词
        """
        ai_role = scene_data.get('ai_role', '客户')
        user_role = scene_data.get('user_role', '客服专员')
        background = scene_data.get('background_info', '')
        questions = scene_data.get('main_questions', [])
        
        prompt = f"""# 角色定义
你是一个{ai_role}，正在与{user_role}进行对话。

# 背景信息
{background}

# 你关心的问题
"""
        
        for i, q in enumerate(questions, 1):
            prompt += f"{i}. {q}\n"
        
        return prompt