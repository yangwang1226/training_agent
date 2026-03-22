"""评估报告查看路由"""
import logging
import json
from flask import Blueprint, render_template, request, jsonify, send_file
from pathlib import Path

from database.record_dao import get_coach_record_by_session_id
from database.scene_dao import get_scene_by_id

logger = logging.getLogger(__name__)

# 创建蓝图
assessment_view_bp = Blueprint(
    'assessment_view',
    __name__,
    url_prefix='/evaluate',
    template_folder=str(Path(__file__).parent.parent / 'front_end' / 'evaluate' / 'templates'),
    static_folder=str(Path(__file__).parent.parent / 'front_end' / 'evaluate' / 'static')
)


@assessment_view_bp.route('/', methods=['GET'])
def view_assessment():
    """渲染评估报告页面"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        # 没有 session_id 时，显示 mock 数据预览
        return render_template('evaluate_v2.html')
    
    return render_template('evaluate_v2.html', session_id=session_id)


@assessment_view_bp.route('/api/report/<session_id>', methods=['GET'])
def get_assessment_report(session_id):
    """获取评估报告数据"""
    try:
        record = get_coach_record_by_session_id(session_id)
        
        # 1. 记录还未保存到数据库
        if not record:
            return jsonify({
                'success': False,
                'status': 'pending',
                'error': '记录尚未生成，请稍候'
            }), 404
            
        # 2. 记录已保存，但评估报告尚未生成完成（dimension_result 和 ai_score 为空）
        if not record.get('dimension_result') and not record.get('ai_score'):
            return jsonify({
                'success': False,
                'status': 'pending',
                'error': '大模型正在深度评估中，请稍候...'
            }), 202
        
        # 解析维度评分结果
        dimension_result = None
        if record.get('dimension_result'):
            try:
                dimension_result = json.loads(record['dimension_result'])
            except:
                logger.error(f"解析维度评分失败: session_id={session_id}")
        
        # 解析SOP质检结果
        sop_result = None
        if record.get('sop_result'):
            try:
                sop_result = json.loads(record['sop_result'])
            except:
                logger.error(f"解析SOP结果失败: session_id={session_id}")
        
        # 音频分析暂不支持
        audio_analysis = None
        
                # 获取场景名称
        scene_name = None
        scene_id = record.get('scene_id')
        if scene_id:
            try:
                scene = get_scene_by_id(scene_id)
                if scene:
                    scene_name = scene.get('scene_name')
            except Exception as e:
                logger.error(f"获取场景信息失败: scene_id={scene_id}, error={e}")
        
        # 组装动态音频访问路径，而非直接返回数据库里的相对路径
        has_audio = bool(record.get('oss_file_path'))
        audio_url = f"/evaluate/api/audio/{session_id}" if has_audio else ""
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': record['session_id'],
                'scene_id': record['scene_id'],
                'scene_name': scene_name or f"场景 #{record['scene_id']}",
                'ai_score': record.get('ai_score', 0),
                'ai_summary': record.get('ai_summary', ''),
                'dimension_result': dimension_result,
                'call_duration': record.get('call_duration', 0),
                'audio_path': audio_url,
                'created_time': str(record.get('created_time', '')),
                'ai_advise': record.get('ai_advise', ''),
                'word_content': record.get('word_content', ''),
                'sop_result': sop_result,
                'sop_score': record.get('sop_score', 0),  # SOP评分
                'final_score': record.get('final_score', 0)  # 综合评分（AI 40% + SOP 60%）
            }
        })
        
    except Exception as e:
        logger.error(f"获取评估报告失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessment_view_bp.route('/api/list', methods=['GET'])
def list_assessments():
    """获取评估报告列表"""
    try:
        from database.connection import get_db
        
        limit = request.args.get('limit', 20, type=int)
        scene_id = request.args.get('scene_id', type=int)
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                if scene_id:
                    sql = """
                        SELECT 
                            session_id,
                            scene_id,
                            score,
                            call_duration,
                            created_time
                        FROM ai_coach_record
                        WHERE is_delete = 0 AND scene_id = %s
                        ORDER BY created_time DESC
                        LIMIT %s
                    """
                    cursor.execute(sql, (scene_id, limit))
                else:
                    sql = """
                        SELECT 
                            session_id,
                            scene_id,
                            score,
                            call_duration,
                            created_time
                        FROM ai_coach_record
                        WHERE is_delete = 0
                        ORDER BY created_time DESC
                        LIMIT %s
                    """
                    cursor.execute(sql, (limit,))
                
                records = cursor.fetchall()
                
                return jsonify({
                    'success': True,
                    'data': records
                })
                
    except Exception as e:
        logger.error(f"获取评估列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessment_view_bp.route('/api/audio/<session_id>', methods=['GET'])
def get_assessment_audio(session_id):
    """通过 session_id 获取对应的音频流文件"""
    try:
        record = get_coach_record_by_session_id(session_id)
        if not record or not record.get('oss_file_path'):
            return "未找到音频文件记录", 404
            
        # os.path 结合项目根目录
        import os
        # 因为 app.py 或运行目录在项目根目录，相对路径 audio_file/... 通常在根下
        # 获取项目根目录 (routes/ 的上级)
        project_root = Path(__file__).parent.parent
        audio_file_path = project_root / record['oss_file_path']
        
        if not audio_file_path.exists() or not audio_file_path.is_file():
            return "音频文件在服务器上不存在", 404
            
        # 动态推断 mimetype
        mimetype = "audio/webm" if audio_file_path.suffix.lower() == ".webm" else "audio/wav"
        return send_file(str(audio_file_path), mimetype=mimetype)
        
    except Exception as e:
        logger.error(f"获取音频文件失败: {e}", exc_info=True)
        return "内部服务器错误", 500

