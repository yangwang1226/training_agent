"""
异步评估功能测试脚本

测试异步评估处理器的功能
"""
import sys
import os
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.service.scene.assessment_service import assessment_service
from agent.service.scene.async_assessment_processor import get_async_processor


def test_async_assessment():
    """测试异步评估功能"""
    
    print("=" * 60)
    print("异步评估功能测试")
    print("=" * 60)
    
    # 测试数据
    session_id = "test_session_001"
    transcript = """
用户：您好，我是XX汽车4S店的销售顾问，欢迎光临！
AI：你好，我想了解一下你们的新款SUV车型。
用户：好的，我们刚推出的XX系列SUV非常受欢迎。这款车配备了2.0T涡轮增压发动机，动力强劲，油耗也相对较低。您平时主要在市区还是高速行驶比较多？
AI：主要是市区通勤，偶尔周末出去自驾游。
用户：那这款车非常适合您。它的底盘调校偏向舒适，市区驾驶很平稳。而且它的智能驾驶辅助系统在高速上也能帮您减轻疲劳。您对价格有什么考虑吗？
AI：预算大概在25万左右。
用户：我们这款车现在的优惠活动力度很大，正好在您的预算范围内。而且我们还提供三年免息贷款，首付只要30%。您看什么时候方便来店里试驾一下？
AI：好的，这周末我有时间。
用户：太好了，那我帮您预约一下周六上午10点的试驾，您看可以吗？
AI：可以。
用户：好的，那我们周六见！我会提前准备好车辆和资料，到时候您可以详细了解这款车的各项配置。
"""
    
    dimensions = [
        {
            "dimension_name": "产品知识",
            "weight": 0.3,
            "sub_criteria": {
                "产品特点": "能够准确介绍产品的主要特点和优势",
                "竞品对比": "能够与竞品进行合理对比",
                "参数熟悉": "熟悉产品的主要技术参数"
            }
        },
        {
            "dimension_name": "沟通技巧",
            "weight": 0.4,
            "sub_criteria": {
                "倾听能力": "能够认真倾听客户需求",
                "提问技巧": "能够通过提问了解客户真实需求",
                "表达清晰": "表达清晰、有条理"
            }
        },
        {
            "dimension_name": "销售技巧",
            "weight": 0.3,
            "sub_criteria": {
                "需求挖掘": "能够深入挖掘客户需求",
                "促成交易": "能够适时促成交易",
                "异议处理": "能够妥善处理客户异议"
            }
        }
    ]
    
    industry = "汽车销售"
    role_type = "销售顾问"
    background_info = "汽车4S店销售场景，客户咨询新款SUV车型"
    scene_id = 1
    user_id = 1
    
    print(f"\n测试参数：")
    print(f"  会话ID: {session_id}")
    print(f"  行业: {industry}")
    print(f"  角色: {role_type}")
    print(f"  维度数量: {len(dimensions)}")
    print(f"  对话轮次: {transcript.count('用户：')}")
    
    # 获取异步评估处理器
    print("\n[步骤1] 初始化异步评估处理器...")
    async_processor = get_async_processor(assessment_service)
    print("✓ 异步评估处理器初始化成功")
    
    # 提交评估任务
    print("\n[步骤2] 提交评估任务...")
    task_id = async_processor.submit_assessment_task(
        session_id=session_id,
        transcript=transcript,
        dimensions=dimensions,
        industry=industry,
        role_type=role_type,
        background_info=background_info,
        scene_id=scene_id,
        user_id=user_id,
        oss_file_path="test_audio.mp3",
        call_duration=180
    )
    print(f"✓ 评估任务已提交: task_id={task_id}")
    
    # 轮询任务状态
    print("\n[步骤3] 轮询任务状态...")
    max_wait = 120  # 最多等待120秒
    wait_interval = 5  # 每5秒查询一次
    elapsed = 0
    
    while elapsed < max_wait:
        task_status = async_processor.get_task_status(task_id)
        
        if task_status:
            status = task_status.get('status')
            print(f"  [{elapsed}s] 任务状态: {status}")
            
            if status == 'completed':
                print("\n✓ 评估任务完成！")
                
                # 显示结果
                result = task_status.get('result', {})
                
                print("\n" + "=" * 60)
                print("评估结果")
                print("=" * 60)
                
                # 能力维度评估结果
                dimension_report = result.get('dimension_report', {})
                print(f"\n【能力维度评估】")
                print(f"  综合得分: {dimension_report.get('overall_score', 0)}")
                
                dimension_scores = dimension_report.get('dimension_scores', [])
                if dimension_scores:
                    print(f"  各维度得分:")
                    for dim in dimension_scores:
                        print(f"    - {dim.get('dimension_name')}: {dim.get('score', 0)}")
                
                # SOP质检结果
                sop_result = result.get('sop_result')
                if sop_result:
                    print(f"\n【SOP质检评估】")
                    print(f"  SOP得分: {sop_result.get('sop_score', 0)}")
                    print(f"  通过率: {sop_result.get('pass_rate', 0):.1%}")
                    print(f"  通过项: {sop_result.get('passed_count', 0)}/{sop_result.get('total_items', 0)}")
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
                
                print("\n" + "=" * 60)
                print("测试成功！")
                print("=" * 60)
                return True
                
            elif status == 'failed':
                error = task_status.get('error', '未知错误')
                print(f"\n✗ 评估任务失败: {error}")
                return False
            
            # 继续等待
            time.sleep(wait_interval)
            elapsed += wait_interval
        else:
            print(f"  [{elapsed}s] 任务不存在")
            return False
    
    print(f"\n✗ 评估任务超时（等待了{max_wait}秒）")
    return False


if __name__ == "__main__":
    try:
        success = test_async_assessment()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
