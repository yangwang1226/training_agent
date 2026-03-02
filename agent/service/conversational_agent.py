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

from dotenv import load_dotenv
load_dotenv()

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
    extended_info: Dict[str, str] = field(default_factory=dict)
    extended_questions: List[str] = field(default_factory=list)
    extended_info_sufficient: bool = False
    dimensions: List[Dict] = field(default_factory=list)
    dimensions_confirmed: bool = False
    training_goal: str = ""
    
    def __post_init__(self):
        self.collected_info = {
            "industry": False,
            "role": False,
            "intent": False,
            "questions": False
        }
    
    def is_complete(self) -> bool:
        basic_complete = all(self.collected_info.values())
        extended_complete = self.extended_info_sufficient or len(self.extended_info) >= 2
        return basic_complete and extended_complete
    
    def is_ready_for_dimensions(self) -> bool:
        basic_complete = all(self.collected_info.values())
        extended_complete = self.extended_info_sufficient or len(self.extended_info) >= 2
        return basic_complete and extended_complete
    
    def is_dimensions_confirmed(self) -> bool:
        return self.dimensions_confirmed and len(self.dimensions) > 0
    
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
    
    def get_extended_info_summary(self) -> str:
        if not self.extended_info:
            return ""
        return "\n".join([f"- {k}: {v}" for k, v in self.extended_info.items()])


class InfoExtraction(BaseModel):
    industry: Optional[str] = Field(default=None, description="识别出的行业")
    role_type: Optional[str] = Field(default=None, description="AI需要模拟的角色类型")
    role_description: Optional[str] = Field(default=None, description="角色描述")
    purchase_intent: Optional[str] = Field(default=None, description="购买意愿：冷淡/一般/感兴趣/非常感兴趣")
    custom_questions: Optional[List[str]] = Field(default=None, description="用户期望的问题列表")
    additional_requirements: Optional[str] = Field(default=None, description="其他要求")
    extended_info: Optional[Dict[str, str]] = Field(default=None, description="延展信息，如车型、预算、城市等")
    extended_info_sufficient: Optional[bool] = Field(default=None, description="延展信息是否已经足够丰富")


class ExtendedInfoJudge(BaseModel):
    need_more_info: bool = Field(description="是否需要继续收集延展信息")
    next_question: Optional[str] = Field(default=None, description="下一个建议询问的问题")
    reason: str = Field(description="判断理由")
    current_extended_info: Dict[str, str] = Field(default_factory=dict, description="当前已收集的延展信息")


SYSTEM_PROMPT = """你是一个友好的提示词生成助手，通过自然对话的方式收集用户需求信息。

你的任务是通过对话了解以下信息：

【基础信息】（必须收集）
1. 行业：用户所在的行业领域（如教育培训、房地产、汽车、金融、客服、安保、心理咨询等）
2. 角色：用户希望AI模拟的角色（如家长、购房者、购车者、客户、学生、患者等）
3. 购买意愿：模拟客户的购买意愿程度（冷淡/一般/感兴趣/非常感兴趣）
4. 问题：用户期望AI提出的问题，或者让系统自动生成

【延展信息】（根据行业特点智能收集）
当基础信息收集完成后，你需要根据行业特点，主动询问更多背景信息，让生成的提示词更加丰富和真实。

【培训目标】（可选）
询问用户的培训目标，如"提升沟通能力"、"学习异议处理"等。

延展信息收集原则：
- 根据行业特点设计针对性的问题，每个行业关注点不同
- 一次只问一个问题，自然地引导用户
- 收集2-4个关键延展信息即可，不要过于冗长
- 用户如果表示"不需要"或"随便"，可以跳过继续下一个问题

各行业延展信息示例（仅供参考，根据实际情况灵活调整）：
- 汽车行业：咨询的车型/品牌、预算范围、新车还是二手车、购车用途等
- 房地产行业：目标城市/区域、预算范围、学区需求、户型偏好等
- 教育培训行业：学生年级、学科、学习目标、当前水平等
- 金融行业：投资类型、风险偏好、资金规模、投资目标等
- 客服行业：问题类型、客户情绪、服务场景等
- 安保行业：工作场景、安全风险、应急类型等
- 心理咨询：来访者问题类型、情绪状态、咨询目标等
- 其他行业：根据行业特点自行判断关键信息

对话风格要求：
- 像朋友聊天一样自然，不要像在填表或审问
- 一次只问一个问题，等待用户回答后再继续
- 根据用户的回答灵活调整对话方向
- 如果用户提供了部分信息，先确认理解是否正确
- 基础信息收集完成后，自然过渡到延展信息收集
- 当延展信息收集足够后，告诉用户可以开始生成提示词

请以JSON格式返回你的回答，包含以下字段：
- "content"：你的问题或回答内容
- "options"：如果是需要用户选择的问题，填写选项数组；如果不是选择问题，填写空数组

示例1（选择问题）：
{
  "content": "好的，是哪个行业的培训呢？",
  "options": ["房地产", "汽车", "教育", "金融", "客服", "安保", "心理咨询", "其他"]
}

示例2（非选择问题）：
{
  "content": "了解了，没有特别的问题，我会帮您自动生成。",
  "options": []
}
"""


