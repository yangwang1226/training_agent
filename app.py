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

from flask import Flask, render_template, send_from_directory, session, redirect
from flask_sock import Sock
import uuid

from routes import scene_bp, prompt_bp, progress_bp, realtime_bp
from routes.scene.scene_agent_routes import scene_create_bp
from routes.scene.preset_scene_routes import preset_scene_bp
from routes.sop.sop_routes import sop_bp
from routes.sop.sop_routes_extension import sop_extraction_bp
from routes.assessment_view_routes import assessment_view_bp
from routes.manage_routes import manage_bp
from routes.scene.custom_scene_routes import custom_scene_bp
from routes.scene.scene_prompt_routes import scene_prompt_bp
from routes.progress_routes import register_progress_websocket
from routes.realtime_routes import register_websocket

app = Flask(__name__, template_folder='front_end/templates', static_folder='front_end/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON 输出


@app.before_request
def ensure_session_id():
    """为每个用户生成唯一的 session_id"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

sock = Sock(app)

EVALUATE_STATIC_DIR = Path(__file__).parent / "front_end" / "evaluate" / "static"
SOP_STATIC_DIR = Path(__file__).parent / "front_end" / "sop" / "static"


@app.route('/evaluate/static/<path:filename>')
def evaluate_static(filename):
    return send_from_directory(EVALUATE_STATIC_DIR, filename)


@app.route('/sop/static/<path:filename>')
def sop_static(filename):
    return send_from_directory(SOP_STATIC_DIR, filename)


@app.route('/')
def index():
    """
    首页 - 重定向到后台管理系统
    """
    return redirect('/manage_system/')


@app.route('/sop/config')
def sop_config_page():
    """SOP 质检清单配置页面"""
    from flask import render_template_string
    sop_template_path = Path(__file__).parent / "front_end" / "sop" / "templates" / "sop_config.html"
    with open(sop_template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    return render_template_string(template_content)

# 评估页面已迁移到 assessment_view_bp Blueprint
# @app.route('/evaluate/')
# def evaluate_page():
#     evaluate_template_path = Path(__file__).parent / "front_end" / "evaluate" / "templates" / "evaluate.html"
#     with open(evaluate_template_path, 'r', encoding='utf-8') as f:
#         return f.read()


@app.route('/scene/create/')
def scene_create_page():
    scene_template_path = Path(__file__).parent / "front_end" / "scene" / "templates" / "create.html"
    with open(scene_template_path, 'r', encoding='utf-8') as f:
        return f.read()


INDUSTRY_TEMPLATE_DIR = Path(__file__).parent / "front_end" / "industry" / "templates"
INDUSTRY_STATIC_DIR = Path(__file__).parent / "front_end" / "industry" / "static"


@app.route('/industry/')
def industry_page():
    """行业选择页面"""
    industry_template_path = INDUSTRY_TEMPLATE_DIR / "index.html"
    with open(industry_template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/industry/scene-config')
def scene_config_page():
    """场景配置页面"""
    scene_config_template_path = INDUSTRY_TEMPLATE_DIR / "scene_config.html"
    with open(scene_config_template_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/industry/static/<path:filename>')
def industry_static(filename):
    return send_from_directory(INDUSTRY_STATIC_DIR, filename)


SCENE_STATIC_DIR = Path(__file__).parent / "front_end" / "scene" / "static"


@app.route('/scene/static/<path:filename>')
def scene_static(filename):
    return send_from_directory(SCENE_STATIC_DIR, filename)


app.register_blueprint(scene_bp)
app.register_blueprint(scene_create_bp)
app.register_blueprint(preset_scene_bp)
app.register_blueprint(prompt_bp)
# app.register_blueprint(evaluate_bp)
app.register_blueprint(assessment_view_bp)  # 新的评估查看页面
app.register_blueprint(manage_bp)  # 后台管理系统
app.register_blueprint(custom_scene_bp)  # 自定义场景创建
app.register_blueprint(scene_prompt_bp)  # 场景提示词生成
# app.register_blueprint(dimension_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(realtime_bp)
app.register_blueprint(sop_bp)
app.register_blueprint(sop_extraction_bp)   

register_progress_websocket(sock)
register_websocket(sock)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
