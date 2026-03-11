#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 SOP API 路由
"""

import sys
import os
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def test_sop_routes():
    """测试 SOP 路由是否正确配置"""
    print("\n=== 测试 SOP API 路由 ===")
    
    with app.test_client() as client:
        # 测试新的预设场景路由
        print("\n1. 测试 GET /api/sop/checklist/preset/<scene_code>")
        response = client.get('/api/sop/checklist/preset/auto_first_visit')
        print(f"   状态码: {response.status_code}")
        print(f"   ✓ 路由存在" if response.status_code != 404 else "   ✗ 路由不存在")
        
        # 测试新的场景实例路由
        print("\n2. 测试 GET /api/sop/checklist/scene/<scene_id>")
        response = client.get('/api/sop/checklist/scene/1')
        print(f"   状态码: {response.status_code}")
        print(f"   ✓ 路由存在" if response.status_code != 404 else "   ✗ 路由不存在")
        
        # 测试保存接口
        print("\n3. 测试 POST /api/sop/save-checklist")
        response = client.post('/api/sop/save-checklist', 
                              json={'scene_id': 1, 'checklist': []})
        print(f"   状态码: {response.status_code}")
        print(f"   ✓ 路由存在" if response.status_code != 404 else "   ✗ 路由不存在")
        
        # 确认旧路由已删除
        print("\n4. 验证旧路由已删除")
        print("   测试 PUT /api/sop/checklist/<scene_code>")
        response = client.put('/api/sop/checklist/auto_first_visit',
                             json={'checklist': []})
        print(f"   状态码: {response.status_code}")
        if response.status_code == 405:
            print("   ✓ 旧路由已删除（405 Method Not Allowed）")
        else:
            print("   ✗ 旧路由仍然存在")
        
        print("\n" + "="*60)
        print("API 路由测试完成")
        print("="*60)

if __name__ == '__main__':
    test_sop_routes()