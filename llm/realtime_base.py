import os
import base64
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from dotenv import load_dotenv

_project_root = Path(__file__).parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderType(Enum):
    QWEN = "qwen"
    VOLC = "volc"


VOLC_RESOURCE_ID = "volc.speech.dialog"
VOLC_APP_KEY = "PlgvMymc7f3tQnJ6"


@dataclass
class RealtimeConfig:
    provider: ProviderType = ProviderType.QWEN
    
    api_key: str = ""
    model: str = ""
    voice: str = ""
    
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    
    volc_app_id: str = ""
    
    @classmethod
    def from_provider(cls, provider: ProviderType = ProviderType.QWEN) -> 'RealtimeConfig':
        config = cls(provider=provider)
        
        if provider == ProviderType.QWEN:
            config.api_key = os.getenv("DASHSCOPE_API_KEY", "")
            config.model = os.getenv("QWEN_MODEL", "qwen3-omni-flash-realtime")
            config.voice = os.getenv("QWEN_VOICE", "Bellona")
        elif provider == ProviderType.VOLC:
            config.api_key = os.getenv("VOLC_ACCESS_KEY", "")
            config.volc_app_id = os.getenv("VOLC_APP_ID", "")
            config.model = os.getenv("VOLC_MODEL", "O")
            config.voice = os.getenv("VOLC_VOICE", "vv")
        
        return config


class RealtimeCallback(ABC):
    def __init__(self):
        self._text_handlers: List[Callable] = []
        self._audio_handlers: List[Callable] = []
        self._status_handlers: List[Callable] = []
        self._on_open_handler: Optional[Callable] = None
        self._on_close_handler: Optional[Callable] = None
    
    def on_text(self, handler: Callable):
        self._text_handlers.append(handler)
        return handler
    
    def on_audio(self, handler: Callable):
        self._audio_handlers.append(handler)
        return handler
    
    def on_status(self, handler: Callable):
        self._status_handlers.append(handler)
        return handler
    
    def set_on_open(self, handler: Callable):
        self._on_open_handler = handler
    
    def set_on_close(self, handler: Callable):
        self._on_close_handler = handler
    
    def _emit_text(self, text: str, role: str = "ai", is_final: bool = False):
        for handler in self._text_handlers:
            try:
                handler(text, role, is_final)
            except Exception as e:
                logger.error(f"Text handler error: {e}")
    
    def _emit_audio(self, audio_b64: str):
        for handler in self._audio_handlers:
            try:
                handler(audio_b64)
            except Exception as e:
                logger.error(f"Audio handler error: {e}")
    
    def _emit_status(self, status: str, message: str = ""):
        for handler in self._status_handlers:
            try:
                handler(status, message)
            except Exception as e:
                logger.error(f"Status handler error: {e}")
    
    @abstractmethod
    def on_open(self) -> None:
        pass
    
    @abstractmethod
    def on_close(self, close_status_code, close_msg) -> None:
        pass
    
    @abstractmethod
    def on_event(self, response: dict) -> None:
        pass


class RealtimeClient(ABC):
    def __init__(self, config: RealtimeConfig):
        self.config = config
        self.callback: Optional[RealtimeCallback] = None
        self.is_connected = False
        self._instructions = ""
    
    @classmethod
    def create(cls, provider: str = "qwen", config: RealtimeConfig = None) -> RealtimeClient:
        provider_type = ProviderType(provider.lower())
        
        if config is None:
            config = RealtimeConfig.from_provider(provider_type)
        
        if provider_type == ProviderType.QWEN:
            from llm.qwen.qwen_omni import QwenOmniRealtime
            return QwenOmniRealtime(config)
        elif provider_type == ProviderType.VOLC:
            from llm.volc.volc_realtime import VolcRealtimeClient
            return VolcRealtimeClient(config)
            
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
    @abstractmethod
    def set_api_key(self, api_key: str = None):
        pass
    
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
    
    @abstractmethod
    def connect(self, instructions: str = "", api_key: str = None):
        pass
    
    @abstractmethod
    def send_audio(self, audio_data: bytes):
        pass
    
    @abstractmethod
    def send_text(self, text: str):
        pass
    
    @abstractmethod
    def read_mic_audio(self) -> Optional[bytes]:
        pass
    
    @abstractmethod
    def close(self):
        pass



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
        
        
        self.client = RealtimeClient.create(self.provider, self.config)
        
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
