import logging
import json
from flask import Blueprint, jsonify, request

import db as db_module
from agent.service.scene.preset_scene_service import PresetSceneService
from agent.service.scene.prompt_generation_service import PromptGenerationService

logger = logging.getLogger(__name__)

preset_scene_bp = Blueprint('preset_scene', __name__, url_prefix='/api/preset-scene')

# 预设场景服务实例
preset_service = PresetSceneService()

# 动态提示词生成服务实例
prompt_service = PromptGenerationService()


@preset_scene_bp.route('/industry/<industry_code>', methods=['GET'])
def get_scenes_by_industry(industry_code: str):
    """
    根据行业代码获取预设场景列表
    
    路径参数:
        industry_code: 行业代码 (如 'automobile', 'education')
    
    返回:
        {
            "success": true,
            "scenes": [
                {
                    "id": 1,
                    "scene_code": "auto_first_visit",
                    "scene_name": "客户首次到店接待",
                    "scene_description": "模拟客户首次进入4S店的接待场景",
                    "scene_tag": "hot",
                    "ai_role": "想看车的客户",
                    "user_role": "汽车销售顾问",
                    "difficulty": "easy",
                    "estimated_duration": 300,
                    "usage_count": 150
                },
                ...
            ]
        }
    """
    try:
        scenes = db_module.get_preset_scenes_by_industry(industry_code)
        
        return jsonify({
            'success': True,
            'industry_code': industry_code,
            'count': len(scenes),
            'scenes': scenes
        })
    except Exception as e:
        logger.error(f"获取预设场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/detail/<scene_code>', methods=['GET'])
def get_scene_detail(scene_code: str):
    """
    根据场景代码获取完整的预设场景信息（包含模板）
    
    路径参数:
        scene_code: 场景代码 (如 'auto_first_visit')
    
    返回:
        {
            "success": true,
            "scene": {
                "id": 1,
                "scene_code": "auto_first_visit",
                "scene_name": "客户首次到店接待",
                "scene_description": "模拟客户首次进入4S店的接待场景",
                "ai_role": "想看车的客户",
                "user_role": "汽车销售顾问",
                "difficulty": "easy",
                "estimated_duration": 300,
                "default_params": {...},
                "background_template": "...",
                "main_questions_template": "...",
                "trigger_groups_template": "...",
                "dimensions_template": "...",
                "emotion_template": "..."
            }
        }
    """
    try:
        scene = db_module.get_preset_scene_by_code(scene_code)
        
        if not scene:
            return jsonify({
                'success': False,
                'error': f'场景不存在: {scene_code}'
            }), 404
        
        # 解析 JSON 字段
        if scene.get('default_params'):
            try:
                scene['default_params'] = json.loads(scene['default_params'])
            except:
                scene['default_params'] = {}
        
        return jsonify({
            'success': True,
            'scene': scene
        })
    except Exception as e:
        logger.error(f"获取场景详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/all', methods=['GET'])
def get_all_scenes():
    """
    获取所有激活的预设场景
    
    返回:
        {
            "success": true,
            "count": 10,
            "scenes": [...]
        }
    """
    try:
        scenes = db_module.get_all_active_preset_scenes()
        
        return jsonify({
            'success': True,
            'count': len(scenes),
            'scenes': scenes
        })
    except Exception as e:
        logger.error(f"获取所有预设场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/industries', methods=['GET'])
def get_industries():
    """
    获取所有行业及其场景数量
    
    返回:
        {
            "success": true,
            "industries": [
                {"industry_code": "automobile", "scene_count": 5},
                {"industry_code": "education", "scene_count": 5}
            ]
        }
    """
    try:
        industries = db_module.get_industries_with_scene_count()
        
        return jsonify({
            'success': True,
            'count': len(industries),
            'industries': industries
        })
    except Exception as e:
        logger.error(f"获取行业列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/use/<scene_code>', methods=['POST'])
def use_preset_scene(scene_code: str):
    """
    使用预设场景（增加使用次数）
    
    路径参数:
        scene_code: 场景代码
    
    返回:
        {
            "success": true,
            "message": "使用次数已更新"
        }
    """
    try:
        success = db_module.increment_usage_count(scene_code)
        
        if success:
            return jsonify({
                'success': True,
                'message': '使用次数已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新失败'
            }), 500
    except Exception as e:
        logger.error(f"更新使用次数失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
                }), 500


@preset_scene_bp.route('/generate-from-preset', methods=['POST'])
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
        
        # 新增：获取用户配置的字段
        opening_line = data.get('opening_line')
        fixed_questions = data.get('fixed_questions')
        related_questions = data.get('related_questions')
        sop_checklist = data.get('sop_checklist')
        
        if not scene_code:
            return jsonify({
                'success': False,
                'error': '缺少场景代码参数'
            })
        
        logger.info(f"开始基于预设场景生成: {scene_code}")
        
        # 1. 加载预设场景配置
        preset_data = preset_service.load_preset_scene(scene_code)
        
        if not preset_data:
            return jsonify({
                'success': False,
                'error': f'预设场景不存在: {scene_code}'
            })
        
        # 2. 使用动态提示词生成服务生成高质量对练提示词
        logger.info(f"开始动态生成对练提示词: {preset_data.get('scene_name')}")
        
        # 准备场景数据
        scene_data = {
            'ai_role': preset_data.get('ai_role'),
            'user_role': preset_data.get('user_role'),
            'industry': preset_data.get('industry_code'),
            'scene_description': preset_data.get('scene_description'),
            'background_info': user_background or preset_data.get('background_info', ''),
            'fixed_questions': fixed_questions or preset_data.get('fixed_questions', []),
            'related_questions': related_questions or preset_data.get('related_questions', []),
        }
        
        # 判断场景类型（从预设数据或默认为 sales）
        scene_type = preset_data.get('scene_type', 'sales')
        
        full_prompt = prompt_service.generate_scene_prompt(
            scene_type=scene_type,
            scene_data=scene_data,
            use_dynamic=True
        )
        
        # 如果动态生成失败，降级为预设场景服务的生成方式
        if not full_prompt:
            logger.warning("动态生成失败，降级为预设场景服务")
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
            
            full_prompt = preset_service.build_full_prompt(scene_content)
            
            if not full_prompt:
                return jsonify({
                    'success': False,
                    'error': '提示词构建失败'
                })
            
            # 使用 scene_content 中的数据
            scene_name = f"{scene_content.industry}_{scene_content.ai_role}_场景"
            industry = scene_content.industry
            ai_role = scene_content.ai_role
            role_type = scene_content.role_type
            role_description = scene_content.role_description
        else:
            logger.info(f"动态生成对练提示词成功，长度: {len(full_prompt)} 字符")
            # 使用预设数据
            scene_name = preset_data.get('scene_name')
            industry = preset_data.get('industry_code')
            ai_role = preset_data.get('ai_role')
            role_type = preset_data.get('user_role')
            role_description = f"训练{role_type}的沟通技巧"
        
        # 3. 准备维度配置
        dimension_config = json.dumps({
            "industry": industry,
            "role_type": role_type,
            "ai_role": ai_role,
            "role_description": role_description,
            "dimensions": []
        }, ensure_ascii=False)
        
        # 3.5 处理 SOP 质检项（优先使用用户自定义，否则从预设复制）
        from database.sop_dao import sop_dao
        sop_checklist_json = None
        
        if sop_checklist:
            # 用户自定义了 SOP 质检项
            sop_checklist_json = json.dumps(sop_checklist, ensure_ascii=False)
            logger.info(f"使用用户自定义的 {len(sop_checklist)} 项 SOP 质检项")
        else:
            # 从预设场景复制
            preset_sop = sop_dao.get_preset_sop_checklist(scene_code)
            if preset_sop:
                sop_checklist_json = json.dumps(preset_sop, ensure_ascii=False)
                logger.info(f"从预设场景复制了 {len(preset_sop)} 项 SOP 质检项")
        
        # 4. 保存到数据库
        scene_id = db_module.save_scene(
            scene_name=scene_name,
            scene_prompt=full_prompt,
            dimension_config=dimension_config,
            role_type=role_type,
            role_description=role_description,
            industry=industry,
            training_goal=f"提升{role_type}的沟通能力",
            full_evaluation_prompt=full_prompt,
            sop_checklist=sop_checklist_json,
            # 新增字段
            preset_scene_code=scene_code,
            opening_line=opening_line,
            fixed_questions=json.dumps(fixed_questions, ensure_ascii=False) if fixed_questions else None,
            related_questions=json.dumps(related_questions, ensure_ascii=False) if related_questions else None,
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
                'industry': industry,
                'ai_role': ai_role,
                'role_type': role_type,
                'background_info': user_background or '',
                'prompt_length': len(full_prompt)
            }
        })
        
    except Exception as e:
        logger.error(f"基于预设场景生成失败：{str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'生成失败：{str(e)}'
        })


