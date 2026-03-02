"""
AI教练评估模块 - 数据模型定义
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DifficultyLevel(Enum):
    EASY = "入门"
    MEDIUM = "进阶"
    HARD = "熟练"
    EXPERT = "专家"


class TrainingStatus(Enum):
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    ABANDONED = "已放弃"


@dataclass
class DimensionScore:
    dimension_name: str
    score: float
    weight: float
    reason: str
    sub_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class KeyMoment:
    time: str
    moment_type: str
    content: str
    handling_quality: str
    suggestion: Optional[str] = None


@dataclass
class TranscriptMessage:
    role: str
    content: str
    timestamp: str


@dataclass
class AssessmentResult:
    overall_score: float
    dimension_scores: List[DimensionScore]
    highlights: List[str]
    improvements: List[str]
    golden_sentences: List[str]
    key_moments: List[KeyMoment]
    completion_rate: float
    total_turns: int
    duration_seconds: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingSession:
    session_id: str
    user_id: str
    scene_id: str
    industry: str
    role: str
    purchase_intent: str
    difficulty: DifficultyLevel
    status: TrainingStatus
    
    
    transcript: List[TranscriptMessage] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    
    assessment: Optional[AssessmentResult] = None
    
    system_prompt: str = ""
    customer_persona: str = ""
    dimension_config: Optional[Any] = None


@dataclass
class UserAbilityProfile:
    user_id: str
    overall_score: float = 0.0
    
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    dimension_config_snapshot: Optional[Dict] = None
    
    training_count: int = 0
    total_duration: int = 0
    level: str = "入门"
    
    weak_points: List[str] = field(default_factory=list)
    strong_points: List[str] = field(default_factory=list)
    
    improvement_history: List[Dict] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_level(self):
        if self.overall_score >= 90:
            self.level = "专家"
        elif self.overall_score >= 75:
            self.level = "熟练"
        elif self.overall_score >= 60:
            self.level = "进阶"
        else:
            self.level = "入门"
    
    def update_strengths_weaknesses(self):
        if not self.dimension_scores:
            return
        sorted_dims = sorted(
            self.dimension_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        self.strong_points = [dim for dim, score in sorted_dims[:2] if score >= 70]
        self.weak_points = [dim for dim, score in sorted_dims[-2:] if score < 70]


@dataclass
class TrainingHistory:
    user_id: str
    sessions: List[TrainingSession] = field(default_factory=list)
    
    def get_recent_sessions(self, limit: int = 10) -> List[TrainingSession]:
        return sorted(
            self.sessions, 
            key=lambda x: x.start_time, 
            reverse=True
        )[:limit]
    
    def get_average_score(self) -> float:
        if not self.sessions:
            return 0.0
        scores = [s.assessment.overall_score for s in self.sessions if s.assessment]
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_score_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [s for s in self.sessions if s.start_time >= cutoff and s.assessment]
        return [
            {
                "date": s.start_time.strftime("%Y-%m-%d"),
                "score": s.assessment.overall_score,
                "industry": s.industry
            }
            for s in sorted(recent, key=lambda x: x.start_time)
        ]


EVALUATION_DIMENSIONS = {
    "沟通技巧": {
        "weight": 0.20,
        "sub_criteria": {
            "表达清晰": "语言表达是否清晰、有条理",
            "语速适中": "语速是否合适，不快不慢",
            "礼貌用语": "是否使用礼貌用语，态度友好",
            "倾听能力": "是否认真倾听客户，不打断"
        }
    },
    "产品知识": {
        "weight": 0.20,
        "sub_criteria": {
            "特点介绍": "产品特点介绍是否准确",
            "优势对比": "与竞品对比是否清晰",
            "参数回答": "技术参数回答是否正确",
            "案例引用": "是否引用成功案例"
        }
    },
    "需求挖掘": {
        "weight": 0.20,
        "sub_criteria": {
            "提问技巧": "提问是否有针对性",
            "信息收集": "收集的信息是否完整",
            "痛点识别": "是否识别客户痛点",
            "需求确认": "是否确认理解客户需求"
        }
    },
    "异议处理": {
        "weight": 0.20,
        "sub_criteria": {
            "价格异议": "价格异议处理是否得当",
            "竞品对比": "竞品对比应对是否有效",
            "信任建立": "是否建立客户信任",
            "顾虑消除": "是否消除客户顾虑"
        }
    },
    "促成技巧": {
        "weight": 0.20,
        "sub_criteria": {
            "时机把握": "促单时机把握是否准确",
            "话术运用": "促单话术是否恰当",
            "紧迫感": "是否营造紧迫感",
            "成交引导": "是否引导客户成交"
        }
    }
}


INDUSTRY_ASSESSMENT_WEIGHTS = {
    "教育": {
        "需求挖掘": 0.30,
        "产品知识": 0.25,
        "沟通技巧": 0.20,
        "异议处理": 0.15,
        "促成技巧": 0.10
    },
    "汽车": {
        "产品知识": 0.30,
        "异议处理": 0.25,
        "需求挖掘": 0.20,
        "促成技巧": 0.15,
        "沟通技巧": 0.10
    },
    "房地产": {
        "需求挖掘": 0.30,
        "产品知识": 0.25,
        "促成技巧": 0.20,
        "异议处理": 0.15,
        "沟通技巧": 0.10
    },
    "金融": {
        "产品知识": 0.35,
        "需求挖掘": 0.25,
        "异议处理": 0.20,
        "沟通技巧": 0.10,
        "促成技巧": 0.10
    }
}


from datetime import timedelta
