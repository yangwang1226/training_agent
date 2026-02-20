import os
import json
import logging
from typing import Optional, List, Dict, Any, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
from operator import add

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from .template_manager import TemplateManager
from .models import MainQuestion, TriggerGroup, FollowUpQuestion


class PurchaseIntent(Enum):
    COLD = "冷淡"
    NEUTRAL = "一般"
    INTERESTED = "感兴趣"
    VERY_INTERESTED = "非常感兴趣"


@dataclass
class ConversationState:
    industry: str = ""
    role_type: str = ""
    role_description: str = ""
    purchase_intent: str = "一般"
    custom_questions: List[str] = field(default_factory=list)
    additional_requirements: str = ""
    emotion_type: str = ""
    emotion_description: str = ""
    speaking_style: str = ""
    attitude: str = ""
    background_info: str = ""
    main_questions: List[Dict] = field(default_factory=list)
    trigger_groups: List[Dict] = field(default_factory=list)
    collected_info: Dict[str, bool] = field(default_factory=dict)
    
    def __post_init__(self):
        self.collected_info = {
            "industry": False,
            "role": False,
            "intent": False,
            "questions": False
        }
    
    def is_complete(self) -> bool:
        return all(self.collected_info.values())
    
    def get_missing_info(self) -> List[str]:
        missing = []
        if not self.collected_info.get("industry"):
            missing.append("行业")
        if not self.collected_info.get("role"):
            missing.append("角色")
        if not self.collected_info.get("intent"):
            missing.append("购买意愿")
        if not self.collected_info.get("questions"):
            missing.append("问题列表")
        return missing


class InfoExtraction(BaseModel):
    industry: Optional[str] = Field(default=None, description="识别出的行业")
    role_type: Optional[str] = Field(default=None, description="AI需要模拟的角色类型")
    role_description: Optional[str] = Field(default=None, description="角色描述")
    purchase_intent: Optional[str] = Field(default=None, description="购买意愿：冷淡/一般/感兴趣/非常感兴趣")
    custom_questions: Optional[List[str]] = Field(default=None, description="用户期望的问题列表")
    additional_requirements: Optional[str] = Field(default=None, description="其他要求")


SYSTEM_PROMPT = """你是一个友好的提示词生成助手，通过自然对话的方式收集用户需求信息。

你的任务是通过对话了解以下信息：
1. 行业：用户所在的行业领域（如教育培训、房地产、汽车、金融等）
2. 角色：用户希望AI模拟的角色（如家长、购房者、购车者等）
3. 购买意愿：模拟客户的购买意愿程度（冷淡/一般/感兴趣/非常感兴趣）
4. 问题：用户期望AI提出的问题，或者让系统自动生成

对话风格要求：
- 像朋友聊天一样自然，不要像在填表或审问
- 一次只问一个问题，等待用户回答后再继续
- 根据用户的回答灵活调整对话方向
- 如果用户提供了部分信息，先确认理解是否正确
- 当收集到足够信息后，告诉用户可以开始生成提示词

示例对话：
用户：我想生成一个销售培训的提示词
助手：好的，是哪个行业的销售培训呢？比如房产、汽车、教育还是其他？

用户：汽车销售
助手：明白了，汽车销售培训。那您希望AI模拟什么角色呢？比如购车者、试驾客户？

用户：购车者
助手：好的，购车者角色。那这个购车者的购买意愿是怎样的呢？
- 比较冷淡，只是随便看看
- 一般，有购车意向但还在对比
- 感兴趣，已经看中了某款车
- 非常感兴趣，准备下单了

用户：感兴趣
助手：了解了。您有没有特别想让AI提出的问题？比如关于价格、配置、售后这些？如果没有的话我可以帮您自动生成。

用户：没有，自动生成吧
助手：好的，我已经收集到所有需要的信息了：
- 行业：汽车销售
- 角色：购车者
- 购买意愿：感兴趣
- 问题：自动生成

现在可以为您生成提示词了，请回复"开始生成"或者还有其他需要补充的？
"""


