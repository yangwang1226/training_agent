import logging
from typing import Optional, List, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


class SceneStatus:
    """场景状态枚举"""
    DRAFT = 0           # 草稿（对话创建中，未完成）
    PRESET_TEMPLATE = 1 # 预设模板（从预设场景快速生成，可直接使用）
    CUSTOMIZED = 2      # 已定制（对话创建完成，包含个性化背景）
    ARCHIVED = 9        # 已归档（禁用/删除）


def save_scene(
    scene_name: str, 
    scene_prompt: str, 
    status: int = SceneStatus.CUSTOMIZED, 
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
    """获取场景详情（不限制状态）"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ai_coach_scene WHERE id = %s AND deleted = 0"
            cursor.execute(sql, (scene_id,))
            return cursor.fetchone()


def get_scene_by_name(scene_name: str) -> Optional[Dict[str, Any]]:
    """获取场景详情（不限制状态）"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ai_coach_scene WHERE scene_name = %s AND deleted = 0"
            cursor.execute(sql, (scene_name,))
            return cursor.fetchone()


def list_scenes() -> List[Dict[str, Any]]:
    """获取所有可用场景（排除草稿和归档）"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT id, scene_name, status, created_time, auto_update_time 
                FROM ai_coach_scene 
                WHERE deleted = 0 AND status IN (%s, %s)
                ORDER BY created_time DESC
            """
            cursor.execute(sql, (SceneStatus.PRESET_TEMPLATE, SceneStatus.CUSTOMIZED))
            return cursor.fetchall()


def get_active_scenes() -> List[Dict[str, Any]]:
    """获取所有可用场景（排除草稿和归档）- 别名函数"""
    return list_scenes()


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
