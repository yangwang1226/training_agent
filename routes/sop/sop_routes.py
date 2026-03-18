"""
SOP质检项管理路由
提供 SOP 质检项的 CRUD 接口
"""

from flask import Blueprint, request, jsonify
from database.sop_dao import sop_dao
import logging

logger = logging.getLogger(__name__)

sop_bp = Blueprint('sop', __name__, url_prefix='/api/sop')


@sop_bp.route('/checklist/scene/<int:scene_id>', methods=['GET'])
def get_scene_sop_checklist_api(scene_id):
    """
    获取场景实例的 SOP 质检项（用户私有）
    
    Args:
        scene_id: 场景实例ID
    
    Returns:
        JSON: {
            "success": bool,
            "data": {
                "scene_id": int,
                "checklist": list
            },
            "message": str
        }
    """
    try:
        checklist = sop_dao.get_scene_sop_checklist(scene_id)
        
        if checklist is None:
            # 返回空列表
            return jsonify({
                "success": True,
                "data": {
                    "scene_id": scene_id,
                    "checklist": []
                },
                "message": "该场景暂未配置 SOP 质检项"
            })
        
        return jsonify({
            "success": True,
            "data": {
                "scene_id": scene_id,
                "checklist": checklist
            },
            "message": "获取成功"
        })
    
    except Exception as e:
        logger.error(f"获取场景 SOP 质检项失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取失败: {str(e)}"
        }), 500


@sop_bp.route('/checklist/preset/<scene_code>', methods=['GET'])
def get_preset_sop_checklist_api(scene_code):
    """
    获取预设场景的默认 SOP 质检项（只读，模板）
    
    Args:
        scene_code: 预设场景代码
    
    Returns:
        JSON: {
            "success": bool,
            "data": {
                "scene_code": str,
                "checklist": list
            },
            "message": str
        }
    """
    try:
        checklist = sop_dao.get_preset_sop_checklist(scene_code)
        
        if checklist is None:
            return jsonify({
                "success": True,
                "data": {
                    "scene_code": scene_code,
                    "checklist": []
                },
                "message": "该预设场景暂未配置默认 SOP 质检项"
            })
        
        return jsonify({
            "success": True,
            "data": {
                "scene_code": scene_code,
                "checklist": checklist
            },
            "message": "获取成功"
        })
    
    except Exception as e:
        logger.error(f"获取预设 SOP 质检项失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取失败: {str(e)}"
        }), 500


@sop_bp.route('/scenes', methods=['GET'])
def get_all_scenes_with_sop():
    """
    获取所有配置了 SOP 的场景列表
    
    Returns:
        JSON: {
            "success": bool,
            "data": [
                {
                    "scene_code": str,
                    "scene_name": str,
                    "industry_code": str,
                    "checklist_count": int,
                    "created_time": str,
                    "updated_time": str
                }
            ],
            "message": str
        }
    """
    try:
        scenes = sop_dao.get_all_scenes_with_sop()
        
        return jsonify({
            "success": True,
            "data": scenes,
            "message": "获取成功"
        })
    
    except Exception as e:
        logger.error(f"获取场景列表失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取失败: {str(e)}"
        }), 500