class ConversationalPromptAgent:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.state = ConversationState()
        self.messages: List = [SystemMessage(content=SYSTEM_PROMPT)]
        
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen3.5-plus")
        self.generation = MultiModalConversation
    
    def _call_model(self, messages: List, temperature: float = 0.7) -> str:
        """调用通义千问API"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": [{"text": msg.content}]})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": [{"text": msg.content}]})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": [{"text": msg.content}]})
            elif isinstance(msg, dict):
                if isinstance(msg.get("content"), list):
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({"role": msg.get("role", "user"), "content": [{"text": msg.get("content", "")}]})
            else:
                formatted_messages.append({"role": "user", "content": [{"text": str(msg)}]})
        
        response = self.generation.call(
            model=self.llm_model,
            enable_thinking=False,
            messages=formatted_messages
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        self.messages.append(HumanMessage(content=user_input))
        
        extraction_result = self._extract_info(user_input)
        self._update_state(extraction_result)
        
        if self._is_confirming_dimensions(user_input):
            return self._handle_dimension_confirmation(user_input)
        
        if self.state.is_ready_for_dimensions() and not self.state.dimensions:
            return self._generate_and_show_dimensions()
        
        response_content = self._call_model(self.messages, temperature=0.7)
        self.messages.append(AIMessage(content=response_content))
        
        content = response_content
        options = []
            
        try:
            json_content = self._extract_json(content)
            parsed_response = json.loads(json_content)
            content = parsed_response.get('content', content)
            options = parsed_response.get('options', [])
        except Exception as e:
            logging.warning(f"解析JSON失败: {str(e)}")
        
        return {
            "content": content,
            "options": options,
            "show_dimensions": False
        }
    
    def _is_confirming_dimensions(self, user_input: str) -> bool:
        if not self.state.dimensions:
            return False
        confirm_keywords = ["确认", "可以", "没问题", "好的", "同意", "接受", "是", "对"]
        reject_keywords = ["重新", "换", "不行", "不好", "修改", "调整"]
        
        user_input_lower = user_input.lower()
        if any(kw in user_input_lower for kw in reject_keywords):
            return True
        if any(kw in user_input_lower for kw in confirm_keywords):
            return True
        return False
    
    def _handle_dimension_confirmation(self, user_input: str) -> Dict[str, Any]:
        user_input_lower = user_input.lower()
        reject_keywords = ["重新", "换", "不行", "不好", "修改", "调整"]
        
        if any(kw in user_input_lower for kw in reject_keywords):
            self.state.dimensions = []
            return self._generate_and_show_dimensions()
        
        self.state.dimensions_confirmed = True
        return {
            "content": "好的，维度已确认！现在可以生成完整的场景提示词了。点击「生成提示词」按钮即可。",
            "options": [],
            "show_dimensions": False,
            "dimensions_confirmed": True
        }
    
    def _generate_and_show_dimensions(self) -> Dict[str, Any]:
        from agent.evaluate_agent.dimension_generator import DimensionGenerator
        
        generator = DimensionGenerator()
        result = generator.generate_dimensions(
            industry=self.state.industry,
            role_type=self.state.role_type,
            role_description=self.state.role_description or self.state.background_info,
            training_goal=self.state.training_goal or f"提升{self.state.role_type}沟通能力"
        )
        
        if result.success:
            self.state.dimensions = [d.to_dict() for d in result.dimensions]
            
            dim_text = "我为您生成了以下考核维度，请确认：\n\n"
            for i, dim in enumerate(self.state.dimensions, 1):
                dim_text += f"**{i}. {dim['dimension_name']}** (权重: {dim['weight']*100:.0f}%)\n"
                for criterion, desc in dim.get('sub_criteria', {}).items():
                    dim_text += f"   - {criterion}: {desc}\n"
                dim_text += "\n"
            
            dim_text += "您可以直接确认，或者说「重新生成」来调整。"
            
            return {
                "content": dim_text,
                "options": ["确认，继续", "重新生成"],
                "show_dimensions": True,
                "dimensions": self.state.dimensions
            }
        else:
            return {
                "content": f"维度生成遇到问题: {result.error_message}，将使用默认维度继续。",
                "options": ["继续"],
                "show_dimensions": False
            }
    
    def _extract_info(self, user_input: str) -> Dict[str, Any]:
        extended_info_summary = self.state.get_extended_info_summary()
        
        extraction_prompt = f"""从以下用户输入中提取信息，如果某项信息未提及则返回null：

