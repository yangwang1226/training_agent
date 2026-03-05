import logging
from typing import Optional, List, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


def save_scene(
    scene_name: str, 
    scene_prompt: str, 
    status: int = 0, 
    org_id: int = None, 
    creator_id: int = None, 
    create_name: str = None,
    dimension_config: str = None,
    role_type: str = None,
    role_description: str = None,
    industry: str = None,
    training_goal: str = None,
    full_evaluation_prompt: str = None
) -> Optional[int]:
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO ai_coach_scene 
                (scene_name, scene_prompt, status, org_id, creator_id, create_name,
                 dimension_config, role_type, role_description, industry, training_goal, full_evaluation_prompt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                scene_name, scene_prompt, status, org_id, creator_id, create_name,
                dimension_config, role_type, role_description, industry, training_goal, full_evaluation_prompt
            ))
            conn.commit()
            scene_id = cursor.lastrowid
            logger.info(f"场景保存成功：id={scene_id}, scene_name={scene_name}")
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
