"""
场景提示词生成相关路由
"""

import logging
import json
from flask import Blueprint, request, jsonify
import db as db_module
from agent.service.scene.prompt_generation_service import PromptGenerationService

logger = logging.getLogger(__name__)

scene_prompt_bp = Blueprint('scene_prompt', __name__, url_prefix='/api/scene-prompt')

prompt_service = PromptGenerationService()


@scene_prompt_bp.route('/generate-and-save', methods=['POST'])
def generate_and_save_prompt():
    """
    生成场景提示词并保存为草稿
    
    请求体:
    {
        "scene_name": "场景名称",
        "scene_type": "sales" 或 "service",
        "ai_role": "AI角色",
        "user_role": "用户角色",
        "industry": "行业",
        "scene_description": "场景描述",
        "background_info": "背景信息",
        "fixed_questions": [{"question": "问题1", "order": 1}, ...],
        "related_questions": [{"question": "关联问题", "trigger_keywords": [...]}, ...],
        "purchase_intent": "一般" (仅sales场景),
        "problem_severity": "中等" (仅service场景),
        "use_dynamic": true/false,
        "status": 0  (0=草稿, 2=已定制)
    }
    
    返回:
    {
        "success": true,
        "scene_id": 123,
        "scene_prompt": "生成的提示词"
    }
    """
    try:
        data = request.json
        
        # 必填字段验证
        required_fields = ['scene_name', 'scene_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'缺少必填字段: {field}'
                }), 400
        
        scene_name = data['scene_name']
        scene_type = data['scene_type']
        
        # 验证场景类型
        if scene_type not in ['sales', 'service']:
            return jsonify({
                'success': False,
                'error': '场景类型必须是 sales 或 service'
            }), 400
        
        # 生成提示词
        logger.info(f"开始生成 {scene_type} 场景提示词: {scene_name}")
        
        use_dynamic = data.get('use_dynamic', True)
        
        scene_prompt = prompt_service.generate_scene_prompt(
            scene_type=scene_type,
            scene_data=data,
            use_dynamic=use_dynamic
        )
        
        if not scene_prompt:
            return jsonify({
                'success': False,
                'error': '提示词生成失败'
            }), 500
        
        logger.info(f"提示词生成成功，长度: {len(scene_prompt)} 字符")
        
        # 准备保存数据
        save_data = {
            'scene_name': scene_name,
            'scene_prompt': scene_prompt,
            'scene_type': scene_type,
            'status': data.get('status', 0),  # 默认草稿状态
            'role_type': data.get('ai_role'),
            'industry': data.get('industry')
        }
        
        # 处理固定问题和关联问题
        fixed_questions = data.get('fixed_questions')
        if fixed_questions:
            save_data['fixed_questions'] = json.dumps(fixed_questions, ensure_ascii=False)
        
        related_questions = data.get('related_questions')
        if related_questions:
            save_data['related_questions'] = json.dumps(related_questions, ensure_ascii=False)
        
        # 保存到数据库
        scene_id = db_module.save_scene(**save_data)
        
        if not scene_id:
            return jsonify({
                'success': False,
                'error': '保存场景失败'
            }), 500
        
        logger.info(f"场景保存成功，ID: {scene_id}")
        
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'scene_prompt': scene_prompt,
            'message': '场景提示词生成并保存成功'
        })
        
    except Exception as e:
        logger.error(f"生成并保存场景提示词失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scene_prompt_bp.route('/regenerate/<int:scene_id>', methods=['POST'])
def regenerate_prompt(scene_id):
    """
    重新生成指定场景的提示词
    
    请求体:
    {
        "use_dynamic": true/false
    }
    """
    try:
        # 获取场景数据
        scene = db_module.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({
                'success': False,
                'error': '场景不存在'
            }), 404
        
        scene_type = scene.get('scene_type', 'sales')
        
        # 准备场景数据
        scene_data = {
            'ai_role': scene.get('role_type'),
            'user_role': scene.get('user_role'),
            'industry': scene.get('industry'),
            'scene_description': scene.get('scene_description'),
            'background_info': scene.get('background_info', ''),
            'fixed_questions': scene.get('fixed_questions'),
            'related_questions': scene.get('related_questions')
        }
        
        # 重新生成提示词
        data = request.json or {}
        use_dynamic = data.get('use_dynamic', True)
        
        new_prompt = prompt_service.generate_scene_prompt(
            scene_type=scene_type,
            scene_data=scene_data,
            use_dynamic=use_dynamic
        )
        
        if not new_prompt:
            return jsonify({
                'success': False,
                'error': '提示词重新生成失败'
            }), 500
        
        # 更新场景提示词
        success = db_module.update_scene(
            scene_id=scene_id,
            scene_prompt=new_prompt
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': '更新场景失败'
            }), 500
        
        return jsonify({
            'success': True,
            'scene_prompt': new_prompt,
            'message': '提示词重新生成成功'
        })
        
    except Exception as e:
        logger.error(f"重新生成提示词失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scene_prompt_bp.route('/preview', methods=['POST'])
def preview_prompt():
    """
    预览生成的提示词（不保存）
    
    请求体格式同 /generate-and-save
    """
    try:
        data = request.json
        
        scene_type = data.get('scene_type', 'sales')
        if scene_type not in ['sales', 'service']:
            return jsonify({
                'success': False,
                'error': '场景类型必须是 sales 或 service'
            }), 400
        
        use_dynamic = data.get('use_dynamic', True)
        
        scene_prompt = prompt_service.generate_scene_prompt(
            scene_type=scene_type,
            scene_data=data,
            use_dynamic=use_dynamic
        )
        
        if not scene_prompt:
            return jsonify({
                'success': False,
                'error': '提示词生成失败'
            }), 500
        
        return jsonify({
            'success': True,
            'scene_prompt': scene_prompt
        })
        
    except Exception as e:
        logger.error(f"预览提示词失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500