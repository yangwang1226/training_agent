import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .llm_client import LLMClient
from .template_manager import TemplateManager
from .models import BackgroundInfo, MainQuestion, TriggerGroup, FollowUpQuestion


class PurchaseIntent(Enum):
    COLD = "冷淡"
    NEUTRAL = "一般"
    INTERESTED = "感兴趣"
    VERY_INTERESTED = "非常感兴趣"


class EmotionType(Enum):
    CALM = "平和"
    ANXIOUS = "焦虑"
    IMPATIENT = "急躁"
    FRIENDLY = "友善"
    SUSPICIOUS = "多疑"
    DECISIVE = "果断"


@dataclass
class UserInfo:
    industry: str = ""
    role_type: str = ""
    purchase_intent: PurchaseIntent = PurchaseIntent.NEUTRAL
    custom_questions: List[str] = field(default_factory=list)
    auto_generate_questions: bool = True
    additional_requirements: str = ""


@dataclass
class InteractiveResult:
    success: bool
    full_prompt: str = ""
    user_info: Optional[UserInfo] = None
    error_message: str = ""


INDUSTRY_SYSTEM_PROMPT = """你是一个专业的行业分析助手。根据用户输入，识别用户所属的行业领域。

请从以下行业中选择最匹配的一个：
- 教育培训（K12、考研、留学等）
- 房地产（新房、二手房、租房等）
- 汽车（新车、二手车、汽车后市场等）
- 金融服务（银行、保险、理财等）
- 医疗健康（医院、诊所、体检等）
- 电商零售（线上商城、线下零售等）
- 旅游出行（旅行社、酒店、机票等）
- 其他

如果用户输入的行业不在上述列表中，请直接返回用户输入的行业名称。"""

INDUSTRY_USER_PROMPT = """用户输入：{user_input}

请严格按照以下JSON格式输出：
{{"industry": "识别出的行业"}}"""


ROLE_SYSTEM_PROMPT = """你是一个角色识别助手。根据用户描述，识别用户希望AI模拟的角色类型。

常见的角色类型包括：
- 家长/学生（教育场景）
- 购房者/租房者（房地产场景）
- 购车者（汽车场景）
- 投资者/借款人（金融场景）
- 患者/家属（医疗场景）
- 消费者（零售场景）
- 游客/旅客（旅游场景）

请根据用户描述识别角色，并生成角色描述。"""

ROLE_USER_PROMPT = """用户输入：{user_input}
行业：{industry}

请严格按照以下JSON格式输出：
{{
    "role_type": "角色类型",
    "role_description": "角色详细描述（一句话）"
}}"""


QUESTIONS_SYSTEM_PROMPT = """你是一个专业的销售培训场景设计专家。根据行业、角色和购买意愿，生成客户向销售/顾问提出的问题列表。

重要说明：
1. 这些问题是AI模拟的客户向销售/顾问提出的问题，用于训练销售的话术和应变能力
2. 问题必须口语化、接地气，像普通客户在电话里会问的话
3. 避免使用专业术语，用通俗易懂的表达方式
4. 问题要简短直接，不要太长太复杂
5. 问题要涵盖客户关心的各个方面（价格、服务、效果、对比、售后等）
6. 问题数量必须不少于10个

问题风格示例：
- 好的表达："这个多少钱？"、"你们和XX比有什么优势？"、"能便宜点吗？"、"要是出了问题找谁？"
- 不好的表达："请问该产品的定价策略是怎样的？"、"贵公司的核心竞争力体现在哪些方面？"
"""

QUESTIONS_USER_PROMPT = """行业：{industry}
AI模拟的角色：{role_type}（客户）
购买意愿：{purchase_intent}
自定义问题：{custom_questions}
其他要求：{additional_requirements}

请严格按照以下JSON格式输出，问题数量不少于10个：
{{
    "main_questions": [
        {{"question": "问题1", "order": 1}},
        {{"question": "问题2", "order": 2}}
    ],
    "background_info": "背景信息描述（包含客户的基本情况和需求，用口语化表达）"
}}"""


FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT = """你是一个关联问题生成专家。根据主问题列表和角色信息，生成关联问题分组。

关联问题是指：当销售/顾问回答某个主问题时，如果回答中包含特定的关键词，客户应该追问的问题。

重要要求：
1. 问题必须口语化、接地气，像普通人在日常对话中会说的话
2. 避免使用专业术语，用通俗易懂的表达方式
3. 问题要简短直接，不要太长太复杂
4. 关联问题应该像是在聊天中自然追问出来的

问题风格示例：
- 好的表达："那保养一次大概多少钱？"、"这车保值率怎么样？"
- 不好的表达："请问该车型的常规保养费用区间是多少？"、"该车型的二手车保值率数据如何？"

生成规则：
1. 每个分组针对一个或多个主问题
2. 触发关键词要具体、可识别
3. 关联问题要有逻辑性，是对回答的合理追问
4. 每个分组的关联问题数量控制在1-2个
5. 根据购买意愿调整关联问题的数量"""

