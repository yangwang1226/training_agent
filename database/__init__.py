from .connection import get_connection, get_db
from .scene_dao import (
    save_scene,
    get_scene_by_id,
    get_scene_by_name,
    list_scenes,
    get_active_scenes,
    get_prompt_by_scene_id,
    get_prompt_by_name,
    SceneStatus
)
from .record_dao import (
    save_coach_record,
    get_coach_record_by_session_id,
    update_coach_record,
    calculate_final_score
)
from .dimension_dao import (
    save_dimension_config,
    get_dimension_config,
    update_dimension_config
)
from .preset_scene_dao import (
    get_preset_scenes_by_industry,
    get_preset_scene_by_code,
    get_all_active_preset_scenes,
    increment_usage_count,
    get_industries_with_scene_count,
    create_scene_from_preset,
    build_preset_prompt
)

__all__ = [
    'get_connection',
    'get_db',
    'save_scene',
    'get_scene_by_id',
    'get_scene_by_name',
    'list_scenes',
    'get_active_scenes',
    'get_prompt_by_scene_id',
    'get_prompt_by_name',
    'SceneStatus',
        'save_coach_record',
    'get_coach_record_by_session_id',
    'update_coach_record',
    'calculate_final_score',
    'save_dimension_config',
    'get_dimension_config',
    'update_dimension_config',
    'get_preset_scenes_by_industry',
    'get_preset_scene_by_code',
    'get_all_active_preset_scenes',
    'increment_usage_count',
    'get_industries_with_scene_count',
    'create_scene_from_preset',
    'build_preset_prompt'
]
