"""
预设场景服务模块

负责从数据库加载预设场景，并基于预设场景生成完整的场景提示词。

核心功能：
1. 从数据库加载预设场景（auto_first_visit 等）
2. 使用 LLM 基于预设场景生成个性化内容
3. 结合手工模板（骨架）和 LLM 生成内容（血肉）
4. 提供兜底数据（预设场景中的默认内容）
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

from .models import (
    SceneContent, Dimension, MainQuestion,
    TriggerGroup, TriggerQuestion, EmotionProfile
)

import db as db_module

logger = logging.getLogger(__name__)


class PresetSceneService:
    """
    预设场景服务
    
    方案总结：
    ├── 手工模板贡献（骨架，固定不变）：
    │   ├── 对话控制机制（强制提问队列、顺序控制）
    │   ├── 结束流程（根据意愿选择结束语）
    │   ├── 关联问题触发规则
    │   └── 防御性对话设计
    │
    ├── LLM 贡献（血肉，动态生成）：
    │   ├── 融合用户背景的背景信息
    │   ├── 个性化的主问题列表
    │   ├── 个性化的关联问题和触发词
    │   └── 角色情绪画像
    │
    └── 预设场景贡献（基础，保底数据）：
        ├── 行业、角色、场景基本信息
        ├── 默认主问题（LLM失败时的兜底）
        ├── 默认关联问题（LLM失败时的兜底）
        └── 默认考核维度
    """
    
    def __init__(self):
        # 初始化 LLM
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
        self.generation = MultiModalConversation
        
        # 手工模板（骨架）
        self.manual_template = self._load_manual_template()

    def _load_manual_template(self) -> Dict[str, str]:
        """加载手工模板（固定的骨架部分）"""
        return {
            "dialogue_control": """
# 对话控制机制

## 启动阶段：
- 默认第一个问题是："你好，哪位？"

## 核心提问机制
1. 设置强制提问队列：
   - 创建`待提问队列` = 【待提问主列表】副本
   - 按顺序提问（不可跳过或乱序）

2. 每次响应规则：
   - 当销售提出问题，回应判断步骤：
        1.判断销售提出的问题是否在【基本信息】中存在，如果有选用【基本信息】中的问题回应。
        2.判断销售提出的问题是否在【基本信息】中不存在，可以自行组织相关信息进行回应。
   - 当销售完成回答后，判断提出问题步骤：
        1. 是否满足【触发关联问题规则】，如果满足，按照【触发关联问题规则】回答关联问题
        2. 没有触发关联问题，你必须立即提出【待提问主列表】中的下一个问题
   - 使用背景信息优化提问语气，回答时的格式为：如果销售提问：先【回应销售问题】。
   - 提问后自动从队列移除该问题
    
3. 未完成问题处理：
    if 待提问队列 非空:
        禁止任何形式的结束对话表达
        必须继续提问队列中的下一个问题
        
4. 完成所有问题后的结束流程：
- 当队列空时，根据购买意愿选择结束语：
  - 冷淡："好的，我了解了，有需要再联系你。"
  - 一般："好的，我再考虑考虑，有需要联系你。"
  - 感兴趣："好的，那我先了解一下，加个微信吧。"
  - 非常感兴趣："好的，那我们加个微信，你发些资料给我看看。"
- 等待销售回应：
  - 若销售5秒内无响应 → 直接结束
  - 若销售有回应 → 等其说完后结束
5.结束对话后，不再回答任何问题，需要单独一条会话记录进行提示："培训已结束"，不要与之前的会话内容连接在一起。
""",
            
            "trigger_rules": """
# 关联问题触发规则

## 必须要满足触发关联问题规则：
- 在命中"对方话术中触发问题的关键信息"中的任意关键字或语义近似，均触发该分组中的触发问题列表问题。
- 在触发关联问题后，如果是陈述句，不允许在陈述句后加【待提问主列表】中的问题
""",
            
            "defensive_design": """
# 防御性对话设计

