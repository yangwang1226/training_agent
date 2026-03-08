import logging
from typing import Optional, List, Dict, Any

from .connection import get_db

logger = logging.getLogger(__name__)


def get_preset_scenes_by_industry(industry_code: str) -> List[Dict[str, Any]]:
    """
    根据行业代码获取预设场景列表
    
    Args:
        industry_code: 行业代码 (如 'automobile', 'education')
    
    Returns:
        预设场景列表
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, industry_code, scene_code, scene_name, scene_description,
                    scene_tag, ai_role, user_role, difficulty, estimated_duration,
                    display_order, usage_count
                FROM ai_coach_preset_scene 
                WHERE industry_code = %s AND is_active = 1
                ORDER BY display_order ASC, usage_count DESC
            """
            cursor.execute(sql, (industry_code,))
            return cursor.fetchall()


def get_preset_scene_by_code(scene_code: str) -> Optional[Dict[str, Any]]:
    """
    根据场景代码获取完整的预设场景信息
    
    Args:
        scene_code: 场景代码 (如 'auto_first_visit')
    
    Returns:
        完整的预设场景信息（包含模板）
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT * FROM ai_coach_preset_scene 
                WHERE scene_code = %s AND is_active = 1
            """
            cursor.execute(sql, (scene_code,))
            return cursor.fetchone()


def get_all_active_preset_scenes() -> List[Dict[str, Any]]:
    """
    获取所有激活的预设场景（用于管理页面）
    
    Returns:
        所有激活的预设场景列表
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, industry_code, scene_code, scene_name, scene_description,
                    scene_tag, ai_role, user_role, difficulty, estimated_duration,
                    display_order, usage_count, created_time
                FROM ai_coach_preset_scene 
                WHERE is_active = 1
                ORDER BY industry_code ASC, display_order ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()


def increment_usage_count(scene_code: str) -> bool:
    """
    增加场景使用次数
    
    Args:
        scene_code: 场景代码
    
    Returns:
        是否成功
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE ai_coach_preset_scene 
                    SET usage_count = usage_count + 1 
                    WHERE scene_code = %s
                """
                cursor.execute(sql, (scene_code,))
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"更新使用次数失败: {e}")
        return False


def get_industries_with_scene_count() -> List[Dict[str, Any]]:
    """
    获取所有行业及其场景数量
    
    Returns:
        行业列表（包含场景数量）
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    industry_code,
                    COUNT(*) as scene_count
                FROM ai_coach_preset_scene 
                WHERE is_active = 1
                GROUP BY industry_code
                ORDER BY industry_code ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()