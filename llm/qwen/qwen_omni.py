import os
import base64
import logging
import pyaudio
from typing import Optional, Callable

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


class B64PCMPlayer:
    def __init__(self, pya: pyaudio.PyAudio, sample_rate: int = 24000):
        self.pya = pya
        self.sample_rate = sample_rate
        self.stream = None
        self.is_playing = False
        self.audio_queue = []
    
    def start(self):
        if not self.stream:
            self.stream = self.pya.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
        self.is_playing = True
    
    def add_data(self, audio_b64: str):
        try:
            audio_data = base64.b64decode(audio_b64)
            if self.stream and self.is_playing:
                self.stream.write(audio_data)
        except Exception as e:
            logger.error(f"Play audio error: {e}")
    
    def stop(self):
        self.is_playing = False
        if self.stream:
            self.stream.stop_stream()
    
    def cancel(self):
        self.audio_queue = []
        self.stop()
    
    def shutdown(self):
        self.stop()
        if self.stream:
            self.stream.close()
            self.stream = None


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


class RealtimeSession:
    def __init__(self, api_key: str = "", prompt_file: str = "", provider: str = "qwen"):
        from pathlib import Path
        self.config = RealtimeConfig.from_provider(ProviderType(provider.lower()))
        if api_key:
            self.config.api_key = api_key
        self.prompt_file = prompt_file
        self.provider = provider.lower()
        self.client: Optional[RealtimeClient] = None
        self.system_prompt: str = ""
        self.is_running: bool = False
        self._audio_buffer: list = []
        self._text_buffer: str = ""
    
    def load_prompt(self) -> str:
        from pathlib import Path
        prompt_path = Path(self.prompt_file)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_file}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
        
        logger.info(f"Loaded prompt from: {self.prompt_file}")
        return self.system_prompt
    
    def start(self):
        if self.is_running:
            return
        
        if not self.system_prompt:
            self.load_prompt()
        
        from llm.realtime_base import create_realtime_client
        self.client = create_realtime_client(self.provider, self.config)
        
        self.client.on_text(self._on_text)
        self.client.on_audio(self._on_audio)
        self.client.on_status(self._on_status)
        
        self.client.connect(instructions=self.system_prompt)
        self.is_running = True
    
    def _on_text(self, text: str, role: str, is_final: bool):
        if role == "user":
            self._text_buffer = f"[用户] {text}"
        else:
            self._text_buffer = f"[AI] {text}"
    
    def _on_audio(self, audio_b64: str):
        self._audio_buffer.append(audio_b64)
    
    def _on_status(self, status: str, message: str):
        logger.info(f"Status: {status} - {message}")
    
    def send_audio(self, audio_data: bytes):
        if self.client and self.is_running:
            self.client.send_audio(audio_data)
    
    def send_text(self, text: str):
        if self.client and self.is_running:
            self.client.send_text(text)
    
    def read_mic(self) -> Optional[bytes]:
        if self.client and self.is_running:
            return self.client.read_mic_audio()
        return None
    
    def stop(self):
        if self.client:
            self.client.close()
        self.is_running = False
    
    def get_text_buffer(self) -> str:
        return self._text_buffer
    
    def clear_text_buffer(self):
        self._text_buffer = ""
    
    def get_audio_buffer(self) -> list:
        return self._audio_buffer
    
    def clear_audio_buffer(self):
        self._audio_buffer = []
