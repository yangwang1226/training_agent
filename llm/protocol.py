import gzip
import json
from typing import Dict, Any

CLIENT_FULL_REQUEST = 0x01
CLIENT_AUDIO_ONLY_REQUEST = 0x02
SERVER_FULL_RESPONSE = 0x09
SERVER_ACK = 0x0B
SERVER_ERROR = 0x0F

NO_SERIALIZATION = 0x00
JSON_SERIALIZATION = 0x01

NO_COMPRESSION = 0x00
GZIP_COMPRESSION = 0x01


def generate_header(message_type: int = CLIENT_FULL_REQUEST, serial_method: int = JSON_SERIALIZATION,
                    compression: int = GZIP_COMPRESSION) -> bytes:
    byte0 = (0x01 << 4) | 0x01
    byte1 = (message_type << 4) | 0x04
    byte2 = (serial_method << 4) | compression
    byte3 = 0x00
    return bytes([byte0, byte1, byte2, byte3])


def parse_response(data: bytes) -> Dict[str, Any]:
    if len(data) < 4:
        return {}
    
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
            'message_type': 'SERVER_ERROR',
            'error_code': error_code,
            'payload_msg': error_msg
        }
    
    if message_type_flags & 0x04:
        event = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        
        if event in [50, 51, 52]:
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
                    payload_msg = json.loads(payload_data.decode('utf-8'))
                except Exception:
                    payload_msg = {}
            else:
                payload_msg = payload_data
            
            return {
                'message_type': 'SERVER_FULL_RESPONSE',
                'event': event,
                'payload_msg': payload_msg
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
                    payload_msg = json.loads(payload_data.decode('utf-8'))
                except Exception:
                    payload_msg = {}
            else:
                payload_msg = payload_data
            
            return {
                'message_type': 'SERVER_FULL_RESPONSE',
                'event': event,
                'session_id': session_id,
                'payload_msg': payload_msg
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
            'message_type': 'SERVER_ACK',
            'session_id': session_id,
            'sequence': sequence,
            'payload_msg': audio_data
        }
    
    return {}
