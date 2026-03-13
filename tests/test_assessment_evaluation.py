#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试评估功能

用法:
    python tests/test_assessment_evaluation.py <session_id>
    
示例:
    python tests/test_assessment_evaluation.py 85609242-8440-4079-9268-bfbdc087a43e
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保正确的导入路径
import sys
os.chdir(str(project_root))

from database.record_dao import get_coach_record_by_session_id
import db as db_module
from agent.service.scene.assessment_service import assessment_service as scene_assessment_service
from agent.service.scene.async_assessment_processor import get_async_processor

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_section(title):
    """打印章节"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def test_assessment_with_mock_data():
    """使用mock数据测试评估流程（完全模拟对练结束后的流程）"""
    import time
    import uuid
    
    print_header("模拟对练结束后的评估流程测试")
    
    # Mock数据
    session_id = str(uuid.uuid4())
    scene_id = 15
    user_id = 1
    audio_file_path = "test_audio_mock.wav"
    call_duration = 180
    
    # Mock对话内容（word_content）- 采用真实使用功能时保存对练记录的数据结构
    word_content = json.dumps([
        {
            "role": "user",
            "content": "您好，我是XX汽车4S店的销售顾问，欢迎光临！",
            "timestamp": "10:00:01"
        },
        {
            "role": "ai",
            "content": "你好，我想了解一下你们的新款SUV车型。",
            "timestamp": "10:00:05"
        },
        {
            "role": "user",
            "content": "好的，我们刚推出的XX系列SUV非常受欢迎。这款车配备了2.0T涡轮增压发动机，动力强劲，油耗也相对较低。您平时主要在市区还是高速行驶比较多？",
            "timestamp": "10:00:10"
        },
        {
            "role": "ai",
            "content": "主要是市区通勤，偶尔周末出去自驾游。",
            "timestamp": "10:00:15"
        },
        {
            "role": "user",
            "content": "那这款车非常适合您。它的底盘调校偏向舒适，市区驾驶很平稳。而且它的智能驾驶辅助系统在高速上也能帮您减轻疲劳。您对价格有什么考虑吗？",
            "timestamp": "10:00:20"
        },
        {
            "role": "ai",
            "content": "预算大概在25万左右。",
            "timestamp": "10:00:25"
        },
        {
            "role": "user",
            "content": "我们这款车现在的优惠活动力度很大，正好在您的预算范围内。而且我们还提供三年免息贷款，首付只要30%。您看什么时候方便来店里试驾一下？",
            "timestamp": "10:00:30"
        },
        {
            "role": "ai",
            "content": "好的，这周末我有时间。",
            "timestamp": "10:00:35"
        },
        {
            "role": "user",
            "content": "太好了，那我帮您预约一下周六上午10点的试驾，您看可以吗？",
            "timestamp": "10:00:40"
        },
        {
            "role": "ai",
            "content": "可以。",
            "timestamp": "10:00:45"
        },
        {
            "role": "user",
            "content": "好的，那我们周六见！我会提前准备好车辆和资料，到时候您可以详细了解这款车的各项配置。",
            "timestamp": "10:00:50"
        }
    ], ensure_ascii=False)
    
    print(f"\nMock数据：")
    print(f"  Session ID: {session_id}")
    print(f"  Scene ID: {scene_id}")
    print(f"  User ID: {user_id}")
    print(f"  音频文件: {audio_file_path}")
    print(f"  通话时长: {call_duration}秒")
    
    # 解析JSON格式的word_content并统计对话轮次
    messages = json.loads(word_content)
    print(f"  对话轮次: {len(messages)}")
    print(f"  数据格式: JSON (真实使用功能时的数据结构）")
    
    # 步骤1: 获取场景配置
    print_section("1. 获取场景配置")
    try:
        scene = db_module.get_scene_by_id(scene_id)
        
        print(f"[OK] 场景信息获取成功")
        print(f"  场景名称: {scene.get('scene_name', 'N/A')}")
        print(f"  行业: {scene.get('industry', 'N/A')}")
        print(f"  AI角色: {scene.get('role_type', 'N/A')}")
        
        industry = scene.get('industry', '')
        role_type = scene.get('role_type', '')
        role_description = scene.get('role_description', '')
        
        # 获取维度配置
        dimension_config = scene.get('dimension_config')
        dimensions = []
        if dimension_config:
            try:
                config_data = json.loads(dimension_config)
                dimensions = config_data.get('dimensions', [])
                print(f"  维度数量: {len(dimensions)}")
                if dimensions:
                    print(f"  维度列表:")
                    for dim in dimensions:
                        print(f"    - {dim.get('dimension_name', 'N/A')}")
            except Exception as e:
                print(f"  [WARN] 维度配置解析失败: {e}")
        else:
            print(f"  [INFO] 未配置维度")
                
    except Exception as e:
        print(f"[ERROR] 获取场景配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤2: 提交异步评估任务
    print_section("2. 提交异步评估任务")
    
    if not dimensions:
        print("[WARN] 警告: 未配置评估维度，将使用空维度列表")
        user_input = input("是否继续测试？(y/n): ")
        if user_input.lower() != 'y':
            print("测试中止")
            return False
    
    try:
        # 获取异步评估处理器
        async_processor = get_async_processor(scene_assessment_service)
        
        # 提交异步评估任务
        task_id = async_processor.submit_assessment_task(
            session_id=session_id,
            word_content=word_content,  # 使用转换后的可读文本
            dimensions=dimensions,
            industry=industry,
            role_type=role_type,
            role_description=role_description,
            scene_id=scene_id,
            user_id=user_id,
            oss_file_path=audio_file_path,
            call_duration=call_duration
        )
        
        print(f"[OK] 异步评估任务已提交")
        print(f"  Task ID: {task_id}")
        
    except Exception as e:
        print(f"[ERROR] 提交异步评估任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤3: 轮询任务状态
    print_section("3. 轮询任务状态")
    
    try:
        max_wait = 120  # 最多等待120秒
        wait_interval = 5  # 每5秒查询一次
        elapsed = 0
        
        while elapsed < max_wait:
            task_status = async_processor.get_task_status(task_id)
            
            if task_status:
                status = task_status.get('status')
                print(f"  [{elapsed}s] 任务状态: {status}")
                
                if status == 'completed':
                    print("\n[OK] 评估任务完成！")
                    break
                    
                elif status == 'failed':
                    error = task_status.get('error', '未知错误')
                    print(f"\n[ERROR] 评估任务失败: {error}")
                    return False
                
                # 继续等待
                time.sleep(wait_interval)
                elapsed += wait_interval
            else:
                print(f"  [{elapsed}s] 任务不存在")
                return False
        
        if elapsed >= max_wait:
            print(f"\n[ERROR] 评估任务超时（等待了{max_wait}秒）")
            return False
            
    except Exception as e:
        print(f"[ERROR] 轮询任务状态失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤4: 显示评估结果
    print_section("4. 评估结果")
    
    try:
        task_status = async_processor.get_task_status(task_id)
        result = task_status.get('result', {})
        
        # 能力维度评估结果
        dimension_report = result.get('dimension_report', {})
        print(f"\n【能力维度评估】")
        print(f"  综合得分: {dimension_report.get('overall_score', 0)}")
        
        dimension_scores = dimension_report.get('dimension_scores', [])
        if dimension_scores:
            print(f"  各维度得分:")
            for dim in dimension_scores:
                dim_name = dim.get('dimension_name', 'N/A')
                score = dim.get('score', 0)
                feedback = dim.get('feedback', '')[:50]
                print(f"    - {dim_name}: {score} 分")
                print(f"      {feedback}...")
        
        highlights = dimension_report.get('highlights', [])
        if highlights:
            print(f"\n  【表现亮点】:")
            for i, h in enumerate(highlights[:3], 1):
                print(f"    {i}. {h}")
        
        improvements = dimension_report.get('improvements', [])
        if improvements:
            print(f"\n  【改进建议】:")
            for i, imp in enumerate(improvements[:3], 1):
                print(f"    {i}. {imp}")
        
        # SOP质检结果
        sop_result = result.get('sop_result')
        if sop_result:
            print(f"\n【SOP质检评估】")
            print(f"  SOP得分: {sop_result.get('sop_score', 0)}")
            print(f"  通过率: {sop_result.get('pass_rate', 0):.1%}")
            print(f"  通过项: {sop_result.get('passed_count', 0)}/{sop_result.get('total_items', 0)}")
            
            details = sop_result.get('details', [])
            if details:
                print(f"\n  【质检详情】:")
                for detail in details[:5]:
                    item_name = detail.get('item_name', 'N/A')
                    check_type = detail.get('check_type', 'N/A')
                    passed = detail.get('passed', False)
                    status = "✓ 通过" if passed else "✗ 未通过"
                    print(f"    - [{check_type}] {item_name}: {status}")
        else:
            print(f"\n【SOP质检评估】")
            print(f"  未配置SOP质检项")
        
        # AI总结建议
        ai_advise = result.get('ai_advise', '')
        if ai_advise:
            print(f"\n【AI总结建议】")
            print(f"  {ai_advise}")
        
        # 最终得分
        final_score = result.get('final_score', 0)
        print(f"\n【最终得分】")
        print(f"  {final_score}")
        print(f"  (计算方式: 能力维度70% + SOP质检30%)")
        
    except Exception as e:
        print(f"[ERROR] 显示评估结果失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤5: 完整评估报告JSON（可选）
    print_section("5. 完整评估报告JSON")
    
    print_header("[SUCCESS] 测试完成")
    print("\n总结:")
    print(f"  - 使用Mock数据模拟对练结束流程")
    print(f"  - 成功提交异步评估任务")
    print(f"  - 异步评估完成 (最终得分: {final_score} 分)")
    print(f"  - 能力维度得分: {dimension_report.get('overall_score', 0)}")
    print(f"  - SOP得分: {sop_result.get('sop_score', 0) if sop_result else 'N/A'}")
    print(f"  - 评估维度数量: {len(dimension_scores)}")
    print(f"  - 亮点数量: {len(highlights)}")
    print(f"  - 改进建议数量: {len(improvements)}")
    return True


if __name__ == '__main__':
    success = test_assessment_with_mock_data()
 

