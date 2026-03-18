import os
import base64
import logging
import pyaudio
from typing import Optional

import dashscope
from dashscope.audio.qwen_omni import (
    OmniRealtimeConversation,
    OmniRealtimeCallback,
    MultiModality,
    AudioFormat
)

from llm.realtime_base import (
    RealtimeConfig, RealtimeCallback, RealtimeClient,
    ProviderType, logger
)

from llm.untils.audio_player import B64PCMPlayer

class QwenOmniCallback(OmniRealtimeCallback, RealtimeCallback):
    def __init__(self):
        OmniRealtimeCallback.__init__(self)
        RealtimeCallback.__init__(self)
        self.pya: Optional[pyaudio.PyAudio] = None
        self.mic_stream = None
        self.player: Optional[B64PCMPlayer] = None
        self.conversation = None
    
    def on_open(self) -> None:
        logger.info("Qwen: Connection opened, initializing audio devices")
        
        self.pya = pyaudio.PyAudio()
        
        self.mic_stream = self.pya.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=3200
        )
        
        self.player = B64PCMPlayer(self.pya, sample_rate=24000)
        self.player.start()
        
        self._emit_status("connected", "已连接")
        
        if self._on_open_handler:
            self._on_open_handler()
    
    def on_close(self, close_status_code, close_msg) -> None:
        logger.info(f"Qwen: Connection closed: code={close_status_code}, msg={close_msg}")
        
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
        
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
        try:
            event_type = response.get('type', '')
            
            if event_type == 'session.error':
                error_msg = response.get('session', {}).get('error', 'Unknown error')
                logger.error(f"Session error: {error_msg}")
                self._emit_status("error", error_msg)
            
            elif event_type == 'session.created':
                session_id = response.get('session', {}).get('id', '')
                logger.info(f"Session created: {session_id}")
                self._emit_status("session_created", f"会话已创建: {session_id}")
            
            elif event_type == 'session.updated':
                logger.info("Session updated")
                self._emit_status("ready", "会话已就绪")
            
            elif event_type == 'conversation.item.input_audio_transcription.completed':
                transcript = response.get('transcript', '')
                logger.info(f"User said: {transcript}")
                self._emit_text(transcript, role="user", is_final=True)
            
            elif event_type == 'response.audio_transcript.delta':
                pass
            
            elif event_type == 'response.audio_transcript.done':
                text = response.get('transcript', '')
                if text:
                    logger.info(f"AI response: {text}")
                    self._emit_text(text, role="ai", is_final=True)
            
            elif event_type == 'response.audio.delta':
                audio_b64 = response.get('delta', '')
                if audio_b64:
                    logger.info(f"Qwen audio delta, length: {len(audio_b64)}")
                    self._emit_audio(audio_b64)
            
            elif event_type == 'input_audio_buffer.speech_started':
                logger.info("VAD: Speech started")
                if self.player:
                    self.player.cancel()
                self._emit_status("speaking", "用户正在说话...")
            
            elif event_type == 'response.done':
                logger.info("Response done")
                self._emit_status("listening", "等待用户输入...")
            
        except Exception as e:
            logger.error(f"Event processing error: {e}")


class QwenOmniRealtime(RealtimeClient):
    def __init__(self, config: RealtimeConfig):
        super().__init__(config)
        self.callback = QwenOmniCallback()
        self.conversation: Optional[OmniRealtimeConversation] = None
    
    def set_api_key(self, api_key: str = None):
        if api_key:
            dashscope.api_key = api_key
            logger.info("API key set from parameter")
        elif 'DASHSCOPE_API_KEY' in os.environ:
            dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
            logger.info("API key loaded from environment variable")
        else:
            raise ValueError("API key not provided. Set DASHSCOPE_API_KEY in .env file or pass api_key parameter.")
    
    def connect(self, instructions: str = "", api_key: str = None):
        if api_key:
            self.set_api_key(api_key)
        elif not dashscope.api_key:
            self.set_api_key()
        
        self._instructions = instructions or "你是一个友好的助手。"
        
        self.conversation = OmniRealtimeConversation(
            model=self.config.model,
            callback=self.callback
        )
        
        self.callback.conversation = self.conversation
        
        self.conversation.connect()
        
        self.conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice=self.config.voice,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
            enable_input_audio_transcription=True,
            input_audio_transcription_model='gummy-realtime-v1',
            enable_turn_detection=True,
            turn_detection_type='server_vad',
            instructions=self._instructions
        )
        
        self.is_connected = True
        logger.info("Connected to Qwen Omni Realtime")
    
    def send_audio(self, audio_data: bytes):
        if not self.is_connected or not self.conversation:
            logger.warning("Not connected, cannot send audio")
            return
        
        try:
            audio_b64 = base64.b64encode(audio_data).decode('ascii')
            self.conversation.append_audio(audio_b64)
        except Exception as e:
            logger.error(f"Send audio error: {e}")
    
    def send_text(self, text: str):
        if not self.is_connected or not self.conversation:
            logger.warning("Not connected, cannot send text")
            return
        
        try:
            self.conversation.append_text(text)
        except Exception as e:
            logger.error(f"Send text error: {e}")
    
    def read_mic_audio(self) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if not self.callback.mic_stream:
            return None
        try:
            return self.callback.mic_stream.read(3200, exception_on_overflow=False)
        except OSError as e:
            if "Stream closed" in str(e) or e.errno == -9988:
                return None
            logger.error(f"Read mic error: {e}")
            return None
        except Exception as e:
            logger.error(f"Read mic error: {e}")
            return None
    
    def close(self):
        self.is_connected = False
        
        if self.callback.mic_stream:
            try:
                self.callback.mic_stream.stop_stream()
                self.callback.mic_stream.close()
            except Exception:
                pass
            finally:
                self.callback.mic_stream = None
        
        if self.callback.player:
            try:
                self.callback.player.shutdown()
            except Exception:
                pass
            finally:
                self.callback.player = None
        
        if self.callback.pya:
            try:
                self.callback.pya.terminate()
            except Exception:
                pass
            finally:
                self.callback.pya = None
        
        if self.conversation:
            try:
                self.conversation.close()
            except Exception as e:
                logger.error(f"Close error: {e}")
            finally:
                self.conversation = None
        
        logger.info("Disconnected")
