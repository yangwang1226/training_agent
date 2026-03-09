import logging
import json
from flask import Blueprint, jsonify, request, session
from typing import Dict, Any

import db as db_module
from agent.service.scene import SceneAgent
from agent.service.scene.preset_scene_service import PresetSceneService

logger = logging.getLogger(__name__)

scene_create_bp = Blueprint('scene_create', __name__, url_prefix='/api/scene')

# 存储场景智能体实例
scene_agents: Dict[str, SceneAgent] = {}

# 预设场景服务实例
preset_service = PresetSceneService()


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


@scene_create_bp.route('/generate-from-preset', methods=['POST'])
def generate_from_preset():
    """
    基于预设场景生成完整的场景提示词
    
    请求参数:
        scene_code: 预设场景代码（如 'auto_first_visit'）
        user_background: 用户补充的背景信息（可选）
        custom_requirements: 用户自定义需求（可选）
    
    返回:
        场景 ID 和跳转 URL
    """
    try:
        data = request.json
        scene_code = data.get('scene_code')
        user_background = data.get('user_background')
        custom_requirements = data.get('custom_requirements')
        
        if not scene_code:
            return jsonify({
                'success': False,
                'error': '缺少场景代码参数'
            })
        
        logger.info(f"开始基于预设场景生成: {scene_code}")
        
        # 1. 使用预设场景服务生成场景内容
        scene_content = preset_service.generate_from_preset(
            scene_code=scene_code,
            user_background=user_background,
            custom_requirements=custom_requirements
        )
        
        if not scene_content:
            return jsonify({
                'success': False,
                'error': '场景内容生成失败'
            })
        
        # 2. 构建完整提示词（结合手工模板）
        full_prompt = preset_service.build_full_prompt(scene_content)
        
        if not full_prompt:
            return jsonify({
                'success': False,
                'error': '提示词构建失败'
            })
        
        # 3. 准备场景数据
        scene_name = f"{scene_content.industry}_{scene_content.ai_role}_场景"
        dimension_config = json.dumps({
            "industry": scene_content.industry,
            "role_type": scene_content.role_type,
            "ai_role": scene_content.ai_role,
            "role_description": scene_content.role_description,
            "dimensions": [d.to_dict() for d in scene_content.dimensions]
        }, ensure_ascii=False)
        
        # 4. 保存到数据库
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
        
        logger.info(f"预设场景保存成功：id={scene_id}, name={scene_name}")
        
        # 5. 增加预设场景的使用次数
        db_module.increment_usage_count(scene_code)
        
        # 6. 返回结果
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'scene_name': scene_name,
            'redirect_url': f'/realtime/{scene_id}',
            'message': '场景生成成功！准备开始对练',
            'scene_content': {
                'industry': scene_content.industry,
                'ai_role': scene_content.ai_role,
                'role_type': scene_content.role_type,
                'background_info': scene_content.background_info,
                'main_questions_count': len(scene_content.main_questions),
                'trigger_groups_count': len(scene_content.trigger_groups),
                'dimensions_count': len(scene_content.dimensions)
            }
        })
        
    except Exception as e:
        logger.error(f"基于预设场景生成失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'生成失败：{str(e)}'
        })


@scene_create_bp.route('/preview-preset/<scene_code>', methods=['GET'])
def preview_preset(scene_code: str):
    """
    预览预设场景信息（不生成完整内容）
    
    用于在选择场景时快速查看场景基本信息
    """
    try:
        preset_data = preset_service.load_preset_scene(scene_code)
        
        if not preset_data:
            return jsonify({
                'success': False,
                'error': f'预设场景不存在: {scene_code}'
            })
        
        return jsonify({
            'success': True,
            'preset_scene': {
                'scene_code': preset_data.get('scene_code'),
                'scene_name': preset_data.get('scene_name'),
                'scene_description': preset_data.get('scene_description'),
                'ai_role': preset_data.get('ai_role'),
                'user_role': preset_data.get('user_role'),
                'difficulty': preset_data.get('difficulty'),
                'estimated_duration': preset_data.get('estimated_duration'),
                'usage_count': preset_data.get('usage_count', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"预览预设场景失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'预览失败：{str(e)}'
        })
