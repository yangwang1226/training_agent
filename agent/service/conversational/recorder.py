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
        if not text:
            return
            
        clean_text = text.strip()
        if not clean_text:
            return
            
        # 统一角色名称映射（避免出现 user/trainer 和 ai/assistant 混用的情况）
        normalized_role = role
        if role in ['user', 'User', '用户']:
            normalized_role = 'user'
        elif role in ['ai', 'assistant', 'AI', 'trainer']:
            normalized_role = 'ai'
            
        now = datetime.now()
        current_time_str = now.strftime('%H:%M:%S')
        
        # 如果消息列表为空，直接添加
        if not self.messages:
            self.messages.append({
                'role': normalized_role,
                'text': clean_text,
                'timestamp': current_time_str,
                '_time': now  # 内部使用，用于时间判断
            })
            logger.info(f"[{normalized_role}] {clean_text[:50]}...")
            return
            
        last_msg = self.messages[-1]
        
        # 判断是否应该合并到上一条消息：
        # 1. 角色相同
        # 2. 与上一条消息的时间间隔在 5 秒以内（针对流式分块）
        time_diff = (now - last_msg.get('_time', now)).total_seconds()
        
        if last_msg['role'] == normalized_role and time_diff < 5.0:
            # 拼接文本，如果原文本不为空且新文本不是标点，可能需要加空格（英文），中文直接拼
            last_msg['text'] += clean_text
            last_msg['_time'] = now  # 更新最后活动时间
            # 这里不打印 log 避免日志被切片刷屏
        else:
            self.messages.append({
                'role': normalized_role,
                'text': clean_text,
                'timestamp': current_time_str,
                '_time': now
            })
            logger.info(f"[{normalized_role}] {clean_text[:50]}...")
    
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
        # ⚠️ [架构变更]：录音功能已迁移至前端混音并直接上传
        # 此处的单向 PCM 保存逻辑已废弃，避免生成只有 AI 声音的冗余 wav 文件。
        # 真实的文件路径将在前端调用 /api/upload_audio 时更新进数据库
        logger.info("Skip backend audio save. Using frontend mixed audio recording instead.")
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
