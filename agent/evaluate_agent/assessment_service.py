"""
AI教练评估模块 - 评估服务核心逻辑
"""
import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

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
from .evaluation_prompts import (
    EVALUATION_SYSTEM_PROMPT,
    EVALUATION_PROMPT_TEMPLATE,
    QUICK_FEEDBACK_PROMPT,
    IMPROVEMENT_SUGGESTION_PROMPT
)


RECORD_DIR = Path(__file__).parent.parent.parent / "record"
ASSESSMENT_DIR = Path(__file__).parent.parent.parent / "assessment"
USER_PROFILE_DIR = Path(__file__).parent.parent.parent / "user_profiles"


class AssessmentService:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment='gpt-4o',
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", "c8575027653b42b1b47747f0b4ab135b"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://menshen.test.xdf.cn/"),
            api_version="2024-12-01-preview",
            temperature=0.3
        )
        
        RECORD_DIR.mkdir(exist_ok=True)
        ASSESSMENT_DIR.mkdir(exist_ok=True)
        USER_PROFILE_DIR.mkdir(exist_ok=True)
        
        self.sessions: Dict[str, TrainingSession] = {}
        self.user_profiles: Dict[str, UserAbilityProfile] = {}
    
    def create_session(
        self,
        user_id: str,
        scene_id: str,
        industry: str,
        role: str,
        purchase_intent: str,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        system_prompt: str = "",
        customer_persona: str = ""
    ) -> TrainingSession:
        session_id = str(uuid.uuid4())
        
        session = TrainingSession(
            session_id=session_id,
            user_id=user_id,
            scene_id=scene_id,
            industry=industry,
            role=role,
            purchase_intent=purchase_intent,
            difficulty=difficulty,
            status=TrainingStatus.IN_PROGRESS,
            system_prompt=system_prompt,
            customer_persona=customer_persona
        )
        
        self.sessions[session_id] = session
        logging.info(f"创建训练会话: {session_id}")
        
        return session
    
    def add_transcript(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: Optional[str] = None
    ):
        if session_id not in self.sessions:
            logging.error(f"会话不存在: {session_id}")
            return
        
        message = TranscriptMessage(
            role=role,
            content=content,
            timestamp=timestamp or datetime.now().strftime("%H:%M:%S")
        )
        
        self.sessions[session_id].transcript.append(message)
    
    def end_session(self, session_id: str) -> Optional[TrainingSession]:
        if session_id not in self.sessions:
            logging.error(f"会话不存在: {session_id}")
            return None
        
        session = self.sessions[session_id]
        session.status = TrainingStatus.COMPLETED
        session.end_time = datetime.now()
        session.duration_seconds = int(
            (session.end_time - session.start_time).total_seconds()
        )
        
        self._save_session_record(session)
        
        logging.info(f"结束训练会话: {session_id}, 时长: {session.duration_seconds}秒")
        
        return session
    
    def evaluate_session(self, session_id: str) -> Optional[AssessmentResult]:
        if session_id not in self.sessions:
            logging.error(f"会话不存在: {session_id}")
            return None
        
        session = self.sessions[session_id]
        
        if not session.transcript:
            logging.warning(f"会话无对话记录: {session_id}")
            return None
        
        weights = self._get_industry_weights(session.industry)
        
        transcript_text = self._format_transcript(session.transcript)
        
        prompt = EVALUATION_PROMPT_TEMPLATE.format(
            industry=session.industry,
            role=session.role,
            purchase_intent=session.purchase_intent,
            difficulty=session.difficulty.value,
            duration=session.duration_seconds,
            turn_count=len(session.transcript),
            transcript=transcript_text,
            weight_communication=int(weights.get("沟通技巧", 0.20) * 100),
            weight_product=int(weights.get("产品知识", 0.20) * 100),
            weight_needs=int(weights.get("需求挖掘", 0.20) * 100),
            weight_objection=int(weights.get("异议处理", 0.20) * 100),
            weight_closing=int(weights.get("促成技巧", 0.20) * 100)
        )
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=EVALUATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            result_json = self._extract_json(response.content)
            result_data = json.loads(result_json)
            
            assessment = self._parse_assessment_result(result_data, session)
            
            session.assessment = assessment
            
            self._save_assessment(session_id, assessment)
            
            self._update_user_profile(session.user_id, assessment)
            
            logging.info(f"评估完成: {session_id}, 综合得分: {assessment.overall_score}")
            
            return assessment
            
        except Exception as e:
            logging.error(f"评估失败: {str(e)}", exc_info=True)
            return None
    
    def _get_industry_weights(self, industry: str) -> Dict[str, float]:
        for key, weights in INDUSTRY_ASSESSMENT_WEIGHTS.items():
            if key in industry:
                return weights
        return EVALUATION_DIMENSIONS
    
    def _format_transcript(self, transcript: List[TranscriptMessage]) -> str:
        lines = []
        for i, msg in enumerate(transcript, 1):
            role_name = "销售" if msg.role == "user" else "客户"
            lines.append(f"[{msg.timestamp}] {role_name}: {msg.content}")
        return "\n".join(lines)
    
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
    
    def _parse_assessment_result(
        self, 
        data: Dict, 
        session: TrainingSession
    ) -> AssessmentResult:
        dimension_scores = []
        for dim_data in data.get("dimension_scores", []):
            score = DimensionScore(
                dimension_name=dim_data.get("dimension", ""),
                score=dim_data.get("score", 0),
                weight=EVALUATION_DIMENSIONS.get(
                    dim_data.get("dimension", ""), 
                    {"weight": 0.20}
                )["weight"],
                reason=dim_data.get("reason", ""),
                sub_scores=dim_data.get("sub_scores", {})
            )
            dimension_scores.append(score)
        
        key_moments = []
        for moment_data in data.get("key_moments", []):
            moment = KeyMoment(
                time=str(moment_data.get("turn", "")),
                moment_type=moment_data.get("type", ""),
                content=moment_data.get("content", ""),
                handling_quality=moment_data.get("handling", ""),
                suggestion=moment_data.get("suggestion")
            )
            key_moments.append(moment)
        
        return AssessmentResult(
            overall_score=data.get("overall_score", 0),
            dimension_scores=dimension_scores,
            highlights=data.get("highlights", []),
            improvements=data.get("improvements", []),
            golden_sentences=data.get("golden_sentences", []),
            key_moments=key_moments,
            completion_rate=data.get("completion_rate", 0),
            total_turns=len(session.transcript),
            duration_seconds=session.duration_seconds
        )
    
    def _save_session_record(self, session: TrainingSession):
        record_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "scene_id": session.scene_id,
            "industry": session.industry,
            "role": session.role,
            "purchase_intent": session.purchase_intent,
            "difficulty": session.difficulty.value,
            "status": session.status.value,
            "start_time": session.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else None,
            "duration_seconds": session.duration_seconds,
            "transcript": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in session.transcript
            ]
        }
        
        filename = f"{session.session_id}.json"
        filepath = RECORD_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"保存会话记录: {filepath}")
    
    def _save_assessment(self, session_id: str, assessment: AssessmentResult):
        assessment_data = {
            "session_id": session_id,
            "overall_score": assessment.overall_score,
            "dimension_scores": [
                {
                    "dimension": ds.dimension_name,
                    "score": ds.score,
                    "weight": ds.weight,
                    "reason": ds.reason,
                    "sub_scores": ds.sub_scores
                }
                for ds in assessment.dimension_scores
            ],
            "highlights": assessment.highlights,
            "improvements": assessment.improvements,
            "golden_sentences": assessment.golden_sentences,
            "key_moments": [
                {
                    "turn": km.time,
                    "type": km.moment_type,
                    "content": km.content,
                    "handling": km.handling_quality,
                    "suggestion": km.suggestion
                }
                for km in assessment.key_moments
            ],
            "completion_rate": assessment.completion_rate,
            "total_turns": assessment.total_turns,
            "duration_seconds": assessment.duration_seconds,
            "created_at": assessment.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"{session_id}_assessment.json"
        filepath = ASSESSMENT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(assessment_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"保存评估结果: {filepath}")
    
    def _update_user_profile(self, user_id: str, assessment: AssessmentResult):
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserAbilityProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        profile.training_count += 1
        profile.total_duration += assessment.duration_seconds
        
        for ds in assessment.dimension_scores:
            old_score = profile.dimension_scores.get(ds.dimension_name, 0)
            new_score = (old_score * (profile.training_count - 1) + ds.score) / profile.training_count
            profile.dimension_scores[ds.dimension_name] = round(new_score, 1)
        
        total_weight = sum(ds.weight for ds in assessment.dimension_scores)
        weighted_score = sum(
            ds.score * ds.weight for ds in assessment.dimension_scores
        ) / total_weight if total_weight > 0 else 0
        
        old_overall = profile.overall_score
        profile.overall_score = round(
            (old_overall * (profile.training_count - 1) + assessment.overall_score) / profile.training_count, 1
        )
        
        profile.update_level()
        profile.update_strengths_weaknesses()
        
        profile.improvement_history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "score": assessment.overall_score,
            "improvement": assessment.improvements[:2] if assessment.improvements else []
        })
        
        profile.updated_at = datetime.now()
        
        self._save_user_profile(profile)
        
        logging.info(f"更新用户能力画像: {user_id}, 综合得分: {profile.overall_score}")
    
    def _save_user_profile(self, profile: UserAbilityProfile):
        profile_data = {
            "user_id": profile.user_id,
            "overall_score": profile.overall_score,
            "dimension_scores": profile.dimension_scores,
            "training_count": profile.training_count,
            "total_duration": profile.total_duration,
            "level": profile.level,
            "weak_points": profile.weak_points,
            "strong_points": profile.strong_points,
            "improvement_history": profile.improvement_history[-20:],
            "achievements": profile.achievements,
            "created_at": profile.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": profile.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"{profile.user_id}.json"
        filepath = USER_PROFILE_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)
    
    def get_user_profile(self, user_id: str) -> Optional[UserAbilityProfile]:
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        filepath = USER_PROFILE_DIR / f"{user_id}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = UserAbilityProfile(
                user_id=data["user_id"],
                overall_score=data["overall_score"],
                dimension_scores=data["dimension_scores"],
                training_count=data["training_count"],
                total_duration=data["total_duration"],
                level=data["level"],
                weak_points=data["weak_points"],
                strong_points=data["strong_points"],
                improvement_history=data["improvement_history"],
                achievements=data["achievements"],
                created_at=datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S"),
                updated_at=datetime.strptime(data["updated_at"], "%Y-%m-%d %H:%M:%S")
            )
            
            self.user_profiles[user_id] = profile
            return profile
        
        return None
    
    def get_session(self, session_id: str) -> Optional[TrainingSession]:
        return self.sessions.get(session_id)
    
    def get_assessment(self, session_id: str) -> Optional[Dict]:
        filepath = ASSESSMENT_DIR / f"{session_id}_assessment.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_training_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        history = []
        
        for session in self.sessions.values():
            if session.user_id == user_id and session.assessment:
                history.append({
                    "session_id": session.session_id,
                    "industry": session.industry,
                    "role": session.role,
                    "score": session.assessment.overall_score,
                    "duration": session.duration_seconds,
                    "date": session.start_time.strftime("%Y-%m-%d %H:%M")
                })
        
        history.sort(key=lambda x: x["date"], reverse=True)
        
        return history[:limit]
    
    def generate_improvement_suggestions(
        self, 
        user_id: str
    ) -> Optional[Dict]:
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        weak_dims = []
        for dim_name in profile.weak_points:
            score = profile.dimension_scores.get(dim_name, 0)
            weak_dims.append(f"- {dim_name}: {score}分")
        
        prompt = IMPROVEMENT_SUGGESTION_PROMPT.format(
            user_profile=json.dumps({
                "level": profile.level,
                "overall_score": profile.overall_score,
                "training_count": profile.training_count,
                "dimension_scores": profile.dimension_scores
            }, ensure_ascii=False, indent=2),
            weak_dimensions="\n".join(weak_dims) if weak_dims else "无明显薄弱项"
        )
        
        try:
            response = self.llm.invoke([
                HumanMessage(content=prompt)
            ])
            
            result_json = self._extract_json(response.content)
            return json.loads(result_json)
            
        except Exception as e:
            logging.error(f"生成改进建议失败: {str(e)}")
            return None


assessment_service = AssessmentService()
