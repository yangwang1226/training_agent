#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOP 配置功能集成测试
测试新的前端和后端集成是否正常工作
"""

import requests
import json

# 测试配置
BASE_URL = 'http://localhost:5000'
SCENE_CODE = 'auto_first_visit'


def test_get_checklist():
    """测试获取质检项"""
    print("\n=== 测试获取质检项 ===")
    url = f"{BASE_URL}/api/sop/checklist/{SCENE_CODE}"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_extract_from_text():
    """测试文字智能提取"""
    print("\n=== 测试文字智能提取 ===")
    url = f"{BASE_URL}/api/sop/extract-from-text"
    data = {
        "scene_code": SCENE_CODE,
        "text_content": """
        销售：您好，欢迎光临！我是您的专属顾问小王。请问您今天想了解哪款车型？
        
        客户：我想看看SUV，预算在20万左右。
        
        销售：好的，根据您的预算，我为您推荐几款性价比很高的SUV。请问您平时主要是自己开还是家庭用车？
        
        客户：主要是家庭用车，周末带孩子出去玩。
        
        销售：明白了。那您对空间和安全性应该比较关注。我们这边有一款非常适合家庭的SUV，空间宽敞，安全配置齐全。
        """,
        "extract_must_do": True,
        "extract_must_not": True
    }
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_save_checklist():
    """测试保存质检项"""
    print("\n=== 测试保存质检项 ===")
    url = f"{BASE_URL}/api/sop/save-checklist"
    data = {
        "scene_code": SCENE_CODE,
        "checklist": [
            {
                "item_name": "30秒内主动问候客户",
                "check_type": "must_do",
                "keywords": "您好,欢迎,问候",
                "category": "greeting"
            },
            {
                "item_name": "了解客户基本需求和预算",
                "check_type": "must_do",
                "keywords": "需求,预算,用途",
                "category": "needs_analysis"
            },
            {
                "item_name": "禁止贬低竞品",
                "check_type": "must_not",
                "keywords": "竞品,差,不好",
                "category": "product_intro"
            }
        ]
    }
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def main():
    print("\n" + "="*60)
    print("SOP 配置功能集成测试")
    print("="*60)
    
    try:
        # 测试 1: 获取质检项
        result1 = test_get_checklist()
        
        # 测试 2: 智能提取
        result2 = test_extract_from_text()
        
        # 测试 3: 保存质检项
        result3 = test_save_checklist()
        
        # 测试 4: 再次获取验证保存
        result4 = test_get_checklist()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器，请确保服务器正在运行")
        print(f"   服务器地址: {BASE_URL}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()