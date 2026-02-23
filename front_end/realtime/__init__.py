import os
import sys
import json
import logging
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, render_template, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_realtime_dir = Path(__file__).parent

realtime_bp = Blueprint('realtime', __name__, 
                        url_prefix='/realtime',
                        template_folder=str(_realtime_dir / 'templates'),
                        static_folder=str(_realtime_dir / 'static'),
                        static_url_path='/realtime/static')

SCENE_PROMPT_DIR = Path(__file__).parent.parent.parent / "scene_prompt"
RECORD_DIR = Path(__file__).parent.parent.parent / "record"
RECORD_DIR.mkdir(exist_ok=True)

DEFAULT_PROVIDER = os.getenv("REALTIME_PROVIDER", "qwen").lower()

active_sessions = {}


class ConversationRecorder:
    def __init__(self, scene_id: str, scene_name: str, provider: str = "qwen"):
        self.scene_id = scene_id
        self.scene_name = scene_name
        self.provider = provider
        self.start_time = datetime.now()
        self.messages = []
        self.system_prompt = ""
    
    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
    
    def add_message(self, role: str, text: str):
        if text and text.strip():
            self.messages.append({
                'role': role,
                'text': text.strip(),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            logger.info(f"[{role}] {text[:50]}...")
    
    def save(self):
        if not self.messages:
            logger.info("No messages to save")
            return None
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        record = {
            'scene_id': self.scene_id,
            'scene_name': self.scene_name,
            'provider': self.provider,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': int(duration),
            'message_count': len(self.messages),
            'system_prompt': self.system_prompt,
            'messages': self.messages
        }
        
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        safe_scene_name = "".join(c for c in self.scene_name if c.isalnum() or c in ('_', '-'))
        filename = f"{safe_scene_name}_{timestamp}.json"
        filepath = RECORD_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            logger.info(f"Conversation saved to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Save conversation error: {e}")
            return None
    
    def get_text_content(self) -> str:
        lines = []
        lines.append(f"场景: {self.scene_name}")
        lines.append(f"服务商: {self.provider}")
        lines.append(f"时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")
        
        for msg in self.messages:
            role_name = "用户" if msg['role'] == 'user' else "AI"
            lines.append(f"[{msg['timestamp']}] {role_name}:")
            lines.append(msg['text'])
            lines.append("")
        
        return "\n".join(lines)


@realtime_bp.route('/<scene_id>')
def index(scene_id):
    scene_file = find_scene_file(scene_id)
    if not scene_file:
        return "场景不存在", 404
    
    scene_name = scene_file.stem.rsplit('_', 2)[0] if '_' in scene_file.stem else scene_file.stem
    
    provider = request.args.get('provider', DEFAULT_PROVIDER)
    
    return render_template('realtime.html', 
                          scene_id=scene_id, 
                          scene_name=scene_name,
                          provider=provider)


@realtime_bp.route('/prompt/<scene_id>')
def get_prompt(scene_id):
    scene_file = find_scene_file(scene_id)
    if not scene_file:
        return jsonify({'success': False, 'error': '场景不存在'})
    
    try:
        with open(scene_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        return jsonify({'success': True, 'prompt': prompt})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def find_scene_file(scene_id):
    if not SCENE_PROMPT_DIR.exists():
        return None
    
    for file in SCENE_PROMPT_DIR.glob('*.txt'):
        if scene_id in file.name or file.name == scene_id:
            return file
    
    return None


def register_websocket(app, sock):
    app.register_blueprint(realtime_bp)
    logger.info("Registered realtime blueprint")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        provider = request.args.get('provider', DEFAULT_PROVIDER).lower()
        logger.info(f"WebSocket connection for scene: {scene_id}, provider: {provider}")
        
        scene_file = find_scene_file(scene_id)
        if not scene_file:
            ws.send(json.dumps({'type': 'error', 'message': '场景不存在'}))
            ws.close()
            return
        
        scene_name = scene_file.stem.rsplit('_', 2)[0] if '_' in scene_file.stem else scene_file.stem
        
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'读取提示词失败: {str(e)}'}))
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
                'message': f'正在连接服务器 (服务商: {provider})...'
            }))
            
            client.connect(instructions=system_prompt)
            
            ws.send(json.dumps({
                'type': 'status',
                'status': 'connected',
                'message': f'已连接到服务器 (服务商: {provider})'
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
