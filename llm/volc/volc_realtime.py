import os
import json
import base64
import logging
import threading
import websocket
from typing import Optional
from uuid import uuid4

from llm.realtime_base import (
    RealtimeConfig, RealtimeCallback, RealtimeClient,
    ProviderType, VOLC_RESOURCE_ID, VOLC_APP_KEY, logger
)
from llm.volc.volc_protocol import VolcBinaryProtocol

VOLC_REALTIME_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"


class VolcRealtimeCallback(RealtimeCallback):
    def __init__(self):
        super().__init__()
    
    def on_open(self) -> None:
        logger.info("Volc: Connection opened")
        self._emit_status("connected", "已连接")
        
        if self._on_open_handler:
            self._on_open_handler()
    
    def on_close(self, close_status_code, close_msg) -> None:
        logger.info(f"Volc: Connection closed: code={close_status_code}, msg={close_msg}")
        self._emit_status("disconnected", f"连接关闭: {close_msg}")
        
        if self._on_close_handler:
            self._on_close_handler(close_status_code, close_msg)
    
    def on_event(self, response: dict) -> None:
        pass


class VolcRealtimeClient(RealtimeClient):
    def __init__(self, config: RealtimeConfig):
        super().__init__(config)
        self.callback = VolcRealtimeCallback()
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self._session_id: str = ""
        self._is_session_started: bool = False
        self._is_connection_started: bool = False
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
        payload = {
            "asr": {
                "audio_info": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "channel": 1
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
                "speaking_style": "friendly",
                "extra": {
                    "model": self.config.model,
                    "input_mod": "keep_alive"
                }
            }
        }
        return payload
    
    def _on_ws_open(self, ws):
        logger.info("Volc WebSocket connected")
        
        self._session_id = str(uuid4())
        self._connection_ready.clear()
        self._session_ready.clear()
        
        start_connection_frame = VolcBinaryProtocol.build_connect_frame(
            event_id=VolcBinaryProtocol.EVENT_START_CONNECTION,
            payload={}
        )
        ws.send(start_connection_frame, websocket.ABNF.OPCODE_BINARY)
        logger.info("Volc: Sent StartConnection")
        
        self.callback.on_open()
        self.is_connected = True
    
    def _on_ws_message(self, ws, message):
        try:
            if isinstance(message, bytes):
                parsed = VolcBinaryProtocol.parse_frame(message)
                logger.info(f"Volc received: type={parsed.get('type')}, event_id={parsed.get('event_id')}")
                
                if parsed['type'] == 'audio':
                    audio_data = parsed.get('audio', b'')
                    logger.info(f"Volc audio data size: {len(audio_data)} bytes")
                    if audio_data:
                        audio_b64 = base64.b64encode(audio_data).decode('ascii')
                        self.callback._emit_audio(audio_b64)
                
                elif parsed['type'] == 'event':
                    event_id = parsed.get('event_id', 0)
                    payload = parsed.get('payload', {})
                    logger.info(f"Volc event: id={event_id}, payload={payload}")
                    
                    if event_id == VolcBinaryProtocol.EVENT_CONNECTION_STARTED:
                        logger.info("Volc: Connection started")
                        self._is_connection_started = True
                        self._connection_ready.set()
                        self.callback._emit_status("connected", "连接已建立")
                        self._send_start_session()
                    
                    elif event_id == VolcBinaryProtocol.EVENT_CONNECTION_FAILED:
                        error_msg = payload.get('error', 'Connection failed')
                        logger.error(f"Volc: Connection failed: {error_msg}")
                        self.callback._emit_status("error", f"连接失败: {error_msg}")
                    
                    elif event_id == VolcBinaryProtocol.EVENT_SESSION_STARTED:
                        logger.info(f"Volc session started: {parsed.get('session_id', '')}")
                        self._is_session_started = True
                        self._session_ready.set()
                        self.callback._emit_status("session_created", "会话已创建")
                    
                    elif event_id == VolcBinaryProtocol.EVENT_SESSION_FINISHED:
                        logger.info("Volc: Session finished")
                        self._is_session_started = False
                        self.callback._emit_status("session_finished", "会话已结束")
                    
                    elif event_id == VolcBinaryProtocol.EVENT_SESSION_FAILED:
                        error_msg = payload.get('error', 'Session failed')
                        logger.error(f"Volc: Session failed: {error_msg}")
                        self.callback._emit_status("error", f"会话失败: {error_msg}")
                    
                    elif event_id == 350:
                        text = payload.get('text', '')
                        tts_type = payload.get('tts_type', '')
                        logger.info(f"Volc TTS start ({tts_type}): {text[:50] if text else ''}")
                        if text:
                            self.callback._emit_text(text, role="ai", is_final=False)
                    
                    elif event_id == 450:
                        logger.info("Volc: ASR detected speech")
                        self.callback._emit_status("speaking", "用户正在说话...")
                    
                    elif event_id == 451:
                        results = payload.get('results', [])
                        for result in results:
                            text = result.get('text', '')
                            is_interim = result.get('is_interim', False)
                            if text:
                                self.callback._emit_text(text, role="user", is_final=not is_interim)
                    
                    elif event_id == 459:
                        logger.info("Volc: ASR ended")
                        self.callback._emit_status("processing", "处理中...")
                    
                    elif event_id == 550:
                        text = payload.get('content', '')
                        if text:
                            self.callback._emit_text(text, role="ai", is_final=True)
                    
                    elif event_id == 559:
                        logger.info("Volc: Chat ended")
                        self.callback._emit_status("listening", "等待用户输入...")
                    
                    elif event_id == 599:
                        error_msg = payload.get('message', 'Unknown error')
                        status_code = payload.get('status_code', '')
                        logger.error(f"Volc dialog error [{status_code}]: {error_msg}")
                        self.callback._emit_status("error", error_msg)
                
                elif parsed['type'] == 'error':
                    error_msg = parsed.get('error', {})
                    if isinstance(error_msg, dict):
                        error_str = error_msg.get('error', str(error_msg))
                    else:
                        error_str = str(error_msg)
                    logger.error(f"Volc error: {error_str}")
                    self.callback._emit_status("error", error_str)
            
        except Exception as e:
            logger.error(f"Volc message processing error: {e}")
    
    def _on_ws_error(self, ws, error):
        logger.error(f"Volc WebSocket error: {error}")
        self.callback._emit_status("error", str(error))
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        logger.info(f"Volc WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self._is_session_started = False
        self.callback.on_close(close_status_code, close_msg)
    
    def _send_start_session(self):
        if not self.ws or not self._is_connection_started:
            logger.warning("Volc: Cannot start session - connection not ready")
            return
        
        start_session_payload = self._build_start_session_payload(self._instructions)
        start_session_frame = VolcBinaryProtocol.build_session_frame(
            event_id=VolcBinaryProtocol.EVENT_START_SESSION,
            session_id=self._session_id,
            payload=start_session_payload
        )
        self.ws.send(start_session_frame, websocket.ABNF.OPCODE_BINARY)
        logger.info(f"Volc: Sent StartSession with session_id: {self._session_id}")
    
    def connect(self, instructions: str = "", api_key: str = None):
        if api_key:
            self.set_api_key(api_key)
        elif not self.config.api_key:
            self.set_api_key()
        
        self._instructions = instructions or "你是一个友好的助手。"
        
        headers = self._get_headers()
        logger.info(f"Volc connecting with AppID: {self.config.volc_app_id}")
        
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
        
        import time
        timeout = 10
        
        if not self._connection_ready.wait(timeout):
            raise ConnectionError("Failed to start connection to Volc Realtime API")
        
        if not self._session_ready.wait(timeout):
            raise ConnectionError("Failed to start session with Volc Realtime API")
        
        if not self.is_connected:
            raise ConnectionError("Failed to connect to Volc Realtime API")
        
        logger.info("Connected to Volc Realtime")
    
    def send_audio(self, audio_data: bytes):
        if not self.is_connected or not self.ws:
            logger.warning("Volc: Not connected, cannot send audio")
            return
        
        if not self._is_session_started:
            logger.warning("Volc: Session not started, cannot send audio")
            return
        
        try:
            audio_frame = VolcBinaryProtocol.build_audio_frame(
                session_id=self._session_id,
                audio_data=audio_data
            )
            self.ws.send(audio_frame, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.error(f"Volc send audio error: {e}")
    
    def send_text(self, text: str):
        if not self.is_connected or not self.ws:
            logger.warning("Volc: Not connected, cannot send text")
            return
        
        if not self._is_session_started:
            logger.warning("Volc: Session not started, cannot send text")
            return
        
        try:
            text_frame = VolcBinaryProtocol.build_session_frame(
                event_id=501,
                session_id=self._session_id,
                payload={"content": text}
            )
            self.ws.send(text_frame, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.error(f"Volc send text error: {e}")
    
    def read_mic_audio(self) -> Optional[bytes]:
        return None
    
    def close(self):
        self.is_connected = False
        self._is_session_started = False
        self._is_connection_started = False
        self._connection_ready.clear()
        self._session_ready.clear()
        
        if self.ws:
            try:
                finish_session_frame = VolcBinaryProtocol.build_session_frame(
                    event_id=VolcBinaryProtocol.EVENT_FINISH_SESSION,
                    session_id=self._session_id,
                    payload={}
                )
                self.ws.send(finish_session_frame, websocket.ABNF.OPCODE_BINARY)
                logger.info("Volc: Sent FinishSession")
            except Exception:
                pass
            
            try:
                finish_connection_frame = VolcBinaryProtocol.build_connect_frame(
                    event_id=VolcBinaryProtocol.EVENT_FINISH_CONNECTION,
                    payload={}
                )
                self.ws.send(finish_connection_frame, websocket.ABNF.OPCODE_BINARY)
                logger.info("Volc: Sent FinishConnection")
            except Exception:
                pass
            
            try:
                self.ws.close()
            except Exception:
                pass
            finally:
                self.ws = None
        
        logger.info("Volc Disconnected")
