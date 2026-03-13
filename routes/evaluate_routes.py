import logging
from pathlib import Path
from flask import Blueprint, jsonify, request, session

# from agent.evaluate_agent import assessment_service, DifficultyLevel
from agent.service.scene.assessment_service import SceneAssessmentService

logger = logging.getLogger(__name__)

evaluate_bp = Blueprint('evaluate', __name__, url_prefix='/api/evaluate')

EVALUATE_TEMPLATE_PATH = Path(__file__).parent.parent / "front_end" / "evaluate" / "templates" / "evaluate.html"


@evaluate_bp.route('/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """
    获取用户的能力画像
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户能力画像数据
    """
    try:
        from database.record_dao import get_coach_record_by_session_id
        
        # TODO: 从数据库获取用户的能力画像数据
        # 这里暂时返回示例数据
        profile = {
            'level': '入门',
            'overall_score': 75,
            'training_count': 5,
            'total_duration': 600,
            'strong_points': ['沟通技巧', '产品知识'],
            'weak_points': ['需求挖掘', '促成技巧']
        }
        
        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        logger.error(f"获取用户画像失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })


@evaluate_bp.route('/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    """
    获取用户的训练历史
    
    Args:
        user_id: 用户ID
        industry: 可选的行业筛选参数
        
    Returns:
        训练历史数据
    """
    try:
        from database.record_dao import get_coach_record_by_session_id
        from database.connection import get_db
        
        industry_filter = request.args.get('industry', '')
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                if industry_filter:
                    sql = """
                        SELECT 
                            session_id,
                            scene_id,
                            call_duration,
                            ai_score,
                            created_time
                        FROM ai_coach_record
                        WHERE user_id = %s AND is_delete = 0 AND ai_score IS NOT NULL
                        ORDER BY created_time DESC
                        LIMIT 20
                    """
                    cursor.execute(sql, (user_id,))
                else:
                    sql = """
                        SELECT 
                            session_id,
                            scene_id,
                            call_duration,
                            ai_score,
                            created_time
                        FROM ai_coach_record
                        WHERE user_id = %s AND is_delete = 0 AND ai_score IS NOT NULL
                        ORDER BY created_time DESC
                        LIMIT 20
                    """
                    cursor.execute(sql, (user_id,))
                
                records = cursor.fetchall()
                
                # 获取场景信息
                history = []
                for record in records:
                    scene = None
                    try:
                        import db as db_module
                        scene = db_module.get_scene_by_id(record['scene_id'])
                    except:
                        pass
                    
                    history.append({
                        'session_id': record['session_id'],
                        'industry': scene.get('industry', '') if scene else '',
                        'role': scene.get('ai_role', '') if scene else '',
                        'date': record['created_time'].strftime('%Y-%m-%d'),
                        'duration': record['call_duration'] or 0,
                        'score': record['ai_score'] or 0
                    })
                
                return jsonify({
                    'success': True,
                    'history': history
                })
    except Exception as e:
        logger.error(f"获取训练历史失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })


@evaluate_bp.route('/assessment/<session_id>', methods=['GET'])
def get_assessment(session_id):
    """
    获取评估报告
    
    Args:
        session_id: 会话ID
        
    Returns:
        评估报告数据
    """
    try:
        from database.record_dao import get_coach_record_by_session_id
        import db as db_module
        
        record = get_coach_record_by_session_id(session_id)
        
        if not record:
            return jsonify({
                'success': False,
                'error': '评估报告不存在'
            })
        
        # 获取场景信息
        scene = db_module.get_scene_by_id(record.get('scene_id'))
        
        # 解析维度结果
        dimension_scores = []
        highlights = []
        improvements = []
        golden_sentences = []
        key_moments = []
        
        if record.get('dimension_result'):
            try:
                dims = json.loads(record['dimension_result'])
                dimension_scores = [
                    {
                        'dimension': dim.get('dimension_name', ''),
                        'score': dim.get('score', 0),
                        'weight': 0,
                        'reason': dim.get('feedback', ''),
                        'sub_scores': []
                    }
                    for dim in dims
                ]
                
                # 提取亮点
                highlights = dim.get('highlights', []) if dims else []
                
                # 提取改进建议
                improvements = dim.get('improvements', []) if dims else []
                
                # 提取金句
                golden_sentences = dim.get('golden_sentences', []) if dims else []
                
                # 提取关键时刻
                key_moments = dim.get('key_moments', []) if dims else []
            except:
                pass
        
        # 解析AI总结
        ai_summary = record.get('ai_summary', '')
        
        # 从AI总结中提取关键对话时刻（如果有的话）
        if ai_summary and not key_moments:
            try:
                import re
                pattern = r'关键时刻.*?[:\s*(\d+).*?[:\s*([^]]+)'
                matches = re.findall(pattern, ai_summary)
                if matches:
                    key_moments = [
                        {
                            'turn': int(match[0]),
                            'type': '关键时刻',
                            'content': match[1].strip(),
                            'handling': '较好',
                            'suggestion': ''
                        }
                        for match in matches
                    ]
            except:
                pass
        
        return jsonify({
            'success': True,
            'assessment': {
                'overall_score': record.get('ai_score', 0),
                'dimension_scores': dimension_scores,
                'highlights': highlights,
                'improvements': improvements,
                'golden_sentences': golden_sentences,
                'key_moments': key_moments,
                'completion_rate': 0,
                'total_turns': 0,
                'duration_seconds': record.get('call_duration', 0),
                'industry': scene.get('industry', '') if scene else '',
                'role': scene.get('ai_role', '') if scene else '',
                'date': record.get('created_time', '').strftime('%Y-%m-%d') if record.get('created_time') else ''
            }
        })
    except Exception as e:
        logger.error(f"获取评估报告失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })


@evaluate_bp.route('/suggestions/<user_id>', methods=['POST'])
def generate_suggestions(user_id):
    """
    生成改进建议
    
    Args:
        user_id: 用户ID
        
    Returns:
        改进建议数据
    """
    try:
        from database.record_dao import get_coach_record_by_session_id
        
        # TODO: 实现生成改进建议的逻辑
        # 这里暂时返回示例数据
        suggestions = {
            'priority': '高',
            'learning_path': [
                {
                    'step': 1,
                    'action': '加强产品知识学习',
                    'resource': '产品手册',
                    'estimated_time': '2小时'
                },
                {
                    'step': 2,
                    'action': '提升沟通技巧',
                    'resource': '沟通技巧培训视频',
                    'estimated_time': '3小时'
                }
            ],
            'practice_scenarios': ['场景A', '场景B'],
            'key_points': ['要点1', '要点2']
        }
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"生成改进建议失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

