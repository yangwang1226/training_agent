import logging
from typing import Optional, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


def save_coach_record(
    session_id: str,
    scene_id: int,
    user_id: int,
    word_content: str = None,
    oss_file_path: str = None,
    call_duration: int = None,
    ai_evaluate: str = None,
    ai_advise: str = None,
    score: int = None,
    sop_result: str = None,
    audio_analysis: str = None
) -> bool:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO ai_coach_record 
                (session_id, scene_id, user_id, word_content, oss_file_path, call_duration,
                 ai_evaluate, ai_advise, score, sop_result, audio_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                word_content = VALUES(word_content),
                oss_file_path = VALUES(oss_file_path),
                call_duration = VALUES(call_duration),
                ai_evaluate = VALUES(ai_evaluate),
                ai_advise = VALUES(ai_advise),
                score = VALUES(score),
                sop_result = VALUES(sop_result),
                audio_analysis = VALUES(audio_analysis)
            """
            cursor.execute(sql, (
                session_id, scene_id, user_id, word_content, oss_file_path, call_duration,
                ai_evaluate, ai_advise, score, sop_result, audio_analysis
            ))
            conn.commit()
            logger.info(f"训练记录保存成功: session_id={session_id}")
            return True


def get_coach_record_by_session_id(session_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ai_coach_record WHERE session_id = %s AND is_delete = 0"
            cursor.execute(sql, (session_id,))
            return cursor.fetchone()


def update_coach_record(session_id: str, **kwargs) -> bool:
    if not kwargs:
        return False
    
    set_clauses = []
    values = []
    for key, value in kwargs.items():
        if key in ['word_content', 'oss_file_path', 'call_duration', 'ai_evaluate', 
                   'ai_advise', 'score', 'sop_result', 'audio_analysis']:
            set_clauses.append(f"{key} = %s")
            values.append(value)
    
    if not set_clauses:
        return False
    
    values.append(session_id)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = f"UPDATE ai_coach_record SET {', '.join(set_clauses)} WHERE session_id = %s"
            cursor.execute(sql, values)
            conn.commit()
            logger.info(f"训练记录更新成功: session_id={session_id}")
            return True
