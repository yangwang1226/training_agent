from dataclasses import dataclass, field
from typing import List, Dict


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
