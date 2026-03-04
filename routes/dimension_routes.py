import logging
from flask import Blueprint, jsonify, request

from agent.evaluate_agent.dimension_generator import DimensionGenerator
from agent.evaluate_agent.dimension_models import DimensionConfig, SceneDimensionConfig
from agent.evaluate_agent.prompt_builder import build_evaluation_prompt
import db as db_module

logger = logging.getLogger(__name__)

dimension_bp = Blueprint('dimension', __name__, url_prefix='/api')


@dimension_bp.route('/dimensions/generate', methods=['POST'])
def generate_dimensions():
    data = request.json
    industry = data.get('industry', '')
    role_type = data.get('role_type', '')
    role_description = data.get('role_description', '')
    training_goal = data.get('training_goal', '')
    
    generator = DimensionGenerator()
    result = generator.generate_dimensions(
        industry=industry,
        role_type=role_type,
        role_description=role_description,
        training_goal=training_goal
    )
    
    if result.success:
        full_prompt = build_evaluation_prompt(result.dimensions)
        return jsonify({
            'success': True,
            'dimensions': [d.to_dict() for d in result.dimensions],
            'full_evaluation_prompt': full_prompt,
            'design_rationale': result.design_rationale
        })
    else:
        return jsonify({
            'success': False,
            'error': result.error_message
        })


@dimension_bp.route('/dimensions/templates', methods=['GET'])
def list_dimension_templates():
    generator = DimensionGenerator()
    templates = generator.list_templates()
    
    return jsonify({
        'success': True,
        'templates': templates
    })


@dimension_bp.route('/dimensions/templates/<template_name>', methods=['GET'])
def get_dimension_template(template_name):
    generator = DimensionGenerator()
    dimensions = generator.get_template(template_name)
    full_prompt = build_evaluation_prompt(dimensions)
    
    return jsonify({
        'success': True,
        'dimensions': [d.to_dict() for d in dimensions],
        'full_evaluation_prompt': full_prompt
    })


@dimension_bp.route('/scenes/<int:scene_id>/dimensions', methods=['GET'])
def get_scene_dimensions(scene_id):
    config_data = db_module.get_dimension_config(scene_id)
    
    if config_data and config_data.get('dimension_config'):
        config = SceneDimensionConfig.from_json(config_data['dimension_config'])
        return jsonify({
            'success': True,
            'dimension_config': config.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': '该场景暂无维度配置'
        })


@dimension_bp.route('/scenes/<int:scene_id>/dimensions', methods=['POST'])
def save_scene_dimensions(scene_id):
    data = request.json
    dimensions_data = data.get('dimensions', [])
    
    dimensions = [
        DimensionConfig.from_dict(d) for d in dimensions_data
    ]
    
    full_prompt = build_evaluation_prompt(dimensions)
    
    config = SceneDimensionConfig(
        scene_id=str(scene_id),
        role_type=data.get('role_type', ''),
        role_description=data.get('role_description', ''),
        industry=data.get('industry', ''),
        training_goal=data.get('training_goal', ''),
        dimensions=dimensions,
        full_evaluation_prompt=full_prompt
    )
    
    success = db_module.save_dimension_config(
        scene_id=scene_id,
        role_type=config.role_type,
        role_description=config.role_description,
        industry=config.industry,
        training_goal=config.training_goal,
        dimensions_json=config.to_json(),
        full_evaluation_prompt=full_prompt
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': '维度配置保存成功',
            'dimension_config': config.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': '保存失败'
        })


@dimension_bp.route('/scenes/<int:scene_id>/regenerate-dimensions', methods=['POST'])
def regenerate_scene_dimensions(scene_id):
    scene = db_module.get_scene_by_id(scene_id)
    if not scene:
        return jsonify({
            'success': False,
            'error': '场景不存在'
        })
    
    data = request.json or {}
    
    generator = DimensionGenerator()
    result = generator.generate_dimensions(
        industry=data.get('industry', ''),
        role_type=data.get('role_type', ''),
        role_description=data.get('role_description', ''),
        training_goal=data.get('training_goal', '')
    )
    
    if result.success:
        full_prompt = build_evaluation_prompt(result.dimensions)
        return jsonify({
            'success': True,
            'dimensions': [d.to_dict() for d in result.dimensions],
            'full_evaluation_prompt': full_prompt,
            'design_rationale': result.design_rationale
        })
    else:
        return jsonify({
            'success': False,
            'error': result.error_message
        })


@dimension_bp.route('/dimensions/build-prompt', methods=['POST'])
def build_dimension_prompt():
    data = request.json
    dimensions_data = data.get('dimensions', [])
    
    dimensions = [
        DimensionConfig.from_dict(d) for d in dimensions_data
    ]
    
    full_prompt = build_evaluation_prompt(dimensions)
    
    return jsonify({
        'success': True,
        'full_evaluation_prompt': full_prompt
    })
