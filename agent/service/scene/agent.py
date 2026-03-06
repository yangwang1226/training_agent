import os
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from dotenv import load_dotenv
load_dotenv()

from .models import (
    SceneContent, ConversationState, Dimension, MainQuestion,
    TriggerGroup, TriggerQuestion, EmotionProfile
)
from .prompts import (
    SYSTEM_PROMPT, INFO_EXTRACTION_PROMPT,
    CHAIN_OF_THOUGHT_BACKGROUND, CHAIN_OF_THOUGHT_QUESTIONS,
    CHAIN_OF_THOUGHT_TRIGGERS, CHAIN_OF_THOUGHT_DIMENSIONS,
    CHAIN_OF_THOUGHT_EMOTION
)

logger = logging.getLogger(__name__)


class SceneAgent:
    """
    场景智能体
    
    通过对话式交互收集场景信息，使用思维链能力生成完整的场景内容
    """
    
    def __init__(self):
        self.state = ConversationState()
        self.extract_info = None
        # self.messages: List = [SystemMessage(content=SYSTEM_PROMPT)]
        self.messages: List = [SystemMessage(content=INFO_EXTRACTION_PROMPT.format(
            user_input="",
            collected_info="暂无"
        ))]
        self.scene_content: Optional[SceneContent] = None
        
        # 初始化 LLM
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen3.5-plus")
        self.generation = MultiModalConversation

    def _call_model(self, messages: List, temperature: float = 0.7) -> str:
        """调用 Qwen 模型"""
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
            messages=formatted_messages,
            temperature=temperature
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")

    # def get_collected_info(self) -> Dict[str, Any]:
    #     """获取当前已经收集的信息"""
    #     info = None
    #     if self.state.collected_info.get("Industry", None):
    #         info = "已经收集了行业信息"
    #     if self.state.collected_info.get("Role", None):
    #         info = info + "\n" + "已经收集了角色信息"
    #     if self.state.collected_info.get("AiRole", None):
    #         info = info + "\n" + "已经收集了AI扮演的角色信息"
    #     if self.state.collected_info.get("Intent", None):
    #         info = info + "\n" + "已经收集了购买意愿信息"
    #     if self.state.collected_info.get("Questions", None):
    #         info = info + "\n" + "已经收集了问题列表信息"
    #     return info

    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        对话交互
        
        Args:
            user_input: 用户输入
            
        Returns:
            对话响应和状态信息
        """
        self.messages.append(HumanMessage(content=user_input))
        
        # 提取信息
        extraction_result = self._extract_info(user_input)
        # 根据提取结果拼接返回内容
        content_parts = ["感谢您的反馈，目前收到的信息包括："]
        missing_parts = []
        
        # 映射字段到中文描述
        field_map = {
            "industry": "所属行业",
            "training_role": "希望AI模拟的角色",
            "ai_role": "被训练者岗位",
            "training_scene": "训练场景的描述"
        }
        
        # 遍历提取结果，拼接已存在的信息
        for field, desc in field_map.items():
            item_obj = extraction_result.get(field, "")
            item_exist = item_obj.get("exist", False)
            if item_exist is True:
                content_parts.append(f"1.{desc}：{item_obj.get('content', '')}")
            else:
                missing_parts.append(f"【{desc}】")
        
        # 如果有缺失字段，拼接提示语句
        if missing_parts:
            content_parts.append("请您再介绍一下" + "、".join(missing_parts)
             + "，例如：“希望AI模拟购车客户，帮我生成一个用于训练问界汽车销售的训练场景，”谢谢。")
        
        response_content = "\n".join(content_parts)
        
        # 将拼接好的内容加入消息列表并返回
        self.messages.append(AIMessage(content=response_content))
        
        return {
            "content": response_content,
        }
        # self._update_state(extraction_result)
        
        # # 获取当前已经提取的信息
        # current_info = self.get_collected_info()
        # if current_info:
        #     self.messages.append(AIMessage(content=current_info))
        
        # # 正常对话回复
        # response_content = self._call_model(self.messages, temperature=0.7)
        # self.messages.append(AIMessage(content=response_content))
        
        # # 解析响应
        # content = response_content
        # # options = []
        # # multi_select = False
        
        # try:
        #     json_content = self._extract_json(content)
        #     parsed_response = json.loads(json_content)
        #     content = parsed_response.get('content', content)
        #     # options = parsed_response.get('options', [])
        #     # multi_select = parsed_response.get('multi_select', False)
        # except Exception as e:
        #     logger.warning(f"解析 JSON 失败：{str(e)}")
        
        # return {
        #     "content": content,
        #     # "options": options,
        #     # "multi_select": multi_select,
        #     # "is_ready": False,
        #     # "state": self._get_state()
        # }

    def _extract_info(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取信息"""
        prompt = INFO_EXTRACTION_PROMPT.format(
            user_input=user_input,
            collected_info=self.extract_info is None and "暂无" or json.dumps(self.extract_info)
        )
        
        try:
            # parser = JsonOutputParser()
            response_content = self._call_model(
                [HumanMessage(content=prompt + "\n\n请返回 JSON 格式结果。")]
            )
            self.extract_info = json.loads(self._extract_json(response_content))
            return self.extract_info
        except Exception as e:
            logger.error(f"信息提取失败：{str(e)}")
            return {}

    def _update_state(self, extraction_result: Dict[str, Any]):
        """更新状态"""
        if extraction_result.get("industry"):
            self.state.industry = extraction_result["industry"]
            self.state.collected_info["industry"] = True
        
        if extraction_result.get("role_type"):
            self.state.role_type = extraction_result["role_type"]
            self.state.collected_info["role"] = True
        
        # 更新 AI 角色
        if extraction_result.get("ai_role"):
            self.state.ai_role = extraction_result["ai_role"]
            self.state.collected_info["ai_role"] = True
        
        if extraction_result.get("role_description"):
            self.state.role_description = extraction_result["role_description"]
        
        if extraction_result.get("extended_info"):
            for key, value in extraction_result["extended_info"].items():
                if value:
                    self.state.extended_info[key] = value
        
        if extraction_result.get("additional_requirements"):
            self.state.additional_requirements = extraction_result["additional_requirements"]
        
        # 检查延展信息是否足够
        if len(self.state.extended_info) >= 2:
            self.state.extended_info_sufficient = True

    def _get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "industry": self.state.industry,
            "role_type": self.state.role_type,
            "ai_role": self.state.ai_role,  # AI 扮演的角色
            "role_description": self.state.role_description,
            "purchase_intent": self.state.purchase_intent,
            "custom_questions": self.state.custom_questions,
            "collected_info": self.state.collected_info,
            "missing_info": self.state.get_missing_info(),
            "extended_info": self.state.extended_info,
            "extended_info_sufficient": self.state.extended_info_sufficient,
            "is_ready": self.state.is_ready_for_generation()
        }

    def generate_scene_content(self) -> Optional[SceneContent]:
        """
        生成场景内容 (使用思维链)
        
        Returns:
            SceneContent 对象，如果生成失败则返回 None
        """
        try:
            logger.info("=" * 50)
            logger.info("开始生成场景内容...")
            logger.info(f"行业：{self.state.industry}")
            logger.info(f"角色：{self.state.role_type}")
            logger.info(f"延展信息：{len(self.state.extended_info)} 项")
            logger.info("=" * 50)
            
            # 1. 生成背景信息
            background_info = self._generate_background_info()
            if not background_info:
                logger.error("背景信息生成失败")
                return None
            
            # 2. 生成主问题列表
            main_questions = self._generate_main_questions(background_info)
            if not main_questions:
                logger.error("主问题生成失败")
                return None
            
            # 3. 生成关联问题分组
            trigger_groups = self._generate_trigger_groups(main_questions, background_info)
            
            # 4. 生成考核维度
            dimensions = self._generate_dimensions(background_info)
            if not dimensions:
                logger.error("考核维度生成失败")
                return None
            
            # 5. 生成情绪画像
            emotion_profile = self._generate_emotion_profile(background_info)
            
            # 构建场景内容对象
            self.scene_content = SceneContent(
                industry=self.state.industry,
                role_type=self.state.role_type,
                ai_role=self.state.ai_role,  # ✅ 新增：保存 AI 角色
                role_description=self.state.role_description,
                background_info=background_info,
                main_questions=main_questions,
                trigger_groups=trigger_groups,
                dimensions=dimensions,
                emotion_profile=emotion_profile,
                additional_requirements=self.state.additional_requirements
            )
            
            logger.info("场景内容生成成功!")
            logger.info(f"背景信息长度：{len(background_info)}")
            logger.info(f"主问题数量：{len(main_questions)}")
            logger.info(f"关联问题分组：{len(trigger_groups)}")
            logger.info(f"考核维度数量：{len(dimensions)}")
            
            return self.scene_content
            
        except Exception as e:
            logger.error(f"生成场景内容失败：{str(e)}", exc_info=True)
            return None

    def _generate_background_info(self) -> str:
        """生成背景信息"""
        logger.info("步骤 1: 生成背景信息...")
        
        context_info = self._build_context_info()
        # ✅ 关键修改：传入 ai_role 而不是 role_type
        prompt = CHAIN_OF_THOUGHT_BACKGROUND.format(
            industry=self.state.industry,
            ai_role=self.state.ai_role,  # ← 改为 ai_role
            context_info=context_info
        )
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            return response.strip()
        except Exception as e:
            logger.error(f"生成背景信息失败：{str(e)}")
            return ""

    def _generate_main_questions(self, background_info: str) -> List[MainQuestion]:
        """生成主问题列表"""
        logger.info("步骤 2: 生成主问题列表...")
        
        context_info = self._build_context_info(background_info)
        prompt = CHAIN_OF_THOUGHT_QUESTIONS.format(
            industry=self.state.industry,
            role_type=self.state.role_type,
            context_info=context_info
        )
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            questions_data = result.get("main_questions", [])
            questions = [
                MainQuestion(question=q.get("question", ""), order=q.get("order", i+1))
                for i, q in enumerate(questions_data)
            ]
            
            logger.info(f"成功生成 {len(questions)} 个主问题")
            return questions
        except Exception as e:
            logger.error(f"生成主问题失败：{str(e)}")
            return []

    def _generate_trigger_groups(
        self, 
        main_questions: List[MainQuestion], 
        background_info: str
    ) -> List[TriggerGroup]:
        """生成关联问题分组"""
        logger.info("步骤 3: 生成关联问题分组...")
        
        if not main_questions:
            logger.warning("没有主问题，跳过关联问题生成")
            return []
        
        context_info = self._build_context_info(background_info)
        context_info += f"\n主问题列表:\n"
        for q in main_questions:
            context_info += f"- {q.question}\n"
        
        prompt = CHAIN_OF_THOUGHT_TRIGGERS.format(
            industry=self.state.industry,
            role_type=self.state.role_type,
            context_info=context_info
        )
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            groups_data = result.get("trigger_groups", [])
            groups = []
            for g in groups_data:
                questions = [
                    TriggerQuestion(question=q.get("question", ""), order=q.get("order", i+1))
                    for i, q in enumerate(g.get("questions", []))
                ]
                groups.append(TriggerGroup(
                    group_name=g.get("group_name", ""),
                    trigger_keywords=g.get("trigger_keywords", []),
                    questions=questions
                ))
            
            logger.info(f"成功生成 {len(groups)} 个关联问题分组")
            return groups
        except Exception as e:
            logger.error(f"生成关联问题失败：{str(e)}")
            return []

    def _generate_dimensions(self, background_info: str) -> List[Dimension]:
        """生成考核维度"""
        logger.info("步骤 4: 生成考核维度...")
        
        context_info = self._build_context_info(background_info)
        prompt = CHAIN_OF_THOUGHT_DIMENSIONS.format(
            industry=self.state.industry,
            role_type=self.state.role_type,
            context_info=context_info
        )
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            dimensions_data = result.get("dimensions", [])
            dimensions = [
                Dimension(
                    dimension_name=d.get("dimension_name", ""),
                    weight=d.get("weight", 0.0),
                    sub_criteria=d.get("sub_criteria", {})
                )
                for d in dimensions_data
            ]
            
            logger.info(f"成功生成 {len(dimensions)} 个考核维度")
            return dimensions
        except Exception as e:
            logger.error(f"生成考核维度失败：{str(e)}")
            return []

    def _generate_emotion_profile(self, background_info: str) -> EmotionProfile:
        """生成情绪画像"""
        logger.info("步骤 5: 生成情绪画像...")
        
        context_info = self._build_context_info(background_info)
        prompt = CHAIN_OF_THOUGHT_EMOTION.format(
            industry=self.state.industry,
            role_type=self.state.role_type,
            context_info=context_info
        )
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            emotion = EmotionProfile(
                emotion_type=result.get("emotion_type", "平和"),
                emotion_description=result.get("emotion_description", ""),
                speaking_style=result.get("speaking_style", ""),
                attitude=result.get("attitude", "")
            )
            
            logger.info(f"情绪类型：{emotion.emotion_type}")
            return emotion
        except Exception as e:
            logger.error(f"生成情绪画像失败：{str(e)}")
            return EmotionProfile()

    def _build_context_info(self, background_info: str = "") -> str:
        """构建上下文信息"""
        context_parts = [
            f"行业：{self.state.industry}",
            f"角色：{self.state.role_type}",
        ]
        
        if self.state.role_description:
            context_parts.append(f"角色描述：{self.state.role_description}")
        
        if background_info:
            context_parts.append(f"背景信息：{background_info}")
        
        if self.state.extended_info:
            context_parts.append("延展信息:")
            for k, v in self.state.extended_info.items():
                context_parts.append(f"- {k}: {v}")
        
        if self.state.additional_requirements:
            context_parts.append(f"额外需求：{self.state.additional_requirements}")
        
        return "\n".join(context_parts)

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()
        
        # 移除 markdown 代码块标记
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # 找到第一个 { 的位置
        start_idx = text.find("{")
        if start_idx == -1:
            return text
        
        # 匹配括号
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

    def build_prompt(self) -> str:
        """
        构建完整的场景提示词
        
        Returns:
            完整的提示词字符串
        """
        if not self.scene_content:
            logger.error("场景内容未生成，无法构建提示词")
            return ""
        
        content = self.scene_content
        
        # ✅ 关键修改：使用 ai_role 而不是 role_type
        # 确定 AI 应该扮演的角色
        ai_character = content.ai_role if hasattr(content, 'ai_role') and content.ai_role else content.role_type
        
        # 构建提示词
        prompt_parts = [
            "# 角色设定",
            f"你是一名{content.industry}行业的{ai_character}。",
            "",
            "# 场景背景",
            content.background_info,
            "",
            "# 情绪与态度",
            f"- 情绪基调：{content.emotion_profile.emotion_type}",
            f"- 情绪描述：{content.emotion_profile.emotion_description}",
            f"- 说话风格：{content.emotion_profile.speaking_style}",
            f"- 沟通态度：{content.emotion_profile.attitude}",
            "",
            "# 主问题列表",
        ]
        
        for q in content.main_questions:
            prompt_parts.append(f"{q.order}. {q.question}")
        
        if content.trigger_groups:
            prompt_parts.append("")
            prompt_parts.append("# 关联问题分组")
            for group in content.trigger_groups:
                keywords_str = "、".join([f'"{kw}"' for kw in group.trigger_keywords])
                prompt_parts.append(f"\n## {group.group_name}")
                prompt_parts.append(f"触发关键词：{keywords_str}")
                prompt_parts.append("触发问题:")
                for q in group.questions:
                    prompt_parts.append(f"  {q.order}. {q.question}")
        
        if content.dimensions:
            prompt_parts.append("")
            prompt_parts.append("# 考核维度")
            prompt_parts.append("本次训练将按以下维度进行评估:")
            prompt_parts.append("")
            for dim in content.dimensions:
                prompt_parts.append(f"## {dim.dimension_name} (权重：{dim.weight*100:.0f}%)")
                prompt_parts.append("评估要点:")
                for criterion, desc in dim.sub_criteria.items():
                    prompt_parts.append(f"- {criterion}: {desc}")
                prompt_parts.append("")
        
        if content.additional_requirements:
            prompt_parts.append("")
            prompt_parts.append("# 额外要求")
            prompt_parts.append(content.additional_requirements)
        
        return "\n".join(prompt_parts)

    def get_scene_content_dict(self) -> Dict[str, Any]:
        """获取场景内容的字典格式"""
        if not self.scene_content:
            return {}
        return self.scene_content.to_dict()

    def reset(self):
        """重置智能体状态"""
        self.state = ConversationState()
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
        self.scene_content = None
        logger.info("场景智能体已重置")
