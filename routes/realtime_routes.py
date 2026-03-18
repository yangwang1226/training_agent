import os
import sys
import json
import logging
from pathlib import Path

from flask import Blueprint, render_template, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db as db_module
from agent.service.conversational import ConversationRecorder
from agent.service.scene.assessment_service import assessment_service as scene_assessment_service
from agent.service.scene.async_assessment_processor import get_async_processor

from .realtime.websocket_handler import WebSocketHandler
from .realtime.provider_config import ProviderConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_realtime_dir = Path(__file__).parent

# 模板和静态文件实际在 front_end/realtime 目录下
# 从 routes/ 目录向上两级到项目根目录，然后到 front_end/realtime
project_root = _realtime_dir.parent
_realtime_template_dir = project_root / 'front_end' / 'realtime' / 'templates'
_realtime_static_dir = project_root / 'front_end' / 'realtime' / 'static'

realtime_bp = Blueprint('realtime', __name__, 
                        url_prefix='/realtime',
                        template_folder=str(_realtime_template_dir),
                        static_folder=str(_realtime_static_dir),
                        static_url_path='/realtime/static')

DEFAULT_PROVIDER = os.getenv("REALTIME_PROVIDER", "qwen").lower()

# 场景实时训练页面
@realtime_bp.route('/<scene_id>')
def index(scene_id):
    try:
        scene_id_int = int(scene_id)
        scene = db_module.get_scene_by_id(scene_id_int)
        if not scene:
            return "场景不存在", 404
        
        scene_name = scene.get('scene_name', '未知场景')
        provider = request.args.get('provider', DEFAULT_PROVIDER)
        
        return render_template('realtime.html', 
                              scene_id=scene_id, 
                              scene_name=scene_name,
                              provider=provider)
    except ValueError:
        return "无效的场景 ID", 400
    except Exception as e:
        logger.error(f"获取场景失败：{e}")
        return "获取场景失败", 500

# 获取场景提示词
@realtime_bp.route('/prompt/<scene_id>')
def get_prompt(scene_id):
    try:
        scene_id_int = int(scene_id)
        prompt = db_module.get_prompt_by_scene_id(scene_id_int)
        if prompt:
            return jsonify({'success': True, 'prompt': prompt})
        else:
            return jsonify({'success': False, 'error': '场景不存在'})
    except ValueError:
        return jsonify({'success': False, 'error': '无效的场景 ID'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 查询评估任务状态
@realtime_bp.route('/api/assessment/status/<task_id>')
def get_assessment_status(task_id):
    """
    查询评估任务状态
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务状态信息
    """
    try:
        async_processor = get_async_processor(scene_assessment_service)
        task_status = async_processor.get_task_status(task_id)
        
        if task_status:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'status': task_status.get('status'),
                'created_at': task_status.get('created_at').isoformat() if task_status.get('created_at') else None,
                'started_at': task_status.get('started_at').isoformat() if task_status.get('started_at') else None,
                'completed_at': task_status.get('completed_at').isoformat() if task_status.get('completed_at') else None,
                'failed_at': task_status.get('failed_at').isoformat() if task_status.get('failed_at') else None,
                'error': task_status.get('error'),
                'result': task_status.get('result')
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            })
    except Exception as e:
        logger.error(f"查询评估任务状态失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

# 获取支持的 provider 列表
@realtime_bp.route('/api/providers')
def list_providers():
    """列出所有支持的 realtime provider"""
    try:
        providers = ProviderConfigManager.list_providers()
        return jsonify({
            'success': True,
            'providers': providers,
            'default': DEFAULT_PROVIDER
        })
    except Exception as e:
        logger.error(f"获取 provider 列表失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


# 注册 WebSocket 路由
def register_websocket(sock):
    """注册 WebSocket 路由"""
    logger.info("Registering WebSocket routes")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        """
        场景实时训练 WebSocket 路由
        
        Args:
            ws: WebSocket 连接对象
            scene_id: 场景 ID
        """
        provider = request.args.get('provider', DEFAULT_PROVIDER).lower()
        
        # 获取异步评估处理器
        async_processor = get_async_processor(scene_assessment_service)
        
        # 创建并处理 WebSocket 连接
        handler = WebSocketHandler(
            ws=ws,
            scene_id=scene_id,
            provider=provider,
            db_module=db_module,
            ConversationRecorder=ConversationRecorder,
            async_processor=async_processor
        )
        
        handler.handle()
