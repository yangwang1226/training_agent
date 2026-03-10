#!/usr/bin/env python3
"""
SOP 质检项配置功能测试脚本
测试 SOP 配置的前后端功能
"""

import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:5000"
TEST_SCENE_CODE = "auto_sales_001"  # 测试用的场景代码


def test_get_sop_checklist():
    """测试获取 SOP 质检清单"""
    print("\n=== 测试 1: 获取 SOP 质检清单 ===")
    
    url = f"{BASE_URL}/api/sop/checklist/{TEST_SCENE_CODE}"
    response = requests.get(url)
    
    print(f"请求 URL: {url}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if data.get('success'):
            checklist = data.get('data', {}).get('checklist', [])
            print(f"✓ 成功获取质检清单，共 {len(checklist)} 项")
            return True
        else:
            print(f"✗ 获取失败: {data.get('message')}")
            return False
    else:
        print(f"✗ 请求失败: HTTP {response.status_code}")
        return False


def test_update_sop_checklist():
    """测试更新 SOP 质检清单"""
    print("\n=== 测试 2: 更新 SOP 质检清单 ===")
    
    # 测试数据
    test_checklist = [
        {
            "item_id": "SOP001",
            "item_name": "30秒内问候客户",
            "check_type": "must_do",
            "keywords": ["你好", "欢迎", "请问"],
            "category": "接待礼仪",
            "item_desc": "客户进店后，销售顾问应在30秒内主动问候"
        },
        {
            "item_id": "SOP002",
            "item_name": "自我介绍",
            "check_type": "must_do",
            "keywords": ["我是", "我叫", "销售顾问"],
            "category": "接待礼仪",
            "item_desc": "向客户介绍自己的姓名和职位"
        },
        {
            "item_id": "SOP003",
            "item_name": "禁止贬低竞品",
            "check_type": "must_not",
            "keywords": ["垃圾", "不行", "差"],
            "category": "禁止行为",
            "item_desc": "不得使用贬低性词汇评价竞品"
        }
    ]
    
    url = f"{BASE_URL}/api/sop/checklist/{TEST_SCENE_CODE}"
    response = requests.put(
        url,
        json={"checklist": test_checklist},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"请求 URL: {url}")
    print(f"请求数据: {json.dumps(test_checklist, ensure_ascii=False, indent=2)}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if data.get('success'):
            print(f"✓ 成功更新质检清单")
            return True
        else:
            print(f"✗ 更新失败: {data.get('message')}")
            return False
    else:
        print(f"✗ 请求失败: HTTP {response.status_code}")
        try:
            error_data = response.json()
            print(f"错误信息: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"错误信息: {response.text}")
        return False


def test_validate_checklist():
    """测试验证质检清单格式"""
    print("\n=== 测试 3: 验证质检清单格式 ===")
    
    # 测试有效数据
    valid_checklist = [
        {
            "item_id": "SOP001",
            "item_name": "测试项",
            "check_type": "must_do",
            "keywords": ["测试"]
        }
    ]
    
    url = f"{BASE_URL}/api/sop/checklist/{TEST_SCENE_CODE}/validate"
    response = requests.post(
        url,
        json={"checklist": valid_checklist},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"请求 URL: {url}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if data.get('valid'):
            print(f"✓ 数据格式验证通过")
            return True
        else:
            print(f"✗ 数据格式验证失败: {data.get('message')}")
            return False
    else:
        print(f"✗ 请求失败: HTTP {response.status_code}")
        return False


def test_get_all_scenes():
    """测试获取所有场景"""
    print("\n=== 测试 4: 获取所有配置了 SOP 的场景 ===")
    
    url = f"{BASE_URL}/api/sop/scenes"
    response = requests.get(url)
    
    print(f"请求 URL: {url}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        scenes = data.get('data', [])
        print(f"✓ 成功获取场景列表，共 {len(scenes)} 个场景")
        
        for scene in scenes[:3]:  # 只显示前3个
            print(f"  - {scene.get('scene_name')} ({scene.get('scene_code')}): {scene.get('checklist_count', 0)} 个质检项")
        
        return True
    else:
        print(f"✗ 请求失败: HTTP {response.status_code}")
        return False


def test_page_access():
    """测试页面访问"""
    print("\n=== 测试 5: 访问 SOP 配置页面 ===")
    
    url = f"{BASE_URL}/sop/config"
    response = requests.get(url)
    
    print(f"请求 URL: {url}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ 页面访问成功")
        print(f"页面大小: {len(response.text)} 字节")
        return True
    else:
        print(f"✗ 页面访问失败: HTTP {response.status_code}")
        return False


def main():
    print("="*60)
    print("SOP 质检项配置功能测试")
    print("="*60)
    print(f"测试服务器: {BASE_URL}")
    print(f"测试场景: {TEST_SCENE_CODE}")
    
    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("\n✓ 服务器运行正常")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ 无法连接到服务器: {e}")
        print("请确保 Flask 应用正在运行 (python app.py)")
        sys.exit(1)
    
    # 运行测试
    tests = [
        ("页面访问", test_page_access),
        ("获取质检清单", test_get_sop_checklist),
        ("更新质检清单", test_update_sop_checklist),
        ("验证清单格式", test_validate_checklist),
        ("获取场景列表", test_get_all_scenes),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步：")
        print(f"1. 在浏览器中访问: {BASE_URL}/sop/config")
        print("2. 选择一个场景")
        print("3. 添加或编辑 SOP 质检项")
        print("4. 点击保存按钮")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
