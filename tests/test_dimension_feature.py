"""
能力画像维度动态化功能测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.evaluate_agent.dimension_generator import DimensionGenerator
from agent.evaluate_agent.dimension_models import DimensionConfig, SceneDimensionConfig
from agent.evaluate_agent.prompt_builder import build_evaluation_prompt
import json


def test_dimension_generator():
    print("=" * 60)
    print("测试1: 维度生成器 - 销售场景")
    print("=" * 60)
    
    generator = DimensionGenerator()
    
    result = generator.generate_dimensions(
        industry="教育",
        role_type="家长",
        role_description="一位关心孩子学习的家长，对孩子成绩不太满意",
        training_goal="提升教师与家长的沟通能力"
    )
    
    print(f"生成成功: {result.success}")
    print(f"设计理由: {result.design_rationale}")
    print("\n生成的维度:")
    for dim in result.dimensions:
        print(f"  - {dim.dimension_name} (权重: {dim.weight*100:.0f}%)")
        for criterion, desc in dim.sub_criteria.items():
            print(f"      {criterion}: {desc}")
    
    return result


def test_preset_templates():
    print("\n" + "=" * 60)
    print("测试2: 预设模板")
    print("=" * 60)
    
    generator = DimensionGenerator()
    templates = generator.list_templates()
    
    print("可用模板列表:")
    for t in templates:
        print(f"  - {t['key']}: {t['name']} - {t['description']}")
    
    print("\n获取销售模板:")
    sales_dims = generator.get_template("sales")
    for dim in sales_dims:
        print(f"  - {dim.dimension_name} (权重: {dim.weight*100:.0f}%)")
    
    return sales_dims


def test_prompt_builder():
    print("\n" + "=" * 60)
    print("测试3: 提示词构建")
    print("=" * 60)
    
    dimensions = [
        DimensionConfig(
            dimension_name="沟通技巧",
            weight=0.25,
            sub_criteria={
                "表达清晰": "语言表达是否清晰",
                "倾听能力": "是否认真倾听"
            },
            score_levels={
                "优秀": "表达精准",
                "良好": "表达清晰",
                "及格": "基本表达清楚",
                "不及格": "表达混乱"
            }
        ),
        DimensionConfig(
            dimension_name="专业知识",
            weight=0.25,
            sub_criteria={
                "知识掌握": "专业知识掌握程度",
                "知识运用": "能否运用知识解决问题"
            },
            score_levels={
                "优秀": "专业精通",
                "良好": "知识扎实",
                "及格": "基本掌握",
                "不及格": "知识薄弱"
            }
        )
    ]
    
    prompt = build_evaluation_prompt(dimensions)
    print("生成的评估提示词:")
    print("-" * 40)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    return prompt


def test_scene_dimension_config():
    print("\n" + "=" * 60)
    print("测试4: 场景维度配置序列化")
    print("=" * 60)
    
    dimensions = [
        DimensionConfig(
            dimension_name="沟通技巧",
            weight=0.20,
            sub_criteria={"表达清晰": "语言表达是否清晰"},
            score_levels={"优秀": "表达精准", "良好": "表达清晰"}
        )
    ]
    
    config = SceneDimensionConfig(
        scene_id="test_scene_001",
        role_type="客户",
        role_description="潜在客户",
        industry="教育",
        training_goal="提升销售能力",
        dimensions=dimensions,
        full_evaluation_prompt="测试提示词"
    )
    
    json_str = config.to_json()
    print("序列化后的JSON:")
    print(json_str[:300] + "..." if len(json_str) > 300 else json_str)
    
    parsed_config = SceneDimensionConfig.from_json(json_str)
    print(f"\n反序列化成功: {parsed_config.scene_id}")
    print(f"维度数量: {len(parsed_config.dimensions)}")
    
    return config


def test_api_endpoints():
    print("\n" + "=" * 60)
    print("测试5: API端点测试 (需要启动服务)")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    import requests
    
    try:
        response = requests.get(f"{base_url}/api/dimensions/templates", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("模板列表API测试成功:")
            for t in data.get('templates', []):
                print(f"  - {t['key']}: {t['name']}")
        else:
            print(f"API返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("服务未启动，跳过API测试")
        print("请先启动服务: python app.py")
    except Exception as e:
        print(f"API测试失败: {str(e)}")


def main():
    print("\n" + "=" * 60)
    print("能力画像维度动态化功能测试")
    print("=" * 60)
    
    test_dimension_generator()
    test_preset_templates()
    test_prompt_builder()
    test_scene_dimension_config()
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n下一步:")
    print("1. 执行数据库迁移脚本: scripts/migration_add_dimension_config.sql")
    print("2. 启动服务: python app.py")
    print("3. 调用API测试维度生成功能")


if __name__ == "__main__":
    main()
