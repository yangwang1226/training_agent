import sys
import os
import logging
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, session
from flask_sock import Sock
from agent import ConversationalPromptAgent, InteractivePromptAgent

app = Flask(__name__, template_folder='front_end/templates', static_folder='front_end/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

sock = Sock(app)

SCENE_PROMPT_DIR = Path(__file__).parent / "scene_prompt"
SCENE_PROMPT_DIR.mkdir(exist_ok=True)

from front_end.realtime import register_websocket
register_websocket(app, sock)

agents = {}
interactive_agents = {}


def get_agent(session_id):
    if session_id not in agents:
        agents[session_id] = ConversationalPromptAgent()
    return agents[session_id]


def get_interactive_agent(session_id):
    if session_id not in interactive_agents:
        interactive_agents[session_id] = InteractivePromptAgent()
    return interactive_agents[session_id]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/interactive')
def interactive():
    return render_template('interactive.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    session_id = session.get('session_id', 'default')
    
    logging.info(f"收到用户消息: {user_input}")
    
    agent = get_agent(session_id)
    response = agent.chat(user_input)
    
    state = agent.get_current_state()
    
    logging.info(f"当前状态: industry={state.industry}, role={state.role_type}, intent={state.purchase_intent}")
    logging.info(f"是否可以生成: {agent.is_ready_to_generate()}")
    
    return jsonify({
        'response': response,
        'is_ready': agent.is_ready_to_generate(),
        'state': {
            'industry': state.industry,
            'role_type': state.role_type,
            'purchase_intent': state.purchase_intent,
            'custom_questions': state.custom_questions,
            'collected_info': state.collected_info,
            'missing_info': state.get_missing_info(),
            'extended_info': state.extended_info,
            'extended_info_sufficient': state.extended_info_sufficient
        }
    })

@app.route('/api/generate', methods=['POST'])
def generate():
    session_id = session.get('session_id', 'default')
    agent = get_agent(session_id)
    
    logging.info(f"开始生成提示词, session_id: {session_id}")
    
    if not agent.is_ready_to_generate():
        state = agent.get_current_state()
        missing = state.get_missing_info()
        logging.warning(f"信息不完整，缺少: {missing}")
        return jsonify({
            'success': False,
            'error': f"还需要以下信息：{', '.join(missing)}"
        })
    
    try:
        full_prompt = agent.generate_prompt()
        logging.info("提示词生成成功")
        
        return jsonify({
            'success': True,
            'full_prompt': full_prompt
        })
    except Exception as e:
        logging.error(f"生成提示词失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"生成失败: {str(e)}"
        })

@app.route('/api/reset', methods=['POST'])
def reset():
    session_id = session.get('session_id', 'default')
    
    if session_id in agents:
        agents[session_id].reset()
    else:
        agents[session_id] = ConversationalPromptAgent()
    
    agent = get_agent(session_id)
    response = agent.chat("你好")
    
    return jsonify({
        'response': response,
        'is_ready': False,
        'state': {
            'industry': '',
            'role_type': '',
            'purchase_intent': '',
            'custom_questions': [],
            'collected_info': {
                'industry': False,
                'role': False,
                'intent': False,
                'questions': False
            },
            'missing_info': ['行业', '角色', '购买意愿', '问题列表'],
            'extended_info': {},
            'extended_info_sufficient': False
        }
    })

@app.route('/api/init', methods=['GET'])
def init():
    session_id = session.get('session_id', 'default')
    agent = get_agent(session_id)
    response = agent.chat("你好")
    
    state = agent.get_current_state()
    
    return jsonify({
        'response': response,
        'is_ready': False,
        'state': {
            'industry': state.industry,
            'role_type': state.role_type,
            'purchase_intent': state.purchase_intent,
            'custom_questions': state.custom_questions,
            'collected_info': state.collected_info,
            'missing_info': state.get_missing_info(),
            'extended_info': state.extended_info,
            'extended_info_sufficient': state.extended_info_sufficient
        }
    })

@app.route('/api/save', methods=['POST'])
def save():
    data = request.json
    name = data.get('name', '').strip()
    prompt = data.get('prompt', '')
    
    logging.info(f"收到保存请求: name={name}")
    
    if not name:
        return jsonify({
            'success': False,
            'error': '请输入场景名称'
        })
    
    if not prompt:
        return jsonify({
            'success': False,
            'error': '没有可保存的提示词'
        })
    
    safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
    safe_name = safe_name.replace(' ', '_')
    
    if not safe_name:
        safe_name = f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{safe_name}_{timestamp}.txt"
    
    filepath = SCENE_PROMPT_DIR / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        logging.info(f"场景保存成功: {filepath}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'scene_id': filename,
            'message': f'场景已保存为 {filename}'
        })
    except Exception as e:
        logging.error(f"保存场景失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        })

@app.route('/api/scenes', methods=['GET'])
def list_scenes():
    scenes = []
    if SCENE_PROMPT_DIR.exists():
        for file in SCENE_PROMPT_DIR.glob('*.txt'):
            scenes.append({
                'id': file.name,
                'name': file.stem.rsplit('_', 2)[0] if '_' in file.stem else file.stem,
                'created_at': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    return jsonify({'scenes': scenes})

@app.route('/api/realtime/prompt/<scene_id>')
def get_realtime_prompt(scene_id):
    scene_file = find_scene_file(scene_id)
    if not scene_file:
        return jsonify({'success': False, 'error': '场景不存在'})
    
    try:
        with open(scene_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        return jsonify({'success': True, 'prompt': prompt})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def find_scene_file(scene_id):
    if not SCENE_PROMPT_DIR.exists():
        return None
    
    for file in SCENE_PROMPT_DIR.glob('*.txt'):
        if scene_id in file.name or file.name == scene_id:
            return file
    
    return None


@app.route('/api/interactive/init', methods=['GET'])
def interactive_init():
    agent = get_interactive_agent(session.get('session_id', 'default'))
    
    return jsonify({
        'message': agent.get_initial_message(),
        'options': {
            'position': agent.get_position_options()
        }
    })


@app.route('/api/interactive/select', methods=['POST'])
def interactive_select():
    data = request.json
    step = data.get('step')
    value = data.get('value')
    session_id = session.get('session_id', 'default')
    
    agent = get_interactive_agent(session_id)
    
    if step == 'position':
        agent.set_position(value)
        return jsonify({
            'success': True,
            'next_step': 'industry',
            'message': '请选择您所在的行业：',
            'options': agent.get_industry_options()
        })
    elif step == 'industry':
        agent.set_industry(value)
        if value == '其他':
            return jsonify({
                'success': True,
                'next_step': 'industry_input',
                'message': '请输入您的行业：',
                'show_input': True
            })
        return jsonify({
            'success': True,
            'next_step': 'product',
            'message': '请选择您要销售/服务的产品：',
            'options': agent.get_product_options()
        })
    elif step == 'product':
        agent.set_product(value)
        if value == '其他':
            return jsonify({
                'success': True,
                'next_step': 'product_input',
                'message': '请输入产品名称：',
                'show_input': True
            })
        return jsonify({
            'success': True,
            'next_step': 'personality',
            'message': '请选择模拟客户的性格：',
            'options': agent.get_personality_options()
        })
    elif step == 'personality':
        agent.set_personality(value)
        return jsonify({
            'success': True,
            'next_step': 'interest_level',
            'message': '请选择模拟客户的感兴趣程度：',
            'options': agent.get_interest_level_options()
        })
    elif step == 'interest_level':
        agent.set_interest_level(value)
        return jsonify({
            'success': True,
            'next_step': 'background',
            'message': '请编辑模拟客户的背景信息（也可以自动生成）：',
            'show_background': True
        })
    
    return jsonify({'success': False, 'error': 'Invalid step'})


@app.route('/api/interactive/input', methods=['POST'])
def interactive_input():
    data = request.json
    step = data.get('step')
    value = data.get('value')
    session_id = session.get('session_id', 'default')
    
    agent = get_interactive_agent(session_id)
    
    if step == 'industry_input':
        agent.set_industry(value)
        return jsonify({
            'success': True,
            'next_step': 'product',
            'message': '请选择您要销售/服务的产品：',
            'options': agent.get_product_options()
        })
    elif step == 'product_input':
        agent.set_product(value)
        return jsonify({
            'success': True,
            'next_step': 'personality',
            'message': '请选择模拟客户的性格：',
            'options': agent.get_personality_options()
        })
    
    return jsonify({'success': False, 'error': 'Invalid step'})


@app.route('/api/interactive/generate-background', methods=['POST'])
def interactive_generate_background():
    session_id = session.get('session_id', 'default')
    agent = get_interactive_agent(session_id)
    
    try:
        result = agent.generate_questions_and_background()
        background = result.get('background_info', '')
        return jsonify({
            'success': True,
            'background': background
        })
    except Exception as e:
        logging.error(f"生成背景失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/interactive/generate', methods=['POST'])
def interactive_generate():
    data = request.json
    background_info = data.get('background_info', '')
    session_id = session.get('session_id', 'default')
    
    agent = get_interactive_agent(session_id)
    
    if background_info:
        agent.set_background_info(background_info)
    
    try:
        result = agent.generate_full_prompt()
        if result.success:
            return jsonify({
                'success': True,
                'prompt': result.full_prompt
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error_message
            })
    except Exception as e:
        logging.error(f"生成提示词失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
