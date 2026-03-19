"""火山引擎实时对话 - 符合 RealtimeCallback + RealtimeClient 模板"""
import os
import base64
import logging
import threading
import queue
import time
from typing import Optional
from uuid import uuid4

import pyaudio
import websocket

from llm.realtime_base import (
    RealtimeConfig, RealtimeCallback, RealtimeClient, logger
)
from llm.volc.volc_protocol import VolcBinaryProtocol

VOLC_REALTIME_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"

VOLC_RESOURCE_ID = "volc.speech.dialog"
VOLC_APP_KEY = "PlgvMymc7f3tQnJ6"

# ===== 音频设备管理（类似 Qwen 的实现）=====

class AudioPlayer:
    """线程安全的音频播放器，支持队列缓冲和打断清空"""

    def __init__(self, pya: pyaudio.PyAudio, sample_rate: int = 24000, channels: int = 1):
        self.pya = pya
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream: Optional[pyaudio.Stream] = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_playing = False
        self._player_thread: Optional[threading.Thread] = None
        self._instance_id = id(self)
        logger.info(f"🎵 AudioPlayer created: instance_id={self._instance_id}")

    def start(self):
        if not self.stream:
            try:
                self.stream = self.pya.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=3200
                )
                logger.info(f"🎧 Audio output stream opened: {self.sample_rate}Hz, {self.channels}ch")
            except Exception as e:
                logger.error(f"❌ Failed to open audio stream: {e}", exc_info=True)
                return
        self.is_playing = True
        self._player_thread = threading.Thread(target=self._play_loop, daemon=True)
        self._player_thread.start()

    def _play_loop(self):
        """独立线程播放音频，避免阻塞主逻辑"""
        logger.info(f"🔊 Audio player thread started [instance {self._instance_id}]")
        if not self.stream:
            logger.error(f"❌ Audio stream is None, cannot play! [instance {self._instance_id}]")
            return
        logger.info(f"✅ Stream is ready [instance {self._instance_id}]: active={self.stream.is_active()}")
        loop_count = 0
        while self.is_playing:
            loop_count += 1
            current_queue_size = self.audio_queue.qsize()
            if loop_count % 10 == 1:  # 每10次循环打印一次
                logger.info(f"🔄 Play loop iteration {loop_count} [instance {self._instance_id}], queue size: {current_queue_size}")
            
            try:
                audio_data = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error getting from queue: {e}", exc_info=True)
                time.sleep(0.1)
                continue
            
            # 处理获取到的音频数据
            try:
                logger.debug(f"🎯 Playing {len(audio_data)} bytes from queue")
                if audio_data and self.stream:
                    self.stream.write(audio_data)
                    logger.debug(f"✅ Played {len(audio_data)} bytes successfully")
                else:
                    logger.warning(f"⚠️ Skipped playback: audio_data={len(audio_data) if audio_data else 'empty'}, stream={'exists' if self.stream else 'None'}")
            except Exception as e:
                logger.error(f"❌ Audio play error: {e}", exc_info=True)
                # 检查stream是否还有效
                if self.stream:
                    logger.error(f"Stream state: active={self.stream.is_active()}, stopped={self.stream.is_stopped()}")
                time.sleep(0.1)
        logger.info("🔇 Audio player thread stopped")

    def add_audio_bytes(self, audio_data: bytes):
        """接收原始 bytes 音频（Volc 协议直接产出 bytes）"""
        if audio_data:
            # 验证音频数据大小（PCM Int16 应该是偶数字节）
            if len(audio_data) % 2 != 0:
                logger.warning(f"⚠️ Odd audio data size: {len(audio_data)} bytes")
            
            self.audio_queue.put(audio_data, block=False)  # 使用非阻塞put
            logger.debug(f"🎵 Audio queued [instance {self._instance_id}]: {len(audio_data)} bytes, queue size: {self.audio_queue.qsize()}")

    def cancel(self):
        """用户打断时清空所有缓冲音频"""
        cleared_count = 0
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                cleared_count += 1
            except queue.Empty:
                break
        logger.info(f"🗑️ Audio buffer cleared: {cleared_count} chunks removed")

    def stop(self):
        self.is_playing = False
        if self._player_thread:
            self._player_thread.join(timeout=2)
            self._player_thread = None
        if self.stream:
            try:
                self.stream.stop_stream()
            except Exception:
                pass

    def shutdown(self):
        self.stop()
        self.cancel()
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = None


class MicRecorder:
    """麦克风录音器"""

    def __init__(self, pya: pyaudio.PyAudio, sample_rate: int = 16000, channels: int = 1):
        self.pya = pya
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream: Optional[pyaudio.Stream] = None

    def start(self):
        self.stream = self.pya.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=3200
        )

    def read(self) -> Optional[bytes]:
        if not self.stream:
            return None
        try:
            return self.stream.read(3200, exception_on_overflow=False)
        except OSError as e:
            if "Stream closed" in str(e) or e.errno == -9988:
                return None
            logger.error(f"Mic read error: {e}")
            return None
        except Exception as e:
            logger.error(f"Mic read error: {e}")
            return None

    def stop(self):
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None


