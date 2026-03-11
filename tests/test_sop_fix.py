#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 SOP 质检项配置修复
验证模板和实例分离的设计
"""

import sys
import os
import io

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.sop_dao import sop_dao
from database.scene_dao import save_scene
import json

def test_preset_sop():
    """测试获取预设场景的 SOP（只读）"""
    print("\n=== 测试 1: 获取预设场景的默认 SOP ===")
    scene_code = 'auto_first_visit'
    
    checklist = sop_dao.get_preset_sop_checklist(scene_code)
    
    if checklist:
        print(f"✓ 成功获取预设 SOP: {len(checklist)} 项")
        for item in checklist[:2]:  # 只显示前2项
            print(f"  - {item.get('item_name')}: {item.get('check_type')}")
        return True
    else:
        print("✗ 未找到预设 SOP")
        return False

def test_create_scene_with_sop():
    """测试创建场景时复制 SOP"""
    print("\n=== 测试 2: 创建场景并复制 SOP ===")
    
    # 获取预设的 SOP
    scene_code = 'auto_first_visit'
    preset_sop = sop_dao.get_preset_sop_checklist(scene_code)
    
    if not preset_sop:
        print("⚠ 预设场景没有 SOP，跳过测试")
        return True
    
    # 创建场景实例
    sop_json = json.dumps(preset_sop, ensure_ascii=False)
    scene_id = save_scene(
        scene_name="测试场景_SOP复制",
        scene_prompt="测试提示词",
        sop_checklist=sop_json,
        status=2
    )
    
    if scene_id:
        print(f"✓ 场景创建成功: ID={scene_id}")
        
        # 验证 SOP 是否正确复制
        scene_sop = sop_dao.get_scene_sop_checklist(scene_id)
        if scene_sop:
            print(f"✓ 成功获取场景实例 SOP: {len(scene_sop)} 项")
            return True
        else:
            print("✗ 场景实例 SOP 为空")
            return False
    else:
        print("✗ 场景创建失败")
        return False

def test_modify_scene_sop():
    """测试修改场景实例的 SOP"""
    print("\n=== 测试 3: 修改场景实例的 SOP ===")
    
    # 创建测试场景
    scene_id = save_scene(
        scene_name="测试场景_SOP修改",
        scene_prompt="测试提示词",
        status=2
    )
    
    if not scene_id:
        print("✗ 场景创建失败")
        return False
    
    # 添加自定义 SOP
    custom_sop = [
        {
            'item_id': 'CUSTOM001',
            'item_name': '用户自定义质检项',
            'check_type': 'must_do',
            'keywords': '自定义,测试',
            'category': 'custom'
        }
    ]
    
    success = sop_dao.save_scene_sop_checklist(scene_id, custom_sop)
    
    if success:
        print(f"✓ 成功保存自定义 SOP 到场景 {scene_id}")
        
        # 验证
        saved_sop = sop_dao.get_scene_sop_checklist(scene_id)
        if saved_sop and len(saved_sop) == 1:
            print(f"✓ 验证成功: {saved_sop[0]['item_name']}")
            return True
        else:
            print("✗ 验证失败")
            return False
    else:
        print("✗ 保存失败")
        return False

def test_preset_immutable():
    """测试预设场景的 SOP 不受影响"""
    print("\n=== 测试 4: 验证预设 SOP 不可修改 ===")
    
    scene_code = 'auto_first_visit'
    
    # 获取原始 SOP
    original_sop = sop_dao.get_preset_sop_checklist(scene_code)
    
    if not original_sop:
        print("⚠ 预设场景没有 SOP，跳过测试")
        return True
    
    original_count = len(original_sop)
    
    # 创建场景实例并修改
    sop_json = json.dumps(original_sop, ensure_ascii=False)
    scene_id = save_scene(
        scene_name="测试场景_验证隔离",
        scene_prompt="测试提示词",
        sop_checklist=sop_json,
        status=2
    )
    
    # 修改场景实例的 SOP
    modified_sop = original_sop + [{
        'item_id': 'TEST001',
        'item_name': '新增的测试项',
        'check_type': 'must_do',
        'keywords': '测试',
        'category': 'test'
    }]
    
    sop_dao.save_scene_sop_checklist(scene_id, modified_sop)
    
    # 再次获取预设 SOP
    preset_sop_after = sop_dao.get_preset_sop_checklist(scene_code)
    
    if preset_sop_after and len(preset_sop_after) == original_count:
        print(f"✓ 预设 SOP 保持不变: {original_count} 项")
        print("✓ 验证通过: 预设模板和用户实例完全隔离")
        return True
    else:
        print("✗ 预设 SOP 被意外修改")
        return False

if __name__ == '__main__':
    print("="*60)
    print("SOP 质检项配置 - 模板与实例分离测试")
    print("="*60)
    
    tests = [
        ("获取预设SOP", test_preset_sop),
        ("创建场景复制SOP", test_create_scene_with_sop),
        ("修改场景实例SOP", test_modify_scene_sop),
        ("验证预设不可变", test_preset_immutable),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    sys.exit(0 if passed == total else 1)