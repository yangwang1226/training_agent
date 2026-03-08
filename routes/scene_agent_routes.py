import logging
import json
from flask import Blueprint, jsonify, request, session
from typing import Dict, Any

import db as db_module
from agent.service.scene import SceneAgent

logger = logging.getLogger(__name__)

scene_create_bp = Blueprint('scene_create', __name__, url_prefix='/api/scene')

# 存储场景智能体实例
scene_agents: Dict[str, SceneAgent] = {}


def get_scene_agent(session_id: str) -> SceneAgent:
    """获取或创建场景智能体"""
    if session_id not in scene_agents:
        scene_agents[session_id] = SceneAgent()
    return scene_agents[session_id]


@scene_create_bp.route('/create', methods=['POST'])
def create_scene_session():
    """
    创建场景会话
    初始化场景智能体，返回 session_id
    """
    try:
        session_id = session.get('session_id', 'default')
        agent = get_scene_agent(session_id)
        
        # 重置智能体
        agent.reset()
        
        # 初始化对话 - 精简版（200 字以内）
        initial_message = """你好，我是你的AI培训教练小新，
        我会根据你的需求，为你创建一个定制化的AI培训场景。
        我需要你告诉我：
        1. 您所在的行业？ （例如：汽车行业、金融行业、医疗行业等）
        2. 需要AI模拟的角色？（例如：挑剔的客户、陌生的访客、接电话的客户等）
        3. 被训练者的角色？（例如：新销售、客户服务代表等）
        
        当然你也可以一句话告诉我您培训的这个场景？
        例如：“我们是汽车行业，最近公司来了很多新的销售，我想让AI模拟客户，训练新销售的销售技巧。让他们快速熟悉汽车销售流程。”"""
        
        # response = agent.chat(initial_message)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'response': initial_message
        })
    except Exception as e:
        logger.error(f"创建场景会话失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'创建失败：{str(e)}'
        })


@scene_create_bp.route('/chat', methods=['POST'])
def chat():
    """
    场景对话交互
    接收用户输入，返回对话响应和状态信息
    """
    try:
        data = request.json
        user_input = data.get('message', '')
        session_id = session.get('session_id', 'default')
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': '请输入内容'
            })
        
        logger.info(f"收到用户输入：{user_input}")
        
        agent = get_scene_agent(session_id)
        response = agent.chat(user_input)
        
        return jsonify({
            'success': True,
            'response': response.get('content', ''),
            'options': response.get('options', []),
            'multi_select': response.get('multi_select', False),
            'is_ready': response.get('is_ready', False),
            'conversation_ended': response.get('conversation_ended', False),  # ✅ 新增
            'state': response.get('state', {})
        })
    except Exception as e:
        logger.error(f"对话交互失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'对话失败：{str(e)}'
        })


@scene_create_bp.route('/generate', methods=['POST'])
def generate_scene():
    """
    生成场景内容并保存
    调用 SceneAgent 生成场景内容，保存到数据库，返回场景 ID
    """
    try:
        session_id = session.get('session_id', 'default')
        agent = get_scene_agent(session_id)
        
        logger.info(f"开始生成场景内容，session_id: {session_id}")
        
        # 生成场景内容
        scene_content = agent.generate_scene_content()
        
        if not scene_content:
            return jsonify({
                'success': False,
                'error': '场景内容生成失败'
            })
        
        # 构建完整提示词
        full_prompt = agent.build_prompt()
        
        if not full_prompt:
            return jsonify({
                'success': False,
                'error': '提示词构建失败'
            })
        
        # 准备场景数据
        scene_name = f"{scene_content.industry}_{scene_content.role_type}_场景"
        dimension_config = json.dumps({
            "industry": scene_content.industry,
            "role_type": scene_content.role_type,
            "role_description": scene_content.role_description,
            "dimensions": [d.to_dict() for d in scene_content.dimensions]
        }, ensure_ascii=False)
        
        # 保存到数据库
        scene_id = db_module.save_scene(
            scene_name=scene_name,
            scene_prompt=full_prompt,
            dimension_config=dimension_config,
            role_type=scene_content.role_type,
            role_description=scene_content.role_description,
            industry=scene_content.industry,
            training_goal=f"提升{scene_content.role_type}的沟通能力",
            full_evaluation_prompt=full_prompt,
            status=0
        )
        
        if not scene_id:
            return jsonify({
                'success': False,
                'error': '数据库保存失败'
            })
        
        logger.info(f"场景保存成功：id={scene_id}, name={scene_name}")
        
        # 返回场景信息和跳转 URL
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'scene_name': scene_name,
            'redirect_url': f'/realtime/{scene_id}',
            'message': '场景生成成功！是否开始对练测试？',
            'scene_content': agent.get_scene_content_dict()
        })
    except Exception as e:
        logger.error(f"生成场景失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'生成失败：{str(e)}'
        })


@scene_create_bp.route('/status', methods=['GET'])
def get_status():
    """
    获取当前场景创建状态
    """
    try:
        session_id = session.get('session_id', 'default')
        agent = get_scene_agent(session_id)
        
        state = agent.state
        
        return jsonify({
            'success': True,
            'state': {
                'industry': state.industry,
                'role_type': state.role_type,
                'role_description': state.role_description,
                'collected_info': state.collected_info,
                'missing_info': state.get_missing_info(),
                'extended_info': state.extended_info,
                'extended_info_sufficient': state.extended_info_sufficient,
                'is_ready': state.is_ready_for_generation()
            }
        })
    except Exception as e:
        logger.error(f"获取状态失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取状态失败：{str(e)}'
        })


@scene_create_bp.route('/reset', methods=['POST'])
def reset():
    """
    重置场景智能体
    """
    try:
        session_id = session.get('session_id', 'default')
        
        if session_id in scene_agents:
            scene_agents[session_id].reset()
        else:
            scene_agents[session_id] = SceneAgent()
        
        return jsonify({
            'success': True,
            'message': '场景智能体已重置'
        })
    except Exception as e:
        logger.error(f"重置失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'重置失败：{str(e)}'
        })
