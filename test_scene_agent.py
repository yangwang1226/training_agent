#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
场景智能体测试脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("=" * 50)
    print("测试模块导入...")
    print("=" * 50)
    
    try:
        from agent.service.scene import SceneAgent
        print("✓ SceneAgent 导入成功")
    except Exception as e:
        print(f"✗ SceneAgent 导入失败：{e}")
        return False
    
    try:
        from agent.service.scene.models import SceneContent, Dimension, MainQuestion
        print("✓ SceneContent 导入成功")
    except Exception as e:
        print(f"✗ SceneContent 导入失败：{e}")
        return False
    
    try:
        from agent.service.scene.assessment_service import SceneAssessmentService
        print("✓ SceneAssessmentService 导入成功")
    except Exception as e:
        print(f"✗ SceneAssessmentService 导入失败：{e}")
        return False
    
    try:
        from routes.scene_create_routes import scene_create_bp
        print("✓ scene_create_bp 导入成功")
    except Exception as e:
        print(f"✗ scene_create_bp 导入失败：{e}")
        return False
    
    print("=" * 50)
    print("所有模块导入测试通过!")
    print("=" * 50)
    return True

def test_scene_agent():
    """测试 SceneAgent 基本功能"""
    print("\n" + "=" * 50)
    print("测试 SceneAgent 基本功能...")
    print("=" * 50)
    
    try:
        from agent.service.scene import SceneAgent
        
        agent = SceneAgent()
        print("✓ SceneAgent 创建成功")
        
        # 测试对话
        response = agent.chat("我想创建一个汽车销售的培训场景")
        print(f"✓ 对话测试成功，响应：{response.get('content', '')[:50]}...")
        
        # 测试状态
        state = agent.state
        print(f"✓ 状态检查成功，行业：{state.industry}")
        
        print("=" * 50)
        print("SceneAgent 功能测试通过!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"✗ SceneAgent 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试功能
    if not test_scene_agent():
        success = False
    
    if success:
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败!")
        sys.exit(1)
