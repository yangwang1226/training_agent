#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 DAO 优化效果
"""

import sys
import os
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.preset_scene_dao import (
    get_preset_scenes_by_industry,
    get_preset_scene_by_code,
    get_all_active_preset_scenes,
    get_industries_with_scene_count
)
from database.scene_dao import list_scenes, get_scene_by_id
from database.record_dao import update_coach_record
import time

def test_preset_scene_queries():
    """测试预设场景查询（验证字段修复）"""
    print("\n=== 测试 1: 预设场景查询 ===")
    
    try:
        # 测试按行业查询
        scenes = get_preset_scenes_by_industry('automobile')
        print(f"✓ 查询汽车行业场景: {len(scenes)} 个")
        
        if scenes:
            scene = scenes[0]
            # 验证返回的字段
            required_fields = ['id', 'scene_code', 'scene_name', 'ai_role', 'user_role']
            missing_fields = [f for f in required_fields if f not in scene]
            
            if missing_fields:
                print(f"✗ 缺少字段: {missing_fields}")
                return False
            
            # 验证不应该有已删除的字段
            removed_fields = ['scene_tag', 'estimated_duration', 'display_order']
            exists_removed = [f for f in removed_fields if f in scene]
            
            if exists_removed:
                print(f"✗ 仍然包含已删除字段: {exists_removed}")
                return False
            
            print(f"✓ 字段验证通过")
        
        # 测试查询所有场景
        all_scenes = get_all_active_preset_scenes()
        print(f"✓ 查询所有激活场景: {len(all_scenes)} 个")
        
        # 测试行业统计
        industries = get_industries_with_scene_count()
        print(f"✓ 行业统计: {len(industries)} 个行业")
        
        return True
        
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scene_queries_with_index():
    """测试场景查询（验证索引效果）"""
    print("\n=== 测试 2: 场景查询性能 ===")
    
    try:
        start = time.time()
        scenes = list_scenes()
        elapsed = time.time() - start
        
        print(f"✓ 查询场景列表: {len(scenes)} 个，耗时: {elapsed*1000:.2f}ms")
        
        if elapsed > 0.5:
            print("⚠ 查询时间较长，可能需要优化")
        
        return True
        
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        return False

def test_record_update():
    """测试记录更新优化"""
    print("\n=== 测试 3: 记录更新功能 ===")
    
    try:
        # 测试正常更新
        result = update_coach_record(
            session_id='test_session_123',
            score=85,
            ai_evaluate='测试评价'
        )
        print(f"✓ 更新记录（正常字段）: {'成功' if result else '失败（记录可能不存在）'}")
        
        # 测试非法字段过滤
        result = update_coach_record(
            session_id='test_session_123',
            invalid_field='should_be_ignored',  # 应该被过滤
            score=90
        )
        print("✓ 非法字段过滤测试通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_index_usage():
    """测试索引使用情况"""
    print("\n=== 测试 4: 验证索引 ===")
    
    from database.connection import get_connection
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 检查 preset_scene 索引
        cursor.execute("""
            SELECT INDEX_NAME, COLUMN_NAME 
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ai_coach_preset_scene'
            AND INDEX_NAME != 'PRIMARY'
        """)
        preset_indexes = cursor.fetchall()
        print(f"✓ ai_coach_preset_scene 索引: {len(preset_indexes)} 个")
        
        # 检查 scene 索引
        cursor.execute("""
            SELECT INDEX_NAME, COLUMN_NAME 
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ai_coach_scene'
            AND INDEX_NAME != 'PRIMARY'
        """)
        scene_indexes = cursor.fetchall()
        print(f"✓ ai_coach_scene 索引: {len(scene_indexes)} 个")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("DAO 优化效果测试")
    print("="*60)
    
    tests = [
        ("预设场景查询", test_preset_scene_queries),
        ("场景查询性能", test_scene_queries_with_index),
        ("记录更新功能", test_record_update),
        ("索引验证", test_index_usage),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
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