# ===== 火山回调 - 管理音频设备生命周期 =====

class VolcRealtimeCallback(RealtimeCallback):
    """火山回调 - 与 QwenOmniCallback 对称，管理音频设备"""

    def __init__(self):
        super().__init__()
        self.pya: Optional[pyaudio.PyAudio] = None
        self.mic: Optional[MicRecorder] = None
        self.player: Optional[AudioPlayer] = None

    def on_open(self) -> None:
        logger.info("Volc: Connection opened, initializing audio devices")

        self.pya = pyaudio.PyAudio()

        self.mic = MicRecorder(self.pya, sample_rate=16000)
        self.mic.start()

        self.player = AudioPlayer(self.pya, sample_rate=24000)
        self.player.start()

        self._emit_status("connected", "已连接")

        if self._on_open_handler:
            self._on_open_handler()

    def on_close(self, close_status_code, close_msg) -> None:
        logger.info(f"Volc: Connection closed: code={close_status_code}, msg={close_msg}")

        if self.mic:
            self.mic.stop()
            self.mic = None

        if self.player:
            self.player.shutdown()
            self.player = None

        if self.pya:
            self.pya.terminate()
            self.pya = None

        self._emit_status("disconnected", f"连接关闭: {close_msg}")

        if self._on_close_handler:
            self._on_close_handler(close_status_code, close_msg)

    def on_event(self, response: dict) -> None:
        """处理已解析的协议事件（实际分发在 VolcRealtimeClient 中）"""
        pass


# ===== 火山客户端 - 实现完整的实时对话功能 =====

