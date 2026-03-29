"""
测试动态提示词生成服务集成
验证场景配置页面是否正确调用动态生成服务
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.scene.prompt_generation_service import PromptGenerationService


def test_custom_scene_prompt_generation():
    """测试自定义场景的动态提示词生成"""
    print("\n" + "="*80)
    print("测试 1: 自定义场景动态提示词生成")
    print("="*80)
    
    service = PromptGenerationService()
    
    # 模拟前端提交的自定义场景数据
    scene_data = {
        'ai_role': '意向购车客户',
        'user_role': '汽车销售顾问',
        'industry': '汽车行业',
        'scene_description': '客户首次进店，对SUV感兴趣，预算20万左右',
        'background_info': '客户是30岁女性，首次购车，关注安全性和外观',
        'fixed_questions': [
            {'question': '你们这款车的安全配置怎么样？', 'order': 1},
            {'question': '这个价位有什么优惠吗？', 'order': 2},
            {'question': '什么时候能提车？', 'order': 3}
        ],
        'related_questions': [
            {
                'question': '那保养费用大概多少？',
                'trigger_keywords': ['保养', '维护', '后期费用']
            }
        ]
    }
    
    print("\n场景数据:")
    print(f"  - AI角色: {scene_data['ai_role']}")
    print(f"  - 用户角色: {scene_data['user_role']}")
    print(f"  - 行业: {scene_data['industry']}")
    print(f"  - 固定问题数: {len(scene_data['fixed_questions'])}")
    
    # 动态生成提示词
    print("\n开始动态生成...")
    prompt = service.generate_scene_prompt(
        scene_type='sales',
        scene_data=scene_data,
        use_dynamic=True
    )
    
    if prompt:
        print("\n✅ 动态生成成功!")
        print(f"   提示词长度: {len(prompt)} 字符")
        print(f"\n前 500 字符预览:")
        print("-" * 80)
        print(prompt[:500])
        print("-" * 80)
        return True
    else:
        print("\n❌ 动态生成失败")
        return False


def test_preset_scene_prompt_generation():
    """测试预设场景的动态提示词生成"""
    print("\n" + "="*80)
    print("测试 2: 预设场景动态提示词生成")
    print("="*80)
    
    service = PromptGenerationService()
    
    # 模拟预设场景数据（来自数据库）
    scene_data = {
        'ai_role': '潜在客户',
        'user_role': '销售顾问',
        'industry': '教育培训',
        'scene_description': '电话邀约家长参加课程说明会',
        'background_info': '家长孩子初二，成绩中等，周末有时间',
        'fixed_questions': [
            {'question': '你们的课程效果怎么样？', 'order': 1},
            {'question': '学费是多少？', 'order': 2}
        ],
        'related_questions': []
    }
    
    print("\n场景数据:")
    print(f"  - AI角色: {scene_data['ai_role']}")
    print(f"  - 用户角色: {scene_data['user_role']}")
    
    # 动态生成提示词
    print("\n开始动态生成...")
    prompt = service.generate_scene_prompt(
        scene_type='sales',
        scene_data=scene_data,
        use_dynamic=True
    )
    
    if prompt:
        print("\n✅ 动态生成成功!")
        print(f"   提示词长度: {len(prompt)} 字符")
        return True
    else:
        print("\n❌ 动态生成失败")
        return False


def test_fallback_mechanism():
    """测试动态生成失败时的降级机制"""
    print("\n" + "="*80)
    print("测试 3: 降级机制（动态生成关闭时）")
    print("="*80)
    
    service = PromptGenerationService()
    
    scene_data = {
        'ai_role': '客户',
        'user_role': '客服',
        'industry': '电商',
        'scene_description': '处理退货申请',
        'background_info': '商品质量问题',
        'fixed_questions': [
            {'question': '为什么要退货？', 'order': 1}
        ],
        'related_questions': []
    }
    
    print("\n使用静态模板生成...")
    prompt = service.generate_scene_prompt(
        scene_type='service',
        scene_data=scene_data,
        use_dynamic=False
    )
    
    if prompt:
        print("\n✅ 静态模板生成成功（降级机制正常）!")
        print(f"   提示词长度: {len(prompt)} 字符")
        return True
    else:
        print("\n❌ 静态模板生成失败")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("动态提示词生成服务集成测试")
    print("="*80)
    
    print("\n⚠️  注意事项:")
    print("1. 请确保已配置 DASHSCOPE_API_KEY 环境变量")
    print("2. 动态生成需要调用 Qwen 模型，可能需要几秒钟")
    print("3. 如果动态生成失败，会自动降级到静态模板")
    
    results = []
    
    # 运行测试
    results.append(("自定义场景动态生成", test_custom_scene_prompt_generation()))
    results.append(("预设场景动态生成", test_preset_scene_prompt_generation()))
    results.append(("降级机制", test_fallback_mechanism()))
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！动态提示词生成服务已成功集成！")
    else:
        print("\n⚠️  部分测试失败，请检查配置和日志")
