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

# 全局评估服务实例
_assessment_service = None

def get_assessment_service():
    """获取评估服务实例（单例模式）"""
    global _assessment_service
    
    if _assessment_service is not None:
        return _assessment_service
    
    try:
        # 方法1: 直接实例化
        from agent.service.scene.assessment_service import SceneAssessmentService
        _assessment_service = SceneAssessmentService()
        print("[INFO] 评估服务加载成功")
        return _assessment_service
    except Exception as e:
        print(f"[WARN] 方法1失败: {e}，尝试方法2...")
        try:
            # 方法2: 导入全局实例
            import importlib
            assessment_module = importlib.import_module('agent.service.scene.assessment_service')
            _assessment_service = assessment_module.assessment_service
            print("[INFO] 评估服务加载成功（方法2）")
            return _assessment_service
        except Exception as e2:
            print(f"[ERROR] 加载评估服务失败: {e2}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"无法加载评估服务: {e2}")


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


def test_assessment_by_session_id(session_id: str):
    """通过session_id测试评估功能
    
    Args:
        session_id: 训练记录的session_id
    """
    
    print_header("评估功能测试")
    print(f"Session ID: {session_id}")
    
    # 1. 获取训练记录
    print_section("1. 获取训练记录")
    try:
        record = get_coach_record_by_session_id(session_id)
        
        if not record:
            print(f"[ERROR] 错误: 未找到 session_id={session_id} 的记录")
            return False
        
        print(f"[OK] 找到记录")
        print(f"  Scene ID: {record.get('scene_id')}")
        print(f"  User ID: {record.get('user_id')}")
        print(f"  通话时长: {record.get('call_duration')}秒")
        print(f"  创建时间: {record.get('created_time')}")
        print(f"  音频文件: {record.get('oss_file_path', 'N/A')}")
        
        # 检查是否已有评估（使用新字段）
        if record.get('ai_score') or record.get('dimension_result'):
            print(f"  [INFO] 已有评估报告")
            print(f"    - AI评分: {record.get('ai_score', 'N/A')}")
            print(f"    - 评估总结: {record.get('ai_summary', 'N/A')[:50] if record.get('ai_summary') else 'N/A'}...")
            has_existing_evaluation = True
        else:
            print(f"  [INFO] 尚无评估报告")
            has_existing_evaluation = False
            
    except Exception as e:
        print(f"[ERROR] 获取记录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. 提取对话转录
    print_section("2. 提取对话转录")
    try:
        word_content = record.get('word_content', '')
        
        if not word_content:
            print("[ERROR] 错误: 对话内容为空")
            return False
        
        # 尝试解析word_content
        try:
            # 如果是JSON格式的消息列表
            messages = json.loads(word_content)
            if isinstance(messages, list):
                transcript_lines = []
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if content:
                        transcript_lines.append(f"{role}: {content}")
                transcript = "\n".join(transcript_lines)
            else:
                transcript = word_content
        except json.JSONDecodeError:
            # 如果不是JSON，直接使用
            transcript = word_content
        
        print(f"[OK] 对话转录提取成功")
        print(f"  转录长度: {len(transcript)} 字符")
        print(f"\n  【转录预览】（前500字符）")
        print(f"  {transcript[:500]}...")
        
    except Exception as e:
        print(f"[ERROR] 提取转录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 获取场景信息和维度配置
    print_section("3. 获取场景配置")
    try:
        scene_id = record.get('scene_id')
        scene = db_module.get_scene_by_id(scene_id)
        
        if not scene:
            print(f"[WARN] 警告: 未找到场景 ID={scene_id}")
            dimensions = []
            industry = ""
            role_type = ""
        else:
            print(f"[OK] 场景信息获取成功")
            print(f"  场景名称: {scene.get('scene_name', 'N/A')}")
            print(f"  行业: {scene.get('industry', 'N/A')}")
            print(f"  AI角色: {scene.get('ai_role', 'N/A')}")
            
            industry = scene.get('industry', '')
            role_type = scene.get('ai_role', '')
            
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
    
    # 4. 生成评估报告
    print_section("4. 生成评估报告")
    
    if not dimensions:
        print("[WARN] 警告: 未配置评估维度，将使用空维度列表")
        user_input = input("是否继续测试？(y/n): ")
        if user_input.lower() != 'y':
            print("测试中止")
            return False
    
    try:
        print("正在调用 Qwen Plus 3.5 生成评估报告...")
        print("（这可能需要几秒钟）\n")
        
        # 获取评估服务实例
        assessment_service = get_assessment_service()
        
        report = assessment_service.generate_report(
            session_id=session_id,
            transcript=transcript,
            dimensions=dimensions,
            industry=industry,
            role_type=role_type,
            background_info=scene.get('background', '') if scene else ''
        )
        
        if not report:
            print("[ERROR] 错误: 评估报告生成失败")
            return False
        
        print("[OK] 评估报告生成成功！\n")
        
        # 显示评估结果
        print(f"  【综合评分】: {report.get('overall_score', 0)} 分")
        
        dimension_scores = report.get('dimension_scores', [])
        if dimension_scores:
            print(f"\n  【维度评分】:")
            for dim in dimension_scores:
                dim_name = dim.get('dimension_name', 'N/A')
                score = dim.get('score', 0)
                print(f"    - {dim_name}: {score} 分")
        
        highlights = report.get('highlights', [])
        if highlights:
            print(f"\n  【表现亮点】:")
            for i, h in enumerate(highlights[:3], 1):  # 只显示前3个
                print(f"    {i}. {h}")
        
        improvements = report.get('improvements', [])
        if improvements:
            print(f"\n  【改进建议】:")
            for i, imp in enumerate(improvements[:3], 1):  # 只显示前3个
                print(f"    {i}. {imp}")
        
    except Exception as e:
        print(f"[ERROR] 生成评估报告失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 保存评估报告（可选）
    print_section("5. 保存评估报告")
    
    if has_existing_evaluation:
        user_input = input("该记录已有评估报告，是否覆盖保存新的评估？(y/n): ")
        if user_input.lower() != 'y':
            print("跳过保存步骤")
            print_header("测试完成")
            return True
    
    try:
        print("正在保存评估报告到数据库...")
        
        # 获取场景的 SOP 质检项
        sop_result = None
        if scene and scene.get('sop_checklist'):
            try:
                print("  检测到场景配置了 SOP 质检项，开始执行 SOP 质检...")
                sop_checklist = json.loads(scene['sop_checklist'])
                
                # 获取评估服务实例
                assessment_service = get_assessment_service()
                
                # 执行 SOP 质检
                sop_result = assessment_service.evaluate_sop(
                    transcript=transcript,
                    sop_checklist=sop_checklist
                )
                
                print(f"  [OK] SOP 质检完成: 得分={sop_result.get('score', 0)}, 通过={sop_result.get('passed_count', 0)}/{sop_result.get('total_items', 0)}")
                
            except Exception as e:
                print(f"  [WARN] SOP 质检失败: {e}")
                sop_result = None
        else:
            print("  [INFO] 场景未配置 SOP 质检项，跳过 SOP 评估")
        
        # 获取评估服务实例
        assessment_service = get_assessment_service()
        
        success = assessment_service.save_to_database(
            session_id=session_id,
            report=report,
            scene_id=record.get('scene_id'),
            user_id=record.get('user_id', 1),
            word_content=transcript,
            oss_file_path=record.get('oss_file_path', ''),
            call_duration=record.get('call_duration', 0),
            sop_result=sop_result
        )
        
        if success:
            print("[OK] 评估报告已保存到数据库")
        else:
            print("[WARN] 保存失败，但不影响测试结果")
            
    except Exception as e:
        print(f"[WARN] 保存评估报告失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 完整评估报告JSON（可选）
    print_section("6. 完整评估报告JSON")
    
    user_input = input("是否显示完整的评估报告JSON？(y/n): ")
    if user_input.lower() == 'y':
        print("\n" + json.dumps(report, ensure_ascii=False, indent=2))
    
    print_header("[SUCCESS] 测试完成")
    print("\n总结:")
    print(f"  - 成功获取训练记录")
    print(f"  - 成功提取对话转录 ({len(transcript)} 字符)")
    print(f"  - 成功生成评估报告 (综合评分: {report.get('overall_score', 0)} 分)")
    print(f"  - 评估维度数量: {len(dimension_scores)}")
    print(f"  - 亮点数量: {len(highlights)}")
    print(f"  - 改进建议数量: {len(improvements)}")
    
    return True


def list_recent_records(limit=10):
    """列出最近的训练记录"""
    from database.connection import get_db
    
    print_header("最近的训练记录")
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT 
                        session_id,
                        scene_id,
                        call_duration,
                        ai_score,
                        CASE 
                            WHEN ai_score IS NOT NULL THEN 'YES'
                            ELSE 'NO'
                        END as has_evaluate,
                        created_time
                    FROM ai_coach_record
                    WHERE is_delete = 0
                    ORDER BY created_time DESC
                    LIMIT %s
                """
                cursor.execute(sql, (limit,))
                records = cursor.fetchall()
                
                if not records:
                    print("没有找到记录")
                    return
                
                print(f"\n共找到 {len(records)} 条记录：\n")
                print(f"{'序号':<5} {'Session ID':<40} {'场景':<8} {'时长':<8} {'评分':<8} {'有评估':<10} {'创建时间'}")
                print("─" * 120)
                
                for idx, record in enumerate(records, 1):
                    print(f"{idx:<5} {record['session_id']:<40} {record['scene_id']:<8} {record['call_duration'] or 0:<8} {record.get('ai_score') or '-':<8} {record['has_evaluate']:<10} {record['created_time']}")
                
                print("\n提示: 复制上面的 Session ID 用于测试")
                print("用法: python tests/test_assessment_evaluation.py <session_id>")
                
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python tests/test_assessment_evaluation.py <session_id>")
        print("      python tests/test_assessment_evaluation.py --list  (列出最近的记录)\n")
        
        # 自动列出最近的记录
        list_recent_records(10)
        sys.exit(1)
    
    if sys.argv[1] == '--list' or sys.argv[1] == '-l':
        list_recent_records(20)
        sys.exit(0)
    
    session_id = sys.argv[1]
    
    try:
        success = test_assessment_by_session_id(session_id)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

