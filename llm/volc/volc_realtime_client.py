"""
火山引擎实时对话客户端
继承 RealtimeClient，复用 DialogSession 的成熟逻辑
"""
import asyncio
import base64
import logging
import threading
import queue
from typing import Callable, Optional, Dict, Any
from uuid import uuid4

from llm.realtime_base import RealtimeClient, RealtimeConfig, RealtimeCallback
from llm.volc.realtime_dialog.audio_manager import DialogSession
from llm.volc.realtime_dialog import config as volc_config

logger = logging.getLogger(__name__)


class VolcRealtimeCallback(RealtimeCallback):
    """
    火山引擎回调
    
    将 DialogSession 的响应转换为标准 RealtimeCallback 格式
    """
    
    def __init__(self):
        super().__init__()
        logger.info("VolcRealtimeCallback initialized")
    
    def on_open(self) -> None:
        """连接打开时调用"""
        logger.info("Volc connection opened")
        self._emit_status("connected", "已连接")
    
    def on_close(self, close_status_code, close_msg) -> None:
        """连接关闭时调用"""
        logger.info(f"Volc connection closed: {close_status_code} - {close_msg}")
        self._emit_status("disconnected", "连接已关闭")
    
    def on_event(self, event: dict) -> None:
        """接收到事件时调用（可选处理）"""
        # 事件已在 CustomDialogSession.handle_server_response 中处理
        pass


