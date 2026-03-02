import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ai_coach_test'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


@contextmanager
def get_db():
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def save_scene(scene_name: str, scene_prompt: str, status: int = 0, org_id: int = None, 
               creator_id: int = None, create_name: str = None) -> Optional[int]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO ai_coach_scene (scene_name, scene_prompt, status, org_id, creator_id, create_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (scene_name, scene_prompt, status, org_id, creator_id, create_name))
            conn.commit()
            scene_id = cursor.lastrowid
            logger.info(f"场景保存成功: id={scene_id}, scene_name={scene_name}")
            return scene_id


def get_scene_by_id(scene_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ai_coach_scene WHERE id = %s AND deleted = 0 AND status = 0"
            cursor.execute(sql, (scene_id,))
            return cursor.fetchone()


def get_scene_by_name(scene_name: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ai_coach_scene WHERE scene_name = %s AND deleted = 0 AND status = 0"
            cursor.execute(sql, (scene_name,))
            return cursor.fetchone()


def list_scenes() -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, scene_name, created_time, auto_update_time FROM ai_coach_scene WHERE deleted = 0 AND status = 0 ORDER BY created_time DESC"
            cursor.execute(sql)
            return cursor.fetchall()


def get_prompt_by_scene_id(scene_id: int) -> Optional[str]:
    scene = get_scene_by_id(scene_id)
    if scene:
        return scene.get('scene_prompt')
    return None


def get_prompt_by_name(scene_name: str) -> Optional[str]:
    scene = get_scene_by_name(scene_name)
    if scene:
        return scene.get('scene_prompt')
    return None


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


def save_dimension_config(
    scene_id: int,
    role_type: str,
    role_description: str,
    industry: str,
    training_goal: str,
    dimensions_json: str,
    full_evaluation_prompt: str
) -> bool:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                UPDATE ai_coach_scene 
                SET dimension_config = %s,
                    role_type = %s,
                    role_description = %s,
                    industry = %s,
                    training_goal = %s,
                    full_evaluation_prompt = %s
                WHERE id = %s
            """
            cursor.execute(sql, (
                dimensions_json, role_type, role_description, industry, 
                training_goal, full_evaluation_prompt, scene_id
            ))
            conn.commit()
            logger.info(f"维度配置保存成功: scene_id={scene_id}")
            return True


def get_dimension_config(scene_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT id, scene_name, dimension_config, role_type, role_description, 
                       industry, training_goal, full_evaluation_prompt
                FROM ai_coach_scene 
                WHERE id = %s AND deleted = 0
            """
            cursor.execute(sql, (scene_id,))
            result = cursor.fetchone()
            if result and result.get('dimension_config'):
                return result
            return None


def update_dimension_config(scene_id: int, dimensions_json: str, full_evaluation_prompt: str) -> bool:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                UPDATE ai_coach_scene 
                SET dimension_config = %s,
                    full_evaluation_prompt = %s
                WHERE id = %s
            """
            cursor.execute(sql, (dimensions_json, full_evaluation_prompt, scene_id))
            conn.commit()
            logger.info(f"维度配置更新成功: scene_id={scene_id}")
            return True
