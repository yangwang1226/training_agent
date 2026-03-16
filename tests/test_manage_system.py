# -*- coding: utf-8 -*-
"""
测试后台管理系统功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_page_access():
    """测试页面访问"""
    print("\n=== 测试 1: 页面访问 ===")
    
    pages = [
        ('/manage_system/', '仪表盘'),
        ('/manage_system/scenes', '场景管理'),
    ]
    
    for url, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{url}")
            if response.status_code == 200:
                print(f"✓ {name}页面访问成功")
            else:
                print(f"✗ {name}页面访问失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {name}页面访问异常: {e}")

def test_get_scenes():
    """测试获取场景列表"""
    print("\n=== 测试 2: 获取场景列表 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/manage_system/api/scenes")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                scenes = data.get('data', [])
                print(f"✓ 获取成功，共 {len(scenes)} 个场景")
                
                if scenes:
                    print("\n前3个场景:")
                    for scene in scenes[:3]:
                        print(f"  - ID: {scene.get('id')}, 名称: {scene.get('scene_name')}, 状态: {scene.get('status')}")
            else:
                print(f"✗ 获取失败: {data.get('message')}")
        else:
            print(f"✗ 请求失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def test_get_scene_detail():
    """测试获取场景详情"""
    print("\n=== 测试 3: 获取场景详情 ===")
    
    # 先获取场景列表
    try:
        response = requests.get(f"{BASE_URL}/manage_system/api/scenes")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                scene_id = data['data'][0]['id']
                
                # 获取详情
                detail_response = requests.get(f"{BASE_URL}/manage_system/api/scenes/{scene_id}")
                print(f"状态码: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get('success'):
                        scene = detail_data.get('data', {})
                        print(f"✓ 获取成功")
                        print(f"  场景名称: {scene.get('scene_name')}")
                        print(f"  行业: {scene.get('industry', '-')}")
                        print(f"  角色: {scene.get('role_type', '-')}")
                        print(f"  创建时间: {scene.get('created_time')}")
                    else:
                        print(f"✗ 获取失败: {detail_data.get('message')}")
                else:
                    print(f"✗ 请求失败: HTTP {detail_response.status_code}")
            else:
                print("⚠ 没有可用场景，跳过详情测试")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def test_stats_overview():
    """测试统计概览"""
    print("\n=== 测试 4: 统计概览 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/manage_system/api/stats/overview")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('data', {})
                print(f"✓ 获取成功")
                print(f"  场景总数: {stats.get('total_scenes', 0)}")
                print(f"  预设场景: {stats.get('preset_scenes', 0)}")
                print(f"  自定义场景: {stats.get('custom_scenes', 0)}")
                print(f"  草稿: {stats.get('draft_scenes', 0)}")
            else:
                print(f"✗ 获取失败: {data.get('message')}")
        else:
            print(f"✗ 请求失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

if __name__ == '__main__':
    print("="*60)
    print("后台管理系统功能测试")
    print("="*60)
    print(f"\n测试服务器: {BASE_URL}")
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("\n⚠ 警告: 服务器可能未运行，请先启动 Flask 应用")
            sys.exit(1)
    except:
        print("\n❌ 错误: 无法连接到服务器，请确保 Flask 应用正在运行")
        sys.exit(1)
    
    # 运行测试
    tests = [
        ("页面访问", test_page_access),
        ("获取场景列表", test_get_scenes),
        ("获取场景详情", test_get_scene_detail),
        ("统计概览", test_stats_overview),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            test_func()
            results[test_name] = True
        except Exception as e:
            print(f"\n✗ 测试 '{test_name}' 执行失败: {e}")
            results[test_name] = False
    
    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n通过: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)