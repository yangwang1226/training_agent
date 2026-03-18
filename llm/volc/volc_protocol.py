import gzip
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CLIENT_FULL_REQUEST = 0x01
CLIENT_AUDIO_ONLY_REQUEST = 0x02
SERVER_FULL_RESPONSE = 0x09
SERVER_ACK = 0x0B
SERVER_ERROR = 0x0F

NO_SERIALIZATION = 0x00
JSON_SERIALIZATION = 0x01

NO_COMPRESSION = 0x00
GZIP_COMPRESSION = 0x01

EVENT_START_CONNECTION = 1
EVENT_FINISH_CONNECTION = 2
EVENT_START_SESSION = 100
EVENT_FINISH_SESSION = 102
EVENT_TASK_REQUEST = 200

EVENT_CONNECTION_STARTED = 50
EVENT_CONNECTION_FAILED = 51
EVENT_CONNECTION_FINISHED = 52
EVENT_SESSION_STARTED = 150
EVENT_SESSION_FINISHED = 152
EVENT_SESSION_FAILED = 153


def generate_header(message_type: int = CLIENT_FULL_REQUEST, serial_method: int = JSON_SERIALIZATION,
                    compression: int = GZIP_COMPRESSION) -> bytes:
    byte0 = (0x01 << 4) | 0x01
    byte1 = (message_type << 4) | 0x04
    byte2 = (serial_method << 4) | compression
    byte3 = 0x00
    return bytes([byte0, byte1, byte2, byte3])


def build_connect_frame(event_id: int, payload: dict) -> bytes:
    header = generate_header()
    
    event_bytes = event_id.to_bytes(4, 'big')
    
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    payload_bytes = gzip.compress(payload_bytes)
    payload_size = len(payload_bytes).to_bytes(4, 'big')
    
    return header + event_bytes + payload_size + payload_bytes


def build_session_frame(event_id: int, session_id: str, payload: dict) -> bytes:
    header = generate_header()
    
    event_bytes = event_id.to_bytes(4, 'big')
    
    session_id_bytes = session_id.encode('utf-8')
    session_id_size = len(session_id_bytes).to_bytes(4, 'big')
    
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    payload_bytes = gzip.compress(payload_bytes)
    payload_size = len(payload_bytes).to_bytes(4, 'big')
    
    return header + event_bytes + session_id_size + session_id_bytes + payload_size + payload_bytes


def build_audio_frame(session_id: str, audio_data: bytes) -> bytes:
    header = generate_header(
        message_type=CLIENT_AUDIO_ONLY_REQUEST,
        serial_method=NO_SERIALIZATION,
        compression=GZIP_COMPRESSION
    )
    
    event_bytes = EVENT_TASK_REQUEST.to_bytes(4, 'big')
    
    session_id_bytes = session_id.encode('utf-8')
    session_id_size = len(session_id_bytes).to_bytes(4, 'big')
    
    payload_bytes = gzip.compress(audio_data)
    payload_size = len(payload_bytes).to_bytes(4, 'big')
    
    return header + event_bytes + session_id_size + session_id_bytes + payload_size + payload_bytes


def parse_response(data: bytes) -> Dict[str, Any]:
    if len(data) < 4:
        return {'type': 'error', 'error': {'message': 'Invalid frame: too short'}}
    
    byte0 = data[0]
    byte1 = data[1]
    byte2 = data[2]
    
    header_size = (byte0 & 0x0F) * 4
    message_type = (byte1 >> 4) & 0x0F
    message_type_flags = byte1 & 0x0F
    serialization = (byte2 >> 4) & 0x0F
    compression = byte2 & 0x0F
    
    offset = header_size
    
    if message_type == SERVER_ERROR:
        error_code = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        payload_size = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        error_data = data[offset:offset+payload_size]
        
        if compression == GZIP_COMPRESSION:
            try:
                error_data = gzip.decompress(error_data)
            except Exception:
                pass
        
        try:
            error_msg = json.loads(error_data.decode('utf-8'))
        except Exception:
            error_msg = {'error': error_data.decode('utf-8', errors='ignore')}
        
        return {
            'type': 'error',
            'error_code': error_code,
            'error': error_msg
        }
    
    if message_type_flags & 0x04:
        event_id = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        
        if event_id in [EVENT_CONNECTION_STARTED, EVENT_CONNECTION_FAILED, EVENT_CONNECTION_FINISHED]:
            payload_size = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            payload_data = data[offset:offset+payload_size]
            
            if compression == GZIP_COMPRESSION:
                try:
                    payload_data = gzip.decompress(payload_data)
                except Exception:
                    pass
            
            if serialization == JSON_SERIALIZATION:
                try:
                    payload = json.loads(payload_data.decode('utf-8'))
                except Exception:
                    payload = {'raw': payload_data.hex()}
            else:
                payload = {'raw': payload_data.hex()}
            
            return {
                'type': 'event',
                'event_id': event_id,
                'payload': payload
            }
        else:
            session_id_size = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            session_id = data[offset:offset+session_id_size].decode('utf-8')
            offset += session_id_size
            
            payload_size = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            payload_data = data[offset:offset+payload_size]
            
            if compression == GZIP_COMPRESSION:
                try:
                    payload_data = gzip.decompress(payload_data)
                except Exception:
                    pass
            
            if serialization == JSON_SERIALIZATION:
                try:
                    payload = json.loads(payload_data.decode('utf-8'))
                except Exception:
                    payload = {'raw': payload_data.hex()}
            else:
                payload = {'raw': payload_data.hex()}
            
            return {
                'type': 'event',
                'event_id': event_id,
                'session_id': session_id,
                'payload': payload
            }
    
    elif message_type == SERVER_ACK:
        if message_type_flags & 0x01:
            sequence = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
        else:
            sequence = 0
        
        session_id_size = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        session_id = data[offset:offset+session_id_size].decode('utf-8')
        offset += session_id_size
        
        payload_size = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        audio_data = data[offset:offset+payload_size]
        
        if compression == GZIP_COMPRESSION:
            try:
                audio_data = gzip.decompress(audio_data)
            except Exception:
                pass
        
        return {
            'type': 'audio',
            'session_id': session_id,
            'sequence': sequence,
            'audio': audio_data
        }
    
    return {'type': 'unknown', 'raw': data.hex()}


class VolcBinaryProtocol:
    EVENT_START_CONNECTION = EVENT_START_CONNECTION
    EVENT_FINISH_CONNECTION = EVENT_FINISH_CONNECTION
    EVENT_START_SESSION = EVENT_START_SESSION
    EVENT_FINISH_SESSION = EVENT_FINISH_SESSION
    
    EVENT_CONNECTION_STARTED = EVENT_CONNECTION_STARTED
    EVENT_CONNECTION_FAILED = EVENT_CONNECTION_FAILED
    EVENT_SESSION_STARTED = EVENT_SESSION_STARTED
    EVENT_SESSION_FINISHED = EVENT_SESSION_FINISHED
    EVENT_SESSION_FAILED = EVENT_SESSION_FAILED
    
    @classmethod
    def build_connect_frame(cls, event_id: int, payload: dict) -> bytes:
        return build_connect_frame(event_id, payload)
    
    @classmethod
    def build_session_frame(cls, event_id: int, session_id: str, payload: dict) -> bytes:
        return build_session_frame(event_id, session_id, payload)
    
    @classmethod
    def build_audio_frame(cls, session_id: str, audio_data: bytes) -> bytes:
        return build_audio_frame(session_id, audio_data)
    
    @classmethod
    def parse_frame(cls, data: bytes) -> Dict[str, Any]:
        return parse_response(data)
