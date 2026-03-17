"""
SOP质检项智能提取和评分路由扩展
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

sop_extraction_bp = Blueprint('sop_extraction', __name__, url_prefix='/api/sop')


@sop_extraction_bp.route('/extract-with-scoring', methods=['POST'])
def extract_with_scoring():
    """
    智能提取质检项并自动评分
    
    Request:
    {
        "scene_code": "real_estate_sales",
        "text_content": "SOP文档内容...",
        "scene_description": "房地产销售场景",
        "extract_must_do": true,
        "extract_must_not": true,
        "extract_should_do": true,
        "auto_scoring": true,
        "target_total": 100
    }
    
    Response:
    {
        "success": true,
        "items": [...],
        "scoring_summary": {...}
    }
    """
    try:
        from agent.service.scene.sop_extraction_service import sop_extraction_service
        from agent.service.scene.sop_scoring_service import sop_scoring_service
        
        data = request.get_json()
        scene_code = data.get('scene_code')
        text_content = data.get('text_content')
        scene_description = data.get('scene_description', '')
        extract_must_do = data.get('extract_must_do', True)
        extract_must_not = data.get('extract_must_not', True)
        extract_should_do = data.get('extract_should_do', True)
        auto_scoring = data.get('auto_scoring', True)
        target_total = data.get('target_total', 100)
        
        if not text_content:
            return jsonify({
                "success": False,
                "error": "缺少文字内容"
            }), 400
        
        logger.info(f"开始智能提取质检项，场景：{scene_code}")
        
        # 调用提取服务
        items = sop_extraction_service.extract_from_text(
            scene_code=scene_code,
            text_content=text_content,
            scene_description=scene_description,
            extract_must_do=extract_must_do,
            extract_must_not=extract_must_not,
            extract_should_do=extract_should_do,
            auto_scoring=auto_scoring
        )
        
        # 获取评分摘要
        scoring_summary = sop_scoring_service.get_scoring_summary(items)
        
        logger.info(f"提取完成，共 {len(items)} 个质检项，总分：{scoring_summary['total_score']}")
        
        return jsonify({
            "success": True,
            "items": items,
            "scoring_summary": scoring_summary
        })
        
    except Exception as e:
        logger.error(f"智能提取失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_extraction_bp.route('/adjust-score', methods=['POST'])
def adjust_score():
    """
    调整质检项分数
    
    Request:
    {
        "item_id": "SOP_001",
        "new_score": 25,
        // 或
        "new_importance": "critical",
        "checklist": [...]
    }
    
    Response:
    {
        "success": true,
        "updated_item": {...},
        "rebalanced_checklist": [...]
    }
    """
    try:
        from agent.service.scene.sop_scoring_service import sop_scoring_service
        
        data = request.get_json()
        item_id = data.get('item_id')
        new_score = data.get('new_score')
        new_importance = data.get('new_importance')
        checklist = data.get('checklist', [])
        
        if not item_id:
            return jsonify({
                "success": False,
                "error": "缺少 item_id"
            }), 400
        
        # 找到要调整的质检项
        target_item = None
        for item in checklist:
            if item.get('item_id') == item_id:
                target_item = item
                break
        
        if not target_item:
            return jsonify({
                "success": False,
                "error": f"未找到质检项: {item_id}"
            }), 404
        
        # 调整分数
        updated_item = sop_scoring_service.adjust_item_score(
            target_item,
            new_score=new_score,
            new_importance=new_importance
        )
        
        # 重新平衡整个列表
        rebalanced_checklist = sop_scoring_service.balance_scores(checklist, 100)
        
        return jsonify({
            "success": True,
            "updated_item": updated_item,
            "rebalanced_checklist": rebalanced_checklist
        })
        
    except Exception as e:
        logger.error(f"调整分数失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_extraction_bp.route('/scoring-rules', methods=['GET'])
def get_scoring_rules():
    """
    获取评分规则配置
    
    Response:
    {
        "importance_scores": {...},
        "type_weights": {...},
        "category_weights": {...},
        "customizable": true,
        "formula": "..."
    }
    """
    try:
        from agent.service.scene.sop_scoring_service import sop_scoring_service
        
        rules = sop_scoring_service.get_scoring_rules()
        
        return jsonify({
            "success": True,
            "rules": rules
        })
        
    except Exception as e:
        logger.error(f"获取评分规则失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@sop_extraction_bp.route('/rebalance-scores', methods=['POST'])
def rebalance_scores():
    """
    重新平衡质检项分数
    
    Request:
    {
        "checklist": [...],
        "target_total": 100
    }
    
    Response:
    {
        "success": true,
        "rebalanced_checklist": [...],
        "scoring_summary": {...}
    }
    """
    try:
        from agent.service.scene.sop_scoring_service import sop_scoring_service
        
        data = request.get_json()
        checklist = data.get('checklist', [])
        target_total = data.get('target_total', 100)
        
        if not checklist:
            return jsonify({
                "success": False,
                "error": "质检项列表为空"
            }), 400
        
        # 重新平衡分数
        rebalanced_checklist = sop_scoring_service.balance_scores(checklist, target_total)
        
        # 获取评分摘要
        scoring_summary = sop_scoring_service.get_scoring_summary(rebalanced_checklist)
        
        return jsonify({
            "success": True,
            "rebalanced_checklist": rebalanced_checklist,
            "scoring_summary": scoring_summary
        })
        
    except Exception as e:
        logger.error(f"重新平衡分数失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500