用户输入：{user_input}

当前已收集基础信息：
- 行业：{self.state.industry or '未收集'}
- 角色：{self.state.role_type or '未收集'}
- 购买意愿：{self.state.purchase_intent or '未收集'}
- 自定义问题：{self.state.custom_questions or '未收集'}

当前已收集延展信息：
{extended_info_summary or '暂无'}

请返回JSON格式的提取结果。注意：extended_info字段用于提取行业相关的背景信息（如汽车行业的车型、预算；房地产行业的城市、户型等）。"""
        
        try:
            parser = JsonOutputParser(pydantic_object=InfoExtraction)
            response_content = self._call_model(
                [HumanMessage(content=extraction_prompt + "\n\n" + parser.get_format_instructions())]
            )
            return parser.parse(response_content)
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
        
        if extraction_result.get("extended_info"):
            for key, value in extraction_result["extended_info"].items():
                if value:
                    self.state.extended_info[key] = value
        
        if self.state.collected_info.get("industry") and self.state.collected_info.get("role"):
            self.state.collected_info["questions"] = True
        
        if extraction_result.get("extended_info_sufficient") is not None:
            self.state.extended_info_sufficient = extraction_result["extended_info_sufficient"]
        
        self._check_extended_info_complete()
    
    def _check_extended_info_complete(self):
        basic_info_complete = (
            self.state.collected_info.get("industry") and
            self.state.collected_info.get("role") and
            self.state.collected_info.get("intent") and
            self.state.collected_info.get("questions")
        )
        
        if not basic_info_complete:
            return
        
        if self.state.extended_info_sufficient:
            return
        
        if len(self.state.extended_info) >= 2:
            self.state.extended_info_sufficient = True
            return
        
        judge_result = self._judge_extended_info()
        
        if not judge_result.get("need_more_info", True):
            self.state.extended_info_sufficient = True
            if judge_result.get("current_extended_info"):
                for key, value in judge_result["current_extended_info"].items():
                    if value:
                        self.state.extended_info[key] = value
    
    def _judge_extended_info(self) -> Dict[str, Any]:
        extended_info_summary = self.state.get_extended_info_summary()
        
        prompt = f"""请判断当前延展信息是否足够丰富，能否生成高质量的提示词。

行业：{self.state.industry}
角色：{self.state.role_type}
购买意愿：{self.state.purchase_intent}

当前已收集的延展信息：
{extended_info_summary or '暂无'}

判断标准：
1. 根据行业特点，判断是否收集了关键的背景信息
2. 汽车行业：车型/品牌、预算、新车/二手车等至少收集2项
3. 房地产行业：城市/区域、预算、户型等至少收集2项
4. 教育培训：年级、学科、学习目标等至少收集2项
5. 其他行业：根据行业特点判断，至少收集2项关键信息
6. 如果用户明确表示"不需要"或"随便"，也可以认为足够

