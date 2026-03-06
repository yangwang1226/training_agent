from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class Dimension:
    """考核维度数据模型"""
    dimension_name: str
    weight: float
    sub_criteria: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "weight": self.weight,
            "sub_criteria": self.sub_criteria
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dimension':
        return cls(
            dimension_name=data.get("dimension_name", ""),
            weight=data.get("weight", 0.0),
            sub_criteria=data.get("sub_criteria", {})
        )


@dataclass
class EmotionProfile:
    """情绪画像数据模型"""
    emotion_type: str = "平和"
    emotion_description: str = ""
    speaking_style: str = ""
    attitude: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "emotion_type": self.emotion_type,
            "emotion_description": self.emotion_description,
            "speaking_style": self.speaking_style,
            "attitude": self.attitude
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'EmotionProfile':
        return cls(
            emotion_type=data.get("emotion_type", "平和"),
            emotion_description=data.get("emotion_description", ""),
            speaking_style=data.get("speaking_style", ""),
            attitude=data.get("attitude", "")
        )


@dataclass
class MainQuestion:
    """主问题数据模型"""
    question: str
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "order": self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainQuestion':
        return cls(
            question=data.get("question", ""),
            order=data.get("order", 1)
        )


@dataclass
class TriggerQuestion:
    """触发问题数据模型"""
    question: str
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "order": self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerQuestion':
        return cls(
            question=data.get("question", ""),
            order=data.get("order", 1)
        )


@dataclass
class TriggerGroup:
    """关联问题分组数据模型"""
    group_name: str
    trigger_keywords: List[str] = field(default_factory=list)
    questions: List[TriggerQuestion] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "trigger_keywords": self.trigger_keywords,
            "questions": [q.to_dict() for q in self.questions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerGroup':
        return cls(
            group_name=data.get("group_name", ""),
            trigger_keywords=data.get("trigger_keywords", []),
            questions=[TriggerQuestion.from_dict(q) for q in data.get("questions", [])]
        )


@dataclass
class SceneContent:
    """场景内容数据模型"""
    industry: str = ""
    role_type: str = ""
    ai_role: str = ""  # ✅ 新增：AI 扮演的角色
    role_description: str = ""
    background_info: str = ""
    main_questions: List[MainQuestion] = field(default_factory=list)
    trigger_groups: List[TriggerGroup] = field(default_factory=list)
    dimensions: List[Dimension] = field(default_factory=list)
    emotion_profile: EmotionProfile = field(default_factory=EmotionProfile)
    additional_requirements: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "role_type": self.role_type,
            "ai_role": self.ai_role,  # ✅ 新增
            "role_description": self.role_description,
            "background_info": self.background_info,
            "main_questions": [q.to_dict() for q in self.main_questions],
            "trigger_groups": [g.to_dict() for g in self.trigger_groups],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "emotion_profile": self.emotion_profile.to_dict(),
            "additional_requirements": self.additional_requirements
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneContent':
        return cls(
            industry=data.get("industry", ""),
            role_type=data.get("role_type", ""),
            role_description=data.get("role_description", ""),
            background_info=data.get("background_info", ""),
            main_questions=[MainQuestion.from_dict(q) for q in data.get("main_questions", [])],
            trigger_groups=[TriggerGroup.from_dict(g) for g in data.get("trigger_groups", [])],
            dimensions=[Dimension.from_dict(d) for d in data.get("dimensions", [])],
            emotion_profile=EmotionProfile.from_dict(data.get("emotion_profile", {})),
            additional_requirements=data.get("additional_requirements", "")
        )
    
    def is_complete(self) -> bool:
        """检查场景内容是否完整"""
        return bool(
            self.industry and 
            self.role_type and 
            self.background_info and
            self.main_questions and
            self.dimensions
        )


@dataclass
class ConversationState:
    """对话状态数据模型"""
    industry: str = ""
    role_type: str = ""
    role_description: str = ""
    ai_role: str = ""  # AI 应该扮演的角色（如"客户"、"访客"等）
    purchase_intent: str = ""
    custom_questions: List[str] = field(default_factory=list)
    extended_info: Dict[str, str] = field(default_factory=dict)
    additional_requirements: str = ""
    
    collected_info: Dict[str, bool] = field(default_factory=lambda: {
        "industry": False,
        "role": False,
        "ai_role": False,  # AI 角色是否确认
        "intent": False,
        "questions": False
    })
    
    extended_info_sufficient: bool = False
    dimensions_confirmed: bool = False
    
    def is_ready_for_generation(self) -> bool:
        """检查是否可以开始生成场景内容"""
        # 有行业信息、AI扮演的角色信息就可以开始生成场景内容
        return self.collected_info.get("industry", False) and self.collected_info.get("ai_role", False)
    
    def get_extended_info_summary(self) -> str:
        """获取延展信息摘要"""
        if not self.extended_info:
            return "暂无"
        return "\n".join([f"- {k}: {v}" for k, v in self.extended_info.items()])
    
    def get_missing_info(self) -> List[str]:
        """获取缺失的信息列表"""
        missing = []
        if not self.collected_info.get("industry"):
            missing.append("行业")
        if not self.collected_info.get("role"):
            missing.append("角色")
        if not self.collected_info.get("ai_role"):
            missing.append("AI 扮演角色")
        if not self.collected_info.get("intent"):
            missing.append("购买意愿")
        if not self.collected_info.get("questions"):
            missing.append("问题列表")
        return missing
