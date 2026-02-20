import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, session
from agent import ConversationalPromptAgent

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

agents = {}

def get_agent(session_id):
    if session_id not in agents:
        agents[session_id] = ConversationalPromptAgent()
    return agents[session_id]

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
