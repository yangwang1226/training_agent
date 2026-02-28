"""
AI教练评估模块

提供销售对话评估、能力画像、训练追踪等功能
"""

from .models import (
    TrainingSession,
    AssessmentResult,
    DimensionScore,
    KeyMoment,
    TranscriptMessage,
    UserAbilityProfile,
    TrainingHistory,
    DifficultyLevel,
    TrainingStatus,
    EVALUATION_DIMENSIONS,
    INDUSTRY_ASSESSMENT_WEIGHTS
)

from .assessment_service import (
    AssessmentService,
    assessment_service
)

from .evaluation_prompts import (
    EVALUATION_SYSTEM_PROMPT,
    EVALUATION_PROMPT_TEMPLATE,
    QUICK_FEEDBACK_PROMPT
)


__all__ = [
    'TrainingSession',
    'AssessmentResult',
    'DimensionScore',
    'KeyMoment',
    'TranscriptMessage',
    'UserAbilityProfile',
    'TrainingHistory',
    'DifficultyLevel',
    'TrainingStatus',
    'EVALUATION_DIMENSIONS',
    'INDUSTRY_ASSESSMENT_WEIGHTS',
    'AssessmentService',
    'assessment_service',
    'EVALUATION_SYSTEM_PROMPT',
    'EVALUATION_PROMPT_TEMPLATE',
    'QUICK_FEEDBACK_PROMPT'
]
