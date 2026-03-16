"""后台管理系统路由"""
import logging
from pathlib import Path
from flask import Blueprint, render_template, jsonify, request, send_from_directory, render_template_string

import db as db_module
from database.scene_dao import list_scenes, get_scene_by_id
from database.preset_scene_dao import get_all_active_preset_scenes, get_preset_scene_by_code

logger = logging.getLogger(__name__)

# 创建蓝图
manage_bp = Blueprint(
    'manage',
    __name__,
    url_prefix='/manage_system',
    template_folder=str(Path(__file__).parent.parent / 'front_end' / 'manage_system' / 'templates'),
    static_folder=str(Path(__file__).parent.parent / 'front_end' / 'manage_system' / 'static')
)

# 静态文件路由
@manage_bp.route('/static/<path:filename>')
def manage_static(filename):
    """提供静态文件"""
    static_dir = Path(__file__).parent.parent / 'front_end' / 'manage_system' / 'static'
    return send_from_directory(static_dir, filename)


# ==================== 页面路由 ====================

@manage_bp.route('/')
def index():
    """后台管理首页（仪表盘）"""
    return render_template('dashboard.html')


@manage_bp.route('/scenes')
def scenes_page():
    """场景管理页面"""
    return render_template('scenes/index.html')


@manage_bp.route('/scenes/preset')
def preset_scenes_page():
    """预设场景页面"""
    return render_template('scenes/preset.html')


@manage_bp.route('/scenes/custom')
def custom_scenes_page():
    """自定义场景页面"""
    return render_template('scenes/custom.html')


@manage_bp.route('/scene-config')
def scene_config_page():
    """场景配置页面（嵌入管理系统）"""
    return render_template('scenes/config.html')


@manage_bp.route('/scenes/edit/<int:scene_id>')
def edit_scene_page(scene_id):
    """场景编辑页面"""
    return render_template('scenes/edit.html', scene_id=scene_id)


# ==================== API路由 ====================

@manage_bp.route('/api/scenes', methods=['GET'])
def get_scenes_api():
    """获取场景列表API（包括所有状态的自定义场景）"""
    try:
        # 获取所有未删除的场景（包括草稿、进行中、已完成）
        from database.connection import get_db
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT * 
                    FROM ai_coach_scene 
                    WHERE deleted = 0
                    ORDER BY created_time DESC
                """
                cursor.execute(sql)
                scenes = cursor.fetchall()
        
        # 为每个场景添加训练次数统计（后续可以从训练记录表统计）
        for scene in scenes:
            scene['training_count'] = 0  # 暂时设为0，后续可以从数据库统计
        
        return jsonify({
            'success': True,
            'data': scenes
        })
    except Exception as e:
        logger.error(f"获取场景列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/scenes/<int:scene_id>', methods=['GET'])
def get_scene_detail_api(scene_id):
    """获取场景详情API"""
    try:
        scene = get_scene_by_id(scene_id)
        
        if not scene:
            return jsonify({
                'success': False,
                'message': '场景不存在'
            }), 404
        
        # 添加训练次数统计
        scene['training_count'] = 0  # 暂时设为0
        
        return jsonify({
            'success': True,
            'data': scene
        })
    except Exception as e:
        logger.error(f"获取场景详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/scenes/<int:scene_id>', methods=['DELETE'])
def delete_scene_api(scene_id):
    """删除场景API（软删除）"""
    try:
        scene = get_scene_by_id(scene_id)
        
        if not scene:
            return jsonify({
                'success': False,
                'message': '场景不存在'
            }), 404
        
        # 执行软删除
        success = db_module.soft_delete_scene(scene_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 500
    except Exception as e:
        logger.error(f"删除场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/scenes/<int:scene_id>', methods=['PUT'])
def update_scene_api(scene_id):
    """更新场景API"""
    try:
        scene = get_scene_by_id(scene_id)
        
        if not scene:
            return jsonify({
                'success': False,
                'message': '场景不存在'
            }), 404
        
        data = request.json
        
        # 更新场景信息
        success = db_module.update_scene(
            scene_id=scene_id,
            scene_name=data.get('scene_name'),
            scene_prompt=data.get('scene_prompt'),
            background_hint=data.get('background_hint'),
            role_type=data.get('role_type'),
            role_description=data.get('role_description'),
            industry=data.get('industry'),
            training_goal=data.get('training_goal'),
            dimension_config=data.get('dimension_config'),
            sop_checklist=data.get('sop_checklist')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新失败'
            }), 500
    except Exception as e:
        logger.error(f"更新场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/stats/overview', methods=['GET'])
def get_stats_overview():
    """获取统计概览数据"""
    try:
        # 这里可以添加更多统计数据
        scenes = list_scenes()
        
        total_scenes = len(scenes)
        preset_scenes = len([s for s in scenes if s.get('status') == 1])
        custom_scenes = len([s for s in scenes if s.get('status') == 2])
        draft_scenes = len([s for s in scenes if s.get('status') == 0])
        
        return jsonify({
            'success': True,
            'data': {
                'total_scenes': total_scenes,
                'preset_scenes': preset_scenes,
                'custom_scenes': custom_scenes,
                'draft_scenes': draft_scenes
            }
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/preset-scenes', methods=['GET'])
def get_preset_scenes_api():
    """获取预设场景列表API"""
    try:
        scenes = get_all_active_preset_scenes()
        return jsonify({
            'success': True,
            'data': scenes
        })
    except Exception as e:
        logger.error(f"获取预设场景列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@manage_bp.route('/api/preset-scenes/<scene_code>', methods=['GET'])
def get_preset_scene_detail_api(scene_code):
    """获取预设场景详情API"""
    try:
        scene = get_preset_scene_by_code(scene_code)
        
        if not scene:
            return jsonify({
                'success': False,
                'message': '场景不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': scene
        })
    except Exception as e:
        logger.error(f"获取预设场景详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
