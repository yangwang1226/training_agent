import json
import logging
import base64
import struct
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

AUDIO_DIR = Path(__file__).parent.parent.parent.parent / "audio_file"
AUDIO_DIR.mkdir(exist_ok=True)


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
            import db as db_module
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
        lines.append(f"场景：{self.scene_name}")
        lines.append(f"服务商：{self.provider}")
        lines.append(f"时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")
        
        for msg in self.messages:
            role_name = "用户" if msg['role'] == 'user' else "AI"
            lines.append(f"[{msg['timestamp']}] {role_name}:")
            lines.append(msg['text'])
            lines.append("")
        
        return "\n".join(lines)
    
    def get_transcript_text(self) -> str:
        """获取对话转录文本 (用于评估)"""
        lines = []
        for msg in self.messages:
            role_name = "用户" if msg['role'] == 'user' else "AI"
            lines.append(f"[{msg['timestamp']}] {role_name}: {msg['text']}")
        return "\n".join(lines)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取对话消息列表"""
        return self.messages
    
    def get_duration(self) -> int:
        """获取通话时长 (秒)"""
        return self._calculate_duration()