@preset_scene_bp.route('/preview-preset/<scene_code>', methods=['GET'])
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


@preset_scene_bp.route('/config/<scene_code>', methods=['GET'])
def get_scene_config(scene_code: str):
    """
    获取预设场景的完整配置信息（用于场景配置页面）
    包括：基本信息、固定问题、关联问题、SOP质检项等
    """
    try:
        from database.preset_scene_dao import get_preset_scene_by_code
        from database.sop_dao import SOPChecklistDAO
        
        # 获取场景基本信息
        scene = get_preset_scene_by_code(scene_code)
        if not scene:
            return jsonify({
                'success': False,
                'error': '场景不存在'
            }), 404
        
        # 获取SOP质检项
        sop_checklist = SOPChecklistDAO.get_preset_sop_checklist(scene_code) or []
        
        # 解析固定问题和关联问题
        fixed_questions = []
        related_questions = []
        
        if scene.get('fixed_questions'):
            try:
                fixed_questions = json.loads(scene['fixed_questions']) if isinstance(scene['fixed_questions'], str) else scene['fixed_questions']
            except:
                pass
        
        if scene.get('related_questions'):
            try:
                related_questions = json.loads(scene['related_questions']) if isinstance(scene['related_questions'], str) else scene['related_questions']
            except:
                pass
        
        # 构建响应数据
        config_data = {
            'scene_code': scene['scene_code'],
            'scene_name': scene['scene_name'],
            'scene_description': scene.get('scene_description', ''),
            'industry_code': scene['industry_code'],
            'ai_role': scene.get('ai_role', ''),
            'user_role': scene.get('user_role', ''),
            'difficulty': scene.get('difficulty', 'medium'),
            'estimated_duration': 600,  # 默认10分钟
            'opening_line': scene.get('opening_line', ''),
            'fixed_questions': fixed_questions,
            'related_questions': related_questions,
            'sop_checklist': sop_checklist
        }
        
        return jsonify({
            'success': True,
            'data': config_data
        })
        
    except Exception as e:
        logger.error(f"获取场景配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@preset_scene_bp.route('/quick-start/<scene_code>', methods=['POST'])
def quick_start_scene(scene_code: str):
    """
    快速启动预设场景
    
    路径参数:
        scene_code: 场景代码
    
    请求体:
        {
            "background_hint": "客户是30岁女性..." (可选)
        }
    
    返回:
        {
            "success": true,
            "scene_id": 123,
            "redirect_url": "/realtime/123",
            "message": "场景已准备就绪！"
        }
    """
    try:
        # 获取请求数据
        data = request.json or {}
        background_hint = data.get('background_hint', '').strip()
        
        # 可选的用户信息（如果有登录系统）
        org_id = data.get('org_id')
        creator_id = data.get('creator_id')
        create_name = data.get('create_name')
        
        # 从预设场景快速创建
        scene_id = db_module.create_scene_from_preset(
            preset_scene_code=scene_code,
            background_hint=background_hint if background_hint else None,
            org_id=org_id,
            creator_id=creator_id,
            create_name=create_name
        )
        
        if not scene_id:
            return jsonify({
                'success': False,
                'error': '场景创建失败，请检查场景代码是否正确'
            }), 500
        
        logger.info(f"快速启动场景成功: scene_code={scene_code}, scene_id={scene_id}")
        
        return jsonify({
            'success': True,
            'scene_id': scene_id,
            'redirect_url': f'/realtime/{scene_id}',
            'message': '场景已准备就绪！'
        })
        
    except Exception as e:
        logger.error(f"快速启动场景失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'创建失败: {str(e)}'
        }), 500