class VolcRealtimeClient(RealtimeClient):
    def __init__(self, config: RealtimeConfig):
        super().__init__(config)
        self.callback = VolcRealtimeCallback()
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self._session_id: str = ""
        self._is_session_started: bool = False
        self._is_connection_started: bool = False
        self._is_user_querying: bool = False  # 用户是否正在说话（用于打断判断）
        self._connection_ready = threading.Event()
        self._session_ready = threading.Event()

    def set_api_key(self, api_key: str = None):
        if api_key:
            self.config.api_key = api_key
            logger.info("Volc API key set from parameter")
        elif self.config.api_key:
            logger.info("Volc API key loaded from config")
        else:
            raise ValueError("API key not provided. Set VOLC_ACCESS_KEY in .env file or pass api_key parameter.")

    def _get_headers(self) -> dict:
        return {
            "X-Api-App-ID": self.config.volc_app_id,
            "X-Api-Access-Key": self.config.api_key,
            "X-Api-Resource-Id": VOLC_RESOURCE_ID,
            "X-Api-App-Key": VOLC_APP_KEY,
            "X-Api-Connect-Id": str(uuid4()),
        }

    def _build_start_session_payload(self, instructions: str) -> dict:
        """构建 StartSession 请求体（对齐示例代码配置）"""
        return {
            "asr": {
                "audio_info": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "channel": 1
                },
                "extra": {
                    "end_smooth_window_ms": 1500,  # 示例代码中的 ASR 配置
                }
            },
            "tts": {
                "speaker": self.config.voice,
                "audio_config": {
                    "channel": 1,
                    "format": "pcm",
                    "sample_rate": 24000
                }
            },
            "dialog": {
                "bot_name": "智能助手",
                "system_role": instructions,
                "extra": {
                    "strict_audit": False,
                    "model": self.config.model,
                    "input_mod": "audio",      # audio / audio_file / text
                    "recv_timeout": 120,       # 允许较长静默时间
                }
            }
        }

    # ─── WebSocket 回调 ───────────────────────────────────────────

    def _on_ws_open(self, ws):
        logger.info("🌐 Volc WebSocket connected")

        self._session_id = str(uuid4())
        self._connection_ready.clear()
        self._session_ready.clear()

        start_frame = VolcBinaryProtocol.build_connect_frame(
            event_id=VolcBinaryProtocol.EVENT_START_CONNECTION,
            payload={}
        )
        ws.send(start_frame, websocket.ABNF.OPCODE_BINARY)
        logger.info("📤 Volc: Sent StartConnection")

        self.callback.on_open()
        self.is_connected = True

    def _on_ws_message(self, ws, message):
        try:
            if not isinstance(message, bytes):
                return

            parsed = VolcBinaryProtocol.parse_frame(message)
            msg_type = parsed.get('message_type')
            event_id = parsed.get('event', 0)
            payload = parsed.get('payload_msg', {})

            logger.debug(f"Volc recv: type={msg_type}, event={event_id}")

                        # ── 音频数据（SERVER_ACK，无序列化）──
            if msg_type == 'SERVER_ACK' and isinstance(payload, bytes):
                logger.info(f"📢 Received audio: {len(payload)} bytes, is_querying={self._is_user_querying}")
                if payload and not self._is_user_querying:
                    # 直接送入播放器
                    if self.callback.player:
                        self.callback.player.add_audio_bytes(payload)
                        logger.info(f"✅ Audio added to queue, queue size: {self.callback.player.audio_queue.qsize()}")
                    else:
                        logger.warning("⚠️ Player not available")
                    # 同时通知外部（base64 格式，与 Qwen 保持一致）
                    audio_b64 = base64.b64encode(payload).decode('ascii')
                    self.callback._emit_audio(audio_b64)
                elif self._is_user_querying:
                    logger.debug(f"🚫 Audio dropped (user is speaking)")
                return

            # ── 事件消息（SERVER_FULL_RESPONSE）──
            if msg_type == 'SERVER_FULL_RESPONSE' and event_id:

                # ═══ 连接/会话生命周期 ═══
                if event_id == VolcBinaryProtocol.EVENT_CONNECTION_STARTED:
                    logger.info("🔗 Volc: Connection started")
                    self._is_connection_started = True
                    self._connection_ready.set()
                    self._send_start_session()

                elif event_id == VolcBinaryProtocol.EVENT_CONNECTION_FAILED:
                    logger.error(f"Volc: Connection failed: {payload}")
                    self.callback._emit_status("error", str(payload))

                elif event_id == VolcBinaryProtocol.EVENT_SESSION_STARTED:
                    logger.info("✨ Volc: Session started")
                    self._is_session_started = True
                    self._session_ready.set()
                    self.callback._emit_status("session_created", "会话已创建")

                elif event_id in (VolcBinaryProtocol.EVENT_SESSION_FINISHED,
                                  VolcBinaryProtocol.EVENT_SESSION_FAILED):
                    logger.info(f"Volc: Session ended, event={event_id}")
                    self._is_session_started = False
                    self.callback._emit_status("session_finished", "会话已结束")

                # ═══ TTS 事件 ═══
                elif event_id == VolcBinaryProtocol.EVENT_TTS_START:  # 350
                    text = payload.get('text', '')
                    tts_type = payload.get('tts_type', '')
                    logger.info(f"🗣️ Volc TTS start ({tts_type}): {text[:50]}...")
                    self._is_user_querying = False  # AI开始说话，用户不再查询状态
                    if text:
                        self.callback._emit_text(text, role="ai", is_final=False)

                elif event_id == VolcBinaryProtocol.EVENT_TTS_END:  # 359
                    logger.info("✅ Volc: TTS ended")
                    self.callback._emit_status("listening", "等待用户输入...")

                # ═══ ASR 事件 ═══
                elif event_id == VolcBinaryProtocol.EVENT_ASR_SPEECH_STARTED:  # 450
                    logger.info("🎤 Volc: VAD speech started - interrupting playback")
                    self._is_user_querying = True
                    # 🔴 关键：用户打断时清空播放缓冲
                    if self.callback.player:
                        queue_size_before = self.callback.player.audio_queue.qsize()
                        self.callback.player.cancel()
                        logger.info(f"🗑️ Cleared {queue_size_before} audio chunks from buffer")
                    self.callback._emit_status("speaking", "用户正在说话...")

                elif event_id == VolcBinaryProtocol.EVENT_ASR_RESULT:  # 451
                    results = payload.get('results', [])
                    for result in results:
                        text = result.get('text', '')
                        is_interim = result.get('is_interim', False)
                        if text:
                            status = "(interim)" if is_interim else "(final)"
                            logger.info(f"💬 User said {status}: {text}")
                            self.callback._emit_text(
                                text, role="user", is_final=not is_interim
                            )

                elif event_id == VolcBinaryProtocol.EVENT_ASR_ENDED:  # 459
                    logger.info("🛑 Volc: ASR ended (user stopped speaking)")
                    self._is_user_querying = False
                    self.callback._emit_status("processing", "处理中...")

                # ═══ LLM 对话 ═══
                elif event_id == VolcBinaryProtocol.EVENT_CHAT_TEXT_RESPONSE:  # 550
                    text = payload.get('content', '')
                    if text:
                        self.callback._emit_text(text, role="ai", is_final=True)

                elif event_id == VolcBinaryProtocol.EVENT_CHAT_RESPONSE_END:  # 559
                    logger.info("Volc: Chat ended")
                    self.callback._emit_status("listening", "等待用户输入...")

                elif event_id == VolcBinaryProtocol.EVENT_DIALOG_ERROR:  # 599
                    error_msg = payload.get('message', 'Unknown error')
                    status_code = payload.get('status_code', '')
                    logger.error(f"Volc dialog error [{status_code}]: {error_msg}")
                    self.callback._emit_status("error", error_msg)

            # ── 错误响应 ──
            elif msg_type == 'SERVER_ERROR_RESPONSE':
                logger.error(f"Volc protocol error: {parsed}")
                self.callback._emit_status("error", str(payload))

        except Exception as e:
            logger.error(f"Volc message processing error: {e}", exc_info=True)

    def _on_ws_error(self, ws, error):
        logger.error(f"Volc WebSocket error: {error}")
        self.callback._emit_status("error", str(error))

    def _on_ws_close(self, ws, close_status_code, close_msg):
        logger.info(f"Volc WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self._is_session_started = False
        self._is_user_querying = False
        self.callback.on_close(close_status_code, close_msg)

    # ─── 会话控制 ─────────────────────────────────────────────────

    def _send_start_session(self):
        if not self.ws or not self._is_connection_started:
            return

        payload = self._build_start_session_payload(self._instructions)
        frame = VolcBinaryProtocol.build_session_frame(
            event_id=VolcBinaryProtocol.EVENT_START_SESSION,
            session_id=self._session_id,
            payload=payload
        )
        self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
        logger.info(f"Volc: Sent StartSession, session_id={self._session_id}")

    def say_hello(self, content: str = "你好，有什么可以帮助你的？"):
        """发送 SayHello (event 300) - 示例代码中的功能"""
        if not self._is_session_started or not self.ws:
            return
        try:
            frame = VolcBinaryProtocol.build_session_frame(
                event_id=VolcBinaryProtocol.EVENT_SAY_HELLO,
                session_id=self._session_id,
                payload={"content": content}
            )
            self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
            logger.info(f"Volc: Sent SayHello: {content}")
        except Exception as e:
            logger.error(f"Volc say_hello error: {e}")

    # ─── RealtimeClient 抽象方法实现 ─────────────────────────────

    def connect(self, instructions: str = "", api_key: str = None):
        if api_key:
            self.set_api_key(api_key)
        elif not self.config.api_key:
            self.set_api_key()

        self._instructions = instructions or "你是一个友好的助手。"

        headers = self._get_headers()
        logger.info(f"Volc connecting, AppID={self.config.volc_app_id}")

        self.ws = websocket.WebSocketApp(
            VOLC_REALTIME_URL,
            header=headers,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

        timeout = 10
        if not self._connection_ready.wait(timeout):
            raise ConnectionError("Volc: Connection start timeout")
        if not self._session_ready.wait(timeout):
            raise ConnectionError("Volc: Session start timeout")

        logger.info("Connected to Volc Realtime")

    def send_audio(self, audio_data: bytes):
        if not self.is_connected or not self.ws or not self._is_session_started:
            return
        try:
            frame = VolcBinaryProtocol.build_audio_frame(
                session_id=self._session_id,
                audio_data=audio_data
            )
            self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.error(f"Volc send_audio error: {e}")

    def send_text(self, text: str):
        """ChatTextQuery (event 501)"""
        if not self.is_connected or not self.ws or not self._is_session_started:
            return
        try:
            frame = VolcBinaryProtocol.build_session_frame(
                event_id=VolcBinaryProtocol.EVENT_CHAT_TEXT_QUERY,
                session_id=self._session_id,
                payload={"content": text}
            )
            self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.error(f"Volc send_text error: {e}")

    def read_mic_audio(self) -> Optional[bytes]:
        """从麦克风读取音频（与 Qwen 对称，不再返回 None）"""
        if not self.is_connected or not self.callback.mic:
            return None
        return self.callback.mic.read()

    def close(self):
        self.is_connected = False
        self._is_session_started = False
        self._is_connection_started = False
        self._is_user_querying = False
        self._connection_ready.clear()
        self._session_ready.clear()

        # 1. 关闭音频设备
        if self.callback.mic:
            self.callback.mic.stop()
            self.callback.mic = None

        if self.callback.player:
            self.callback.player.shutdown()
            self.callback.player = None

        if self.callback.pya:
            self.callback.pya.terminate()
            self.callback.pya = None

        # 2. 优雅关闭协议
        if self.ws:
            try:
                frame = VolcBinaryProtocol.build_session_frame(
                    event_id=VolcBinaryProtocol.EVENT_FINISH_SESSION,
                    session_id=self._session_id,
                    payload={}
                )
                self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
            except Exception:
                pass

            try:
                frame = VolcBinaryProtocol.build_connect_frame(
                    event_id=VolcBinaryProtocol.EVENT_FINISH_CONNECTION,
                    payload={}
                )
                self.ws.send(frame, websocket.ABNF.OPCODE_BINARY)
            except Exception:
                pass

            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

        logger.info("Volc Disconnected")