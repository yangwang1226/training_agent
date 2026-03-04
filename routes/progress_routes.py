import json
import logging
from flask import Blueprint, session

logger = logging.getLogger(__name__)

progress_bp = Blueprint('progress', __name__, url_prefix='/api')

progress_connections = {}


def register_progress_websocket(sock):
    @sock.route('/api/progress/ws')
    def progress_ws(ws):
        session_id = session.get('session_id', 'default')
        progress_connections[session_id] = ws
        logger.info(f"Progress WebSocket connected for session: {session_id}")
        
        try:
            while True:
                data = ws.receive(timeout=300)
                if data is None:
                    break
        except Exception as e:
            logger.error(f"Progress WebSocket error: {e}")
        finally:
            if session_id in progress_connections:
                del progress_connections[session_id]
            logger.info(f"Progress WebSocket closed for session: {session_id}")


def send_progress(session_id, message, step):
    if session_id in progress_connections:
        try:
            ws = progress_connections[session_id]
            ws.send(json.dumps({
                'type': 'progress',
                'message': message,
                'step': step
            }))
        except Exception as e:
            logger.error(f"Send progress error: {e}")


def get_progress_connections():
    return progress_connections
