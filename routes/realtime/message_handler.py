"""
消息处理器

处理不同类型的 WebSocket 消息，包括：
- 二进制音频数据
- JSON 格式的控制消息
- 文本消息
- 会话控制消息
"""

import json
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MessageHandler:
    """处理不同类型的 WebSocket 消息"""
    
    def __init__(self, session_manager):
        """
        初始化消息处理器
        
        Args:
            session_manager: RealtimeSessionManager 实例
        """
        self.session = session_manager
        self._handlers: Dict[str, Callable] = self._init_handlers()
    
    def _init_handlers(self) -> Dict[str, Callable]:
        """
        初始化消息类型处理器映射
        
        Returns:
            消息类型到处理函数的映射
        """
        return {
            'audio': self._handle_audio,
            'text': self._handle_text,
            'session_end': self._handle_session_end,
            'stop': self._handle_stop,
            'ping': self._handle_ping,
        }
    
    def handle(self, data: Any) -> bool:
        """
        处理接收到的消息
        
        Args:
            data: 接收到的数据，可以是 bytes 或 str
            
        Returns:
            True 表示继续处理消息，False 表示结束会话
        """
        try:
            # 处理二进制数据（音频）
            if isinstance(data, bytes):
                return self._handle_binary(data)
            
            # 处理 JSON 消息
            if isinstance(data, str):
                return self._handle_json(data)
            
            logger.warning(f"Unknown data type: {type(data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return True  # 出错时继续处理其他消息
    
    def _handle_binary(self, data: bytes) -> bool:
        """
        处理二进制音频数据
        
        Args:
            data: 二进制音频数据
            
        Returns:
            True 继续处理
        """
        try:
            logger.debug(f"Received binary audio data: {len(data)} bytes")
            self.session.client.send_audio(data)
            return True
        except Exception as e:
            logger.error(f"Failed to handle binary audio: {e}")
            return True
    
    def _handle_json(self, data: str) -> bool:
        """
        处理 JSON 格式的消息
        
        Args:
            data: JSON 字符串
            
        Returns:
            True 继续处理，False 结束会话
        """
        try:
            message = json.loads(data)
            msg_type = message.get('type', 'unknown')
            
            # 获取对应的处理函数
            handler = self._handlers.get(msg_type)
            
            if handler:
                return handler(message)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                return True
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON message: {e}")
            return True
        except Exception as e:
            logger.error(f"Error processing JSON message: {e}")
            return True
    
    def _handle_audio(self, message: Dict[str, Any]) -> bool:
        """
        处理音频消息
        
        Args:
            message: 包含音频数据的消息字典
            
        Returns:
            True 继续处理
        """
        try:
            self.session.handle_audio_message(message)
            return True
        except Exception as e:
            logger.error(f"Failed to handle audio message: {e}")
            return True
    
    def _handle_text(self, message: Dict[str, Any]) -> bool:
        """
        处理文本消息
        
        Args:
            message: 包含文本的消息字典
            
        Returns:
            True 继续处理
        """
        try:
            self.session.handle_text_message(message)
            return True
        except Exception as e:
            logger.error(f"Failed to handle text message: {e}")
            return True
    
    def _handle_session_end(self, message: Dict[str, Any]) -> bool:
        """
        处理会话结束消息
        
        Args:
            message: 会话结束消息
            
        Returns:
            False 结束会话
        """
        try:
            self.session.handle_session_end()
            return False  # 结束消息循环
        except Exception as e:
            logger.error(f"Failed to handle session end: {e}")
            return False
    
    def _handle_stop(self, message: Dict[str, Any]) -> bool:
        """
        处理停止消息
        
        Args:
            message: 停止消息
            
        Returns:
            False 结束会话
        """
        logger.info("Received stop message")
        return False
    
    def _handle_ping(self, message: Dict[str, Any]) -> bool:
        """
        处理心跳消息
        
        Args:
            message: 心跳消息
            
        Returns:
            True 继续处理
        """
        try:
            # 回复 pong
            self.session.ws.send(json.dumps({
                'type': 'pong',
                'timestamp': message.get('timestamp')
            }))
            return True
        except Exception as e:
            logger.debug(f"Failed to send pong: {e}")
            return True
    
    def register_handler(self, msg_type: str, handler: Callable[[Dict[str, Any]], bool]):
        """
        注册自定义消息处理器
        
        Args:
            msg_type: 消息类型
            handler: 处理函数，接收消息字典，返回是否继续处理
        """
        self._handlers[msg_type] = handler
        logger.info(f"Registered custom handler for message type: {msg_type}")
    
    def unregister_handler(self, msg_type: str):
        """
        取消注册消息处理器
        
        Args:
            msg_type: 消息类型
        """
        if msg_type in self._handlers:
            del self._handlers[msg_type]
            logger.info(f"Unregistered handler for message type: {msg_type}")