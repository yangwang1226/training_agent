import json
import logging
from typing import Optional, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


def calculate_final_score(ai_score: int = None, sop_score: int = None) -> int:
    """
    计算最终成绩（综合评分）
    公式：final_score = ai_score * 0.4 + sop_score * 0.6
    
    Args:
        ai_score: AI维度评分 (0-100)
        sop_score: SOP流程评分 (0-100)
    
    Returns:
        最终成绩 (0-100)，如果两个分数都为 None 则返回 0
    """
    if ai_score is None:
        ai_score = 0
    if sop_score is None:
        sop_score = 0
    
    # 加权平均：AI 40%, SOP 60%
    final_score = ai_score * 0.4 + sop_score * 0.6
    return round(final_score)


def save_coach_record(
    session_id: str,
    scene_id: int,
    user_id: int,
    word_content: str = None,
    oss_file_path: str = None,
    call_duration: int = None,
    ai_score: int = None,
    ai_summary: str = None,
    dimension_result: str = None,
    ai_advise: str = None,
    sop_result: str = None,
    sop_score: int = None
) -> bool:
    """保存训练记录
    
    Args:
        session_id: 会话ID
        scene_id: 场景ID
        user_id: 用户ID
        word_content: 对话内容
        oss_file_path: 音频文件路径
        call_duration: 通话时长(秒)
        ai_score: AI综合评分(0-100)
        ai_summary: AI评估总结
        dimension_result: 维度评分详情(JSON字符串)
        ai_advise: AI改进建议
        sop_result: SOP质检结果(JSON字符串)
        sop_score: SOP质检总分(0-100)
    """
    def _ensure_str(value, field_name=""):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        logger.warning(f"字段 {field_name} 类型异常: {type(value)}, 将转换为字符串")
        return str(value)
    
    word_content = _ensure_str(word_content, "word_content")
    oss_file_path = _ensure_str(oss_file_path, "oss_file_path")
    ai_summary = _ensure_str(ai_summary, "ai_summary")
    dimension_result = _ensure_str(dimension_result, "dimension_result")
    ai_advise = _ensure_str(ai_advise, "ai_advise")
    sop_result = _ensure_str(sop_result, "sop_result")
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            final_score = calculate_final_score(ai_score, sop_score)
            
            sql = """
                INSERT INTO ai_coach_record 
                (session_id, scene_id, user_id, word_content, oss_file_path, call_duration,
                 ai_score, ai_summary, dimension_result, ai_advise, sop_result, sop_score, final_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                word_content = VALUES(word_content),
                oss_file_path = VALUES(oss_file_path),
                call_duration = VALUES(call_duration),
                ai_score = VALUES(ai_score),
                ai_summary = VALUES(ai_summary),
                dimension_result = VALUES(dimension_result),
                ai_advise = VALUES(ai_advise),
                sop_result = VALUES(sop_result),
                sop_score = VALUES(sop_score)
            """
            cursor.execute(sql, (
                session_id, scene_id, user_id, word_content, oss_file_path, call_duration,
                ai_score, ai_summary, dimension_result, ai_advise, sop_result, sop_score, final_score
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
        'word_content', 'oss_file_path', 'call_duration', 
        'ai_score', 'ai_summary', 'dimension_result', 'ai_advise', 
        'sop_result', 'sop_score', 'final_score'
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
    # 检查是否需要重新计算 final_score
    need_recalculate_final = 'ai_score' in kwargs or 'sop_score' in kwargs
    
    for key, value in kwargs.items():
        if key in ALLOWED_UPDATE_FIELDS:
            set_clauses.append(f"{key} = %s")
            values.append(value)
        else:
            logger.warning(f"update_coach_record: 忽略不允许更新的字段 '{key}'")
    
    # 如果更新了评分字段，自动重新计算 final_score
    if need_recalculate_final:
        # 获取当前记录的评分
        current_record = get_coach_record_by_session_id(session_id)
        if current_record:
            ai_score = kwargs.get('ai_score', current_record.get('ai_score'))
            sop_score = kwargs.get('sop_score', current_record.get('sop_score'))
            new_final_score = calculate_final_score(ai_score, sop_score)
            set_clauses.append("final_score = %s")
            values.append(new_final_score)
            logger.info(f"自动计算 final_score: ai_score={ai_score}, sop_score={sop_score}, final_score={new_final_score}")
    
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