请返回JSON格式的判断结果。"""
        
        try:
            parser = JsonOutputParser(pydantic_object=ExtendedInfoJudge)
            response_content = self._call_model(
                [HumanMessage(content=prompt + "\n\n" + parser.get_format_instructions())]
            )
            return parser.parse(response_content)
        except Exception as e:
            logging.error(f"延展信息判断失败: {str(e)}")
            if len(self.state.extended_info) >= 2:
                return {"need_more_info": False, "reason": "已收集足够信息"}
            return {"need_more_info": True, "reason": "需要更多信息"}
    
    def is_ready_to_generate(self) -> bool:
        return self.state.is_complete() and self.state.is_dimensions_confirmed()
    
    def get_current_state(self) -> ConversationState:
        return self.state
    
    def generate_prompt(self, skip_dimensions: bool = False) -> str:
        if not self.state.is_complete():
            missing = self.state.get_missing_info()
            return f"还需要收集以下信息：{', '.join(missing)}"
        
        if not skip_dimensions and not self.state.is_dimensions_confirmed():
            return "请先确认考核维度后再生成提示词"
        
        logging.info("=" * 50)
        logging.info("开始生成提示词...")
        logging.info(f"行业: {self.state.industry}")
        logging.info(f"角色: {self.state.role_type}")
        logging.info(f"购买意愿: {self.state.purchase_intent}")
        logging.info(f"延展信息: {self.state.extended_info}")
        logging.info(f"考核维度: {len(self.state.dimensions)} 个")
        logging.info("=" * 50)
        
        self._generate_questions()
        self._generate_trigger_groups()
        self._generate_emotion()
        
        logging.info("正在构建完整提示词...")
        result = self._build_full_prompt()
        logging.info("提示词生成完成!")
        
        return result
    
    def _generate_questions(self):
        logging.info("步骤1: 生成主问题列表...")
        
        if self.state.custom_questions:
            logging.info("使用用户自定义问题")
            self.state.main_questions = [
                {"question": q, "order": i + 1}
                for i, q in enumerate(self.state.custom_questions)
            ]
            return
        
        extended_info_summary = self.state.get_extended_info_summary()
        
        prompt = f"""你是一个专业的销售培训场景设计专家。现在需要生成客户向销售/顾问提出的问题列表。

场景背景：
- 行业：{self.state.industry}
- AI模拟的角色：{self.state.role_type}（客户）
- 购买意愿：{self.state.purchase_intent}
- 其他要求：{self.state.additional_requirements or '无'}

延展背景信息：
{extended_info_summary or '无'}

重要说明：
1. 这些问题是AI模拟的客户向销售/顾问提出的问题，用于训练销售的话术和应变能力
2. 问题必须口语化、接地气，像普通客户在电话里会问的话
3. 避免专业术语，用通俗易懂的表达
4. 问题要简短直接，不要太长太复杂
5. 问题要涵盖客户关心的各个方面（价格、服务、效果、对比等）
6. 问题数量必须不少于10个，根据购买意愿适当增加
7. 问题要结合延展背景信息，体现具体场景（如特定车型、预算范围、城市等）

问题风格示例：
- "这个多少钱？"
- "你们和XX比有什么优势？"
- "要是出了问题找谁？"
- "能便宜点吗？"
- "有没有什么优惠活动？"

返回JSON格式：{{"main_questions": [{{"question": "问题", "order": 1}}], "background_info": "背景描述（客户的基本情况和需求，要结合延展信息）"}}"""
        
        try:
            logging.info("正在调用LLM生成问题...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.main_questions = result.get("main_questions", [])
            self.state.background_info = result.get("background_info", "")
            logging.info(f"成功生成 {len(self.state.main_questions)} 个问题")
            logging.info(f"背景信息: {self.state.background_info[:100]}..." if len(self.state.background_info) > 100 else f"背景信息: {self.state.background_info}")
        except Exception as e:
            logging.error(f"生成问题失败: {str(e)}")
            self.state.main_questions = []
    
    def _generate_trigger_groups(self):
        logging.info("步骤2: 生成关联问题分组...")
        
        if not self.state.main_questions:
            logging.warning("没有主问题，跳过关联问题生成")
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
            logging.info("正在调用LLM生成关联问题...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.trigger_groups = result.get("trigger_groups", [])
            logging.info(f"成功生成 {len(self.state.trigger_groups)} 个关联问题分组")
        except Exception as e:
            logging.error(f"生成关联问题失败: {str(e)}")
            self.state.trigger_groups = []
    
    def _generate_emotion(self):
        logging.info("步骤3: 生成情绪描述...")
        
        extended_info_summary = self.state.get_extended_info_summary()
        
        prompt = f"""根据角色和购买意愿生成情绪描述：

