"""
测试快速启动功能
使用方式：python scripts/test_quick_start.py
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_quick_start_without_background():
    """测试不带背景信息的快速启动"""
    print("\n=== 测试1: 不带背景信息的快速启动 ===")
    
    scene_code = "auto_first_visit"
    url = f"{BASE_URL}/api/preset-scene/quick-start/{scene_code}"
    
    response = requests.post(url, json={})
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_quick_start_with_background():
    """测试带背景信息的快速启动"""
    print("\n=== 测试2: 带背景信息的快速启动 ===")
    
    scene_code = "auto_first_visit"
    url = f"{BASE_URL}/api/preset-scene/quick-start/{scene_code}"
    
    payload = {
        "background_hint": "客户是一位30岁的女性，想购买一辆家用SUV，预算在25-30万之间"
    }
    
    response = requests.post(url, json=payload)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_get_scene_detail(scene_id):
    """测试获取创建的场景详情"""
    print(f"\n=== 测试3: 获取场景详情 (ID: {scene_id}) ===")
    
    # 这里需要你实现获取场景详情的API，暂时跳过
    print("提示: 需要实现 GET /api/scene/{scene_id} 接口来验证场景数据")


if __name__ == "__main__":
    print("开始测试快速启动功能...")
    
    # 测试1: 不带背景
    result1 = test_quick_start_without_background()
    
    # 测试2: 带背景
    result2 = test_quick_start_with_background()
    
    print("\n=== 测试完成 ===")
    
    if result1.get('success'):
        print(f"✅ 测试1通过 - 场景ID: {result1.get('scene_id')}")
    else:
        print(f"❌ 测试1失败 - {result1.get('error')}")
    
    if result2.get('success'):
        print(f"✅ 测试2通过 - 场景ID: {result2.get('scene_id')}")
    else:
        print(f"❌ 测试2失败 - {result2.get('error')}")