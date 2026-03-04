import logging
from pathlib import Path
from flask import Blueprint, jsonify, request, session

from agent.evaluate_agent import assessment_service, DifficultyLevel

logger = logging.getLogger(__name__)

evaluate_bp = Blueprint('evaluate', __name__, url_prefix='/api/evaluate')

EVALUATE_TEMPLATE_PATH = Path(__file__).parent.parent / "front_end" / "evaluate" / "templates" / "evaluate.html"


@evaluate_bp.route('/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    profile = assessment_service.get_user_profile(user_id)
    
    if profile:
        return jsonify({
            'success': True,
            'profile': {
                'user_id': profile.user_id,
                'overall_score': profile.overall_score,
                'dimension_scores': profile.dimension_scores,
                'training_count': profile.training_count,
                'total_duration': profile.total_duration,
                'level': profile.level,
                'weak_points': profile.weak_points,
                'strong_points': profile.strong_points,
                'improvement_history': profile.improvement_history,
                'achievements': profile.achievements
            }
        })
    else:
        return jsonify({
            'success': True,
            'profile': {
                'user_id': user_id,
                'overall_score': 0,
                'dimension_scores': {
                    '沟通技巧': 0,
                    '产品知识': 0,
                    '需求挖掘': 0,
                    '异议处理': 0,
                    '促成技巧': 0
                },
                'training_count': 0,
                'total_duration': 0,
                'level': '入门',
                'weak_points': [],
                'strong_points': [],
                'improvement_history': [],
                'achievements': []
            }
        })


@evaluate_bp.route('/history/<user_id>', methods=['GET'])
def get_training_history(user_id):
    industry_filter = request.args.get('industry', '')
    
    history = assessment_service.get_training_history(user_id, limit=20)
    
    if industry_filter:
        history = [h for h in history if industry_filter in h.get('industry', '')]
    
    return jsonify({
        'success': True,
        'history': history
    })


@evaluate_bp.route('/assessment/<session_id>', methods=['GET'])
def get_assessment(session_id):
    assessment = assessment_service.get_assessment(session_id)
    
    if assessment:
        return jsonify({
            'success': True,
            'assessment': assessment
        })
    else:
        return jsonify({
            'success': False,
            'error': '评估报告不存在'
        })


@evaluate_bp.route('/suggestions/<user_id>', methods=['POST'])
def generate_suggestions(user_id):
    suggestions = assessment_service.generate_improvement_suggestions(user_id)
    
    if suggestions:
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    else:
        return jsonify({
            'success': False,
            'error': '无法生成建议，请先完成训练'
        })


@evaluate_bp.route('/session/create', methods=['POST'])
def create_evaluation_session():
    data = request.json
    user_id = session.get('session_id', 'default')
    
    training_session = assessment_service.create_session(
        user_id=user_id,
        scene_id=data.get('scene_id', ''),
        industry=data.get('industry', ''),
        role=data.get('role', ''),
        purchase_intent=data.get('purchase_intent', '一般'),
        difficulty=DifficultyLevel(data.get('difficulty', '进阶')),
        system_prompt=data.get('system_prompt', ''),
        customer_persona=data.get('customer_persona', '')
    )
    
    return jsonify({
        'success': True,
        'session_id': training_session.session_id
    })


@evaluate_bp.route('/session/<session_id>/transcript', methods=['POST'])
def add_transcript(session_id):
    data = request.json
    
    assessment_service.add_transcript(
        session_id=session_id,
        role=data.get('role', 'user'),
        content=data.get('content', ''),
        timestamp=data.get('timestamp')
    )
    
    return jsonify({'success': True})


@evaluate_bp.route('/session/<session_id>/end', methods=['POST'])
def end_evaluation_session(session_id):
    session = assessment_service.end_session(session_id)
    
    if session:
        return jsonify({
            'success': True,
            'duration': session.duration_seconds
        })
    else:
        return jsonify({
            'success': False,
            'error': '会话不存在'
        })


@evaluate_bp.route('/session/<session_id>/evaluate', methods=['POST'])
def evaluate_training_session(session_id):
    assessment = assessment_service.evaluate_session(session_id)
    
    if assessment:
        return jsonify({
            'success': True,
            'assessment': {
                'overall_score': assessment.overall_score,
                'dimension_scores': [
                    {
                        'dimension': ds.dimension_name,
                        'score': ds.score,
                        'weight': ds.weight,
                        'reason': ds.reason,
                        'sub_scores': ds.sub_scores
                    }
                    for ds in assessment.dimension_scores
                ],
                'highlights': assessment.highlights,
                'improvements': assessment.improvements,
                'golden_sentences': assessment.golden_sentences,
                'key_moments': [
                    {
                        'turn': km.time,
                        'type': km.moment_type,
                        'content': km.content,
                        'handling': km.handling_quality,
                        'suggestion': km.suggestion
                    }
                    for km in assessment.key_moments
                ],
                'completion_rate': assessment.completion_rate,
                'total_turns': assessment.total_turns,
                'duration_seconds': assessment.duration_seconds
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': '评估失败'
        })
