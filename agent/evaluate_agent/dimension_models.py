"""
维度配置数据模型
支持动态能力评估维度
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class DimensionConfig:
    dimension_name: str
    weight: float
    sub_criteria: Dict[str, str] = field(default_factory=dict)
    evaluation_prompt: str = ""
    score_levels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "weight": self.weight,
            "sub_criteria": self.sub_criteria,
            "evaluation_prompt": self.evaluation_prompt,
            "score_levels": self.score_levels
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DimensionConfig":
        return cls(
            dimension_name=data.get("dimension_name", ""),
            weight=data.get("weight", 0.2),
            sub_criteria=data.get("sub_criteria", {}),
            evaluation_prompt=data.get("evaluation_prompt", ""),
            score_levels=data.get("score_levels", {})
        )


@dataclass
class SceneDimensionConfig:
    scene_id: str
    role_type: str = ""
    role_description: str = ""
    industry: str = ""
    training_goal: str = ""
    dimensions: List[DimensionConfig] = field(default_factory=list)
    full_evaluation_prompt: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "role_type": self.role_type,
            "role_description": self.role_description,
            "industry": self.industry,
            "training_goal": self.training_goal,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "full_evaluation_prompt": self.full_evaluation_prompt,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneDimensionConfig":
        dimensions = [
            DimensionConfig.from_dict(d) 
            for d in data.get("dimensions", [])
        ]
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        return cls(
            scene_id=data.get("scene_id", ""),
            role_type=data.get("role_type", ""),
            role_description=data.get("role_description", ""),
            industry=data.get("industry", ""),
            training_goal=data.get("training_goal", ""),
            dimensions=dimensions,
            full_evaluation_prompt=data.get("full_evaluation_prompt", ""),
            created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else (created_at or datetime.now()),
            updated_at=datetime.fromisoformat(updated_at) if isinstance(updated_at, str) else (updated_at or datetime.now())
        )

    @classmethod
    def from_json(cls, json_str: str) -> "SceneDimensionConfig":
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class DimensionGenerationResult:
    success: bool
    dimensions: List[DimensionConfig] = field(default_factory=list)
    design_rationale: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "design_rationale": self.design_rationale,
            "error_message": self.error_message
        }
