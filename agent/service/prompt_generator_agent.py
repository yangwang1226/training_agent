import logging
from typing import Optional, List
from dataclasses import dataclass

from .models import (
    BackgroundInfo, 
    MainQuestion, 
    TriggerGroup, 
    GeneratedPrompt,
    UserInput
)
from .llm_client import LLMClient
from .template_manager import TemplateManager
from .background_generator import BackgroundGenerator
from .question_generator import QuestionGenerator
from .follow_up_generator import FollowUpGenerator


@dataclass
class GenerationResult:
    success: bool
    full_prompt: str = ""
    background_info: Optional[BackgroundInfo] = None
    main_questions: List[MainQuestion] = None
    trigger_groups: List[TriggerGroup] = None
    error_message: str = ""
    
    def __post_init__(self):
        if self.main_questions is None:
            self.main_questions = []
        if self.trigger_groups is None:
            self.trigger_groups = []


class PromptGeneratorAgent:
    def __init__(self, 
                 template_name: str = "training_teacher",
                 llm_client: Optional[LLMClient] = None):
        self.template_name = template_name
        self.llm_client = llm_client or LLMClient()
        self.template_manager = TemplateManager()
        self.background_generator = BackgroundGenerator(self.llm_client)
        self.question_generator = QuestionGenerator(self.llm_client)
        self.follow_up_generator = FollowUpGenerator(self.llm_client)
    
    def generate(self, 
                 conversation: str,
                 custom_requirements: Optional[str] = None) -> GenerationResult:
        try:
            logging.info("开始生成背景信息...")
            background_info = self.background_generator.generate(
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            if not background_info.to_prompt_text():
                return GenerationResult(
                    success=False,
                    error_message="背景信息生成失败"
                )
            
            logging.info("开始生成主问题列表...")
            main_questions = self.question_generator.generate(
                background_info=background_info,
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            if not main_questions:
                return GenerationResult(
                    success=False,
                    error_message="主问题列表生成失败"
                )
            
            logging.info("开始生成关联问题...")
            trigger_groups = self.follow_up_generator.generate(
                background_info=background_info,
                main_questions=main_questions,
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            background_text = background_info.to_prompt_text()
            questions_text = self.question_generator.format_questions_text(main_questions)
            trigger_groups_text = self.follow_up_generator.format_trigger_groups_text(trigger_groups)
            
            logging.info("开始合成完整提示词...")
            full_prompt = self.template_manager.generate_full_prompt(
                template_name=self.template_name,
                background_text=background_text,
                questions_text=questions_text,
                trigger_groups_text=trigger_groups_text
            )
            
            return GenerationResult(
                success=True,
                full_prompt=full_prompt,
                background_info=background_info,
                main_questions=main_questions,
                trigger_groups=trigger_groups
            )
            
        except Exception as e:
            logging.error(f"生成提示词失败: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=str(e)
            )
    
    async def async_generate(self,
                             conversation: str,
                             custom_requirements: Optional[str] = None) -> GenerationResult:
        try:
            logging.info("异步开始生成背景信息...")
            background_info = await self.background_generator.async_generate(
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            if not background_info.to_prompt_text():
                return GenerationResult(
                    success=False,
                    error_message="背景信息生成失败"
                )
            
            logging.info("异步开始生成主问题列表...")
            main_questions = await self.question_generator.async_generate(
                background_info=background_info,
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            if not main_questions:
                return GenerationResult(
                    success=False,
                    error_message="主问题列表生成失败"
                )
            
            logging.info("异步开始生成关联问题...")
            trigger_groups = await self.follow_up_generator.async_generate(
                background_info=background_info,
                main_questions=main_questions,
                conversation=conversation,
                custom_requirements=custom_requirements
            )
            
            background_text = background_info.to_prompt_text()
            questions_text = self.question_generator.format_questions_text(main_questions)
            trigger_groups_text = self.follow_up_generator.format_trigger_groups_text(trigger_groups)
            
            logging.info("异步开始合成完整提示词...")
            full_prompt = self.template_manager.generate_full_prompt(
                template_name=self.template_name,
                background_text=background_text,
                questions_text=questions_text,
                trigger_groups_text=trigger_groups_text
            )
            
            return GenerationResult(
                success=True,
                full_prompt=full_prompt,
                background_info=background_info,
                main_questions=main_questions,
                trigger_groups=trigger_groups
            )
            
        except Exception as e:
            logging.error(f"异步生成提示词失败: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=str(e)
            )
    
    def get_available_templates(self) -> List[str]:
        return self.template_manager.get_template_names()
    
    def set_template(self, template_name: str):
        if template_name not in self.template_manager.get_template_names():
            raise ValueError(f"模板不存在: {template_name}")
        self.template_name = template_name


def generate_prompt(conversation: str,
                    template_name: str = "training_teacher",
                    custom_requirements: Optional[str] = None) -> GenerationResult:
    agent = PromptGeneratorAgent(template_name=template_name)
    return agent.generate(conversation=conversation, custom_requirements=custom_requirements)


async def async_generate_prompt(conversation: str,
                                template_name: str = "training_teacher",
                                custom_requirements: Optional[str] = None) -> GenerationResult:
    agent = PromptGeneratorAgent(template_name=template_name)
    return await agent.async_generate(conversation=conversation, custom_requirements=custom_requirements)
