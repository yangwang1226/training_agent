import sys
import os
import logging
import json
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, session, Blueprint, send_from_directory
from flask_sock import Sock
from agent import ConversationalPromptAgent, InteractivePromptAgent
from agent.evaluate_agent import assessment_service, DifficultyLevel
import db as db_module

app = Flask(__name__, template_folder='front_end/templates', static_folder='front_end/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

sock = Sock(app)

# 进度更新的WebSocket连接
progress_connections = {}

EVALUATE_STATIC_DIR = Path(__file__).parent / "front_end" / "evaluate" / "static"


@app.route('/evaluate/static/<path:filename>')
def evaluate_static(filename):
    return send_from_directory(EVALUATE_STATIC_DIR, filename)

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
        'response': response.get('content', ''),
        'options': response.get('options', []),
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
        # 发送开始生成的进度
        send_progress(session_id, "开始生成提示词...", 10)
        
        # 模拟进度更新
        send_progress(session_id, "分析场景信息...", 20)
        
        # 生成主问题
        send_progress(session_id, "生成客户问题列表...", 40)
        
        # 生成关联问题
        send_progress(session_id, "生成关联问题和触发条件...", 60)
        
        # 生成情绪描述
        send_progress(session_id, "生成客户情绪描述...", 80)
        
        # 构建完整提示词
        send_progress(session_id, "构建完整提示词...", 90)
        
        full_prompt = agent.generate_prompt()
        
        # 完成
        send_progress(session_id, "提示词生成完成！", 100)
        
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
        'response': response.get('content', ''),
        'options': response.get('options', []),
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
        'response': response.get('content', ''),
        'options': response.get('options', []),
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
    
    try:
        scene_id = db_module.save_scene(name, prompt, status=0)
        
        if scene_id:
            logging.info(f"场景保存成功: id={scene_id}, name={name}")
            return jsonify({
                'success': True,
                'scene_id': scene_id,
                'message': f'场景已保存'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失败'
            })
    except Exception as e:
        logging.error(f"保存场景失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        })

@app.route('/api/scenes', methods=['GET'])
def list_scenes():
    try:
        scenes = db_module.list_scenes()
        scenes_list = [
            {
                'id': scene['id'],
                'name': scene['scene_name'],
                'created_at': scene['created_time'].strftime('%Y-%m-%d %H:%M:%S') if scene.get('created_time') else ''
            }
            for scene in scenes
        ]
        return jsonify({'scenes': scenes_list})
    except Exception as e:
        logging.error(f"获取场景列表失败: {str(e)}", exc_info=True)
        return jsonify({'scenes': []})

@app.route('/api/realtime/prompt/<scene_id>')
def get_realtime_prompt(scene_id):
    try:
        scene_id_int = int(scene_id)
        prompt = db_module.get_prompt_by_scene_id(scene_id_int)
        if prompt:
            return jsonify({'success': True, 'prompt': prompt})
        else:
            return jsonify({'success': False, 'error': '场景不存在'})
    except ValueError:
        return jsonify({'success': False, 'error': '无效的场景ID'})
    except Exception as e:
        logging.error(f"获取场景提示词失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/interactive/init', methods=['GET'])
def interactive_init():
    agent = get_interactive_agent(session.get('session_id', 'default'))
    
    response = agent.get_initial_message()
    
    return jsonify({
        'message': response.content,
        'options': response.options,
        'next_step': response.next_step
    })


@app.route('/api/interactive/select', methods=['POST'])
def interactive_select():
    data = request.json
    step = data.get('step')
    value = data.get('value')
    session_id = session.get('session_id', 'default')
    
    agent = get_interactive_agent(session_id)
    
    response = agent.process_selection(step, value)
    
    return jsonify({
        'success': True,
        'message': response.content,
        'options': response.options,
        'next_step': response.next_step,
        'show_input': response.show_input,
        'show_background': response.show_background
    })


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


@app.route('/evaluate/')
def evaluate_page():
    evaluate_template_path = Path(__file__).parent / "front_end" / "evaluate" / "templates" / "evaluate.html"
    with open(evaluate_template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/api/evaluate/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    profile = assessment_service.get_user_profile(user_id)
    
    if profile:
        return jsonify({
            'success': True,
            'profile': {
                'user_id': profile.user_id,
                'overall_score': profile.overall_score,
                'dimension_scores': profile.dimension_scores,
                'training_count': profile.training_count,
                'total_duration': profile.total_duration,
                'level': profile.level,
                'weak_points': profile.weak_points,
                'strong_points': profile.strong_points,
                'improvement_history': profile.improvement_history,
                'achievements': profile.achievements
            }
        })
    else:
        return jsonify({
            'success': True,
            'profile': {
                'user_id': user_id,
                'overall_score': 0,
                'dimension_scores': {
                    '沟通技巧': 0,
                    '产品知识': 0,
                    '需求挖掘': 0,
                    '异议处理': 0,
                    '促成技巧': 0
                },
                'training_count': 0,
                'total_duration': 0,
                'level': '入门',
                'weak_points': [],
                'strong_points': [],
                'improvement_history': [],
                'achievements': []
            }
        })


@app.route('/api/evaluate/history/<user_id>', methods=['GET'])
def get_training_history(user_id):
    industry_filter = request.args.get('industry', '')
    
    history = assessment_service.get_training_history(user_id, limit=20)
    
    if industry_filter:
        history = [h for h in history if industry_filter in h.get('industry', '')]
    
    return jsonify({
        'success': True,
        'history': history
    })


@app.route('/api/evaluate/assessment/<session_id>', methods=['GET'])
def get_assessment(session_id):
    assessment = assessment_service.get_assessment(session_id)
    
    if assessment:
        return jsonify({
            'success': True,
            'assessment': assessment
        })
    else:
        return jsonify({
            'success': False,
            'error': '评估报告不存在'
        })


@app.route('/api/evaluate/suggestions/<user_id>', methods=['POST'])
def generate_suggestions(user_id):
    suggestions = assessment_service.generate_improvement_suggestions(user_id)
    
    if suggestions:
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    else:
        return jsonify({
            'success': False,
            'error': '无法生成建议，请先完成训练'
        })


@app.route('/api/evaluate/session/create', methods=['POST'])
def create_evaluation_session():
    data = request.json
    user_id = session.get('session_id', 'default')
    
    training_session = assessment_service.create_session(
        user_id=user_id,
        scene_id=data.get('scene_id', ''),
        industry=data.get('industry', ''),
        role=data.get('role', ''),
        purchase_intent=data.get('purchase_intent', '一般'),
        difficulty=DifficultyLevel(data.get('difficulty', '进阶')),
        system_prompt=data.get('system_prompt', ''),
        customer_persona=data.get('customer_persona', '')
    )
    
    return jsonify({
        'success': True,
        'session_id': training_session.session_id
    })


@app.route('/api/evaluate/session/<session_id>/transcript', methods=['POST'])
def add_transcript(session_id):
    data = request.json
    
    assessment_service.add_transcript(
        session_id=session_id,
        role=data.get('role', 'user'),
        content=data.get('content', ''),
        timestamp=data.get('timestamp')
    )
    
    return jsonify({'success': True})


@app.route('/api/evaluate/session/<session_id>/end', methods=['POST'])
def end_evaluation_session(session_id):
    session = assessment_service.end_session(session_id)
    
    if session:
        return jsonify({
            'success': True,
            'duration': session.duration_seconds
        })
    else:
        return jsonify({
            'success': False,
            'error': '会话不存在'
        })


@app.route('/api/evaluate/session/<session_id>/evaluate', methods=['POST'])
def evaluate_training_session(session_id):
    assessment = assessment_service.evaluate_session(session_id)
    
    if assessment:
        return jsonify({
            'success': True,
            'assessment': {
                'overall_score': assessment.overall_score,
                'dimension_scores': [
                    {
                        'dimension': ds.dimension_name,
                        'score': ds.score,
                        'weight': ds.weight,
                        'reason': ds.reason,
                        'sub_scores': ds.sub_scores
                    }
                    for ds in assessment.dimension_scores
                ],
                'highlights': assessment.highlights,
                'improvements': assessment.improvements,
                'golden_sentences': assessment.golden_sentences,
                'key_moments': [
                    {
                        'turn': km.time,
                        'type': km.moment_type,
                        'content': km.content,
                        'handling': km.handling_quality,
                        'suggestion': km.suggestion
                    }
                    for km in assessment.key_moments
                ],
                'completion_rate': assessment.completion_rate,
                'total_turns': assessment.total_turns,
                'duration_seconds': assessment.duration_seconds
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': '评估失败'
        })


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
    """发送进度更新"""
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
