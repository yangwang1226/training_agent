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
