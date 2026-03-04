import logging
from flask import Blueprint, jsonify, request

import db as db_module

logger = logging.getLogger(__name__)

scene_bp = Blueprint('scene', __name__, url_prefix='/api')


@scene_bp.route('/scenes', methods=['GET'])
def list_scenes():
    try:
        scenes = db_module.list_scenes()
        scenes_list = [
            {
                'id': scene['id'],
                'name': scene['scene_name'],
                'created_at': scene['created_time'].strftime('%Y-%m-%d %H:%M:%S') if scene.get('created_time') else ''
            }
            for scene in scenes
        ]
        return jsonify({'scenes': scenes_list})
    except Exception as e:
        logging.error(f"获取场景列表失败: {str(e)}", exc_info=True)
        return jsonify({'scenes': []})


@scene_bp.route('/save', methods=['POST'])
def save():
    data = request.json
    name = data.get('name', '').strip()
    prompt = data.get('prompt', '')
    
    logging.info(f"收到保存请求: name={name}")
    
    if not name:
        return jsonify({
            'success': False,
            'error': '请输入场景名称'
        })
    
    if not prompt:
        return jsonify({
            'success': False,
            'error': '没有可保存的提示词'
        })
    
    try:
        scene_id = db_module.save_scene(name, prompt, status=0)
        
        if scene_id:
            logging.info(f"场景保存成功: id={scene_id}, name={name}")
            return jsonify({
                'success': True,
                'scene_id': scene_id,
                'message': f'场景已保存'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失败'
            })
    except Exception as e:
        logging.error(f"保存场景失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        })


@scene_bp.route('/realtime/prompt/<scene_id>')
def get_realtime_prompt(scene_id):
    try:
        scene_id_int = int(scene_id)
        prompt = db_module.get_prompt_by_scene_id(scene_id_int)
        if prompt:
            return jsonify({'success': True, 'prompt': prompt})
        else:
            return jsonify({'success': False, 'error': '场景不存在'})
    except ValueError:
        return jsonify({'success': False, 'error': '无效的场景ID'})
    except Exception as e:
        logging.error(f"获取场景提示词失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})
