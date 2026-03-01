import os
import sys
import json
import logging
import base64
import struct
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, render_template, jsonify, request, session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db as db_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_realtime_dir = Path(__file__).parent

realtime_bp = Blueprint('realtime', __name__, 
                        url_prefix='/realtime',
                        template_folder=str(_realtime_dir / 'templates'),
                        static_folder=str(_realtime_dir / 'static'),
                        static_url_path='/realtime/static')

RECORD_DIR = Path(__file__).parent.parent.parent / "record"
RECORD_DIR.mkdir(exist_ok=True)

AUDIO_DIR = Path(__file__).parent.parent.parent / "audio_file"
AUDIO_DIR.mkdir(exist_ok=True)

DEFAULT_PROVIDER = os.getenv("REALTIME_PROVIDER", "qwen").lower()

active_sessions = {}


class ConversationRecorder:
    SAMPLE_RATE = 24000
    CHANNELS = 1
    BITS_PER_SAMPLE = 16
    
    def __init__(self, scene_id: str, scene_name: str, provider: str = "qwen", user_id: int = 0):
        self.session_id = str(uuid.uuid4())
        self.scene_id = scene_id
        self.scene_name = scene_name
        self.provider = provider
        self.user_id = user_id
        self.start_time = datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.system_prompt = ""
        self.audio_chunks: List[bytes] = []
        self._total_audio_bytes = 0
    
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
    
    def add_audio_chunk(self, audio_b64: str):
        try:
            audio_data = base64.b64decode(audio_b64)
            self.audio_chunks.append(audio_data)
            self._total_audio_bytes += len(audio_data)
            logger.debug(f"Added audio chunk: {len(audio_data)} bytes, total: {self._total_audio_bytes}")
        except Exception as e:
            logger.error(f"Add audio chunk error: {e}")
    
    def _create_wav_header(self, data_size: int) -> bytes:
        sample_rate = self.SAMPLE_RATE
        channels = self.CHANNELS
        bits_per_sample = self.BITS_PER_SAMPLE
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)
        
        header = bytearray()
        header.extend(b'RIFF')
        header.extend(struct.pack('<I', 36 + data_size))
        header.extend(b'WAVE')
        header.extend(b'fmt ')
        header.extend(struct.pack('<I', 16))
        header.extend(struct.pack('<H', 1))
        header.extend(struct.pack('<H', channels))
        header.extend(struct.pack('<I', sample_rate))
        header.extend(struct.pack('<I', byte_rate))
        header.extend(struct.pack('<H', block_align))
        header.extend(struct.pack('<H', bits_per_sample))
        header.extend(b'data')
        header.extend(struct.pack('<I', data_size))
        
        return bytes(header)
    
    def _save_audio_file(self) -> Optional[str]:
        if not self.audio_chunks:
            logger.info("No audio data to save")
            return None
        
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        safe_scene_name = "".join(c for c in self.scene_name if c.isalnum() or c in ('_', '-'))
        filename = f"{safe_scene_name}_{timestamp}_{self.session_id[:8]}.wav"
        filepath = AUDIO_DIR / filename
        
        try:
            total_pcm_size = sum(len(chunk) for chunk in self.audio_chunks)
            
            with open(filepath, 'wb') as f:
                wav_header = self._create_wav_header(total_pcm_size)
                f.write(wav_header)
                
                for chunk in self.audio_chunks:
                    f.write(chunk)
            
            relative_path = f"audio_file/{filename}"
            logger.info(f"Audio saved to: {filepath}, size: {total_pcm_size} bytes")
            return relative_path
        except Exception as e:
            logger.error(f"Save audio error: {e}")
            return None
    
    def _calculate_duration(self) -> int:
        if self._total_audio_bytes == 0:
            end_time = datetime.now()
            return int((end_time - self.start_time).total_seconds())
        
        bytes_per_second = self.SAMPLE_RATE * self.CHANNELS * (self.BITS_PER_SAMPLE // 8)
        duration_seconds = self._total_audio_bytes / bytes_per_second
        return int(duration_seconds)
    
    def _generate_word_content(self) -> str:
        word_list = []
        for msg in self.messages:
            role = "ai" if msg['role'] == 'ai' else "trainer"
            word_list.append({
                "role": role,
                "content": msg['text'],
                "timestamp": msg['timestamp']
            })
        return json.dumps(word_list, ensure_ascii=False)
    
    def save(self) -> Dict[str, Any]:
        if not self.messages:
            logger.info("No messages to save")
            return None
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        audio_path = self._save_audio_file()
        call_duration = self._calculate_duration()
        word_content = self._generate_word_content()
        
        try:
            db_module.save_coach_record(
                session_id=self.session_id,
                scene_id=int(self.scene_id),
                user_id=self.user_id,
                word_content=word_content,
                oss_file_path=audio_path,
                call_duration=call_duration
            )
            logger.info(f"Database record saved: session_id={self.session_id}")
        except Exception as e:
            logger.error(f"Save to database error: {e}")
        
        return {
            'session_id': self.session_id,
            'audio_file': audio_path,
            'call_duration': call_duration,
            'message_count': len(self.messages)
        }
    
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
        return "无效的场景ID", 400
    except Exception as e:
        logger.error(f"获取场景失败: {e}")
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
        return jsonify({'success': False, 'error': '无效的场景ID'})
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
            ws.send(json.dumps({'type': 'error', 'message': '无效的场景ID'}))
            ws.close()
            return
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'获取场景失败: {str(e)}'}))
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
