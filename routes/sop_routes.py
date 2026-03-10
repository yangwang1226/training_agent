"""
SOP质检项管理路由
提供 SOP 质检项的 CRUD 接口
"""

from flask import Blueprint, request, jsonify
from database.sop_dao import sop_dao
import logging

logger = logging.getLogger(__name__)

sop_bp = Blueprint('sop', __name__, url_prefix='/api/sop')


@sop_bp.route('/checklist/<scene_code>', methods=['GET'])
def get_sop_checklist(scene_code):
    """
    获取指定场景的 SOP 质检项
    
    Args:
        scene_code: 场景代码
    
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
        checklist = sop_dao.get_scene_sop_checklist(scene_code)
        
        if checklist is None:
            # 返回空列表，前端可以开始配置
            return jsonify({
                "success": True,
                "data": {
                    "scene_code": scene_code,
                    "checklist": []
                },
                "message": "该场景暂未配置 SOP 质检项"
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
        logger.error(f"获取 SOP 质检项失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取失败: {str(e)}"
        }), 500


@sop_bp.route('/checklist/<scene_code>', methods=['PUT'])
def update_sop_checklist(scene_code):
    """
    更新指定场景的 SOP 质检项
    
    Args:
        scene_code: 场景代码
    
    Request Body:
        {
            "checklist": [
                {
                    "item_id": "SOP001",
                    "item_name": "主动问候客户",
                    "check_type": "must_do",
                    "keywords": ["你好", "欢迎"],
                    "category": "接待礼仪",
                    "item_desc": "描述信息"
                }
            ]
        }
    
    Returns:
        JSON: {
            "success": bool,
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
        
        # 验证数据结构
        is_valid, error_msg = sop_dao.validate_checklist_structure(checklist)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": f"数据格式错误: {error_msg}"
            }), 400
        
        # 更新数据库
        success = sop_dao.update_scene_sop_checklist(scene_code, checklist)
        
        if success:
            return jsonify({
                "success": True,
                "message": "保存成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "保存失败，场景不存在或未激活"
            }), 404
    
    except Exception as e:
        logger.error(f"更新 SOP 质检项失败: {e}")
        return jsonify({
            "success": False,
            "message": f"保存失败: {str(e)}"
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