- 当遇到被询问客户相关的工作内容时，例如：请帮我介绍一下您的需求？之类的问题。你回答：我是来咨询产品的。
- 当遇到与咨询产品不相关的问题时："这个问题跟我咨询的内容好像没关系吧"
"""
        }

    def _call_model(self, messages: List, temperature: float = 0.7) -> str:
        """调用 Qwen 模型"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": [{"text": msg.content}]})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": [{"text": msg.content}]})
            elif isinstance(msg, dict):
                if isinstance(msg.get("content"), list):
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({
                        "role": msg.get("role", "user"), 
                        "content": [{"text": msg.get("content", "")}]
                    })
        
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

    def load_preset_scene(self, scene_code: str) -> Optional[Dict[str, Any]]:
        """
        从数据库加载预设场景
        
        Args:
            scene_code: 场景代码（如 'auto_first_visit'）
            
        Returns:
            预设场景数据，如果不存在返回 None
        """
        try:
            scene_data = db_module.get_preset_scene_by_code(scene_code)
            if not scene_data:
                logger.error(f"预设场景不存在: {scene_code}")
                return None
            
            logger.info(f"成功加载预设场景: {scene_data.get('scene_name')}")
            return scene_data
            
        except Exception as e:
            logger.error(f"加载预设场景失败: {str(e)}", exc_info=True)
            return None

    def generate_from_preset(
        self, 
        scene_code: str,
        user_background: Optional[str] = None,
        custom_requirements: Optional[str] = None
    ) -> Optional[SceneContent]:
        """
        基于预设场景生成完整的场景内容
        
        Args:
            scene_code: 预设场景代码
            user_background: 用户提供的背景信息（可选）
            custom_requirements: 用户自定义需求（可选）
            
        Returns:
            SceneContent 对象
        """
        try:
            # 1. 加载预设场景
            preset_data = self.load_preset_scene(scene_code)
            if not preset_data:
                return None
            
            logger.info("=" * 50)
            logger.info(f"开始基于预设场景生成内容: {preset_data.get('scene_name')}")
            logger.info("=" * 50)
            
            # 2. 使用 LLM 生成个性化内容
            background_info = self._generate_personalized_background(
                preset_data, user_background
            )
            
            main_questions = self._generate_personalized_questions(
                preset_data, background_info, user_background
            )
            
            trigger_groups = self._generate_personalized_triggers(
                preset_data, main_questions, background_info
            )
            
            dimensions = self._parse_dimensions(preset_data)
            
            emotion_profile = self._generate_personalized_emotion(
                preset_data, background_info
            )
            
            # 3. 构建场景内容对象
            scene_content = SceneContent(
                industry=preset_data.get('industry_code'),
                role_type=preset_data.get('user_role'),
                ai_role=preset_data.get('ai_role'),
                role_description=preset_data.get('scene_description'),
                background_info=background_info,
                main_questions=main_questions,
                trigger_groups=trigger_groups,
                dimensions=dimensions,
                emotion_profile=emotion_profile,
                additional_requirements=custom_requirements
            )
            
            logger.info("场景内容生成成功!")
            logger.info(f"背景信息长度: {len(background_info)}")
            logger.info(f"主问题数量: {len(main_questions)}")
            logger.info(f"关联问题分组: {len(trigger_groups)}")
            logger.info(f"考核维度数量: {len(dimensions)}")
            
            return scene_content
            
        except Exception as e:
            logger.error(f"生成场景内容失败: {str(e)}", exc_info=True)
            return None

    def _generate_personalized_background(
        self, 
        preset_data: Dict[str, Any],
        user_background: Optional[str] = None
    ) -> str:
        """
        生成个性化的背景信息（LLM 生成 + 预设兜底）
        """
        logger.info("步骤 1: 生成个性化背景信息...")
        
        # 构建提示词
        user_bg_section = f"【用户补充背景】\n{user_background}\n" if user_background else ""
        prompt = f"""你是一个专业的场景设计专家。请为以下预设场景生成详细的背景信息。

【预设场景信息】
场景名称: {preset_data.get('scene_name')}
场景描述: {preset_data.get('scene_description')}
AI 角色: {preset_data.get('ai_role')}
用户角色: {preset_data.get('user_role')}
难度: {preset_data.get('difficulty')}

{user_bg_section}
请生成一段详细的背景信息描述（200-400字），要求：
1. 真实、接地气、有代入感
2. 包含时间、地点、人物关系等细节
3. 如果用户提供了补充背景，要融合进去
4. 确保 AI 扮演 {preset_data.get('ai_role')}，用户扮演 {preset_data.get('user_role')}
"""
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            background = response.strip()
            
            # 如果生成失败或太短，使用预设的背景模板作为兜底
            if len(background) < 50 and preset_data.get('background_template'):
                logger.warning("LLM 生成的背景信息太短，使用预设模板")
                background = preset_data.get('background_template')
            
            return background
            
        except Exception as e:
            logger.error(f"生成背景信息失败: {str(e)}")
            # 兜底：使用预设的背景模板
            return preset_data.get('background_template') or preset_data.get('scene_description')

    def _generate_personalized_questions(
        self,
        preset_data: Dict[str, Any],
        background_info: str,
        user_background: Optional[str] = None
    ) -> List[MainQuestion]:
        """
        生成个性化的主问题列表（LLM 生成 + 预设兜底）
        """
        logger.info("步骤 2: 生成个性化主问题列表...")
        
        user_bg_hint = f"5. 如果用户提供了背景信息，要结合用户背景设计问题\n用户背景: {user_background}" if user_background else ""
        prompt = f"""你是一个专业的场景设计专家。请为 AI 模拟的 {preset_data.get('ai_role')} 角色设计主问题列表。

【场景背景】
{background_info}

【AI 角色】
{preset_data.get('ai_role')}

【要求】
1. 生成 3-5 个主问题
2. 问题要口语化、自然
3. 符合 {preset_data.get('ai_role')} 的身份和沟通风格
4. 按对话顺序排列（开场→了解→深入→收尾）
{user_bg_hint}

请返回 JSON 格式:
{{
    "main_questions": [
        {{"question": "问题 1", "order": 1}},
        {{"question": "问题 2", "order": 2}},
        {{"question": "问题 3", "order": 3}}
    ]
}}
"""
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            questions_data = result.get("main_questions", [])
            questions = [
                MainQuestion(question=q.get("question", ""), order=q.get("order", i+1))
                for i, q in enumerate(questions_data)
            ]
            
            # 如果生成的问题太少，使用预设的主问题作为兜底
            if len(questions) < 3 and preset_data.get('main_questions_template'):
                logger.warning("LLM 生成的问题太少，补充预设问题")
                preset_questions = self._parse_preset_questions(
                    preset_data.get('main_questions_template')
                )
                questions.extend(preset_questions[len(questions):])
            
            logger.info(f"成功生成 {len(questions)} 个主问题")
            return questions
            
        except Exception as e:
            logger.error(f"生成主问题失败: {str(e)}")
            # 兜底：解析预设的主问题模板
            return self._parse_preset_questions(
                preset_data.get('main_questions_template')
            )

    def _generate_personalized_triggers(
        self,
        preset_data: Dict[str, Any],
        main_questions: List[MainQuestion],
        background_info: str
    ) -> List[TriggerGroup]:
        """
        生成个性化的关联问题分组（LLM 生成 + 预设兜底）
        """
        logger.info("步骤 3: 生成个性化关联问题分组...")
        
        if not main_questions:
            logger.warning("没有主问题，跳过关联问题生成")
            return []
        
        main_questions_text = "\n".join([f"{q.order}. {q.question}" for q in main_questions])
        
        prompt = f"""你是一个专业的场景设计专家。请设计关联问题分组。

【场景背景】
{background_info}

【主问题列表】
{main_questions_text}

【要求】
1. 生成 2-4 个关联问题分组
2. 每个分组有明确的触发关键词（2-3 个）
3. 每个分组包含 1-2 个相关问题
4. 问题要口语化、自然
5. 触发关键词要具体明确

请返回 JSON 格式:
{{
    "trigger_groups": [
        {{
            "group_name": "分组 A",
            "trigger_keywords": ["关键词1", "关键词2"],
            "questions": [
                {{"question": "问题 1", "order": 1}},
                {{"question": "问题 2", "order": 2}}
            ]
        }}
    ]
}}
"""
        
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
            
            # 如果生成的分组太少，使用预设的触发分组作为兜底
            if len(groups) < 2 and preset_data.get('trigger_groups_template'):
                logger.warning("LLM 生成的分组太少，补充预设分组")
                preset_groups = self._parse_preset_triggers(
                    preset_data.get('trigger_groups_template')
                )
                groups.extend(preset_groups[len(groups):])
            
            logger.info(f"成功生成 {len(groups)} 个关联问题分组")
            return groups
            
        except Exception as e:
            logger.error(f"生成关联问题失败: {str(e)}")
            # 兜底：解析预设的触发分组模板
            return self._parse_preset_triggers(
                preset_data.get('trigger_groups_template')
            )

    def _generate_personalized_emotion(
        self,
        preset_data: Dict[str, Any],
        background_info: str
    ) -> EmotionProfile:
        """
        生成个性化的情绪画像（LLM 生成 + 预设兜底）
        """
        logger.info("步骤 4: 生成个性化情绪画像...")
        
        prompt = f"""你是一个专业的角色设计师。请为 {preset_data.get('ai_role')} 设计情绪画像。

【场景背景】
{background_info}

【AI 角色】
{preset_data.get('ai_role')}

【难度】
{preset_data.get('difficulty')}

【要求】
1. 设计符合角色和场景的情绪类型
2. 描述情绪状态和变化
3. 设计说话风格（语速、用词、语气）
4. 设计沟通态度（友好程度、配合程度）

请返回 JSON 格式:
{{
    "emotion_type": "情绪类型（如：平和、焦虑、质疑、友好等）",
    "emotion_description": "情绪的详细描述",
    "speaking_style": "说话风格描述",
    "attitude": "沟通态度描述"
}}
"""
        
        try:
            response = self._call_model([HumanMessage(content=prompt)])
            result = json.loads(self._extract_json(response))
            
            emotion = EmotionProfile(
                emotion_type=result.get("emotion_type", "平和"),
                emotion_description=result.get("emotion_description", ""),
                speaking_style=result.get("speaking_style", ""),
                attitude=result.get("attitude", "")
            )
            
            logger.info(f"情绪类型: {emotion.emotion_type}")
            return emotion
            
        except Exception as e:
            logger.error(f"生成情绪画像失败: {str(e)}")
            # 兜底：解析预设的情绪模板或使用默认值
            return self._parse_preset_emotion(
                preset_data.get('emotion_template')
            )

    def _parse_dimensions(self, preset_data: Dict[str, Any]) -> List[Dimension]:
        """
        解析考核维度（从预设场景或数据库）
        """
        logger.info("步骤 5: 解析考核维度...")
        
        try:
            # 优先使用 dimensions_template 字段
            if preset_data.get('dimensions_template'):
                template = preset_data.get('dimensions_template')
                if isinstance(template, str):
                    dimensions_data = json.loads(template)
                else:
                    dimensions_data = template
                
                dimensions = []
                for d in dimensions_data.get('dimensions', []):
                    dimensions.append(Dimension(
                        dimension_name=d.get('dimension_name', ''),
                        weight=d.get('weight', 0.0),
                        sub_criteria=d.get('sub_criteria', {})
                    ))
                
                logger.info(f"成功解析 {len(dimensions)} 个考核维度")
                return dimensions
            
            # 兜底：返回默认维度
            return self._get_default_dimensions()
            
        except Exception as e:
            logger.error(f"解析考核维度失败: {str(e)}")
            return self._get_default_dimensions()

    def _get_default_dimensions(self) -> List[Dimension]:
        """获取默认考核维度（兜底）"""
        return [
            Dimension(
                dimension_name="沟通能力",
                weight=0.3,
                sub_criteria={
                    "表达清晰度": "语言表达是否清晰、逻辑是否连贯",
                    "倾听能力": "是否认真倾听客户需求"
                }
            ),
            Dimension(
                dimension_name="专业知识",
                weight=0.3,
                sub_criteria={
                    "产品知识": "对产品特性和优势的了解程度",
                    "行业知识": "对行业趋势和竞品的了解"
                }
            ),
            Dimension(
                dimension_name="应变能力",
                weight=0.2,
                sub_criteria={
                    "问题处理": "面对客户疑问的应对能力",
                    "异议处理": "处理客户异议的技巧"
                }
            ),
            Dimension(
                dimension_name="促成能力",
                weight=0.2,
                sub_criteria={
                    "需求挖掘": "挖掘客户真实需求的能力",
                    "成交技巧": "引导客户做出购买决策的能力"
                }
            )
        ]

    def _parse_preset_questions(self, template: Optional[str]) -> List[MainQuestion]:
        """解析预设的主问题模板（兜底）"""
        if not template:
            return []
        
        try:
            if isinstance(template, str):
                data = json.loads(template)
            else:
                data = template
            
            questions = []
            for i, q in enumerate(data.get('questions', [])):
                questions.append(MainQuestion(
                    question=q,
                    order=i + 1
                ))
            return questions
            
        except Exception as e:
            logger.error(f"解析预设问题失败: {str(e)}")
            return []

    def _parse_preset_triggers(self, template: Optional[str]) -> List[TriggerGroup]:
        """解析预设的触发分组模板（兜底）"""
        if not template:
            return []
        
        try:
            if isinstance(template, str):
                data = json.loads(template)
            else:
                data = template
            
            groups = []
            for g in data.get('groups', []):
                questions = [
                    TriggerQuestion(question=q, order=i+1)
                    for i, q in enumerate(g.get('questions', []))
                ]
                groups.append(TriggerGroup(
                    group_name=g.get('group_name', ''),
                    trigger_keywords=g.get('trigger_keywords', []),
                    questions=questions
                ))
            return groups
            
        except Exception as e:
            logger.error(f"解析预设触发分组失败: {str(e)}")
            return []

    def _parse_preset_emotion(self, template: Optional[str]) -> EmotionProfile:
        """解析预设的情绪模板（兜底）"""
        if not template:
            return EmotionProfile()
        
        try:
            if isinstance(template, str):
                data = json.loads(template)
            else:
                data = template
            
            return EmotionProfile(
                emotion_type=data.get('emotion_type', '平和'),
                emotion_description=data.get('emotion_description', ''),
                speaking_style=data.get('speaking_style', ''),
                attitude=data.get('attitude', '')
            )
            
        except Exception as e:
            logger.error(f"解析预设情绪失败: {str(e)}")
            return EmotionProfile()

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

    def build_full_prompt(self, scene_content: SceneContent) -> str:
        """
        构建完整的场景提示词
        
        结合：
        1. 手工模板（骨架）
        2. LLM 生成的内容（血肉）
        3. 预设场景的基础信息（保底）
        
        Returns:
            完整的提示词字符串
        """
        if not scene_content:
            logger.error("场景内容未生成，无法构建提示词")
            return ""
        
        # 构建提示词各部分
        prompt_parts = [
            "# 任务描述",
            f"- 你作为{scene_content.ai_role}，销售顾问正在给你打电话，介绍产品或服务",
            "",
            "# 角色定义：",
            f"- 你是一个AI{scene_content.ai_role}，这是你唯一的身份。",
            f"- {scene_content.ai_role}只陈述信息，在对话过程中根据购买意愿表现相应的态度。",
            "---",
            "",
            "# 情绪与态度：",
            f"- 情绪基调：{scene_content.emotion_profile.emotion_type}",
            f"- 情绪描述：{scene_content.emotion_profile.emotion_description}",
            f"- 说话风格：{scene_content.emotion_profile.speaking_style}",
            f"- 沟通态度：{scene_content.emotion_profile.attitude}",
            "",
            "# 背景信息：",
            scene_content.background_info,
            "---",
            "",
            "# 待提问主列表：",
        ]
        
        # 添加主问题列表
        for q in scene_content.main_questions:
            prompt_parts.append(f"{q.order}. {q.question}")
        
        prompt_parts.append("")
        prompt_parts.append("")
        
        # 添加对话控制机制（手工模板）
        prompt_parts.append(self.manual_template["dialogue_control"])
        prompt_parts.append("")
        
        # 添加关联问题
        if scene_content.trigger_groups:
            prompt_parts.append("# 关联问题")
            prompt_parts.append(self.manual_template["trigger_rules"])
            prompt_parts.append("")
            
            for group in scene_content.trigger_groups:
                keywords_str = "、".join([f'"{kw}"' for kw in group.trigger_keywords])
                prompt_parts.append(f"    {group.group_name}:")
                prompt_parts.append(f"    - 对方话术中触发问题的关键信息：{keywords_str}")
                prompt_parts.append(f"    - 触发问题列表的提问方式：按该分组中【触发问题列表】中标号顺序提问")
                prompt_parts.append(f"    - 触发问题列表：")
                for q in group.questions:
                    prompt_parts.append(f"        {q.order}. {q.question}")
                prompt_parts.append("")
        
        # 添加防御性对话设计（手工模板）
        prompt_parts.append(self.manual_template["defensive_design"])
        
        return "\n".join(prompt_parts)