@sop_bp.route('/save-checklist', methods=['POST'])
def save_checklist():
    """
    保存质检项到场景实例（用户私有，可修改）
    
    Request Body:
        {
            "scene_id": int,  # 场景实例ID（必需）
            "checklist": [
                {
                    "item_name": str,
                    "check_type": str,
                    "keywords": str,
                    "category": str
                }
            ]
        }
    """
    try:
        data = request.get_json()
        scene_id = data.get('scene_id')
        checklist = data.get('checklist', [])
        
        if not scene_id:
            return jsonify({
                "success": False,
                "error": "缺少 scene_id 参数"
            }), 400
        
        # 转换数据格式
        formatted_checklist = []
        for item in checklist:
            formatted_item = {
                'item_id': item.get('id', f"SOP_{len(formatted_checklist)+1:03d}"),
                'item_name': item.get('item_name'),
                'check_type': item.get('check_type'),
                'keywords': item.get('keywords') if isinstance(item.get('keywords'), str) else ','.join(item.get('keywords', [])),
                'category': item.get('category', 'general'),
                'item_desc': item.get('desc', '')
            }
            formatted_checklist.append(formatted_item)
        
        # 保存到场景实例
        success = sop_dao.save_scene_sop_checklist(scene_id, formatted_checklist)
        
        if success:
            return jsonify({
                "success": True,
                "message": "保存成功"
            })
        else:
            return jsonify({
                "success": False,
                "error": "保存失败"
            }), 500
            
    except Exception as e:
        logger.error(f"保存质检项失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_bp.route('/extract-from-text', methods=['POST'])
def extract_from_text():
    """
    从文字记录中智能提取质检项
    
    Request Body:
        {
            "scene_code": str,
            "text_content": str,
            "extract_must_do": bool,
            "extract_must_not": bool
        }
    """
    try:
        data = request.get_json()
        scene_code = data.get('scene_code')
        text_content = data.get('text_content')
        extract_must_do = data.get('extract_must_do', True)
        extract_must_not = data.get('extract_must_not', True)
        
        if not text_content:
            return jsonify({
                "success": False,
                "error": "缺少文字内容"
            }), 400
        
        # TODO: 调用 LLM 进行智能提取
        # 这里先返回模拟数据
        items = [
            {
                "name": "30秒内主动问候客户",
                "type": "must_do",
                "keywords": ["您好", "欢迎", "问候"],
                "category": "greeting"
            },
            {
                "name": "了解客户基本需求",
                "type": "must_do",
                "keywords": ["需求", "预算", "用途"],
                "category": "needs_analysis"
            },
            {
                "name": "禁止贬低竞品",
                "type": "must_not",
                "keywords": ["竞品", "对手", "不好"],
                "category": "product_intro"
            }
        ]
        
        return jsonify({
            "success": True,
            "items": items
        })
        
    except Exception as e:
        logger.error(f"智能提取失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_bp.route('/extract-from-audio', methods=['POST'])
def extract_from_audio():
    """
    从音频文件中智能提取质检项
    
    Request: multipart/form-data
        - scene_code: str
        - extract_must_do: bool
        - extract_must_not: bool
        - audio_files: File[]
    """
    try:
        scene_code = request.form.get('scene_code')
        extract_must_do = request.form.get('extract_must_do', 'true') == 'true'
        extract_must_not = request.form.get('extract_must_not', 'true') == 'true'
        audio_files = request.files.getlist('audio_files')
        
        if not audio_files:
            return jsonify({
                "success": False,
                "error": "未上传音频文件"
            }), 400
        
        # TODO: 实现音频转文字 + 智能提取
        # 这里先返回模拟数据
        items = [
            {
                "name": "热情接待客户",
                "type": "must_do",
                "keywords": ["欢迎", "您好"],
                "category": "greeting"
            }
        ]
        
        return jsonify({
            "success": True,
            "items": items
        })
        
    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_bp.route('/checklist/<scene_code>/validate', methods=['POST'])
def validate_checklist(scene_code):
    """
    验证质检项数据格式（不保存）
    
    Request Body:
        {
            "checklist": [...]
        }
    
    Returns:
        JSON: {
            "success": bool,
            "valid": bool,
            "message": str
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'checklist' not in data:
            return jsonify({
                "success": False,
                "message": "缺少必填参数: checklist"
            }), 400
        
        checklist = data['checklist']
        is_valid, error_msg = sop_dao.validate_checklist_structure(checklist)
        
        return jsonify({
            "success": True,
            "valid": is_valid,
            "message": error_msg if not is_valid else "数据格式正确"
        })
    
    except Exception as e:
        logger.error(f"验证质检项失败: {e}")
        return jsonify({
            "success": False,
            "message": f"验证失败: {str(e)}"
        }), 500