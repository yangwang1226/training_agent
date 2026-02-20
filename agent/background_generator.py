import json
import logging
from typing import List, Optional
from .llm_client import LLMClient
from .models import BackgroundInfo


BACKGROUND_SYSTEM_PROMPT = """你是一个专业的背景信息生成助手。你的任务是根据用户提供的对话内容或描述，生成一个完整、合理的背景信息。

背景信息应该包含以下要素：
1. 学生姓名（可以使用化名，如"小明"、"小红"等）
2. 年级（如"初二"、"高一"等）
3. 性别
4. 学科（如"数学"、"英语"等）
5. 近期表现（学习成绩、课堂表现等）
6. 学习问题（具体的学习困难或问题）
7. 家长期望（家长对孩子的期望）

请确保生成的背景信息：
- 符合常理，具有真实性
- 与用户提供的对话内容相关
- 信息完整但不冗余"""

BACKGROUND_USER_PROMPT_TEMPLATE = """请根据以下内容生成背景信息：

{conversation}

{custom_requirements}

请严格按照以下JSON格式输出，不要添加任何其他内容：
{{
    "student_name": "学生姓名",
    "student_grade": "年级",
    "student_gender": "性别",
    "subject": "学科",
    "recent_performance": "近期表现描述",
    "learning_issues": ["问题1", "问题2"],
    "family_expectation": "家长期望",
    "other_info": ["其他信息1", "其他信息2"]
}}"""


class BackgroundGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(self, conversation: str, 
                 custom_requirements: Optional[str] = None) -> BackgroundInfo:
        user_prompt = BACKGROUND_USER_PROMPT_TEMPLATE.format(
            conversation=conversation,
            custom_requirements=custom_requirements or ""
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                BACKGROUND_SYSTEM_PROMPT,
                user_prompt
            )
            
            return BackgroundInfo(
                student_name=result.get("student_name", ""),
                student_grade=result.get("student_grade", ""),
                student_gender=result.get("student_gender", ""),
                subject=result.get("subject", ""),
                recent_performance=result.get("recent_performance", ""),
                learning_issues=result.get("learning_issues", []),
                family_expectation=result.get("family_expectation", ""),
                other_info=result.get("other_info", [])
            )
        except Exception as e:
            logging.error(f"生成背景信息失败: {str(e)}")
            return BackgroundInfo()
    
    async def async_generate(self, conversation: str,
                             custom_requirements: Optional[str] = None) -> BackgroundInfo:
        user_prompt = BACKGROUND_USER_PROMPT_TEMPLATE.format(
            conversation=conversation,
            custom_requirements=custom_requirements or ""
        )
        
        try:
            response = await self.llm_client.async_call(
                BACKGROUND_SYSTEM_PROMPT,
                user_prompt
            )
            json_str = self.llm_client._extract_json(response)
            json_str = self.llm_client._clean_json_string(json_str)
            result = json.loads(json_str)
            
            return BackgroundInfo(
                student_name=result.get("student_name", ""),
                student_grade=result.get("student_grade", ""),
                student_gender=result.get("student_gender", ""),
                subject=result.get("subject", ""),
                recent_performance=result.get("recent_performance", ""),
                learning_issues=result.get("learning_issues", []),
                family_expectation=result.get("family_expectation", ""),
                other_info=result.get("other_info", [])
            )
        except Exception as e:
            logging.error(f"异步生成背景信息失败: {str(e)}")
            return BackgroundInfo()
