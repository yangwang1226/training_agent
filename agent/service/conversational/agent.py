import os
import json
import logging
from typing import Optional, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from dotenv import load_dotenv
load_dotenv()

from ..template_manager import TemplateManager
from .state import ConversationState
from .models import InfoExtraction, ExtendedInfoJudge
from .prompts import SYSTEM_PROMPT, get_customer_questions_prompt, get_service_provider_questions_prompt


SERVICE_PROVIDER_ROLES = ["访客", "快递员", "外卖员", "送货员", "维修人员", "安装师傅", "保洁", "家政"]


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

        if self._should_ask_questions():
            self._inject_role_context_for_questions()

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
            logging.warning(f"解析 JSON 失败：{str(e)}")

        return {
            "content": content,
            "options": options,
            "show_dimensions": False
        }

    def _should_ask_questions(self) -> bool:
        basic_info_complete = (
            self.state.collected_info.get("industry") and
            self.state.collected_info.get("role") and
            self.state.collected_info.get("intent")
        )
        questions_not_collected = not self.state.collected_info.get("questions")
        return basic_info_complete and questions_not_collected

    def _inject_role_context_for_questions(self):
        role_lower = self.state.role_type.lower() if self.state.role_type else ""
        is_service_provider = any(r in role_lower for r in SERVICE_PROVIDER_ROLES)

        if is_service_provider:
            context_message = HumanMessage(content=f"""当前角色是"{self.state.role_type}"，这是一个服务提供者角色。

在询问用户希望 AI 提出什么问题时，请注意：
1. AI 将模拟服务人员（如访客、快递员等）
2. 被培训人员是前台/接待人员/保安
3. 因此示例问题应该是服务人员会说的话，而不是接待人员会问的问题

正确的示例问题：
- 访客："我是来拜访张经理的，约好了下午两点。"、"我找市场部，请问在几楼？"
- 快递员："有您的快递，麻烦签收一下。"、"这个包裹需要本人签收，请问收件人在吗？"
- 外卖员："您的外卖到了，请问放在前台还是送上去？"
- 维修人员："我是来修空调的，请问是哪一台？"

请根据角色类型给出合适的示例问题。""")
        else:
            context_message = HumanMessage(content=f"""当前角色是"{self.state.role_type}"，这是一个客户/咨询者角色。

在询问用户希望 AI 提出什么问题时，请注意：
1. AI 将模拟客户/咨询者
2. 被培训人员是销售/顾问/服务人员
3. 因此示例问题应该是客户会问的问题

示例问题：
- "这个多少钱？"
- "你们和 XX 比有什么优势？"
- "能便宜点吗？"
- "有没有什么优惠活动？"

请根据角色类型给出合适的示例问题。""")

        self.messages.append(context_message)
        self.messages.append(AIMessage(content='{"content": "明白了，我会根据角色类型给出合适的示例问题。", "options": []}'))

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
            self.state.dimensions_confirmed = False
            return self._generate_and_show_dimensions()
        
        self.state.dimensions_confirmed = True
        logging.info(f"维度已确认，当前维度数量：{len(self.state.dimensions)}")
        logging.info(f"is_complete: {self.state.is_complete()}, is_dimensions_confirmed: {self.state.is_dimensions_confirmed()}")
        
        return {
            "content": "好的，维度已确认！现在可以点击底部的「开始生成」按钮生成完整的场景提示词了。",
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
                dim_text += f"**{i}. {dim['dimension_name']}** (权重：{dim['weight']*100:.0f}%)\n"
                for criterion, desc in dim.get('sub_criteria', {}).items():
                    dim_text += f"   - {criterion}: {desc}\n"
                dim_text += "\n"
            
            dim_text += "您可以回复「确认」或「重新生成」来调整。"
            
            return {
                "content": dim_text,
                "options": ["确认，继续", "重新生成"],
                "show_dimensions": True,
                "dimensions": self.state.dimensions
            }
        else:
            self.state.dimensions_confirmed = True
            self.state.dimensions = [
                {"dimension_name": "沟通能力", "weight": 0.3, "sub_criteria": {"表达清晰": "语言流畅，逻辑清晰", "倾听理解": "准确理解对方意图"}},
                {"dimension_name": "专业素养", "weight": 0.3, "sub_criteria": {"专业知识": "熟悉产品/服务知识", "问题解决": "有效解决客户问题"}},
                {"dimension_name": "服务态度", "weight": 0.4, "sub_criteria": {"礼貌待人": "态度友好，用语礼貌", "耐心细致": "耐心解答，关注细节"}}
            ]
            return {
                "content": f"维度生成遇到问题：{result.error_message}，已使用默认维度。请点击底部的「开始生成」按钮继续。",
                "options": [],
                "show_dimensions": False,
                "dimensions_confirmed": True
            }

    def _extract_info(self, user_input: str) -> Dict[str, Any]:
        extended_info_summary = self.state.get_extended_info_summary()
        
        extraction_prompt = f"""从以下用户输入中提取信息，如果某项信息未提及则返回 null：

用户输入：{user_input}

当前已收集基础信息：
- 行业：{self.state.industry or '未收集'}
- 角色：{self.state.role_type or '未收集'}
- 购买意愿：{self.state.purchase_intent or '未收集'}
- 自定义问题：{self.state.custom_questions or '未收集'}

当前已收集延展信息：
{extended_info_summary or '暂无'}

请返回 JSON 格式的提取结果。注意：extended_info 字段用于提取行业相关的背景信息（如汽车行业的车型、预算；房地产行业的城市、户型等）。"""
        
        try:
            parser = JsonOutputParser(pydantic_object=InfoExtraction)
            response_content = self._call_model(
                [HumanMessage(content=extraction_prompt + "\n\n" + parser.get_format_instructions())]
            )
            return parser.parse(response_content)
        except Exception as e:
            logging.error(f"信息提取失败：{str(e)}")
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
        
        # 当行业、角色、意愿都收集完成后，标记问题已收集（即使用户没有明确指定）
        if (self.state.collected_info.get("industry") and 
            self.state.collected_info.get("role") and 
            self.state.collected_info.get("intent")):
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
2. 汽车行业：车型/品牌、预算、新车/二手车等至少收集 2 项
3. 房地产行业：城市/区域、预算、户型等至少收集 2 项
4. 教育培训：年级、学科、学习目标等至少收集 2 项
5. 其他行业：根据行业特点判断，至少收集 2 项关键信息
6. 如果用户明确表示"不需要"或"随便"，也可以认为足够

请返回 JSON 格式的判断结果。"""
        
        try:
            parser = JsonOutputParser(pydantic_object=ExtendedInfoJudge)
            response_content = self._call_model(
                [HumanMessage(content=prompt + "\n\n" + parser.get_format_instructions())]
            )
            return parser.parse(response_content)
        except Exception as e:
            logging.error(f"延展信息判断失败：{str(e)}")
            if len(self.state.extended_info) >= 2:
                return {"need_more_info": False, "reason": "已收集足够信息"}
            return {"need_more_info": True, "reason": "需要更多信息"}

    def is_ready_to_generate(self) -> bool:
        is_complete = self.state.is_complete()
        is_dim_confirmed = self.state.is_dimensions_confirmed()
        logging.info(f"is_ready_to_generate 检查:")
        logging.info(f"  - is_complete: {is_complete}")
        logging.info(f"    - collected_info: {self.state.collected_info}")
        logging.info(f"    - extended_info_sufficient: {self.state.extended_info_sufficient}")
        logging.info(f"    - extended_info count: {len(self.state.extended_info)}")
        logging.info(f"  - is_dimensions_confirmed: {is_dim_confirmed}")
        logging.info(f"    - dimensions_confirmed flag: {self.state.dimensions_confirmed}")
        logging.info(f"    - dimensions count: {len(self.state.dimensions)}")
        return is_complete and is_dim_confirmed

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
        logging.info(f"行业：{self.state.industry}")
        logging.info(f"角色：{self.state.role_type}")
        logging.info(f"购买意愿：{self.state.purchase_intent}")
        logging.info(f"延展信息：{self.state.extended_info}")
        logging.info(f"考核维度：{len(self.state.dimensions)} 个")
        logging.info("=" * 50)
        
        self._generate_questions()
        self._generate_trigger_groups()
        self._generate_emotion()
        
        logging.info("正在构建完整提示词...")
        result = self._build_full_prompt()
        logging.info("提示词生成完成!")
        
        return result

    def _generate_questions(self):
        logging.info("步骤 1: 生成主问题列表...")

        if self.state.custom_questions:
            logging.info("使用用户自定义问题")
            self.state.main_questions = [
                {"question": q, "order": i + 1}
                for i, q in enumerate(self.state.custom_questions)
            ]
            return

        extended_info_summary = self.state.get_extended_info_summary()
        role_lower = self.state.role_type.lower() if self.state.role_type else ""
        is_service_provider = any(r in role_lower for r in SERVICE_PROVIDER_ROLES)

        if is_service_provider:
            prompt = get_service_provider_questions_prompt(
                self.state.industry,
                self.state.role_type,
                self.state.purchase_intent,
                self.state.additional_requirements,
                extended_info_summary
            )
        else:
            prompt = get_customer_questions_prompt(
                self.state.industry,
                self.state.role_type,
                self.state.purchase_intent,
                self.state.additional_requirements,
                extended_info_summary
            )

        try:
            logging.info("正在调用 LLM 生成问题...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回 JSON 格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.main_questions = result.get("main_questions", [])
            self.state.background_info = result.get("background_info", "")
            logging.info(f"成功生成 {len(self.state.main_questions)} 个问题")
        except Exception as e:
            logging.error(f"生成问题失败：{str(e)}")
            self.state.main_questions = []

    def _generate_trigger_groups(self):
        logging.info("步骤 2: 生成关联问题分组...")

        if not self.state.main_questions:
            logging.warning("没有主问题，跳过关联问题生成")
            return

        questions_text = "\n".join([
            f"{q.get('order', i+1)}. {q.get('question', '')}"
            for i, q in enumerate(self.state.main_questions)
        ])

        prompt_parts = [
            "根据主问题列表生成关联问题分组:",
            "",
            f"角色：{self.state.role_type}",
            f"购买意愿：{self.state.purchase_intent}",
            "主问题列表:",
            questions_text,
            "",
            "要求:",
            "1. 问题口语化、接地气",
            "2. 每个分组 1-2 个关联问题",
            "3. 触发关键词要具体",
            "",
            '返回 JSON 格式：{"trigger_groups": [{"group_name": "A", "trigger_keywords": ["关键词"], "questions": [{"question": "问题", "order": 1}]}]}'
        ]
        prompt = "\n".join(prompt_parts)

        try:
            logging.info("正在调用 LLM 生成关联问题...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回 JSON 格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.trigger_groups = result.get("trigger_groups", [])
            logging.info(f"成功生成 {len(self.state.trigger_groups)} 个关联问题分组")
        except Exception as e:
            logging.error(f"生成关联问题失败：{str(e)}")
            self.state.trigger_groups = []

    def _generate_emotion(self):
        logging.info("步骤 3: 生成情绪描述...")
        
        extended_info_summary = self.state.get_extended_info_summary()
        
        prompt_parts = [
            "根据角色和购买意愿生成情绪描述:",
            "",
            f"角色：{self.state.role_type}",
            f"购买意愿：{self.state.purchase_intent}",
            f"行业：{self.state.industry}",
            "",
            "延展背景信息:",
            extended_info_summary or "无",
            "",
            "请结合以上信息，生成符合角色特点的情绪和说话风格。",
            "",
            '返回 JSON 格式：{"emotion_type": "情绪类型", "emotion_description": "情绪描述", "speaking_style": "说话风格", "attitude": "沟通态度"}'
        ]
        prompt = "\n".join(prompt_parts)
        
        try:
            logging.info("正在调用 LLM 生成情绪描述...")
            response_content = self._call_model([HumanMessage(content=prompt + "\n\n请返回 JSON 格式结果。")])
            result = json.loads(self._extract_json(response_content))
            self.state.emotion_type = result.get("emotion_type", "平和")
            self.state.emotion_description = result.get("emotion_description", "")
            self.state.speaking_style = result.get("speaking_style", "")
            self.state.attitude = result.get("attitude", "")
            logging.info(f"情绪类型：{self.state.emotion_type}")
        except Exception as e:
            logging.error(f"生成情绪描述失败：{str(e)}")

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
        
        emotion_text = "# 情绪与态度:\n"
        emotion_text += f"- 情绪基调：{self.state.emotion_type}\n"
        emotion_text += f"- 情绪描述：{self.state.emotion_description}\n"
        emotion_text += f"- 说话风格：{self.state.speaking_style}\n"
        emotion_text += f"- 沟通态度：{self.state.attitude}"
        
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
        
        logging.info(f"提示词构建完成，总长度：{len(result)} 字符")
        
        return result

    def _format_dimensions_for_prompt(self) -> str:
        if not self.state.dimensions:
            return ""
        
        lines = ["# 考核维度说明", ""]
        lines.append("本次训练将按以下维度进行能力评估：")
        lines.append("")
        
        for dim in self.state.dimensions:
            lines.append(f"## {dim['dimension_name']} (权重：{dim['weight']*100:.0f}%)")
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
            
            group_name = group.get('group_name', 'A')
            group_text = f"\t分组{group_name}:\n"
            group_text += f"\t- 对方话术中触发问题的关键信息：{keywords_str}\n"
            group_text += "\t- 触发问题列表的提问方式：按该分组中【触发问题列表】中标号顺序提问\n"
            group_text += "\t- 触发问题列表:\n"
            group_text += f"\t\t{questions_text}"
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
