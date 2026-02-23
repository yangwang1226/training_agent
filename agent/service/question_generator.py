import json
import logging
from typing import List, Optional
from .llm_client import LLMClient
from .models import MainQuestion, BackgroundInfo


QUESTION_SYSTEM_PROMPT = """你是一个专业的问题生成助手。你的任务是根据背景信息和对话内容，生成家长可能会向老师提出的问题列表。

问题应该：
1. 符合家长的身份和关心点
2. 与学生的学习情况相关
3. 具有合理性和真实性
4. 按重要性和逻辑顺序排列
5. 问题应该是具体的、可回答的
6. 问题数量控制在3-8个

问题类型可以包括：
- 学习成绩相关
- 学习方法建议
- 课堂表现询问
- 作业完成情况
- 学习态度问题
- 家校配合建议
- 后续学习规划"""

QUESTION_USER_PROMPT_TEMPLATE = """请根据以下背景信息和对话内容，生成家长可能会向老师提出的问题列表。

## 背景信息：
{background_text}

## 对话内容：
{conversation}

## 自定义要求：
{custom_requirements}

请严格按照以下JSON格式输出，不要添加任何其他内容：
{{
    "questions": [
        {{"question": "问题内容1", "order": 1}},
        {{"question": "问题内容2", "order": 2}},
        {{"question": "问题内容3", "order": 3}}
    ]
}}

注意：
- 问题要口语化，符合家长说话习惯
- 问题之间要有逻辑顺序
- 每个问题都要有明确的编号"""


class QuestionGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(self, background_info: BackgroundInfo,
                 conversation: str,
                 custom_requirements: Optional[str] = None) -> List[MainQuestion]:
        background_text = background_info.to_prompt_text()
        
        user_prompt = QUESTION_USER_PROMPT_TEMPLATE.format(
            background_text=background_text,
            conversation=conversation,
            custom_requirements=custom_requirements or "无特殊要求"
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                QUESTION_SYSTEM_PROMPT,
                user_prompt
            )
            
            questions = []
            for item in result.get("questions", []):
                questions.append(MainQuestion(
                    question=item.get("question", ""),
                    order=item.get("order", len(questions) + 1)
                ))
            
            return sorted(questions, key=lambda x: x.order)
        except Exception as e:
            logging.error(f"生成问题列表失败: {str(e)}")
            return []
    
    async def async_generate(self, background_info: BackgroundInfo,
                             conversation: str,
                             custom_requirements: Optional[str] = None) -> List[MainQuestion]:
        background_text = background_info.to_prompt_text()
        
        user_prompt = QUESTION_USER_PROMPT_TEMPLATE.format(
            background_text=background_text,
            conversation=conversation,
            custom_requirements=custom_requirements or "无特殊要求"
        )
        
        try:
            response = await self.llm_client.async_call(
                QUESTION_SYSTEM_PROMPT,
                user_prompt
            )
            json_str = self.llm_client._extract_json(response)
            json_str = self.llm_client._clean_json_string(json_str)
            result = json.loads(json_str)
            
            questions = []
            for item in result.get("questions", []):
                questions.append(MainQuestion(
                    question=item.get("question", ""),
                    order=item.get("order", len(questions) + 1)
                ))
            
            return sorted(questions, key=lambda x: x.order)
        except Exception as e:
            logging.error(f"异步生成问题列表失败: {str(e)}")
            return []
    
    def format_questions_text(self, questions: List[MainQuestion]) -> str:
        return "\n".join([q.to_prompt_text() for q in questions])
