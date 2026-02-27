import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .llm_client import LLMClient
from .template_manager import TemplateManager
from .models import MainQuestion, TriggerGroup, FollowUpQuestion


class PositionType(Enum):
    SALES = "销售"
    CUSTOMER_SERVICE = "客服"


class PersonalityType(Enum):
    COLD = "冷漠"
    NEUTRAL = "平淡"
    ENTHUSIASTIC = "热情"


class InterestLevel(Enum):
    LOW = "不感兴趣"
    NEUTRAL = "一般"
    HIGH = "感兴趣"


INDUSTRY_PRODUCTS = {
    "房地产": ["住宅", "别墅", "商铺", "写字楼", "其他"],
    "保险": ["寿险", "健康险", "车险", "意外险", "理财险", "其他"],
    "汽车": ["问界", "宝马", "奥迪", "蔚来", "保时捷", "奔驰", "比亚迪", "特斯拉", "理想", "大众", "其他"],
    "教育": ["K12辅导", "考研培训", "留学咨询", "职业培训", "兴趣班", "其他"]
}

INDUSTRIES = ["房地产", "保险", "汽车", "教育", "其他"]

PERSONALITIES = ["冷漠", "平淡", "热情"]

INTEREST_LEVELS = ["不感兴趣", "一般", "感兴趣"]


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
产品：{product}
AI模拟的角色：客户
客户性格：{personality}
感兴趣程度：{interest_level}
背景信息：{background_info}
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

生成规则：
1. 每个分组针对一个或多个主问题
2. 触发关键词要具体、可识别
3. 关联问题要有逻辑性，是对回答的合理追问
4. 每个分组的关联问题数量控制在1-2个
"""

FOLLOW_UP_QUESTIONS_USER_PROMPT = """客户性格：{personality}
感兴趣程度：{interest_level}
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


EMOTION_SYSTEM_PROMPT = """你是一个情绪描述生成专家。根据角色的性格特点和感兴趣程度，生成该角色的情绪描述。

情绪描述应该包含：
1. 整体情绪基调
2. 说话语气特点
3. 对销售/顾问的态度
4. 决策风格

情绪要与性格和感兴趣程度相匹配：
- 冷漠+不感兴趣：很不耐烦、想快速结束对话
- 冷漠+一般：冷淡、有问有答但不热情
- 冷漠+感兴趣：虽然不太热情但会认真询问
- 平淡+不感兴趣：不太想继续聊、礼貌但敷衍
- 平淡+一般：平和、有问有答
- 平淡+感兴趣：比较积极、愿意了解
- 热情+不感兴趣：虽然热情但不太想买
- 热情+一般：友好、愿意沟通
- 热情+感兴趣：非常积极、主动询问细节
"""

EMOTION_USER_PROMPT = """客户性格：{personality}
感兴趣程度：{interest_level}
行业：{industry}
产品：{product}

请严格按照以下JSON格式输出：
{{
    "emotion_type": "情绪类型",
    "emotion_description": "详细情绪描述",
    "speaking_style": "说话风格描述",
    "attitude": "对销售/顾问的态度"
}}"""


@dataclass
class UserInfo:
    position: PositionType = PositionType.SALES
    industry: str = ""
    product: str = ""
    personality: PersonalityType = PersonalityType.NEUTRAL
    interest_level: InterestLevel = InterestLevel.NEUTRAL
    background_info: str = ""
    auto_generate_background: bool = True
    custom_questions: List[str] = field(default_factory=list)
    auto_generate_questions: bool = True
    additional_requirements: str = ""


@dataclass
class InteractiveResult:
    success: bool
    full_prompt: str = ""
    user_info: Optional[UserInfo] = None
    error_message: str = ""


@dataclass
class ChatResponse:
    content: str
    options: List[str] = field(default_factory=list)
    next_step: Optional[str] = None
    show_input: bool = False
    show_background: bool = False