FOLLOW_UP_QUESTIONS_USER_PROMPT = """角色：{role_type}
购买意愿：{purchase_intent}
主问题列表：
{main_questions_text}

请严格按照以下JSON格式输出：
{{
    "trigger_groups": [
        {{
            "group_name": "A",
            "trigger_keywords": ["关键词1", "关键词2"],
            "questions": [
                {{"question": "关联问题1", "order": 1}}
            ]
        }}
    ]
}}"""


EMOTION_SYSTEM_PROMPT = """你是一个情绪描述生成专家。根据角色的购买意愿和性格特点，生成该角色的情绪描述。

情绪描述应该包含：
1. 整体情绪基调（平和、焦虑、急躁等）
2. 说话语气特点
3. 对销售/顾问的态度
4. 决策风格

情绪要与购买意愿相匹配：
- 冷淡：不耐烦、想快速结束对话
- 一般：平和、有问有答
- 感兴趣：积极、愿意深入了解
- 非常感兴趣：热情、主动询问细节"""

EMOTION_USER_PROMPT = """角色：{role_type}
购买意愿：{purchase_intent}
行业：{industry}

请严格按照以下JSON格式输出：
{{
    "emotion_type": "情绪类型",
    "emotion_description": "详细情绪描述",
    "speaking_style": "说话风格描述",
    "attitude": "对销售/顾问的态度"
}}"""


class InteractivePromptAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.template_manager = TemplateManager()
        self.user_info = UserInfo()
    
    def analyze_industry(self, user_input: str) -> str:
        user_prompt = INDUSTRY_USER_PROMPT.format(user_input=user_input)
        try:
            result = self.llm_client.call_with_json_output(
                INDUSTRY_SYSTEM_PROMPT, user_prompt
            )
            self.user_info.industry = result.get("industry", "")
            return self.user_info.industry
        except Exception as e:
            logging.error(f"分析行业失败: {str(e)}")
            return user_input
    
    def analyze_role(self, user_input: str) -> Dict[str, str]:
        user_prompt = ROLE_USER_PROMPT.format(
            user_input=user_input,
            industry=self.user_info.industry
        )
        try:
            result = self.llm_client.call_with_json_output(
                ROLE_SYSTEM_PROMPT, user_prompt
            )
            self.user_info.role_type = result.get("role_type", "")
            return {
                "role_type": result.get("role_type", ""),
                "role_description": result.get("role_description", "")
            }
        except Exception as e:
            logging.error(f"分析角色失败: {str(e)}")
            return {"role_type": user_input, "role_description": ""}
    
    def set_purchase_intent(self, intent: str) -> PurchaseIntent:
        intent_mapping = {
            "冷淡": PurchaseIntent.COLD,
            "一般": PurchaseIntent.NEUTRAL,
            "感兴趣": PurchaseIntent.INTERESTED,
            "非常感兴趣": PurchaseIntent.VERY_INTERESTED
        }
        self.user_info.purchase_intent = intent_mapping.get(intent, PurchaseIntent.NEUTRAL)
        return self.user_info.purchase_intent
    
    def set_custom_questions(self, questions: List[str], auto_generate: bool = True):
        self.user_info.custom_questions = questions
        self.user_info.auto_generate_questions = auto_generate
    
    def generate_questions_and_background(self) -> Dict[str, Any]:
        custom_questions_str = "、".join(self.user_info.custom_questions) if self.user_info.custom_questions else "无"
        
        user_prompt = QUESTIONS_USER_PROMPT.format(
            industry=self.user_info.industry,
            role_type=self.user_info.role_type,
            purchase_intent=self.user_info.purchase_intent.value,
            custom_questions=custom_questions_str,
            additional_requirements=self.user_info.additional_requirements or "无"
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                QUESTIONS_SYSTEM_PROMPT, user_prompt
            )
            return result
        except Exception as e:
            logging.error(f"生成问题和背景失败: {str(e)}")
            return {"main_questions": [], "background_info": ""}
    
    def generate_follow_up_questions(self, main_questions: List[Dict]) -> List[TriggerGroup]:
        main_questions_text = "\n".join([
            f"{q.get('order', i+1)}. {q.get('question', '')}"
            for i, q in enumerate(main_questions)
        ])
        
        user_prompt = FOLLOW_UP_QUESTIONS_USER_PROMPT.format(
            role_type=self.user_info.role_type,
            purchase_intent=self.user_info.purchase_intent.value,
            main_questions_text=main_questions_text
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT, user_prompt
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
    
    def generate_emotion(self) -> Dict[str, str]:
        user_prompt = EMOTION_USER_PROMPT.format(
            role_type=self.user_info.role_type,
            purchase_intent=self.user_info.purchase_intent.value,
            industry=self.user_info.industry
        )
        
        try:
            result = self.llm_client.call_with_json_output(
                EMOTION_SYSTEM_PROMPT, user_prompt
            )
            return result
        except Exception as e:
            logging.error(f"生成情绪描述失败: {str(e)}")
            return {
                "emotion_type": "平和",
                "emotion_description": "情绪稳定，态度平和",
                "speaking_style": "语气平和，表达清晰",
                "attitude": "保持礼貌，理性沟通"
            }
    
    def generate_full_prompt(self, template_name: str = "training_teacher") -> InteractiveResult:
        try:
            logging.info("开始生成问题和背景信息...")
            qa_result = self.generate_questions_and_background()
            
            main_questions_data = qa_result.get("main_questions", [])
            background_text = qa_result.get("background_info", "")
            
            if not main_questions_data:
                return InteractiveResult(
                    success=False,
                    error_message="生成主问题列表失败"
                )
            
            main_questions = [
                MainQuestion(
                    question=q.get("question", ""),
                    order=q.get("order", i + 1)
                )
                for i, q in enumerate(main_questions_data)
            ]
            
            logging.info("开始生成关联问题...")
            trigger_groups = self.generate_follow_up_questions(main_questions_data)
            
            logging.info("开始生成情绪描述...")
            emotion_info = self.generate_emotion()
            
            questions_text = "\n".join([q.to_prompt_text() for q in main_questions])
            trigger_groups_text = "\n\n".join([group.to_prompt_text() for group in trigger_groups])
            
            emotion_text = self._format_emotion_text(emotion_info)
            
            full_prompt = self._build_full_prompt(
                template_name=template_name,
                background_text=background_text,
                questions_text=questions_text,
                trigger_groups_text=trigger_groups_text,
                emotion_text=emotion_text
            )
            
            return InteractiveResult(
                success=True,
                full_prompt=full_prompt,
                user_info=self.user_info
            )
            
        except Exception as e:
            logging.error(f"生成完整提示词失败: {str(e)}")
            return InteractiveResult(
                success=False,
                error_message=str(e)
            )
    
    def _format_emotion_text(self, emotion_info: Dict[str, str]) -> str:
        return f"""# 情绪与态度：
- 情绪基调：{emotion_info.get('emotion_type', '平和')}
- 情绪描述：{emotion_info.get('emotion_description', '情绪稳定')}
- 说话风格：{emotion_info.get('speaking_style', '语气平和')}
- 沟通态度：{emotion_info.get('attitude', '保持礼貌')}"""
    
    def _build_full_prompt(self, template_name: str, background_text: str,
                           questions_text: str, trigger_groups_text: str,
                           emotion_text: str) -> str:
        template = self.template_manager.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        result = self.template_manager.fill_background_info(template, background_text)
        result = self.template_manager.fill_main_questions(result, questions_text)
        result = self.template_manager.fill_trigger_groups(result, trigger_groups_text)
        
        role_section_end = "---"
        role_end_idx = result.find(role_section_end)
        if role_end_idx != -1:
            result = result[:role_end_idx + len(role_section_end)] + "\n\n" + emotion_text + result[role_end_idx + len(role_section_end):]
        
        return result
    
    def get_available_templates(self) -> List[str]:
        return self.template_manager.get_template_names()
    
    def set_additional_requirements(self, requirements: str):
        self.user_info.additional_requirements = requirements


def interactive_generate_prompt(
    industry: str,
    role_type: str,
    purchase_intent: str,
    custom_questions: Optional[List[str]] = None,
    auto_generate: bool = True,
    additional_requirements: str = "",
    template_name: str = "training_teacher"
) -> InteractiveResult:
    agent = InteractivePromptAgent()
    agent.analyze_industry(industry)
    agent.analyze_role(role_type)
    agent.set_purchase_intent(purchase_intent)
    if custom_questions:
        agent.set_custom_questions(custom_questions, auto_generate)
    if additional_requirements:
        agent.set_additional_requirements(additional_requirements)
    return agent.generate_full_prompt(template_name)
