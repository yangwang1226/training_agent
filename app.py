import sys
import os
import logging
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, session
from flask_sock import Sock
import uuid

from routes import scene_bp, prompt_bp, evaluate_bp, dimension_bp, progress_bp, realtime_bp
from routes.scene_create_routes import scene_create_bp
from routes.progress_routes import register_progress_websocket
from routes.realtime_routes import register_websocket

app = Flask(__name__, template_folder='front_end/templates', static_folder='front_end/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')


@app.before_request
def ensure_session_id():
    """为每个用户生成唯一的 session_id"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

sock = Sock(app)

EVALUATE_STATIC_DIR = Path(__file__).parent / "front_end" / "evaluate" / "static"


@app.route('/evaluate/static/<path:filename>')
def evaluate_static(filename):
    return send_from_directory(EVALUATE_STATIC_DIR, filename)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate/')
def evaluate_page():
    evaluate_template_path = Path(__file__).parent / "front_end" / "evaluate" / "templates" / "evaluate.html"
    with open(evaluate_template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/scene/create/')
def scene_create_page():
    scene_template_path = Path(__file__).parent / "front_end" / "scene" / "templates" / "create.html"
    with open(scene_template_path, 'r', encoding='utf-8') as f:
        return f.read()


SCENE_STATIC_DIR = Path(__file__).parent / "front_end" / "scene" / "static"


@app.route('/scene/static/<path:filename>')
def scene_static(filename):
    return send_from_directory(SCENE_STATIC_DIR, filename)


app.register_blueprint(scene_bp)
app.register_blueprint(scene_create_bp)
app.register_blueprint(prompt_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(dimension_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(realtime_bp)

register_progress_websocket(sock)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
