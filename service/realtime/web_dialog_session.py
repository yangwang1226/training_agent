"""
Web 对话会话适配器
完全复用 DialogSession 的实现，将麦克风输入替换为浏览器音频输入
"""
import asyncio
import base64
import json
import logging
import queue
import threading
from typing import Dict, Any, Optional

from llm.volc.realtime_dialog.audio_manager import DialogSession
import llm.volc.realtime_dialog.config as volc_config

logger = logging.getLogger(__name__)


class WebDialogSession(DialogSession):
    """
    Web 对话会话（继承 DialogSession）
    
    复用 DialogSession 的所有逻辑：
    1. 音频队列管理（self.audio_queue）
    2. 音频播放线程（self._audio_player_thread）
    3. 火山引擎交互（self.client）
    4. 响应处理（self.handle_server_response）
    
    只需要：
    1. 替换麦克风输入为 WebSocket 输入
    2. 将输出音频通过 WebSocket 发送而不是本地播放
    """
    
    def __init__(self, frontend_ws, session_id: str, ws_config: Dict[str, Any]):
        """
        初始化 Web 对话会话
        
        Args:
            frontend_ws: 前端 WebSocket 连接
            session_id: 会话ID
            ws_config: 火山引擎配置
        """
        self.frontend_ws = frontend_ws
        self.web_session_id = session_id
        
        # 手动初始化，不调用父类 __init__（避免 signal.signal 错误）
        self._manual_init(ws_config)
        
        # Web 特定的队列（用于从浏览器接收音频）
        self.from_browser_queue = queue.Queue()
        
        # 标记为 Web 模式
        self.is_web_mode = True
        
        logger.info(f"WebDialogSession initialized: {session_id}")
    
    def _manual_init(self, ws_config: Dict[str, Any]):
        """
        手动初始化（复制父类逻辑，但不使用 signal.signal）
        """
        from llm.volc.realtime_dialog.realtime_dialog_client import RealtimeDialogClient
        import uuid
        
        # 基本属性
        self.audio_file_path = ""
        self.recv_timeout = 10
        self.is_audio_file_input = False
        self.mod = "web"
        
        # 会话ID
        self.session_id = str(uuid.uuid4())
        
        # 创建客户端
        # ✅ 使用 pcm_s16le 格式（16位 PCM），与前端期望的格式一致
        self.client = RealtimeDialogClient(
            config=ws_config,
            session_id=self.session_id,
            output_audio_format="pcm_s16le",  # 16位 PCM
            mod="audio",
            recv_timeout=10
        )
        
        # 状态控制
        self.is_running = True
        self.is_session_finished = False
        self.is_user_querying = False
        self.is_sending_chat_tts_text = False
        self.audio_buffer = b''
        
        # 音频队列（关键：用于接收火山引擎的音频响应）
        self.audio_queue = queue.Queue()
        
        # 播放线程控制
        self.is_recording = True
        self.is_playing = True
        
        # 启动 Web 专用的播放线程
        self.player_thread = threading.Thread(target=self._web_player_thread, daemon=True)
        self.player_thread.start()
        
        logger.info("Manual initialization complete")
    

    
    def _web_player_thread(self):
        """
        Web 播放线程（替代父类的 _audio_player_thread）
        
        从 audio_queue 取音频数据，发送给浏览器而不是本地播放
        """
        logger.debug("Web player thread worker started")
        
        while self.is_playing:
            try:
                # 从队列获取音频数据（阻塞等待，和父类一样）
                audio_data = self.audio_queue.get(timeout=1.0)
                
                if audio_data is not None:
                    # 发送到浏览器（base64 编码）
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    try:
                        self.frontend_ws.send(json.dumps({
                            'type': 'audio',
                            'audio': audio_b64  # ✅ 前端期望字段名为 'audio'
                        }))
                        logger.debug(f"Sent audio to browser: {len(audio_data)} bytes")
                    except Exception as e:
                        logger.error(f"Failed to send audio to browser: {e}")
                        break
                        
            except queue.Empty:
                # 队列为空时继续等待（和父类一样）
                continue
            except Exception as e:
                logger.error(f"Web player thread error: {e}")
                break
        
        logger.debug("Web player thread stopped")
    
    async def process_browser_input(self) -> None:
        """
        处理浏览器音频输入（替代父类的 process_microphone_input）
        
        从队列取浏览器发来的音频数据，发送给火山引擎
        """
        logger.info("Started processing browser input")
        
        while self.is_running:
            try:
                # 从浏览器队列获取音频数据（非阻塞）
                try:
                    audio_data = self.from_browser_queue.get_nowait()
                    
                    # 发送给火山引擎
                    await self.client.task_request(audio_data)
                    
                except queue.Empty:
                    # 队列为空时短暂休眠
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Process browser input error: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Stopped processing browser input")
    
    def add_browser_audio(self, audio_b64: str):
        """
        接收浏览器的音频数据（Base64 编码）
        
        Args:
            audio_b64: Base64 编码的音频数据
        """
        try:
            audio_data = base64.b64decode(audio_b64)
            self.from_browser_queue.put(audio_data)
            logger.debug(f"Received audio from browser (base64): {len(audio_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode browser audio: {e}")
    
    def add_browser_audio_bytes(self, audio_data: bytes):
        """
        接收浏览器的音频数据（原始二进制）
        
        Args:
            audio_data: 原始 PCM 音频数据
        """
        try:
            self.from_browser_queue.put(audio_data)
            logger.debug(f"Received audio from browser (binary): {len(audio_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to add browser audio: {e}")
    
    def handle_server_response(self, response: Dict[str, Any]) -> None:
        """
        处理服务器响应（复制父类实现并扩展）
        
        处理音频和事件，然后发送给前端
        """
        if not response:
            return
        
        # 处理音频数据（复制父类逻辑）
        if response.get('message_type') == 'SERVER_ACK' and isinstance(response.get('payload_msg'), bytes):
            if not self.is_sending_chat_tts_text:
                audio_data = response['payload_msg']
                self.audio_queue.put(audio_data)
                self.audio_buffer += audio_data
        
        # 处理完整响应（复制父类逻辑）
        elif response.get('message_type') == 'SERVER_FULL_RESPONSE':
            event = response.get('event')
            payload_msg = response.get('payload_msg', {})
            
            # 🔍 调试：打印所有事件
            logger.info(f"📨 Received event: {event}, payload keys: {list(payload_msg.keys()) if isinstance(payload_msg, dict) else 'not dict'}")
            
            # 处理特殊事件
            if event == 450:
                # 用户开始说话，清空音频缓存
                logger.info(f"清空缓存音频: {response.get('session_id')}")
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        continue
                self.is_user_querying = True
            
            elif event == 350 and self.is_sending_chat_tts_text and payload_msg.get("tts_type") in ["chat_tts_text", "external_rag"]:
                # 清空缓存
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        continue
                self.is_sending_chat_tts_text = False
        
        # 额外发送事件消息给前端
        if response and response.get('message_type') == 'SERVER_FULL_RESPONSE':
            try:
                event = response.get('event')
                payload = response.get('payload_msg', {})
                
                # 提取文字转录
                text_message = self._extract_text_from_event(event, payload)
                if text_message:
                    # 发送文字消息
                    self.frontend_ws.send(json.dumps(text_message))
                    logger.info(f"✅ Sent text to browser: {text_message.get('role')}: {text_message.get('text', '')[:50]}")
                else:
                    logger.debug(f"No text extracted from event {event}")
                
                # 发送事件消息
                self.frontend_ws.send(json.dumps({
                    'type': 'event',
                    'event': event,
                    'payload': payload if isinstance(payload, dict) else {}
                }))
                
                logger.debug(f"Sent event to browser: {event}")
                
            except Exception as e:
                logger.error(f"Failed to send event to browser: {e}")
    
    def _extract_text_from_event(self, event: int, payload: dict) -> Optional[dict]:
        """
        从事件中提取文字转录
        
        Args:
            event: 事件ID
            payload: 事件负载
            
        Returns:
            文字消息字典或 None
        """
        # 事件 350: TTS 开始（AI 说的话）
        if event == 350:
            text = payload.get('text', '')
            if text:
                return {
                    'type': 'text',
                    'role': 'assistant',
                    'text': text,
                    'is_final': False
                }
        
        # 事件 451: ASR 识别结果（用户说的话）
        elif event == 451:
            results = payload.get('results', [])
            for result in results:
                text = result.get('text', '')
                is_final = result.get('is_final', False)
                if text:
                    return {
                        'type': 'text',
                        'role': 'user',
                        'text': text,
                        'is_final': is_final
                    }
        
        # 事件 550: LLM 文本回复
        elif event == 550:
            text = payload.get('text', '')
            if text:
                return {
                    'type': 'text',
                    'role': 'assistant',
                    'text': text,
                    'is_final': True
                }
        
        return None
    
    async def receive_loop(self):
        """
        接收循环：从火山引擎接收响应
        （复制父类实现）
        """
        try:
            while True:
                response = await self.client.receive_server_response()
                self.handle_server_response(response)
                
                # 检查会话结束事件
                if 'event' in response and (response['event'] == 152 or response['event'] == 153):
                    logger.info(f"receive session finished event: {response['event']}")
                    self.is_session_finished = True
                    break
                
                # TTS 结束事件
                if 'event' in response and response['event'] == 359:
                    logger.info(f"receive tts ended event")
                    
        except asyncio.CancelledError:
            logger.info("接收任务已取消")
        except Exception as e:
            logger.error(f"接收消息错误: {e}")
        finally:
            self.is_running = False
            self.is_session_finished = True
    
    async def start(self) -> None:
        """
        启动 Web 对话会话（复用父类逻辑，替换输入方式）
        """
        try:
            # 连接到火山引擎
            await self.client.connect()
            
            # 通知前端连接成功
            try:
                self.frontend_ws.send(json.dumps({
                    'type': 'status',
                    'status': 'connected',
                    'message': '已连接到火山引擎'
                }))
            except Exception as e:
                logger.error(f"Failed to send status to browser: {e}")
            
            # 启动浏览器输入处理和接收循环（类似父类的逻辑）
            asyncio.create_task(self.process_browser_input())
            asyncio.create_task(self.receive_loop())
            
            # 主循环
            while self.is_running:
                await asyncio.sleep(0.1)
            
            # 会话结束处理（复用父类逻辑）
            await self.client.finish_session()
            
            while not self.is_session_finished:
                await asyncio.sleep(0.1)
            
            await self.client.finish_connection()
            await asyncio.sleep(0.1)
            await self.client.close()
            
            logger.info(f"Dialog request logid: {self.client.logid}")
            
        except Exception as e:
            logger.error(f"Web session error: {e}", exc_info=True)
            
            # 通知前端错误
            try:
                self.frontend_ws.send(json.dumps({
                    'type': 'error',
                    'message': f'会话错误: {str(e)}'
                }))
            except:
                pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源（扩展父类清理逻辑）"""
        logger.info("Cleaning up WebDialogSession...")
        
        self.is_playing = False
        self.is_running = False
        
        # 等待播放线程结束
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=2.0)
        
        # 通知前端会话结束
        try:
            self.frontend_ws.send(json.dumps({
                'type': 'session_end',
                'message': '会话已结束'
            }))
        except:
            pass
        
        logger.info("WebDialogSession cleanup complete")


class WebDialogHandler:
    """
    Web 对话处理器（主入口）
    
    管理异步事件循环和 WebSocket 消息处理
    职责：
    1. 启动异步线程运行 WebDialogSession
    2. 在主线程处理前端 WebSocket 消息
    3. 桥接同步 WebSocket（Flask-Sock）和异步会话
    """
    
    def __init__(self, frontend_ws, session_id: str):
        """
        初始化处理器
        
        Args:
            frontend_ws: 前端 WebSocket 连接（Flask-Sock）
            session_id: 会话ID
        """
        self.frontend_ws = frontend_ws
        self.session_id = session_id
        self.ws_config = volc_config.ws_connect_config
        
        self.session: Optional[WebDialogSession] = None
        self.async_thread: Optional[threading.Thread] = None
        self.is_running = True
        
        logger.info(f"WebDialogHandler initialized: {session_id}")
    
    def run(self):
        """
        主循环入口（阻塞运行）
        
        架构：
        - 异步线程：运行 WebDialogSession
        - 主线程：处理前端 WebSocket 消息
        """
        try:
            # 启动异步线程
            self._start_async_thread()
            
            # 主线程处理前端消息（阻塞）
            self._handle_frontend_messages()
            
        except Exception as e:
            logger.error(f"Handler run error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _start_async_thread(self):
        """启动异步事件循环线程"""
        self.async_thread = threading.Thread(
            target=self._async_thread_worker,
            name=f"WebDialog-{self.session_id[:8]}",
            daemon=True
        )
        self.async_thread.start()
        logger.info("Async thread started")
    
    def _async_thread_worker(self):
        """
        异步线程工作函数
        
        创建独立的事件循环，运行 WebDialogSession
        """
        # 创建新的事件循环（独立于主线程）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 创建 Web 对话会话
            self.session = WebDialogSession(
                frontend_ws=self.frontend_ws,
                session_id=self.session_id,
                ws_config=self.ws_config
            )
            
            # 运行会话（阻塞直到会话结束）
            loop.run_until_complete(self.session.start())
            
        except Exception as e:
            logger.error(f"Async thread error: {e}", exc_info=True)
            
            # 通知前端错误
            try:
                self.frontend_ws.send(json.dumps({
                    'type': 'error',
                    'message': f'连接失败: {str(e)}'
                }))
            except:
                pass
        finally:
            loop.close()
            logger.info("Async thread stopped")
    
    def _handle_frontend_messages(self):
        """
        主线程：处理前端 WebSocket 消息
        
        持续接收前端消息并分发处理
        """
        logger.debug("Frontend message loop started")
        
        while self.is_running:
            try:
                # 接收前端消息（同步，带超时）
                # 注意：receive() 可能返回 str 或 bytes
                data = self.frontend_ws.receive(timeout=0.1)
                
                if data:
                    # 处理数据类型
                    if isinstance(data, bytes):
                        # 二进制数据：直接作为音频处理
                        self._process_frontend_message(data)
                    elif isinstance(data, str):
                        # 文本数据：尝试解析为 JSON
                        if not data.strip():  # 空字符串，忽略
                            continue
                        
                        try:
                            message = json.loads(data)
                            self._process_frontend_message(message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON: {e}, data: {data[:100]}")
                            continue
                    else:
                        logger.warning(f"Unknown data type: {type(data)}")
                    
            except queue.Empty:
                # 超时，继续循环
                pass
            except Exception as e:
                # 检查是否是正常关闭
                if "Connection closed" in str(e) or "closed" in str(e).lower():
                    logger.info("Frontend WebSocket closed normally")
                else:
                    logger.error(f"Frontend message error: {e}")
                break
        
        logger.debug("Frontend message loop stopped")
    
    def _process_frontend_message(self, data):
        """
        处理前端消息
        
        Args:
            data: 可以是 bytes (原始音频) 或 dict (JSON 消息)
        """
        try:
            # 如果是字典（已解析的 JSON）
            if isinstance(data, dict):
                msg_type = data.get('type')
                
                if msg_type == 'audio':
                    # Base64 编码的音频数据
                    if self.session:
                        audio_b64 = data.get('data', '')
                        self.session.add_browser_audio(audio_b64)
                    else:
                        logger.warning("Session not ready, ignoring audio data")
                
                elif msg_type == 'text':
                    # 文本消息
                    text = data.get('text', '')
                    logger.info(f"Received text: {text}")
                
                elif msg_type == 'stop' or msg_type == 'session_end':
                    # 停止/结束信号
                    logger.info(f"Received {msg_type} signal from frontend")
                    self.is_running = False
                    if self.session:
                        self.session.is_running = False
                    
                    # 发送确认消息
                    try:
                        self.frontend_ws.send(json.dumps({
                            'type': f'{msg_type}_received',
                            'message': 'Server received'
                        }))
                    except:
                        pass
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
            
            # 如果是二进制数据（原始 PCM 音频）
            elif isinstance(data, bytes):
                if self.session:
                    # 直接添加原始音频数据
                    self.session.add_browser_audio_bytes(data)
                else:
                    logger.warning("Session not ready, ignoring audio data")
            
            else:
                logger.warning(f"Unknown data type: {type(data)}")
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up WebDialogHandler...")
        
        self.is_running = False
        
        # 停止会话
        if self.session:
            self.session.is_running = False
        
        # 等待异步线程结束
        if self.async_thread and self.async_thread.is_alive():
            self.async_thread.join(timeout=3.0)
        
        logger.info("WebDialogHandler cleanup complete")