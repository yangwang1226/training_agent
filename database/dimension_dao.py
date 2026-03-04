import logging
from typing import Optional, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


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
