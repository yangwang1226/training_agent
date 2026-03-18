"""
WebSocket 处理器

提供 WebSocket 路由的核心处理逻辑
"""

import json
import logging
from typing import Callable

from .session_manager import RealtimeSessionManager
from .message_handler import MessageHandler
from .assessment_manager import AssessmentTaskManager
from .provider_config import ProviderConfigManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """WebSocket 连接处理器"""
    
    def __init__(
        self,
        ws,
        scene_id: str,
        provider: str,
        db_module,
        ConversationRecorder,
        async_processor
    ):
        """
        初始化 WebSocket 处理器
        
        Args:
            ws: WebSocket 连接对象
            scene_id: 场景 ID
            provider: realtime provider 名称
            db_module: 数据库模块
            ConversationRecorder: 对话录制器类
            async_processor: 异步评估处理器
        """
        self.ws = ws
        self.scene_id = scene_id
        self.provider = provider
        self.db_module = db_module
        self.ConversationRecorder = ConversationRecorder
        
        # 创建管理器
        self.session_manager = None
        self.message_handler = None
        self.assessment_manager = AssessmentTaskManager(async_processor)
    
    def handle(self):
        """
        处理 WebSocket 连接
        """
        logger.info(f"WebSocket connection for scene: {self.scene_id}, provider: {self.provider}")
        
        try:
            # 1. 验证 provider
            if not self._validate_provider():
                return
            
            # 2. 解析场景 ID
            scene_id_int = self._parse_scene_id()
            if scene_id_int is None:
                return
            
            # 3. 创建会话管理器
            self.session_manager = RealtimeSessionManager(
                ws=self.ws,
                scene_id=scene_id_int,
                provider=self.provider,
                db_module=self.db_module,
                ConversationRecorder=self.ConversationRecorder
            )
            
            # 4. 初始化会话
            if not self.session_manager.initialize():
                return
            
            # 5. 创建消息处理器
            self.message_handler = MessageHandler(self.session_manager)
            
            # 6. 连接到 realtime 服务
            if not self._connect_to_service():
                return
            
            # 7. 处理消息循环
            self._message_loop()
            
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}", exc_info=True)
            self._send_error(f"处理连接时发生错误：{str(e)}")
        finally:
            self._cleanup()
    
    def _validate_provider(self) -> bool:
        """
        验证 provider 是否有效
        
        Returns:
            是否有效
        """
        is_valid, error_msg = ProviderConfigManager.validate_provider(self.provider)
        if not is_valid:
            self._send_error(error_msg)
            self._close_connection()
            return False
        return True
    
    def _parse_scene_id(self) -> int:
        """
        解析场景 ID
        
        Returns:
            场景 ID，解析失败返回 None
        """
        try:
            return int(self.scene_id)
        except ValueError:
            self._send_error('无效的场景 ID')
            self._close_connection()
            return None
    
    def _connect_to_service(self) -> bool:
        """
        连接到 realtime 服务
        
        Returns:
            是否连接成功
        """
        try:
            # 发送连接中状态
            self.session_manager.send_status(
                'connecting',
                f'正在连接服务器 (服务商：{self.provider})...'
            )
            
            # 连接
            if not self.session_manager.connect():
                return False
            
            # 发送已连接状态
            self.session_manager.send_status(
                'connected',
                f'已连接到服务器 (服务商：{self.provider})'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to service: {e}")
            self._send_error(f"连接服务失败：{str(e)}")
            return False
    
    def _message_loop(self):
        """
        消息处理循环
        """
        while True:
            try:
                # 接收消息，60秒超时
                data = self.ws.receive(timeout=60)
                
                # 连接关闭
                if data is None:
                    logger.info("Connection closed by client")
                    break
                
                # 处理消息
                should_continue = self.message_handler.handle(data)
                
                # 如果是会话结束消息，处理保存和评估
                if not should_continue:
                    self._handle_session_completion()
                    break
                    
            except Exception as e:
                if self._is_normal_close(e):
                    logger.debug(f"WebSocket 连接已关闭: {e}")
                else:
                    logger.error(f"WebSocket receive error: {e}")
                break
    
    def _handle_session_completion(self):
        """
        处理会话完成（保存和评估）
        """
        try:
            # 1. 保存对话记录和音频
            save_result = self.session_manager.save_conversation()
            
            # 2. 提交异步评估任务
            task_id = self.assessment_manager.submit_assessment(
                session_manager=self.session_manager,
                save_result=save_result
            )
            
            # 3. 通知前端
            if task_id:
                self.assessment_manager.notify_assessment_submitted(
                    self.ws,
                    self.session_manager.get_session_id(),
                    task_id
                )
            else:
                self.assessment_manager.notify_assessment_error(
                    self.ws,
                    '评估任务提交失败'
                )
            
            # 4. 通知前端可以关闭连接
            self.assessment_manager.notify_ready_to_close(self.ws)
            
        except Exception as e:
            logger.error(f"会话完成处理失败：{str(e)}", exc_info=True)
            self.assessment_manager.notify_assessment_error(self.ws, str(e))
    
    def _cleanup(self):
        """
        清理资源
        """
        try:
            if self.session_manager:
                self.session_manager.cleanup()
            logger.info(f"WebSocket closed for scene: {self.scene_id}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _send_error(self, message: str):
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
    
    def _close_connection(self):
        """
        关闭 WebSocket 连接
        """
        try:
            self.ws.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
    
    @staticmethod
    def _is_normal_close(error: Exception) -> bool:
        """
        判断是否为正常的连接关闭
        
        Args:
            error: 异常对象
            
        Returns:
            是否为正常关闭
        """
        error_str = str(error)
        normal_codes = ["Connection closed", "1005", "1000"]
        return any(code in error_str for code in normal_codes)