角色：{self.state.role_type}
购买意愿：{self.state.purchase_intent}
行业：{self.state.industry}

延展背景信息：
{extended_info_summary or '无'}

请结合以上信息，生成符合角色特点的情绪和说话风格。

返回JSON格式：{{"emotion_type": "情绪类型", "emotion_description": "情绪描述", "speaking_style": "说话风格", "attitude": "沟通态度"}}"""
        
        try:
            logging.info("正在调用LLM生成情绪描述...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回JSON格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.emotion_type = result.get("emotion_type", "平和")
            self.state.emotion_description = result.get("emotion_description", "")
            self.state.speaking_style = result.get("speaking_style", "")
            self.state.attitude = result.get("attitude", "")
            logging.info(f"情绪类型: {self.state.emotion_type}")
        except Exception as e:
            logging.error(f"生成情绪描述失败: {str(e)}")
    
    def _build_full_prompt(self) -> str:
        logging.info("正在加载模板...")
        template = self.template_manager.get_template("training_salse")
        if not template:
            logging.error("模板 training_salse 加载失败")
            return "模板加载失败"
        
        logging.info("模板加载成功，正在填充内容...")
        
        questions_text = "\n".join([
            f"{q.get('order', i+1)}. {q.get('question', '')}"
            for i, q in enumerate(self.state.main_questions)
        ])
        
        logging.info(f"问题列表已生成，共 {len(self.state.main_questions)} 个问题")
        
        trigger_groups_text = self._format_trigger_groups()
        
        emotion_text = f"""# 情绪与态度：
- 情绪基调：{self.state.emotion_type}
- 情绪描述：{self.state.emotion_description}
- 说话风格：{self.state.speaking_style}
- 沟通态度：{self.state.attitude}"""
        
        logging.info("正在填充背景信息...")
        result = self.template_manager.fill_background_info(template, self.state.background_info)
        
        logging.info("正在填充主问题列表...")
        result = self.template_manager.fill_main_questions(result, questions_text)
        
        logging.info("正在填充关联问题...")
        result = self.template_manager.fill_trigger_groups(result, trigger_groups_text)
        
        role_section_end = "---"
        role_end_idx = result.find(role_section_end)
        if role_end_idx != -1:
            result = result[:role_end_idx + len(role_section_end)] + "\n\n" + emotion_text + result[role_end_idx + len(role_section_end):]
        
        if self.state.dimensions:
            dimension_text = self._format_dimensions_for_prompt()
            result = result + "\n\n" + dimension_text
            logging.info("已添加考核维度信息到提示词")
        
        logging.info(f"提示词构建完成，总长度: {len(result)} 字符")
        
        return result
    
    def _format_dimensions_for_prompt(self) -> str:
        if not self.state.dimensions:
            return ""
        
        lines = ["# 考核维度说明", ""]
        lines.append("本次训练将按以下维度进行能力评估：")
        lines.append("")
        
        for dim in self.state.dimensions:
            lines.append(f"## {dim['dimension_name']} (权重: {dim['weight']*100:.0f}%)")
            lines.append("")
            lines.append("评估要点：")
            for criterion, desc in dim.get('sub_criteria', {}).items():
                lines.append(f"- {criterion}：{desc}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_dimension_config(self) -> Dict[str, Any]:
        return {
            "industry": self.state.industry,
            "role_type": self.state.role_type,
            "role_description": self.state.role_description,
            "training_goal": self.state.training_goal,
            "dimensions": self.state.dimensions
        }
    
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
