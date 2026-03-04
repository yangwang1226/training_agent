import logging
from flask import Blueprint, jsonify, request, session

from agent import ConversationalPromptAgent

logger = logging.getLogger(__name__)

prompt_bp = Blueprint('prompt', __name__, url_prefix='/api')

agents = {}


def get_agent(session_id):
    if session_id not in agents:
        agents[session_id] = ConversationalPromptAgent()
    return agents[session_id]


@prompt_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    session_id = session.get('session_id', 'default')
    
    logging.info(f"收到用户消息：{user_input}")
    
    agent = get_agent(session_id)
    response = agent.chat(user_input)
    
    state = agent.get_current_state()
    
    logging.info(f"当前状态：industry={state.industry}, role={state.role_type}, intent={state.purchase_intent}")
    
    return jsonify({
        'response': response.get('content', ''),
        'options': response.get('options', []),
        'show_dimensions': response.get('show_dimensions', False),
        'dimensions': response.get('dimensions', []),
        'dimensions_confirmed': response.get('dimensions_confirmed', False),
        'state': {
            'industry': state.industry,
            'role_type': state.role_type,
            'purchase_intent': state.purchase_intent,
            'custom_questions': state.custom_questions,
            'collected_info': state.collected_info,
            'missing_info': state.get_missing_info(),
            'extended_info': state.extended_info,
            'extended_info_sufficient': state.extended_info_sufficient,
            'dimensions_confirmed': state.dimensions_confirmed
        }
    })


@prompt_bp.route('/generate', methods=['POST'])
def generate():
    session_id = session.get('session_id', 'default')
    agent = get_agent(session_id)
    
    logging.info(f"开始生成提示词，session_id: {session_id}")
    
    try:
        from .progress_routes import send_progress
        
        send_progress(session_id, "开始生成提示词...", 10)
        send_progress(session_id, "分析场景信息...", 20)
        send_progress(session_id, "生成客户问题列表...", 40)
        send_progress(session_id, "生成关联问题和触发条件...", 60)
        send_progress(session_id, "生成客户情绪描述...", 80)
        send_progress(session_id, "构建完整提示词...", 90)
        
        full_prompt = agent.generate_prompt()
        
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


@prompt_bp.route('/reset', methods=['POST'])
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


@prompt_bp.route('/init', methods=['GET'])
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


def get_prompt_agents():
    return agents
