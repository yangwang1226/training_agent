import logging
import json
from flask import Blueprint, jsonify, request

import db as db_module

logger = logging.getLogger(__name__)

preset_scene_bp = Blueprint('preset_scene', __name__, url_prefix='/api/preset-scene')


@preset_scene_bp.route('/industry/<industry_code>', methods=['GET'])
def get_scenes_by_industry(industry_code: str):
    """
    根据行业代码获取预设场景列表
    
    路径参数:
        industry_code: 行业代码 (如 'automobile', 'education')
    
    返回:
        {
            "success": true,
            "scenes": [
                {
                    "id": 1,
                    "scene_code": "auto_first_visit",
                    "scene_name": "客户首次到店接待",
                    "scene_description": "模拟客户首次进入4S店的接待场景",
                    "scene_tag": "hot",
                    "ai_role": "想看车的客户",
                    "user_role": "汽车销售顾问",
                    "difficulty": "easy",
                    "estimated_duration": 300,
                    "usage_count": 150
                },
                ...
            ]
        }
    """
    try:
        scenes = db_module.get_preset_scenes_by_industry(industry_code)
        
        return jsonify({
            'success': True,
            'industry_code': industry_code,
            'count': len(scenes),
            'scenes': scenes
        })
    except Exception as e:
        logger.error(f"获取预设场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/detail/<scene_code>', methods=['GET'])
def get_scene_detail(scene_code: str):
    """
    根据场景代码获取完整的预设场景信息（包含模板）
    
    路径参数:
        scene_code: 场景代码 (如 'auto_first_visit')
    
    返回:
        {
            "success": true,
            "scene": {
                "id": 1,
                "scene_code": "auto_first_visit",
                "scene_name": "客户首次到店接待",
                "scene_description": "模拟客户首次进入4S店的接待场景",
                "ai_role": "想看车的客户",
                "user_role": "汽车销售顾问",
                "difficulty": "easy",
                "estimated_duration": 300,
                "default_params": {...},
                "background_template": "...",
                "main_questions_template": "...",
                "trigger_groups_template": "...",
                "dimensions_template": "...",
                "emotion_template": "..."
            }
        }
    """
    try:
        scene = db_module.get_preset_scene_by_code(scene_code)
        
        if not scene:
            return jsonify({
                'success': False,
                'error': f'场景不存在: {scene_code}'
            }), 404
        
        # 解析 JSON 字段
        if scene.get('default_params'):
            try:
                scene['default_params'] = json.loads(scene['default_params'])
            except:
                scene['default_params'] = {}
        
        return jsonify({
            'success': True,
            'scene': scene
        })
    except Exception as e:
        logger.error(f"获取场景详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/all', methods=['GET'])
def get_all_scenes():
    """
    获取所有激活的预设场景
    
    返回:
        {
            "success": true,
            "count": 10,
            "scenes": [...]
        }
    """
    try:
        scenes = db_module.get_all_active_preset_scenes()
        
        return jsonify({
            'success': True,
            'count': len(scenes),
            'scenes': scenes
        })
    except Exception as e:
        logger.error(f"获取所有预设场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/industries', methods=['GET'])
def get_industries():
    """
    获取所有行业及其场景数量
    
    返回:
        {
            "success": true,
            "industries": [
                {"industry_code": "automobile", "scene_count": 5},
                {"industry_code": "education", "scene_count": 5}
            ]
        }
    """
    try:
        industries = db_module.get_industries_with_scene_count()
        
        return jsonify({
            'success': True,
            'count': len(industries),
            'industries': industries
        })
    except Exception as e:
        logger.error(f"获取行业列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/use/<scene_code>', methods=['POST'])
def use_preset_scene(scene_code: str):
    """
    使用预设场景（增加使用次数）
    
    路径参数:
        scene_code: 场景代码
    
    返回:
        {
            "success": true,
            "message": "使用次数已更新"
        }
    """
    try:
        success = db_module.increment_usage_count(scene_code)
        
        if success:
            return jsonify({
                'success': True,
                'message': '使用次数已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新失败'
            }), 500
    except Exception as e:
        logger.error(f"更新使用次数失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/quick-start/<scene_code>', methods=['POST'])
def quick_start_scene(scene_code: str):
    """
    快速启动预设场景
    
    路径参数:
        scene_code: 场景代码
    
    请求体:
        {
            "background_hint": "客户是30岁女性..." (可选)
        }
    
    返回:
        {
            "success": true,
            "scene_id": 123,
            "redirect_url": "/realtime/123",
            "message": "场景已准备就绪！"
        }
    """
    try:
        # 获取请求数据
        data = request.json or {}
        background_hint = data.get('background_hint', '').strip()
        
        # 可选的用户信息（如果有登录系统）
        org_id = data.get('org_id')
        creator_id = data.get('creator_id')
        create_name = data.get('create_name')
        
        # 从预设场景快速创建
        scene_id = db_module.create_scene_from_preset(
            preset_scene_code=scene_code,
            background_hint=background_hint if background_hint else None,
            org_id=org_id,
            creator_id=creator_id,
            create_name=create_name
        )
        
        if not scene_id:
            return jsonify({
                'success': False,
                'error': '场景创建失败，请检查场景代码是否正确'
            }), 500
        
        logger.info(f"快速启动场景成功: scene_code={scene_code}, scene_id={scene_id}")
        
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'redirect_url': f'/realtime/{scene_id}',
            'message': '场景已准备就绪！'
        })
        
    except Exception as e:
        logger.error(f"快速启动场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'创建失败: {str(e)}'
        }), 500