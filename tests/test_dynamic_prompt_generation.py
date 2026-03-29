"""
测试动态提示词生成功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.scene.prompt_generation_service import PromptGenerationService
import json


def test_sales_scene_prompt():
    """
    测试销售场景提示词生成
    """
    print("\n" + "=" * 60)
    print("测试1: 销售场景提示词生成")
    print("=" * 60)
    
    service = PromptGenerationService()
    
    # 准备测试数据
    scene_data = {
        'scene_name': '汽车销售-首次到店',
        'scene_type': 'sales',
        'ai_role': '潜在购车客户',
        'user_role': '汽车销售顾问',
        'industry': '汽车销售',
        'scene_description': '客户首次到4S店看车',
        'background_info': '客户是30岁的女性，想购买一辆家用SUV，预算25-30万',
        'fixed_questions': [
            {'question': '价格多少？', 'order': 1},
            {'question': '油耗怎么样？', 'order': 2},
            {'question': '有什么优惠？', 'order': 3}
        ],
        'related_questions': [
            {'question': '优惠到什么时候结束？', 'trigger_keywords': ['优惠', '折扣']}
        ],
        'purchase_intent': '一般'
    }
    
    # 测试动态生成
    print("\n[动态生成模式]")
    prompt = service.generate_scene_prompt(
        scene_type='sales',
        scene_data=scene_data,
        use_dynamic=True
    )
    
    if prompt:
        print(f"✅ 动态生成成功")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"\n前500字符预览:")
        print("-" * 60)
        print(prompt[:500])
        print("...")
        print("-" * 60)
    else:
        print("❌ 动态生成失败")
    
    # 测试静态模板降级
    print("\n[静态模板模式]")
    prompt_static = service.generate_scene_prompt(
        scene_type='sales',
        scene_data=scene_data,
        use_dynamic=False
    )
    
    if prompt_static:
        print(f"✅ 静态模板生成成功")
        print(f"提示词长度: {len(prompt_static)} 字符")
    else:
        print("❌ 静态模板生成失败")


def test_service_scene_prompt():
    """
    测试服务场景提示词生成
    """
    print("\n" + "=" * 60)
    print("测试2: 服务场景提示词生成")
    print("=" * 60)
    
    service = PromptGenerationService()
    
    # 准备测试数据
    scene_data = {
        'scene_name': 'SaaS产品-功能故障',
        'scene_type': 'service',
        'ai_role': 'VIP客户',
        'user_role': '技术支持专员',
        'industry': 'SaaS软件',
        'scene_description': '客户反馈产品关键功能无法使用',
        'background_info': '企业付费用户，使用产品2年，关键报表功能无法导出',
        'fixed_questions': [
            {'question': '为什么会出现这个问题？', 'order': 1},
            {'question': '什么时候能修复？', 'order': 2},
            {'question': '数据会丢失吗？', 'order': 3}
        ],
        'related_questions': [],
        'problem_severity': '严重',
        'core_problem': '报表导出功能异常',
        'additional_concerns': ['数据安全', '业务影响', '是否需要赔偿']
    }
    
    # 测试动态生成
    print("\n[动态生成模式]")
    prompt = service.generate_scene_prompt(
        scene_type='service',
        scene_data=scene_data,
        use_dynamic=True
    )
    
    if prompt:
        print(f"✅ 动态生成成功")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"\n前500字符预览:")
        print("-" * 60)
        print(prompt[:500])
        print("...")
        print("-" * 60)
    else:
        print("❌ 动态生成失败")


def test_data_extraction():
    """
    测试数据提取功能
    """
    print("\n" + "=" * 60)
    print("测试3: 数据提取功能")
    print("=" * 60)
    
    service = PromptGenerationService()
    
    # 测试 fixed_questions 提取
    fixed_questions_json = json.dumps([
        {'question': '问题1', 'order': 1},
        {'question': '问题2', 'order': 2}
    ], ensure_ascii=False)
    
    questions = service._extract_main_questions(fixed_questions_json)
    print(f"\n固定问题提取: {questions}")
    assert len(questions) == 2, "应该提取到2个问题"
    print("✅ 固定问题提取测试通过")
    
    # 测试 related_questions 提取
    related_questions_json = json.dumps([
        {'question': '关联问题1', 'trigger_keywords': ['关键词1', '关键词2']},
        {'question': '关联问题2', 'trigger_keywords': ['关键词3']}
    ], ensure_ascii=False)
    
    rules = service._extract_trigger_rules(related_questions_json)
    print(f"\n关联问题规则提取: {rules}")
    assert len(rules) > 0, "应该提取到关联规则"
    print("✅ 关联问题提取测试通过")


if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# 动态提示词生成功能测试")
    print("#" * 60)
    
    try:
        test_data_extraction()
        test_sales_scene_prompt()
        test_service_scene_prompt()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        print("\n提示：")
        print("1. 如果动态生成失败，请检查 .env 中的 OPENAI_API_KEY 配置")
        print("2. 静态模板作为降级方案，应该始终能够生成")
        print("3. 可以通过 /api/scene-prompt/preview 接口测试完整流程")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()