class VolcRealtimeClient(RealtimeClient):
    """
    火山引擎实时对话客户端
    
    架构设计：
    前端 WebSocket → RealtimeSession → VolcRealtimeClient → DialogSession → 火山引擎
    
    职责：
    1. 实现 RealtimeClient 抽象接口
    2. 内部使用 DialogSession 处理火山协议
    3. 将火山响应转换为标准回调
    """
    
    def __init__(self, config: RealtimeConfig):
        super().__init__(config)
        self.callback = VolcRealtimeCallback()
        
        # 内部使用 DialogSession
        self.dialog_session: Optional[DialogSession] = None
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None
        self.async_thread: Optional[threading.Thread] = None
        
        # 浏览器音频输入队列
        self.audio_input_queue = queue.Queue()
        
        # 运行状态
        self.is_running = False
        
        # prompt
        self.prompt = ""
        logger.info("VolcRealtimeClient initialized")
    

    def on_text(self, handler: Callable):
        if self.callback:
            self.callback.on_text(handler)
        return self
    
    def on_audio(self, handler: Callable):
        if self.callback:
            self.callback.on_audio(handler)
        return self
    
    def on_status(self, handler: Callable):
        if self.callback:
            self.callback.on_status(handler)
        return self          
    
    # def _build_ws_config(self) -> Dict[str, Any]:
    #     """构建火山引擎 WebSocket 配置"""
    #     return {
    #         'base_url': "wss://openspeech.bytedance.com/api/v3/realtime/dialogue",
    #         'headers': {
    #             'X-Api-App-ID': self.config.volc_app_id,
    #             'X-Api-Access-Key': self.config.api_key,
    #             'X-Api-Resource-Id': 'volc.speech.dialog',
    #             'X-Api-App-Key': "PlgvMymc7f3tQnJ6",
    #             'X-Api-Connect-Id': str(uuid4()),
    #         },
    #         'prompt' : self.prompt
    #     }
    
    def connect(self, instructions: str = "", api_key: str = None):
        """
        建立连接
        
        Args:
            instructions: 系统提示词（暂不支持自定义）
            api_key: API 密钥（可选，使用配置中的值）
        """
        if api_key:
            self.config.api_key = api_key
        
        if not self.config.api_key or not self.config.volc_app_id:
            raise ValueError("Volc API credentials not configured. Check .env file.")
        
        logger.info(f"🔥 Connecting to Volc Realtime: app_id={self.config.volc_app_id}")
        
        if instructions:
            self.prompt = instructions
        # 启动异步线程
        self.is_running = True
        self.async_thread = threading.Thread(
            target=self._async_worker,
            name="VolcAsyncWorker",
            daemon=True
        )
        self.async_thread.start()
        
        # 等待连接建立
        import time
        timeout = 10
        start_time = time.time()
        while not self.is_connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not self.is_connected:
            raise ConnectionError("Failed to connect to Volc Realtime within timeout")
        
        logger.info("✅ Connected to Volc Realtime")
    
    def _async_worker(self):
        """
        异步工作线程
        
        运行独立的事件循环，管理 DialogSession
        """
        # 创建新的事件循环
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)
        
        try:
            self.async_loop.run_until_complete(self._async_main())
        except Exception as e:
            logger.error(f"❌ Async worker error: {e}", exc_info=True)
            self.callback._emit_status("error", f"连接失败: {str(e)}")
        finally:
            self.async_loop.close()
            logger.info("Async worker stopped")
    
    async def _async_main(self):
        """异步主逻辑"""
        try:
            # 创建自定义的 DialogSession
            self.dialog_session = CustomDialogSession(
                # ws_config=self._build_ws_config(),
                callback=self.callback,
                audio_input_queue=self.audio_input_queue,
                prompt = self.prompt
            )
            
            # 连接到火山引擎
            await self.dialog_session.client.connect()
            
            # 标记为已连接
            self.is_connected = True
            self.callback._emit_status("connected", "已连接到火山引擎")
            
            # 启动音频输入和响应接收循环
            await asyncio.gather(
                self.dialog_session.process_browser_input(),
                self.dialog_session.receive_loop(),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"❌ Async main error: {e}", exc_info=True)
            raise
        finally:
            self.is_connected = False
    
    def send_audio(self, audio_data: bytes):
        """
        发送音频数据
        
        Args:
            audio_data: PCM 音频数据（16kHz, 16bit, 单声道）
        """
        if not self.is_connected:
            logger.warning("Not connected, cannot send audio")
            return
        
        try:
            self.audio_input_queue.put(audio_data)
            logger.debug(f"Audio queued: {len(audio_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to queue audio: {e}")
    
    def send_text(self, text: str):
        """
        发送文本消息
        
        Args:
            text: 文本内容
        """
        if not self.is_connected or not self.dialog_session:
            logger.warning("Not connected, cannot send text")
            return
        
        # TODO: 实现文本发送（如果火山支持）
        logger.warning("Text input not yet implemented for Volc")
    
    def read_mic_audio(self) -> Optional[bytes]:
        """
        读取麦克风音频（Web 模式下不使用）
        
        Returns:
            None（Web 模式下音频来自浏览器）
        """
        return None
    
    def close(self):
        """关闭连接"""
        logger.info("🔚 Closing Volc Realtime connection")
        
        self.is_running = False
        self.is_connected = False
        
        # 停止 DialogSession
        if self.dialog_session:
            self.dialog_session.is_running = False
        
        # 等待异步线程结束
        if self.async_thread and self.async_thread.is_alive():
            self.async_thread.join(timeout=3.0)
        
        logger.info("✅ Volc Realtime connection closed")


