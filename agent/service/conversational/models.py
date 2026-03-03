from typing import Optional, List, Dict
from pydantic import BaseModel, Field


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
