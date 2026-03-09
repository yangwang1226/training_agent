"""
预设场景服务测试脚本

演示如何基于预设场景（如 auto_first_visit）生成完整的场景提示词
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.service.scene.preset_scene_service import PresetSceneService
import json


def test_auto_first_visit():
    """
    测试：基于汽车销售预设场景生成提示词
    
    场景：auto_first_visit（客户首次到店接待）
    """
    print("=" * 80)
    print("测试：基于预设场景 auto_first_visit 生成场景提示词")
    print("=" * 80)
    print()
    
    # 1. 初始化服务
    service = PresetSceneService()
    
    # 2. 场景代码
    scene_code = "auto_first_visit"
    
    # 3. 用户补充的背景信息（可选）
    user_background = """
    客户是一位 35 岁的公司中层管理人员，家有两个孩子（8岁和5岁）。
    预算在 20-30 万之间，主要关注 SUV 车型，用途是家庭出行。
    客户比较注重安全性能和空间，正在对比传统豪华燃油车与新能源车。
    客户性格比较理性，不太容易被推销话术打动，更看重实际的产品价值。
    """
    
    # 4. 用户自定义需求（可选）
    custom_requirements = """
    希望 AI 模拟的客户能够：
    1. 主动询问车辆的安全配置细节
    2. 对比同价位的竞品车型
    3. 关注新能源车的续航和充电问题
    """
    
    print("【步骤 1】加载预设场景...")
    preset_data = service.load_preset_scene(scene_code)
    if preset_data:
        print(f"✅ 预设场景加载成功: {preset_data.get('scene_name')}")
        print(f"   - AI 角色: {preset_data.get('ai_role')}")
        print(f"   - 用户角色: {preset_data.get('user_role')}")
        print(f"   - 难度: {preset_data.get('difficulty')}")
        print()
    else:
        print("❌ 预设场景加载失败")
        return
    
    print("【步骤 2】生成个性化场景内容...")
    scene_content = service.generate_from_preset(
        scene_code=scene_code,
        user_background=user_background,
        custom_requirements=custom_requirements
    )
    
    if not scene_content:
        print("❌ 场景内容生成失败")
        return
    
    print("✅ 场景内容生成成功!")
    print()
    
    print("【步骤 3】查看生成的内容...")
    print()
    
    print("📍 背景信息:")
    print("-" * 80)
    print(scene_content.background_info)
    print()
    
    print("❓ 主问题列表:")
    print("-" * 80)
    for q in scene_content.main_questions:
        print(f"{q.order}. {q.question}")
    print()
    
    print("🔗 关联问题分组:")
    print("-" * 80)
    for group in scene_content.trigger_groups:
        keywords_str = "、".join(group.trigger_keywords)
        print(f"\n{group.group_name} (触发关键词: {keywords_str})")
        for q in group.questions:
            print(f"  {q.order}. {q.question}")
    print()
    
    print("📊 考核维度:")
    print("-" * 80)
    for dim in scene_content.dimensions:
        print(f"\n{dim.dimension_name} (权重: {dim.weight*100:.0f}%)")
        for criterion, desc in dim.sub_criteria.items():
            print(f"  - {criterion}: {desc}")
    print()
    
    print("😊 情绪画像:")
    print("-" * 80)
    print(f"情绪类型: {scene_content.emotion_profile.emotion_type}")
    print(f"情绪描述: {scene_content.emotion_profile.emotion_description}")
    print(f"说话风格: {scene_content.emotion_profile.speaking_style}")
    print(f"沟通态度: {scene_content.emotion_profile.attitude}")
    print()
    
    print("【步骤 4】构建完整提示词...")
    full_prompt = service.build_full_prompt(scene_content)
    
    # 保存到文件
    output_file = "scene_prompt/auto_first_visit_generated.txt"
    os.makedirs("scene_prompt", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_prompt)
    
    print(f"✅ 完整提示词已保存到: {output_file}")
    print()
    
    print("【完整提示词预览】")
    print("=" * 80)
    print(full_prompt)
    print("=" * 80)
    print()
    
    print("✅ 测试完成！")


def test_without_user_background():
    """
    测试：不提供用户背景信息（纯预设场景）
    """
    print("=" * 80)
    print("测试：纯预设场景生成（无用户背景）")
    print("=" * 80)
    print()
    
    service = PresetSceneService()
    scene_code = "auto_first_visit"
    
    print("生成场景内容（无用户背景）...")
    scene_content = service.generate_from_preset(scene_code=scene_code)
    
    if scene_content:
        print("✅ 生成成功（使用预设场景的默认内容）")
        print()
        print("背景信息:")
        print(scene_content.background_info[:200] + "...")
        print()
    else:
        print("❌ 生成失败")


def compare_manual_vs_generated():
    """
    对比：手工模板 vs LLM 生成
    """
    print("=" * 80)
    print("对比：手工模板 vs LLM 生成内容")
    print("=" * 80)
    print()
    
    service = PresetSceneService()
    scene_code = "auto_first_visit"
    
    # 加载预设场景
    preset_data = service.load_preset_scene(scene_code)
    
    print("【手工模板部分（骨架，固定不变）】")
    print("-" * 80)
    print("✅ 对话控制机制")
    print("✅ 结束流程")
    print("✅ 关联问题触发规则")
    print("✅ 防御性对话设计")
    print()
    
    print("【LLM 生成部分（血肉，动态生成）】")
    print("-" * 80)
    
    # 生成内容
    scene_content = service.generate_from_preset(
        scene_code=scene_code,
        user_background="客户预算20万，关注SUV，家庭使用"
    )
    
    if scene_content:
        print("✅ 融合用户背景的背景信息")
        print(f"   示例: {scene_content.background_info[:100]}...")
        print()
        print("✅ 个性化的主问题列表")
        print(f"   生成了 {len(scene_content.main_questions)} 个问题")
        print()
        print("✅ 个性化的关联问题分组")
        print(f"   生成了 {len(scene_content.trigger_groups)} 个分组")
        print()
        print("✅ 角色情绪画像")
        print(f"   情绪类型: {scene_content.emotion_profile.emotion_type}")
        print()
    
    print("【预设场景贡献（基础，保底数据）】")
    print("-" * 80)
    print(f"✅ 行业、角色、场景基本信息")
    print(f"   - 行业: {preset_data.get('industry_code')}")
    print(f"   - AI 角色: {preset_data.get('ai_role')}")
    print(f"   - 用户角色: {preset_data.get('user_role')}")
    print()
    print("✅ 默认主问题（LLM 失败时的兜底）")
    print("✅ 默认关联问题（LLM 失败时的兜底）")
    print("✅ 默认考核维度")
    print()


if __name__ == "__main__":
    print("\n")
    print("🚀 预设场景服务测试")
    print("=" * 80)
    print()
    
    # 测试 1: 完整流程（带用户背景）
    test_auto_first_visit()
    
    print("\n" * 2)
    
    # 测试 2: 无用户背景
    test_without_user_background()
    
    print("\n" * 2)
    
    # 测试 3: 对比分析
    compare_manual_vs_generated()
    
    print("\n")
    print("=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)