class CustomDialogSession(DialogSession):
    """
    自定义的 DialogSession
    
    扩展原有的 DialogSession，将响应转换为 RealtimeCallback
    """
    
    def __init__(self, callback: VolcRealtimeCallback, audio_input_queue: queue.Queue, prompt: str=None):
        # 不调用父类 __init__，手动初始化
        self.callback = callback
        self.audio_input_queue = audio_input_queue
        
        # 手动初始化（复制 _manual_init 逻辑）
        from llm.volc.realtime_dialog.realtime_dialog_client import RealtimeDialogClient
        import uuid
        
        self.session_id = str(uuid.uuid4())
        self.client = RealtimeDialogClient(
            # config=ws_config,
            session_id=self.session_id,
            output_audio_format="pcm_s16le",
            mod="audio",
            recv_timeout=10,
            prompt=prompt
        )
        
        # 状态控制
        self.is_running = True
        self.is_session_finished = False
        self.is_user_querying = False
        self.is_sending_chat_tts_text = False
        self.audio_buffer = b''
        
        # 音频队列
        self.audio_queue = queue.Queue()
        self.from_browser_queue = audio_input_queue
        
        # 不需要播放线程（回调方式发送音频）
        self.is_playing = False
        
        logger.info("CustomDialogSession initialized")
    
    async def process_browser_input(self):
        """处理浏览器音频输入"""
        logger.info("Started processing browser input")
        
        while self.is_running:
            try:
                audio_data = self.from_browser_queue.get_nowait()
                await self.client.task_request(audio_data)
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Process browser input error: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Stopped processing browser input")
    
    async def receive_loop(self):
        """接收循环：从火山引擎接收响应"""
        logger.debug("Receive loop started")
        
        try:
            while self.is_running:
                response = await self.client.receive_server_response()
                self.handle_server_response(response)
                
                # 检查会话结束
                if 'event' in response and response['event'] in [152, 153]:
                    logger.info(f"Session finished event: {response['event']}")
                    self.is_session_finished = True
                    break
                    
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
        finally:
            self.is_running = False
            self.is_session_finished = True
        
        logger.debug("Receive loop stopped")
    
    def handle_server_response(self, response: Dict[str, Any]) -> None:
        """
        处理服务器响应
        
        将火山响应转换为 RealtimeCallback 回调
        """
        if not response:
            return
        
        msg_type = response.get('message_type')
        
        # 音频数据
        if msg_type == 'SERVER_ACK' and isinstance(response.get('payload_msg'), bytes):
            if not self.is_sending_chat_tts_text:
                audio_data = response['payload_msg']
                self.audio_buffer += audio_data
                
                # 🔥 通过回调发送音频（而不是 WebSocket）
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                self.callback._emit_audio(audio_b64)
                logger.debug(f"Emitted audio: {len(audio_data)} bytes")
        
        # 事件消息
        elif msg_type == 'SERVER_FULL_RESPONSE':
            event = response.get('event')
            payload_msg = response.get('payload_msg', {})
            
            logger.debug(f"📨 Event {event}: {list(payload_msg.keys()) if isinstance(payload_msg, dict) else 'binary'}")
            
            # 用户打断（清空缓存）
            if event == 450:
                logger.info("User interrupt detected")
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
                self.is_user_querying = True
                self.callback._emit_status("speaking", "用户正在说话...")
            
            # TTS 开始（AI 说的话）
            elif event == 350:
                text = payload_msg.get('text', '')
                if text:
                    self.callback._emit_text(text, role='assistant', is_final=False)
                    logger.info(f"✅ AI text: {text[:50]}")
                self.callback._emit_status("responding", "AI 正在回复...")
            
            # TTS 结束
            elif event == 359:
                self.callback._emit_status("listening", "等待用户输入...")
            
            # ASR 识别结果（用户说的话）
            elif event == 451:
                results = payload_msg.get('results', [])
                for result in results:
                    text = result.get('text', '')
                    is_final = not result.get('is_interim', False)
                    if text:
                        self.callback._emit_text(text, role='user', is_final=is_final)
                        logger.info(f"✅ User text: {text[:50]} (final={is_final})")
            
            # ASR 结束
            elif event == 459:
                logger.info("User stopped speaking")
                self.is_user_querying = False
                self.callback._emit_status("processing", "处理中...")
            
            # LLM 文本回复
            elif event == 550:
                text = payload_msg.get('content', '')
                if text:
                    self.callback._emit_text(text, role='assistant', is_final=True)
                    logger.info(f"✅ LLM text: {text[:50]}")
        
        # 错误消息
        elif msg_type == 'SERVER_ERROR':
            error_msg = response.get('payload_msg', '未知错误')
            logger.error(f"Server error: {error_msg}")
            self.callback._emit_status("error", str(error_msg))