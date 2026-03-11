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


# 允许更新的字段白名单（从数据库表结构动态获取更好，这里先硬编码）
ALLOWED_UPDATE_FIELDS = {
    'word_content', 'oss_file_path', 'call_duration', 'ai_evaluate',
    'ai_advise', 'score', 'sop_result', 'audio_analysis'
}

def update_coach_record(session_id: str, **kwargs) -> bool:
    """
    更新训练记录
    
    Args:
        session_id: 会话ID
        **kwargs: 要更新的字段和值
    
    Returns:
        是否更新成功
    """
    if not kwargs:
        logger.warning("update_coach_record: 没有提供要更新的字段")
        return False
    
    # 过滤出允许更新的字段
    set_clauses = []
    values = []
    for key, value in kwargs.items():
        if key in ALLOWED_UPDATE_FIELDS:
            set_clauses.append(f"{key} = %s")
            values.append(value)
        else:
            logger.warning(f"update_coach_record: 忽略不允许更新的字段 '{key}'")
    
    if not set_clauses:
        logger.warning("update_coach_record: 没有有效的字段可更新")
        return False
    
    values.append(session_id)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = f"UPDATE ai_coach_record SET {', '.join(set_clauses)} WHERE session_id = %s"
                cursor.execute(sql, values)
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"训练记录不存在或未更新: session_id={session_id}")
                    return False
                    
                logger.info(f"训练记录更新成功: session_id={session_id}, 更新字段: {list(kwargs.keys())}")
                return True
    except Exception as e:
        logger.error(f"更新训练记录失败: {e}")
        return False
