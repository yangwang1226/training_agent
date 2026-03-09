import logging
import json
import time
from typing import Optional, List, Dict, Any

from .connection import get_db
from .scene_dao import save_scene, SceneStatus

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


def build_preset_prompt(preset: Dict[str, Any], background_hint: Optional[str] = None) -> str:
    """
    构建预设场景的完整提示词
    
    Args:
        preset: 预设场景数据
        background_hint: 用户补充的背景信息（可选）
    
    Returns:
        完整的场景提示词
    """
    prompt_parts = []
    
    # 1. 场景背景
    if preset.get('background_template'):
        background = preset['background_template']
        # 如果用户提供了背景补充，融入到模板中
        if background_hint:
            background += f"\n\n【用户补充背景】\n{background_hint}"
        prompt_parts.append(f"## 场景背景\n{background}")
    
    # 2. 主要问题
    if preset.get('main_questions_template'):
        prompt_parts.append(f"## 主要问题\n{preset['main_questions_template']}")
    
    # 3. 触发器组
    if preset.get('trigger_groups_template'):
        prompt_parts.append(f"## 触发器组\n{preset['trigger_groups_template']}")
    
    # 4. 评估维度
    if preset.get('dimensions_template'):
        prompt_parts.append(f"## 评估维度\n{preset['dimensions_template']}")
    
    # 5. 情绪设定
    if preset.get('emotion_template'):
        prompt_parts.append(f"## 情绪设定\n{preset['emotion_template']}")
    
    return "\n\n".join(prompt_parts)


def create_scene_from_preset(
    preset_scene_code: str,
    background_hint: Optional[str] = None,
    org_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    create_name: Optional[str] = None
) -> Optional[int]:
    """
    从预设场景快速创建用户场景
    
    Args:
        preset_scene_code: 预设场景代码
        background_hint: 用户补充的背景信息（可选）
        org_id: 组织ID（可选）
        creator_id: 创建者ID（可选）
        create_name: 创建者名称（可选）
    
    Returns:
        scene_id: 创建的场景ID，失败返回 None
    """
    try:
        # 1. 获取预设场景数据
        preset = get_preset_scene_by_code(preset_scene_code)
        if not preset:
            logger.error(f"预设场景不存在: {preset_scene_code}")
            return None
        
        # 2. 构建场景名称（添加时间戳避免重复）
        timestamp = int(time.time())
        scene_name = f"{preset['scene_name']}_{timestamp}"
        
        # 3. 构建完整的场景提示词
        scene_prompt = build_preset_prompt(preset, background_hint)
        
        # 4. 构建维度配置
        dimension_config_dict = {
            "industry": preset.get('industry_name', preset.get('industry_code', '')),
            "role_type": preset.get('ai_role', ''),
            "dimensions": []
        }
        
        # 如果有维度模板，尝试解析
        if preset.get('dimensions_template'):
            try:
                # 这里可以根据实际需要解析维度模板
                # 暂时使用空列表，后续可以扩展
                pass
            except Exception as e:
                logger.warning(f"解析维度模板失败: {e}")
        
        dimension_config = json.dumps(dimension_config_dict, ensure_ascii=False)
        
        # 5. 保存场景
        scene_id = save_scene(
            scene_name=scene_name,
            scene_prompt=scene_prompt,
            dimension_config=dimension_config,
            role_type=preset.get('ai_role'),
            role_description=preset.get('scene_description'),
            industry=preset.get('industry_name', preset.get('industry_code')),
            training_goal=f"提升{preset.get('user_role', '学员')}的沟通能力",
            full_evaluation_prompt=scene_prompt,
            status=SceneStatus.PRESET_TEMPLATE,  # 标记为预设模板
            org_id=org_id,
            creator_id=creator_id,
            create_name=create_name
        )
        
        if scene_id:
            # 6. 增加预设场景的使用次数
            increment_usage_count(preset_scene_code)
            logger.info(f"从预设场景创建成功: scene_id={scene_id}, preset_code={preset_scene_code}")
        
        return scene_id
        
    except Exception as e:
        logger.error(f"从预设场景创建失败: {e}", exc_info=True)
        return None