import gzip
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ===== 协议版本 =====
PROTOCOL_VERSION = 0b0001
DEFAULT_HEADER_SIZE = 0b0001

# ===== 消息类型 =====
CLIENT_FULL_REQUEST = 0x01
CLIENT_AUDIO_ONLY_REQUEST = 0x02
SERVER_FULL_RESPONSE = 0x09
SERVER_ACK = 0x0B
SERVER_ERROR = 0x0F

# ===== 消息类型标志 =====
NO_SEQUENCE = 0b0000
POS_SEQUENCE = 0b0001
NEG_SEQUENCE = 0b0010
MSG_WITH_EVENT = 0b0100

# ===== 序列化方法 =====
NO_SERIALIZATION = 0x00
JSON_SERIALIZATION = 0x01

# ===== 压缩方法 =====
NO_COMPRESSION = 0x00
GZIP_COMPRESSION = 0x01

# ===== 连接事件 =====
EVENT_START_CONNECTION = 1
EVENT_FINISH_CONNECTION = 2
EVENT_CONNECTION_STARTED = 50
EVENT_CONNECTION_FAILED = 51
EVENT_CONNECTION_FINISHED = 52

# ===== 会话事件 =====
EVENT_START_SESSION = 100
EVENT_FINISH_SESSION = 102
EVENT_SESSION_STARTED = 150
EVENT_SESSION_FINISHED = 152
EVENT_SESSION_FAILED = 153

# ===== 音频任务 =====
EVENT_TASK_REQUEST = 200

# ===== 问候事件 =====
EVENT_SAY_HELLO = 300

# ===== TTS事件 =====
EVENT_TTS_START = 350
EVENT_TTS_END = 359

# ===== ASR事件 =====
EVENT_ASR_SPEECH_STARTED = 450
EVENT_ASR_RESULT = 451
EVENT_ASR_ENDED = 459

# ===== 对话事件 =====
EVENT_CHAT_TTS_TEXT = 500
EVENT_CHAT_TEXT_QUERY = 501
EVENT_CHAT_RAG_TEXT = 502
EVENT_CHAT_TEXT_RESPONSE = 550
EVENT_CHAT_RESPONSE_END = 559
EVENT_DIALOG_ERROR = 599


def generate_header(
        version: int = PROTOCOL_VERSION,
        message_type: int = CLIENT_FULL_REQUEST,
        message_type_specific_flags: int = MSG_WITH_EVENT,
        serial_method: int = JSON_SERIALIZATION,
        compression: int = GZIP_COMPRESSION,
        reserved_data: int = 0x00,
        extension_header: bytes = b''
) -> bytes:
    """生成协议头 (4 bytes + 可选扩展)"""
    header = bytearray()
    header_size = int(len(extension_header) / 4) + 1
    header.append((version << 4) | header_size)
    header.append((message_type << 4) | message_type_specific_flags)
    header.append((serial_method << 4) | compression)
    header.append(reserved_data)
    header.extend(extension_header)
    return bytes(header)


def build_connect_frame(event_id: int, payload: dict = None) -> bytes:
    """构建连接帧 (StartConnection / FinishConnection)"""
    frame = bytearray(generate_header())
    frame.extend(event_id.to_bytes(4, 'big'))
    
    payload_bytes = json.dumps(payload or {}, ensure_ascii=False).encode('utf-8')
    payload_bytes = gzip.compress(payload_bytes)
    frame.extend(len(payload_bytes).to_bytes(4, 'big'))
    frame.extend(payload_bytes)
    
    return bytes(frame)


def build_session_frame(event_id: int, session_id: str, payload: dict = None) -> bytes:
    """构建会话帧 (所有带 session_id 的请求)"""
    frame = bytearray(generate_header())
    frame.extend(event_id.to_bytes(4, 'big'))
    
    session_id_bytes = session_id.encode('utf-8')
    frame.extend(len(session_id_bytes).to_bytes(4, 'big'))
    frame.extend(session_id_bytes)
    
    payload_bytes = json.dumps(payload or {}, ensure_ascii=False).encode('utf-8')
    payload_bytes = gzip.compress(payload_bytes)
    frame.extend(len(payload_bytes).to_bytes(4, 'big'))
    frame.extend(payload_bytes)
    
    return bytes(frame)


def build_audio_frame(session_id: str, audio_data: bytes) -> bytes:
    """构建音频帧 (TaskRequest)"""
    header = generate_header(
        message_type=CLIENT_AUDIO_ONLY_REQUEST,
        serial_method=NO_SERIALIZATION,
        compression=GZIP_COMPRESSION
    )
    
    frame = bytearray(header)
    frame.extend(EVENT_TASK_REQUEST.to_bytes(4, 'big'))
    
    session_id_bytes = session_id.encode('utf-8')
    frame.extend(len(session_id_bytes).to_bytes(4, 'big'))
    frame.extend(session_id_bytes)
    
    payload_bytes = gzip.compress(audio_data)
    frame.extend(len(payload_bytes).to_bytes(4, 'big'))
    frame.extend(payload_bytes)
    
    return bytes(frame)


