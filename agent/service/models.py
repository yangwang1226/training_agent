from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class RoleType(Enum):
    PARENT = "parent"
    STUDENT = "student"
    CUSTOMER = "customer"
    TEACHER = "teacher"


class SceneType(Enum):
    TRAINING_TEACHER = "training_teacher"
    TRAINING_SALES = "training_sales"
    PSYCHOLOGICAL_COUNSELING = "psychological_counseling"


@dataclass
class BackgroundInfo:
    student_name: str = ""
    student_grade: str = ""
    student_gender: str = ""
    subject: str = ""
    recent_performance: str = ""
    learning_issues: List[str] = field(default_factory=list)
    family_expectation: str = ""
    other_info: List[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        lines = []
        if self.student_name:
            lines.append(f"学生姓名：{self.student_name}")
        if self.student_grade:
            lines.append(f"年级：{self.student_grade}")
        if self.student_gender:
            lines.append(f"性别：{self.student_gender}")
        if self.subject:
            lines.append(f"学科：{self.subject}")
        if self.recent_performance:
            lines.append(f"近期表现：{self.recent_performance}")
        for issue in self.learning_issues:
            lines.append(f"学习问题：{issue}")
        if self.family_expectation:
            lines.append(f"家长期望：{self.family_expectation}")
        for info in self.other_info:
            lines.append(info)
        return "\n".join(lines)


@dataclass
class FollowUpQuestion:
    question: str
    order: int = 1


@dataclass
class TriggerGroup:
    group_name: str
    trigger_keywords: List[str]
    questions: List[FollowUpQuestion]

    def to_prompt_text(self) -> str:
        keywords_str = "、".join([f'"{kw}"' for kw in self.trigger_keywords])
        questions_text = "\n\t\t".join([
            f"{q.order}.{q.question}" for q in self.questions
        ])
        return f"""\t分组{self.group_name}:
\t- 对方话术中触发问题的关键信息：{keywords_str}
\t- 触发问题列表的提问方式：按该分组中【触发问题列表】中标号顺序提问
\t- 触发问题列表：
\t\t{questions_text}"""


@dataclass
class MainQuestion:
    question: str
    order: int

    def to_prompt_text(self) -> str:
        return f"{self.order}. {self.question}"


@dataclass
class GeneratedPrompt:
    background_info: BackgroundInfo
    main_questions: List[MainQuestion]
    trigger_groups: List[TriggerGroup]
    full_prompt: str = ""


@dataclass
class UserInput:
    conversation: str
    role_description: Optional[str] = None
    scene_type: Optional[str] = None
    custom_requirements: Optional[str] = None
