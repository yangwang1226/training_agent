"""自定义场景创建路由"""
import logging
import json
import os
from flask import Blueprint, jsonify, request, session

import db as db_module

# 导入 Qwen API
import dashscope
from dashscope import MultiModalConversation
from langchain_core.messages import HumanMessage, SystemMessage

# 初始化 API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 导入动态提示词生成服务
from agent.service.scene.prompt_generation_service import PromptGenerationService

logger = logging.getLogger(__name__)

custom_scene_bp = Blueprint('custom_scene', __name__, url_prefix='/api/scene')

# 初始化动态提示词生成服务
prompt_service = PromptGenerationService()


def call_qwen_model(prompt: str, temperature: float = 0.3) -> str:
    """调用 Qwen 模型生成内容"""
    try:
        model = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
        
        messages = [
            {"role": "system", "content": [{"text": "你是一个专业的销售培训专家，擅长设计训练场景和生成培训内容。"}]},
            {"role": "user", "content": [{"text": prompt}]}
        ]
        
        response = MultiModalConversation.call(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            logger.error(f"Qwen API error: {response.code} - {response.message}")
            return None
    except Exception as e:
        logger.error(f"调用Qwen模型失败: {e}", exc_info=True)
        return None


# 自定义场景生成Prompt
CUSTOM_SCENE_GENERATE_PROMPT = """
你是一个专业的销售培训专家，请根据用户描述生成完整的训练场景配置。

## 用户输入
- 场景描述：{scene_description}
- AI模拟角色：{ai_role}
- 训练者角色：{user_role}

## 请生成以下内容

### 1. 场景基本信息
- 场景名称：简洁有力的名称（如"汽车销售-价格谈判训练"）
- 所属行业：从场景描述中提取行业
- 场景描述：100字以内的完整描述

### 2. AI开场白
生成一句AI（模拟{ai_role}）在对练开始时说的第一句话，要自然、符合角色身份。

### 3. 固定问题（10个）
按照真实销售场景的对话顺序，生成10个AI必须提问的问题。
这些问题应该：
- 覆盖完整的销售/服务流程
- 由浅入深，逐步推进
- 包含常见的客户疑虑和异议
- 符合{ai_role}的身份

格式：
{{
  "id": 1,
  "question": "问题内容",
  "order": 1
}}

### 4. 关联问题（10个）
生成10个可能在对话中触发的关联问题，每个问题配有触发关键词。
当训练者的回答涉及这些关键词时，AI会追问这些问题。

格式：
{{
  "id": "R1",
  "question": "关联问题内容",
  "trigger_keywords": ["关键词1", "关键词2", "关键词3"]
}}

### 5. SOP质检项
根据这个行业的最佳实践，生成SOP质检项（6-10个）：
- "必须做"的关键动作（如：先建立信任再谈价格）
- "禁止做"的错误行为（如：直接否定客户）

格式：
{{
  "title": "质检项标题",
  "description": "具体描述",
  "check_type": "must_do" 或 "must_not",
  "weight": 10
}}

请严格按照以下JSON格式返回，不要包含任何其他文字：
{{
    "scene_name": "场景名称",
    "industry": "所属行业",
    "scene_description": "场景描述",
    "ai_role": "{ai_role}",
    "user_role": "{user_role}",
    "opening_line": "AI开场白",
    "fixed_questions": [
        {{"id": 1, "question": "问题1", "order": 1}},
        ...共10个
    ],
    "related_questions": [
        {{"id": "R1", "question": "关联问题1", "trigger_keywords": ["关键词1", "关键词2"]}},
        ...共10个
    ],
    "sop_checklist": [
        {{"title": "质检项1", "description": "描述", "check_type": "must_do", "weight": 10}},
        ...共6-10个
    ]
}}
"""


@custom_scene_bp.route('/generate-custom', methods=['POST'])
def generate_custom_scene():
    """
    自定义场景生成 - 一键生成所有配置
    
    请求参数：
    {
        "scene_description": "场景描述",
        "ai_role": "AI角色",
        "user_role": "用户角色"
    }
    """
    try:
        data = request.json
        scene_description = data.get('scene_description', '').strip()
        ai_role = data.get('ai_role', '').strip()
        user_role = data.get('user_role', '').strip()
        
        # 参数校验
        if not scene_description or not ai_role or not user_role:
            return jsonify({
                'success': False,
                'error': '缺少必填参数'
            }), 400
        
        logger.info(f"开始生成自定义场景 - 描述: {scene_description[:50]}...")
        
        # 构建Prompt
        prompt = CUSTOM_SCENE_GENERATE_PROMPT.format(
            scene_description=scene_description,
            ai_role=ai_role,
            user_role=user_role
        )
        
        # 调用LLM生成
        logger.info("调用LLM生成场景配置...")
        llm_response = call_qwen_model(prompt)
        
        if not llm_response:
            return jsonify({
                'success': False,
                'error': 'AI生成失败，请重试'
            }), 500
        
        # 解析JSON响应
        try:
            # 尝试提取JSON内容（可能被包裹在```json```中）
            response_text = llm_response.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            scene_config = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"解析LLM响应失败: {e}")
            logger.error(f"原始响应: {llm_response}")
            return jsonify({
                'success': False,
                'error': 'AI响应格式错误，请重试'
            }), 500
        
        # 验证生成的数据
        required_fields = ['scene_name', 'industry', 'opening_line', 'fixed_questions', 'related_questions', 'sop_checklist']
        for field in required_fields:
            if field not in scene_config:
                logger.error(f"生成的配置缺少字段: {field}")
                return jsonify({
                    'success': False,
                    'error': f'生成的配置不完整，缺少{field}'
                }), 500
        
        # 确保角色信息正确
        scene_config['ai_role'] = ai_role
        scene_config['user_role'] = user_role
        
        logger.info(f"场景配置生成成功: {scene_config['scene_name']}")
        
        return jsonify({
            'success': True,
            'data': scene_config,
            'message': '场景配置生成成功'
        })
        
    except Exception as e:
        logger.error(f"生成自定义场景失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'生成失败: {str(e)}'
        }), 500


