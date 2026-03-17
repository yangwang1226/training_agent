"""
动态提示词生成器
使用混合策略：动态生成 + 静态约束
"""

import logging
import json
from typing import Optional
import dashscope
from dashscope import MultiModalConversation
from dotenv import load_dotenv
import os

load_dotenv()

from agent.meta_prompt import MetaPromptManager


class DynamicPromptGenerator:
    """动态提示词生成器"""
    
    def __init__(self):
        self.meta_prompt_manager = MetaPromptManager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Qwen 客户端
        api_key = os.getenv('DASHSCOPE_API_KEY')
        
        if not api_key:
            self.logger.warning("未配置 DASHSCOPE_API_KEY，动态生成功能将不可用")
            self.client = None
        else:
            dashscope.api_key = api_key
            self.client = MultiModalConversation
            self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
    
    def generate_prompt(
        self,
        scene_type: str,
        scene_data: dict,
        model: str = None
    ) -> Optional[str]:
        """
        动态生成场景提示词
        
        Args:
            scene_type: 场景类型（sales/service）
            scene_data: 场景数据
            model: 使用的模型（默认使用 QWEN_PLUS_MODEL）
            
        Returns:
            生成的提示词，失败返回 None
        """
        if not self.client:
            self.logger.error("Qwen 客户端未初始化，无法生成提示词")
            return None
        
        use_model = model or self.llm_model
        
        try:
            # 1. 生成元提示词
            self.logger.info(f"生成 {scene_type} 场景的元提示词...")
            meta_prompt = self.meta_prompt_manager.generate_meta_prompt(
                scene_type, 
                scene_data
            )
            
            # 2. 调用 Qwen 生成最终提示词
            self.logger.info(f"调用 {use_model} 生成最终提示词...")
            
            messages = [
                {
                    "role": "system",
                    "content": [{"text": "你是一个专业的提示词工程专家，擅长设计AI对练场景的提示词。"}]
                },
                {
                    "role": "user",
                    "content": [{"text": meta_prompt}]
                }
            ]
            
            response = self.client.call(
                model=use_model,
                enable_thinking=False,
                messages=messages,
            )
            
            if response.status_code != 200:
                self.logger.error(f"Qwen API error: {response.code} - {response.message}")
                return None
            
            generated_prompt = response.output.choices[0].message.content[0]["text"].strip()
            
            # 3. 验证生成的提示词
            if self._validate_prompt(generated_prompt, scene_type):
                self.logger.info("提示词生成成功并通过验证")
                return generated_prompt
            else:
                self.logger.warning("生成的提示词未通过验证")
                return None
                
        except Exception as e:
            self.logger.error(f"动态生成提示词失败: {str(e)}", exc_info=True)
            return None
    
    def _validate_prompt(self, prompt: str, scene_type: str) -> bool:
        """
        验证生成的提示词质量
        
        Args:
            prompt: 生成的提示词
            scene_type: 场景类型
            
        Returns:
            是否通过验证
        """
        # 基础检查
        basic_checks = [
            len(prompt) > 500,  # 长度检查
            "角色" in prompt or "你是" in prompt,  # 包含角色定义
        ]
        
        # 场景特定检查
        if scene_type == "sales":
            scene_checks = [
                "问题" in prompt or "提问" in prompt,
                "结束" in prompt or "完成" in prompt,
                "字" in prompt or "简短" in prompt  # 话语量控制
            ]
        elif scene_type == "service":
            scene_checks = [
                "问题" in prompt or "故障" in prompt or "咨询" in prompt,
                "解决" in prompt or "处理" in prompt,
                "情绪" in prompt or "着急" in prompt  # 情绪表达
            ]
        else:
            scene_checks = []
        
        all_checks = basic_checks + scene_checks
        passed = sum(all_checks)
        total = len(all_checks)
        
        self.logger.info(f"提示词验证: {passed}/{total} 项通过")
        
        # 至少通过 80% 的检查
        return passed >= total * 0.8
    
    def get_meta_prompt(self, scene_type: str, scene_data: dict) -> str:
        """
        仅获取元提示词（不调用 LLM）
        用于调试或预览
        """
        return self.meta_prompt_manager.generate_meta_prompt(
            scene_type,
            scene_data
        )