class ConversationalPromptAgent:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.state = ConversationState()
        self.messages: List = [SystemMessage(content=SYSTEM_PROMPT)]
        
        self.llm = AzureChatOpenAI(
            azure_deployment='gpt-4o',
            api_key="c8575027653b42b1b47747f0b4ab135b",
            azure_endpoint="https://menshen.test.xdf.cn/",
            api_version="2024-12-01-preview",
            temperature=0.7
        )
        
        self.extraction_llm = AzureChatOpenAI(
            azure_deployment='gpt-4o',
            api_key="c8575027653b42b1b47747f0b4ab135b",
            azure_endpoint="https://menshen.test.xdf.cn/",
            api_version="2024-12-01-preview",
            temperature=0
        )
    
    def chat(self, user_input: str) -> str:
        self.messages.append(HumanMessage(content=user_input))
        
        extraction_result = self._extract_info(user_input)
        self._update_state(extraction_result)
        
        response = self.llm.invoke(self.messages)
        self.messages.append(AIMessage(content=response.content))
        
        return response.content
    
    def _extract_info(self, user_input: str) -> Dict[str, Any]:
        extraction_prompt = f"""从以下用户输入中提取信息，如果某项信息未提及则返回null：

用户输入：{user_input}

当前已收集信息：
- 行业：{self.state.industry or '未收集'}
- 角色：{self.state.role_type or '未收集'}
- 购买意愿：{self.state.purchase_intent or '未收集'}
- 自定义问题：{self.state.custom_questions or '未收集'}

请返回JSON格式的提取结果。"""
        
        try:
            parser = JsonOutputParser(pydantic_object=InfoExtraction)
            response = self.extraction_llm.invoke(
                [HumanMessage(content=extraction_prompt + "\n\n" + parser.get_format_instructions())]
            )
            return parser.parse(response.content)
        except Exception as e:
            logging.error(f"信息提取失败: {str(e)}")
            return {}
    
    def _update_state(self, extraction_result: Dict[str, Any]):
        if extraction_result.get("industry"):
            self.state.industry = extraction_result["industry"]
            self.state.collected_info["industry"] = True
        
        if extraction_result.get("role_type"):
            self.state.role_type = extraction_result["role_type"]
            self.state.collected_info["role"] = True
        
        if extraction_result.get("role_description"):
            self.state.role_description = extraction_result["role_description"]
        
        if extraction_result.get("purchase_intent"):
            intent = extraction_result["purchase_intent"]
            valid_intents = ["冷淡", "一般", "感兴趣", "非常感兴趣"]
            if intent in valid_intents:
                self.state.purchase_intent = intent
                self.state.collected_info["intent"] = True
        
        if extraction_result.get("custom_questions"):
            self.state.custom_questions = extraction_result["custom_questions"]
            self.state.collected_info["questions"] = True
        
        if extraction_result.get("additional_requirements"):
            self.state.additional_requirements = extraction_result["additional_requirements"]
        
        if self.state.collected_info.get("industry") and self.state.collected_info.get("role"):
            self.state.collected_info["questions"] = True
    
    def is_ready_to_generate(self) -> bool:
        return self.state.is_complete()
    
    def get_current_state(self) -> ConversationState:
        return self.state
    
    def generate_prompt(self) -> str:
        if not self.is_ready_to_generate():
            missing = self.state.get_missing_info()
            return f"还需要收集以下信息：{', '.join(missing)}"
        
        self._generate_questions()
        self._generate_trigger_groups()
        self._generate_emotion()
        
        return self._build_full_prompt()
    
    def _generate_questions(self):
        if self.state.custom_questions:
            self.state.main_questions = [
                {"question": q, "order": i + 1}
                for i, q in enumerate(self.state.custom_questions)
            ]
            return
        
        prompt = f"""你是一个专业的销售培训场景设计专家。现在需要生成客户向销售/顾问提出的问题列表。

场景背景：
- 行业：{self.state.industry}
- AI模拟的角色：{self.state.role_type}（客户）
- 购买意愿：{self.state.purchase_intent}
- 其他要求：{self.state.additional_requirements or '无'}

重要说明：
1. 这些问题是AI模拟的客户向销售/顾问提出的问题，用于训练销售的话术和应变能力
2. 问题必须口语化、接地气，像普通客户在电话里会问的话
3. 避免专业术语，用通俗易懂的表达
4. 问题要简短直接，不要太长太复杂
5. 问题要涵盖客户关心的各个方面（价格、服务、效果、对比等）
6. 问题数量必须不少于10个，根据购买意愿适当增加

问题风格示例：
- "这个多少钱？"
- "你们和XX比有什么优势？"
- "要是出了问题找谁？"
- "能便宜点吗？"
- "有没有什么优惠活动？"

返回JSON格式：{{"main_questions": [{{"question": "问题", "order": 1}}], "background_info": "背景描述（客户的基本情况和需求）"}}"""
        
        try:
            response = self.extraction_llm.invoke([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response.content))
            self.state.main_questions = result.get("main_questions", [])
            self.state.background_info = result.get("background_info", "")
        except Exception as e:
            logging.error(f"生成问题失败: {str(e)}")
            self.state.main_questions = []
    
    def _generate_trigger_groups(self):
        if not self.state.main_questions:
            return
        
        questions_text = "\n".join([
            f"{q.get('order', i+1)}. {q.get('question', '')}"
            for i, q in enumerate(self.state.main_questions)
        ])
        
        prompt = f"""根据主问题列表生成关联问题分组：

角色：{self.state.role_type}
购买意愿：{self.state.purchase_intent}
主问题列表：
{questions_text}

要求：
1. 问题口语化、接地气
2. 每个分组1-2个关联问题
3. 触发关键词要具体

返回JSON格式：{{"trigger_groups": [{{"group_name": "A", "trigger_keywords": ["关键词"], "questions": [{{"question": "问题", "order": 1}}]}}]}}"""
        
        try:
            response = self.extraction_llm.invoke([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response.content))
            self.state.trigger_groups = result.get("trigger_groups", [])
        except Exception as e:
            logging.error(f"生成关联问题失败: {str(e)}")
            self.state.trigger_groups = []
    
    def _generate_emotion(self):
        prompt = f"""根据角色和购买意愿生成情绪描述：

角色：{self.state.role_type}
购买意愿：{self.state.purchase_intent}
行业：{self.state.industry}

返回JSON格式：{{"emotion_type": "情绪类型", "emotion_description": "情绪描述", "speaking_style": "说话风格", "attitude": "沟通态度"}}"""
        
        try:
            response = self.extraction_llm.invoke([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response.content))
            self.state.emotion_type = result.get("emotion_type", "平和")
            self.state.emotion_description = result.get("emotion_description", "")
            self.state.speaking_style = result.get("speaking_style", "")
            self.state.attitude = result.get("attitude", "")
        except Exception as e:
            logging.error(f"生成情绪描述失败: {str(e)}")
    
    def _build_full_prompt(self) -> str:
        template = self.template_manager.get_template("training_salse")
        if not template:
            return "模板加载失败"
        
        questions_text = "\n".join([
            f"{q.get('order', i+1)}. {q.get('question', '')}"
            for i, q in enumerate(self.state.main_questions)
        ])
        
        trigger_groups_text = self._format_trigger_groups()
        
        emotion_text = f"""# 情绪与态度：
- 情绪基调：{self.state.emotion_type}
- 情绪描述：{self.state.emotion_description}
- 说话风格：{self.state.speaking_style}
- 沟通态度：{self.state.attitude}"""
        
        result = self.template_manager.fill_background_info(template, self.state.background_info)
        result = self.template_manager.fill_main_questions(result, questions_text)
        result = self.template_manager.fill_trigger_groups(result, trigger_groups_text)
        
        role_section_end = "---"
        role_end_idx = result.find(role_section_end)
        if role_end_idx != -1:
            result = result[:role_end_idx + len(role_section_end)] + "\n\n" + emotion_text + result[role_end_idx + len(role_section_end):]
        
        return result
    
    def _format_trigger_groups(self) -> str:
        if not self.state.trigger_groups:
            return ""
        
        groups_text = []
        for group in self.state.trigger_groups:
            keywords_str = "、".join([f'"{kw}"' for kw in group.get("trigger_keywords", [])])
            questions_text = "\n\t\t".join([
                f"{q.get('order', i+1)}. {q.get('question', '')}"
                for i, q in enumerate(group.get("questions", []))
            ])
            
            group_text = f"""\t分组{group.get('group_name', 'A')}:
\t- 对方话术中触发问题的关键信息：{keywords_str}
\t- 触发问题列表的提问方式：按该分组中【触发问题列表】中标号顺序提问
\t- 触发问题列表：
\t\t{questions_text}"""
            groups_text.append(group_text)
        
        return "\n\n".join(groups_text)
    
    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        start_idx = text.find("{")
        if start_idx == -1:
            return text
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\' and in_string:
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start_idx:i + 1]
        
        return text[start_idx:]
    
    def reset(self):
        self.state = ConversationState()
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