@custom_scene_bp.route('/save-custom', methods=['POST'])
def save_custom_scene():
    """
    保存自定义场景（已定制状态）
    
    请求参数：
    {
        "scene_name": "场景名称",
        "industry": "行业",
        "ai_role": "AI角色",
        "user_role": "用户角色",
        "opening_line": "开场白",
        "fixed_questions": [...],
        "related_questions": [...],
        "sop_checklist": [...],
        "scene_description": "场景描述"
    }
    """
    try:
        data = request.json
        
        # 提取数据
        scene_name = data.get('scene_name', '')
        industry = data.get('industry', '')
        ai_role = data.get('ai_role', '')
        user_role = data.get('user_role', '')
        opening_line = data.get('opening_line', '')
        fixed_questions = data.get('fixed_questions', [])
        related_questions = data.get('related_questions', [])
        sop_checklist = data.get('sop_checklist', [])
        scene_description = data.get('scene_description', '')
        
                # 使用动态提示词生成服务生成高质量对练提示词
        logger.info(f"开始动态生成对练提示词: {scene_name}")
        
        scene_prompt = prompt_service.generate_scene_prompt(
            scene_type='sales',  # 默认使用 sales 类型
            scene_data={
                'ai_role': ai_role,
                'user_role': user_role,
                'industry': industry,
                'scene_description': scene_description,
                'background_info': scene_description,
                'fixed_questions': fixed_questions,
                'related_questions': related_questions,
            },
            use_dynamic=True
        )
        
        # 如果动态生成失败，降级为简单拼接
        if not scene_prompt:
            logger.warning("动态生成失败，使用简单拼接方式")
            scene_prompt = f"""
# 场景：{scene_name}

## 角色设定
- AI角色：{ai_role}
- 训练者角色：{user_role}

## 场景描述
{scene_description}

## AI开场白
{opening_line}

## 固定问题
{json.dumps(fixed_questions, ensure_ascii=False, indent=2)}

## 关联问题
{json.dumps(related_questions, ensure_ascii=False, indent=2)}
"""
        else:
            logger.info(f"动态生成对练提示词成功，长度: {len(scene_prompt)} 字符")
        
        # 构建维度配置
        dimension_config = json.dumps({
            "industry": industry,
            "role_type": user_role,
            "ai_role": ai_role,
            "role_description": f"训练{user_role}的沟通技巧",
            "dimensions": []  # 可以后续添加评估维度
        }, ensure_ascii=False)
        
        # 保存到数据库
        scene_id = db_module.save_scene(
            scene_name=scene_name,
            scene_prompt=scene_prompt,
            dimension_config=dimension_config,
            role_type=user_role,
            role_description=f"模拟{ai_role}，训练{user_role}",
            industry=industry,
            training_goal=f"提升{user_role}的沟通能力",
            full_evaluation_prompt=scene_prompt,
            sop_checklist=json.dumps(sop_checklist, ensure_ascii=False),
            opening_line=opening_line,
            fixed_questions=json.dumps(fixed_questions, ensure_ascii=False),
            related_questions=json.dumps(related_questions, ensure_ascii=False),
            status=2  # 已定制状态
        )
        
        if not scene_id:
            return jsonify({
                'success': False,
                'error': '数据库保存失败'
            }), 500
        
        logger.info(f"自定义场景保存成功: id={scene_id}, name={scene_name}")
        
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'scene_name': scene_name,
            'redirect_url': f'/realtime/{scene_id}',
            'message': '场景保存成功'
        })
        
    except Exception as e:
        logger.error(f"保存自定义场景失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        }), 500


@custom_scene_bp.route('/save-custom-draft', methods=['POST'])
def save_custom_draft():
    """
    保存自定义场景草稿
    """
    try:
        data = request.json
        data['status'] = 0  # 草稿状态
        
        # 复用保存逻辑
        return save_custom_scene()
        
    except Exception as e:
        logger.error(f"保存草稿失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        }), 500