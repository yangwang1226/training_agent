"""
WebSocket 会话管理器

管理 realtime WebSocket 会话的生命周期，包括：
- 会话初始化
- 客户端连接管理
- 对话录制
- 状态通知
"""

import json
import logging
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class RealtimeSessionManager:
    """管理 realtime WebSocket 会话的生命周期"""
    
    def __init__(self, ws, scene_id: int, provider: str, db_module, ConversationRecorder):
        """
        初始化会话管理器
        
        Args:
            ws: WebSocket 连接对象
            scene_id: 场景 ID
            provider: realtime provider 名称
            db_module: 数据库模块
            ConversationRecorder: 对话录制器类
        """
        self.ws = ws
        self.scene_id = scene_id
        self.provider = provider
        self.db_module = db_module
        self.ConversationRecorder = ConversationRecorder
        
        # 会话状态
        self.scene: Optional[Dict] = None
        self.recorder = None
        self.client = None
        self.is_session_ended = False
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """
        初始化会话，验证场景并创建必要的对象
        
        Returns:
            是否初始化成功
        """
        try:
            # 1. 验证并加载场景
            if not self._load_scene():
                return False
            
            # 2. 创建对话录制器
            if not self._create_recorder():
                return False
            
            # 3. 创建 realtime 客户端
            if not self._create_client():
                return False
            
            # 4. 设置客户端回调
            self._setup_callbacks()
            
            self.is_initialized = True
            logger.info(f"Session initialized successfully: scene={self.scene_id}, provider={self.provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}", exc_info=True)
            self.send_error(f"初始化会话失败：{str(e)}")
            self._close_connection()
            return False
    
    def _load_scene(self) -> bool:
        """加载并验证场景"""
        try:
            self.scene = self.db_module.get_scene_by_id(self.scene_id)
            if not self.scene:
                self.send_error('场景不存在')
                self._close_connection()
                return False
            
            logger.info(f"Scene loaded: {self.scene.get('scene_name', '未知场景')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load scene: {e}")
            self.send_error(f"加载场景失败：{str(e)}")
            self._close_connection()
            return False
    
    def _create_recorder(self) -> bool:
        """创建对话录制器"""
        try:
            scene_name = self.scene.get('scene_name', '未知场景')
            self.recorder = self.ConversationRecorder(
                self.scene_id, 
                scene_name, 
                self.provider
            )
            
            # 设置系统提示词
            system_prompt = self.scene.get('scene_prompt', '')
            self.recorder.set_system_prompt(system_prompt)
            
            logger.info(f"Recorder created for session: {self.recorder.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create recorder: {e}")
            self.send_error(f"创建录制器失败：{str(e)}")
            return False
    
    def _create_client(self) -> bool:
        """创建 realtime 客户端"""
        try:
            from llm import RealtimeConfig, ProviderType, RealtimeClient
            
            config = RealtimeConfig.from_provider(ProviderType(self.provider))
            self.client = RealtimeClient.create(self.provider, config)
            
            logger.info(f"Realtime client created: provider={self.provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create realtime client: {e}")
            self.send_error(f"创建客户端失败：{str(e)}")
            return False
    
    def _setup_callbacks(self):
        """设置客户端回调函数"""
        self.client.on_text(self._on_text)
        self.client.on_audio(self._on_audio)
        self.client.on_status(self._on_status)
    
    def _on_text(self, text: str, role: str, is_final: bool):
        """处理文本消息回调"""
        try:
            # 记录最终的消息
            if is_final and text:
                self.recorder.add_message(role, text)
            
            # 发送给前端
            self.ws.send(json.dumps({
                'type': 'text',
                'role': role,
                'text': text,
                'is_final': is_final
            }))
        except Exception as e:
            logger.error(f"Error in text callback: {e}")
    
    def _on_audio(self, audio_b64: str):
        """处理音频数据回调"""
        try:
            logger.debug(f"Received audio data, length: {len(audio_b64)}")
            
            # 记录音频
            self.recorder.add_audio_chunk(audio_b64)
            
            # 发送给前端
            self.ws.send(json.dumps({
                'type': 'audio',
                'audio': audio_b64
            }))
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
    
    def _on_status(self, status: str, message: str):
        """处理状态更新回调"""
        try:
            self.ws.send(json.dumps({
                'type': 'status',
                'status': status,
                'message': message
            }))
        except Exception as e:
            logger.debug(f"Status update failed: {e}")
    
    def connect(self) -> bool:
        """
        连接到 realtime 服务
        
        Returns:
            是否连接成功
        """
        try:
            system_prompt = self.scene.get('scene_prompt', '')
            self.client.connect(instructions=system_prompt)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to realtime service: {e}")
            self.send_error(f"连接服务失败：{str(e)}")
            return False
    
    def send_status(self, status: str, message: str):
        """
        发送状态消息
        
        Args:
            status: 状态标识
            message: 状态消息
        """
        try:
            self.ws.send(json.dumps({
                'type': 'status',
                'status': status,
                'message': message
            }))
        except Exception as e:
            logger.error(f"Failed to send status: {e}")
    
    def send_error(self, message: str):
        """
        发送错误消息
        
        Args:
            message: 错误消息
        """
        try:
            self.ws.send(json.dumps({
                'type': 'error',
                'message': message
            }))
        except Exception as e:
            logger.error(f"Failed to send error: {e}")
    
    def handle_audio_message(self, message: Dict[str, Any]):
        """
        处理音频消息
        
        Args:
            message: 包含音频数据的消息字典
        """
        try:
            audio_b64 = message.get('audio', '')
            if audio_b64:
                audio_data = base64.b64decode(audio_b64)
                self.client.send_audio(audio_data)
        except Exception as e:
            logger.error(f"Failed to handle audio message: {e}")
    
    def handle_text_message(self, message: Dict[str, Any]):
        """
        处理文本消息
        
        Args:
            message: 包含文本的消息字典
        """
        try:
            text = message.get('text', '')
            if text:
                self.client.send_text(text)
        except Exception as e:
            logger.error(f"Failed to handle text message: {e}")
    
    def handle_session_end(self) -> bool:
        """
        处理会话结束
        
        Returns:
            是否处理成功
        """
        if self.is_session_ended:
            logger.warning("Session already ended")
            return False
        
        self.is_session_ended = True
        logger.info("=" * 60)
        logger.info("收到前端会话结束信号，开始保存和评估...")
        
        try:
            # 发送确认消息
            self.ws.send(json.dumps({
                'type': 'session_end_received',
                'message': 'Server received'
            }))
            logger.info("Session end confirmation sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle session end: {e}")
            return False
    
    def save_conversation(self) -> Optional[Dict]:
        """
        保存对话记录
        
        Returns:
            保存结果字典，包含 session_id, audio_file, call_duration
        """
        try:
            save_result = self.recorder.save()
            if save_result:
                logger.info(
                    f"Conversation saved: session_id={save_result['session_id']}, "
                    f"audio={save_result.get('audio_file')}"
                )
                
                # 通知前端保存完成
                self.ws.send(json.dumps({
                    'type': 'save_complete',
                    'session_id': save_result['session_id'],
                    'audio_file': save_result.get('audio_file', ''),
                    'call_duration': save_result.get('call_duration', 0)
                }))
                
                return save_result
            else:
                logger.warning("Failed to save conversation")
                return None
                
        except Exception as e:
            logger.error(f"Error saving conversation: {e}", exc_info=True)
            return None
    
    def get_transcript_text(self) -> str:
        """
        获取对话转录文本
        
        Returns:
            转录文本
        """
        return self.recorder.get_transcript_text()
    
    def get_session_id(self) -> str:
        """获取会话 ID"""
        return self.recorder.session_id if self.recorder else None
    
    def get_user_id(self) -> int:
        """获取用户 ID"""
        return self.recorder.user_id if self.recorder else None
    
    def get_call_duration(self) -> int:
        """获取通话时长"""
        return self.recorder.get_duration() if self.recorder else 0
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            # 关闭 realtime 客户端
            if self.client:
                self.client.close()
                logger.info("Realtime client closed")
            
            # 如果会话没有正常结束，保存对话记录
            if not self.is_session_ended and self.recorder:
                save_result = self.recorder.save()
                if save_result:
                    logger.info(f"Conversation saved during cleanup: {save_result}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    def _close_connection(self):
        """关闭 WebSocket 连接"""
        try:
            self.ws.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
