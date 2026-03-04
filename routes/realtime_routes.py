import os
import sys
import json
import logging
import base64
from pathlib import Path

from flask import Blueprint, render_template, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db as db_module
from agent.service.conversational import ConversationRecorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_realtime_dir = Path(__file__).parent

realtime_bp = Blueprint('realtime', __name__, 
                        url_prefix='/realtime',
                        template_folder=str(_realtime_dir / 'templates'),
                        static_folder=str(_realtime_dir / 'static'),
                        static_url_path='/realtime/static')

DEFAULT_PROVIDER = os.getenv("REALTIME_PROVIDER", "qwen").lower()


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


def register_websocket(app, sock):
    app.register_blueprint(realtime_bp)
    logger.info("Registered realtime blueprint")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        provider = request.args.get('provider', DEFAULT_PROVIDER).lower()
        logger.info(f"WebSocket connection for scene: {scene_id}, provider: {provider}")
        
        try:
            scene_id_int = int(scene_id)
            scene = db_module.get_scene_by_id(scene_id_int)
            if not scene:
                ws.send(json.dumps({'type': 'error', 'message': '场景不存在'}))
                ws.close()
                return
            
            scene_name = scene.get('scene_name', '未知场景')
            system_prompt = scene.get('scene_prompt', '')
        except ValueError:
            ws.send(json.dumps({'type': 'error', 'message': '无效的场景 ID'}))
            ws.close()
            return
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'获取场景失败：{str(e)}'}))
            ws.close()
            return
        
        recorder = ConversationRecorder(scene_id, scene_name, provider)
        recorder.set_system_prompt(system_prompt)
        
        from llm import create_realtime_client, RealtimeConfig, ProviderType
        
        config = RealtimeConfig.from_provider(ProviderType(provider))
        client = create_realtime_client(provider, config)
        
        def on_text(text, role, is_final):
            try:
                if is_final and text:
                    recorder.add_message(role, text)
                
                ws.send(json.dumps({
                    'type': 'text',
                    'role': role,
                    'text': text,
                    'is_final': is_final
                }))
            except Exception as e:
                logger.error(f"Send text error: {e}")
        
        def on_audio(audio_b64):
            try:
                logger.info(f"Received audio data, length: {len(audio_b64)}")
                recorder.add_audio_chunk(audio_b64)
                ws.send(json.dumps({
                    'type': 'audio',
                    'audio': audio_b64
                }))
            except Exception as e:
                logger.error(f"Send audio error: {e}")
        
        def on_status(status, message):
            try:
                ws.send(json.dumps({
                    'type': 'status',
                    'status': status,
                    'message': message
                }))
            except Exception as e:
                logger.error(f"Send status error: {e}")
        
        client.on_text(on_text)
        client.on_audio(on_audio)
        client.on_status(on_status)
        
        try:
            ws.send(json.dumps({
                'type': 'status',
                'status': 'connecting',
                'message': f'正在连接服务器 (服务商：{provider})...'
            }))
            
            client.connect(instructions=system_prompt)
            
            ws.send(json.dumps({
                'type': 'status',
                'status': 'connected',
                'message': f'已连接到服务器 (服务商：{provider})'
            }))
            
            while True:
                try:
                    data = ws.receive(timeout=60)
                    if data is None:
                        break
                    
                    try:
                        if isinstance(data, bytes):
                            client.send_audio(data)
                        else:
                            message = json.loads(data)
                            msg_type = message.get('type', 'unknown')
                            
                            if msg_type == 'audio':
                                audio_b64 = message.get('audio', '')
                                if audio_b64:
                                    audio_data = base64.b64decode(audio_b64)
                                    client.send_audio(audio_data)
                            
                            elif msg_type == 'text':
                                text = message.get('text', '')
                                if text:
                                    client.send_text(text)
                            
                            elif msg_type == 'stop':
                                break
                                
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON message")
                    except Exception as e:
                        logger.error(f"Process message error: {e}")
                        
                except Exception as e:
                    logger.error(f"WebSocket receive error: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Session error: {e}")
            ws.send(json.dumps({'type': 'error', 'message': str(e)}))
        finally:
            client.close()
            
            saved_path = recorder.save()
            if saved_path:
                logger.info(f"Conversation record saved: {saved_path}")
            
            logger.info(f"WebSocket closed for scene: {scene_id}")
