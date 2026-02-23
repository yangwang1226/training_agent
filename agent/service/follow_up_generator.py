import json
import logging
from typing import List, Optional
from .llm_client import LLMClient
from .models import TriggerGroup, FollowUpQuestion, MainQuestion, BackgroundInfo


FOLLOW_UP_SYSTEM_PROMPT = """你是一个专业的关联问题生成助手。你的任务是根据主问题列表和背景信息，生成关联问题分组。

关联问题是指：当老师回答某个主问题时，如果回答中包含特定的关键词或信息，家长应该追问的问题。

关联问题分组格式：
- 每个分组包含：触发关键词、触发问题列表
- 触发关键词：老师回答中可能包含的关键词或短语
- 触发问题列表：当检测到触发关键词时，家长应该追问的问题

生成规则：
1. 每个分组针对一个或多个主问题
2. 触发关键词要具体、可识别
3. 关联问题要有逻辑性，是对老师回答的合理追问
4. 每个分组的关联问题数量控制在1-3个
5. 生成2-5个分组"""

FOLLOW_UP_USER_PROMPT_TEMPLATE = """请根据以下信息生成关联问题分组：

## 背景信息：
{background_text}

## 主问题列表：
{main_questions_text}

## 对话内容：
{conversation}

## 自定义要求：
{custom_requirements}

请严格按照以下JSON格式输出，不要添加任何其他内容：
{{
    "trigger_groups": [
        {{
            "group_name": "A",
            "trigger_keywords": ["关键词1", "关键词2", "关键词3"],
            "questions": [
                {{"question": "关联问题1", "order": 1}},
                {{"question": "关联问题2", "order": 2}}
            ]
        }},
        {{
            "group_name": "B",
            "trigger_keywords": ["关键词1", "关键词2"],
            "questions": [
                {{"question": "关联问题1", "order": 1}}
            ]
        }}
    ]
}}

注意：
- 分组名称使用大写字母（A、B、C...）
- 触发关键词要简洁明确
- 关联问题要口语化
- 每个关联问题要有编号"""


class FollowUpGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(self, background_info: BackgroundInfo,
                 main_questions: List[MainQuestion],
                 conversation: str,
                 custom_requirements: Optional[str] = None) -> List[TriggerGroup]:
        background_text = background_info.to_prompt_text()
        main_questions_text = "\n".join([f"{q.order}. {q.question}" for q in main_questions])
        
        user_prompt = FOLLOW_UP_USER_PROMPT_TEMPLATE.format(
            background_text=background_text,
            main_questions_text=main_questions_text,
            conversation=conversation,
            custom_requirements=custom_requirements or "无特殊要求"
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                FOLLOW_UP_SYSTEM_PROMPT,
                user_prompt
            )
            
            trigger_groups = []
            for group_data in result.get("trigger_groups", []):
                questions = []
                for q_data in group_data.get("questions", []):
                    questions.append(FollowUpQuestion(
                        question=q_data.get("question", ""),
                        order=q_data.get("order", len(questions) + 1)
                    ))
                
                trigger_groups.append(TriggerGroup(
                    group_name=group_data.get("group_name", chr(65 + len(trigger_groups))),
                    trigger_keywords=group_data.get("trigger_keywords", []),
                    questions=sorted(questions, key=lambda x: x.order)
                ))
            
            return trigger_groups
        except Exception as e:
            logging.error(f"生成关联问题失败: {str(e)}")
            return []
    
    async def async_generate(self, background_info: BackgroundInfo,
                             main_questions: List[MainQuestion],
                             conversation: str,
                             custom_requirements: Optional[str] = None) -> List[TriggerGroup]:
        background_text = background_info.to_prompt_text()
        main_questions_text = "\n".join([f"{q.order}. {q.question}" for q in main_questions])
        
        user_prompt = FOLLOW_UP_USER_PROMPT_TEMPLATE.format(
            background_text=background_text,
            main_questions_text=main_questions_text,
            conversation=conversation,
            custom_requirements=custom_requirements or "无特殊要求"
        )
        
        try:
            response = await self.llm_client.async_call(
                FOLLOW_UP_SYSTEM_PROMPT,
                user_prompt
            )
            json_str = self.llm_client._extract_json(response)
            json_str = self.llm_client._clean_json_string(json_str)
            result = json.loads(json_str)
            
            trigger_groups = []
            for group_data in result.get("trigger_groups", []):
                questions = []
                for q_data in group_data.get("questions", []):
                    questions.append(FollowUpQuestion(
                        question=q_data.get("question", ""),
                        order=q_data.get("order", len(questions) + 1)
                    ))
                
                trigger_groups.append(TriggerGroup(
                    group_name=group_data.get("group_name", chr(65 + len(trigger_groups))),
                    trigger_keywords=group_data.get("trigger_keywords", []),
                    questions=sorted(questions, key=lambda x: x.order)
                ))
            
            return trigger_groups
        except Exception as e:
            logging.error(f"异步生成关联问题失败: {str(e)}")
            return []
    
    def format_trigger_groups_text(self, trigger_groups: List[TriggerGroup]) -> str:
        return "\n\n".join([group.to_prompt_text() for group in trigger_groups])