class InteractivePromptAgent:
    INDUSTRIES = INDUSTRIES
    INDUSTRY_PRODUCTS = INDUSTRY_PRODUCTS
    PERSONALITIES = PERSONALITIES
    INTEREST_LEVELS = INTEREST_LEVELS
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.template_manager = TemplateManager()
        self.llm_client = llm_client or LLMClient()
        self.user_info = UserInfo()
    
    def get_initial_message(self) -> ChatResponse:
        return ChatResponse(
            content="我是模拟客户智能体，可以帮您创建您想创建的客户对话场景。请先选择您的岗位：",
            options=self.get_position_options(),
            next_step="position"
        )
    
    def get_position_options(self) -> List[str]:
        return ["销售", "客服"]
    
    def set_position(self, position: str) -> bool:
        if position == "销售":
            self.user_info.position = PositionType.SALES
            return True
        elif position == "客服":
            self.user_info.position = PositionType.CUSTOMER_SERVICE
            return True
        return False
    
    def process_selection(self, step: str, value: str) -> ChatResponse:
        if step == "position":
            if self.set_position(value):
                return ChatResponse(
                    content=f"好的，您选择了{value}岗位。请问您所在的行业是？",
                    options=self.get_industry_options(),
                    next_step="industry"
                )
        elif step == "industry":
            self.set_industry(value)
            return ChatResponse(
                content=f"明白了，{value}行业。请问您要销售/服务的产品是？",
                options=self.get_product_options(),
                next_step="product"
            )
        elif step == "product":
            self.set_product(value)
            return ChatResponse(
                content=f"好的，{value}。请问您希望模拟客户的性格是？",
                options=self.get_personality_options(),
                next_step="personality"
            )
        elif step == "personality":
            if self.set_personality(value):
                return ChatResponse(
                    content=f"好的，客户性格{value}。请问模拟客户的感兴趣程度是？",
                    options=self.get_interest_level_options(),
                    next_step="interest_level"
                )
        elif step == "interest_level":
            if self.set_interest_level(value):
                return ChatResponse(
                    content=f"了解了，感兴趣程度{value}。请编辑模拟客户的背景信息（也可以自动生成）：",
                    next_step="background",
                    show_background=True
                )
        
        return ChatResponse(
            content="抱歉，处理您的选择时出现了问题。",
            options=[]
        )
    
    def get_industry_options(self) -> List[str]:
        return INDUSTRIES
    
    def set_industry(self, industry: str):
        self.user_info.industry = industry
    
    def get_product_options(self) -> List[str]:
        return INDUSTRY_PRODUCTS.get(self.user_info.industry, [])
    
    def set_product(self, product: str):
        self.user_info.product = product
    
    def get_personality_options(self) -> List[str]:
        return PERSONALITIES
    
    def set_personality(self, personality: str) -> bool:
        mapping = {
            "冷漠": PersonalityType.COLD,
            "平淡": PersonalityType.NEUTRAL,
            "热情": PersonalityType.ENTHUSIASTIC
        }
        if personality in mapping:
            self.user_info.personality = mapping[personality]
            return True
        return False
    
    def get_interest_level_options(self) -> List[str]:
        return INTEREST_LEVELS
    
    def set_interest_level(self, level: str) -> bool:
        mapping = {
            "不感兴趣": InterestLevel.LOW,
            "一般": InterestLevel.NEUTRAL,
            "感兴趣": InterestLevel.HIGH
        }
        if level in mapping:
            self.user_info.interest_level = mapping[level]
            return True
        return False
    
    def set_background_info(self, background_info: str):
        self.user_info.background_info = background_info
    
    def set_auto_generate_background(self, auto_generate: bool):
        self.user_info.auto_generate_background = auto_generate
    
    def set_custom_questions(self, questions: List[str], auto_generate: bool = True):
        self.user_info.custom_questions = questions
        self.user_info.auto_generate_questions = auto_generate
    
    def set_additional_requirements(self, requirements: str):
        self.user_info.additional_requirements = requirements
    
    def generate_questions_and_background(self) -> Dict[str, Any]:
        user_prompt = QUESTIONS_USER_PROMPT.format(
            industry=self.user_info.industry,
            product=self.user_info.product,
            personality=self.user_info.personality.value,
            interest_level=self.user_info.interest_level.value,
            background_info=self.user_info.background_info or "无",
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
            personality=self.user_info.personality.value,
            interest_level=self.user_info.interest_level.value,
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
            personality=self.user_info.personality.value,
            interest_level=self.user_info.interest_level.value,
            industry=self.user_info.industry,
            product=self.user_info.product
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
                "emotion_description": "情绪稳定",
                "speaking_style": "语气平和",
                "attitude": "保持礼貌"
            }
    
    def generate_full_prompt(self, template_name: str = "training_salse") -> InteractiveResult:
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


def interactive_generate_prompt(
    position: str,
    industry: str,
    product: str,
    personality: str,
    interest_level: str,
    background_info: str = "",
    template_name: str = "training_salse"
) -> InteractiveResult:
    agent = InteractivePromptAgent()
    agent.set_position(position)
    agent.set_industry(industry)
    agent.set_product(product)
    agent.set_personality(personality)
    agent.set_interest_level(interest_level)
    if background_info:
        agent.set_background_info(background_info)
    return agent.generate_full_prompt(template_name)