def parse_response(response: bytes) -> Dict[str, Any]:
    """
    解析服务器响应帧，返回标准化字典。
    
    返回格式:
    {
        'message_type': 'SERVER_FULL_RESPONSE' | 'SERVER_ACK' | 'SERVER_ERROR_RESPONSE',
        'event': int (可选),
        'session_id': str (可选),
        'seq': int (可选),
        'payload_msg': dict | bytes | str,
        'payload_size': int,
        'code': int (仅错误响应)
    }
    """
    if isinstance(response, str) or len(response) < 4:
        return {}
    
    header_size = (response[0] & 0x0F) * 4
    message_type = (response[1] >> 4) & 0x0F
    message_type_flags = response[1] & 0x0F
    serialization = (response[2] >> 4) & 0x0F
    compression = response[2] & 0x0F
    
    payload = response[header_size:]
    result = {}
    offset = 0
    
    # ── SERVER_FULL_RESPONSE / SERVER_ACK ──
    if message_type in (SERVER_FULL_RESPONSE, SERVER_ACK):
        result['message_type'] = 'SERVER_ACK' if message_type == SERVER_ACK else 'SERVER_FULL_RESPONSE'
        
        # 可选：序列号
        if message_type_flags & NEG_SEQUENCE:
            result['seq'] = int.from_bytes(payload[offset:offset + 4], 'big', signed=False)
            offset += 4
        
        # 可选：事件ID
        if message_type_flags & MSG_WITH_EVENT:
            result['event'] = int.from_bytes(payload[offset:offset + 4], 'big', signed=False)
            offset += 4
        
        # session_id
        session_id_size = int.from_bytes(payload[offset:offset + 4], 'big', signed=True)
        offset += 4
        result['session_id'] = payload[offset:offset + session_id_size].decode('utf-8', errors='ignore')
        offset += session_id_size
        
        # payload
        payload_size = int.from_bytes(payload[offset:offset + 4], 'big', signed=False)
        offset += 4
        payload_data = payload[offset:offset + payload_size]
        
        if compression == GZIP_COMPRESSION:
            try:
                payload_data = gzip.decompress(payload_data)
            except Exception as e:
                logger.error(f"Decompress failed: {e}")
        
        if serialization == JSON_SERIALIZATION:
            try:
                result['payload_msg'] = json.loads(payload_data.decode('utf-8'))
            except Exception as e:
                logger.error(f"JSON parse failed: {e}")
                result['payload_msg'] = payload_data
        elif serialization == NO_SERIALIZATION:
            result['payload_msg'] = payload_data  # 原始二进制（音频）
        else:
            result['payload_msg'] = payload_data.decode('utf-8', errors='ignore')
        
        result['payload_size'] = payload_size
    
    # ── SERVER_ERROR ──
    elif message_type == SERVER_ERROR:
        result['message_type'] = 'SERVER_ERROR_RESPONSE'
        result['code'] = int.from_bytes(payload[0:4], 'big', signed=False)
        
        payload_size = int.from_bytes(payload[4:8], 'big', signed=False)
        payload_data = payload[8:8 + payload_size]
        
        if compression == GZIP_COMPRESSION:
            try:
                payload_data = gzip.decompress(payload_data)
            except Exception:
                pass
        
        try:
            result['payload_msg'] = json.loads(payload_data.decode('utf-8'))
        except Exception:
            result['payload_msg'] = payload_data.decode('utf-8', errors='ignore')
        
        result['payload_size'] = payload_size
    
    else:
        logger.warning(f"Unknown message_type: {message_type}")
        result['message_type'] = 'UNKNOWN'
    
    return result


class VolcBinaryProtocol:
    """火山引擎实时对话协议封装类，统一对外接口"""
    
    # 连接事件
    EVENT_START_CONNECTION = EVENT_START_CONNECTION
    EVENT_FINISH_CONNECTION = EVENT_FINISH_CONNECTION
    EVENT_CONNECTION_STARTED = EVENT_CONNECTION_STARTED
    EVENT_CONNECTION_FAILED = EVENT_CONNECTION_FAILED
    EVENT_CONNECTION_FINISHED = EVENT_CONNECTION_FINISHED
    
    # 会话事件
    EVENT_START_SESSION = EVENT_START_SESSION
    EVENT_FINISH_SESSION = EVENT_FINISH_SESSION
    EVENT_SESSION_STARTED = EVENT_SESSION_STARTED
    EVENT_SESSION_FINISHED = EVENT_SESSION_FINISHED
    EVENT_SESSION_FAILED = EVENT_SESSION_FAILED
    
    # 音频 / 问候
    EVENT_TASK_REQUEST = EVENT_TASK_REQUEST
    EVENT_SAY_HELLO = EVENT_SAY_HELLO
    
    # TTS
    EVENT_TTS_START = EVENT_TTS_START
    EVENT_TTS_END = EVENT_TTS_END
    
    # ASR
    EVENT_ASR_SPEECH_STARTED = EVENT_ASR_SPEECH_STARTED
    EVENT_ASR_RESULT = EVENT_ASR_RESULT
    EVENT_ASR_ENDED = EVENT_ASR_ENDED
    
    # 对话
    EVENT_CHAT_TTS_TEXT = EVENT_CHAT_TTS_TEXT
    EVENT_CHAT_TEXT_QUERY = EVENT_CHAT_TEXT_QUERY
    EVENT_CHAT_RAG_TEXT = EVENT_CHAT_RAG_TEXT
    EVENT_CHAT_TEXT_RESPONSE = EVENT_CHAT_TEXT_RESPONSE
    EVENT_CHAT_RESPONSE_END = EVENT_CHAT_RESPONSE_END
    EVENT_DIALOG_ERROR = EVENT_DIALOG_ERROR
    
    @classmethod
    def build_connect_frame(cls, event_id: int, payload: dict = None) -> bytes:
        return build_connect_frame(event_id, payload)
    
    @classmethod
    def build_session_frame(cls, event_id: int, session_id: str, payload: dict = None) -> bytes:
        return build_session_frame(event_id, session_id, payload)
    
    @classmethod
    def build_audio_frame(cls, session_id: str, audio_data: bytes) -> bytes:
        return build_audio_frame(session_id, audio_data)
    
    @classmethod
    def parse_frame(cls, data: bytes) -> Dict[str, Any]:
        return parse_response(data)
