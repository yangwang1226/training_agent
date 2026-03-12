#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的评估数据检查工具

用法:
    python tests/test_check_assessment.py <session_id>
    python tests/test_check_assessment.py --list
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.record_dao import get_coach_record_by_session_id
from database.connection import get_db


def regenerate_sop_evaluation(session_id: str):
    """重新生成SOP质检评估"""
    print(f"\n{'='*80}")
    print(f"重新生成SOP质检: {session_id}")
    print(f"{'='*80}\n")
    
    # 1. 获取记录
    record = get_coach_record_by_session_id(session_id)
    if not record:
        print(f"[ERROR] 未找到记录")
        return False
    
    scene_id = record.get('scene_id')
    print(f"[OK] 场景ID: {scene_id}")
    
    # 2. 获取SOP配置
    from database.sop_dao import sop_dao
    sop_checklist = sop_dao.get_scene_sop_checklist(scene_id)
    
    if not sop_checklist:
        print(f"[WARN] 该场景未配置SOP质检项")
        return False
    
    print(f"[OK] SOP质检项: {len(sop_checklist)}个")
    for idx, item in enumerate(sop_checklist, 1):
        print(f"  {idx}. {item['item_name']} ({item['check_type']})")
    
    # 3. 获取对话转录
    word_content = record.get('word_content', '')
    if not word_content:
        print(f"[ERROR] 对话内容为空")
        return False
    
    print(f"\n[OK] 对话内容长度: {len(word_content)} 字符")
    
    # 4. 调用SOP评估
    try:
        # 直接创建评估服务实例
        from agent.service.scene.assessment_service import SceneAssessmentService
        assessment_service = SceneAssessmentService()
        
        print(f"\n正在进行SOP质检评估...")
        print(f"（调用 Qwen Plus 3.5，可能需要几秒钟）\n")
        
        sop_result = assessment_service.evaluate_sop(
            transcript=word_content,
            sop_checklist=sop_checklist
        )
        
        # 显示结果
        print(f"\n{'─'*80}")
        print(f"SOP质检结果")
        print(f"{'─'*80}")
        print(f"\n总分: {sop_result.get('score', 0)}/100")
        print(f"质检项总数: {sop_result.get('total_items', 0)}")
        print(f"通过: {sop_result.get('passed_count', 0)}")
        print(f"未通过: {sop_result.get('failed_count', 0)}")
        
        details = sop_result.get('details', [])
        if details:
            print(f"\n详细结果:")
            for item in details:
                status = '[PASS]' if item.get('passed') else '[FAIL]'
                print(f"\n  {status} {item.get('item_name', 'N/A')}")
                print(f"       类型: {item.get('check_type', 'N/A')}")
                print(f"       依据: {item.get('evidence', 'N/A')}")
                if not item.get('passed'):
                    print(f"       建议: {item.get('suggestion', 'N/A')}")
        
        summary = sop_result.get('summary', '')
        if summary:
            print(f"\n总结: {summary}")
        
        # 5. 自动保存到数据库
        print(f"\n正在保存SOP评估结果...")
        import json
        from database.connection import get_db
        
        sop_result_json = json.dumps(sop_result, ensure_ascii=False)
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE ai_coach_record SET sop_result = %s WHERE session_id = %s"
                cursor.execute(sql, (sop_result_json, session_id))
                conn.commit()
                print(f"[OK] SOP评估结果已保存到数据库")
        
        return True
            
    except Exception as e:
        print(f"\n[ERROR] SOP评估失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_assessment_by_session_id(session_id: str, regenerate_sop: bool = False):
    """检查评估数据
    
    Args:
        session_id: 会话ID
        regenerate_sop: 是否重新生成SOP评估
    """
    print(f"\n{'='*80}")
    print(f"检查评估数据: {session_id}")
    print(f"{'='*80}\n")
    
    # 获取记录
    record = get_coach_record_by_session_id(session_id)
    
    if not record:
        print(f"[ERROR] 未找到记录")
        return False
    
    print("[OK] 记录信息:")
    print(f"  Scene ID: {record.get('scene_id')}")
    print(f"  User ID: {record.get('user_id')}")
    print(f"  通话时长: {record.get('call_duration')}秒")
    print(f"  创建时间: {record.get('created_time')}")
    print(f"  音频文件: {record.get('oss_file_path', 'N/A')}")
    
    # 检查评分
    score = record.get('score')
    if score:
        print(f"\n[OK] 评分: {score} 分")
    else:
        print(f"\n[WARN] 无评分")
    
    # 检查评估报告
    ai_evaluate = record.get('ai_evaluate')
    if ai_evaluate:
        print(f"\n[OK] 评估报告存在")
        try:
            report = json.loads(ai_evaluate)
            print(f"\n评估报告内容:")
            print(f"  综合评分: {report.get('overall_score', 'N/A')}")
            
            dimension_scores = report.get('dimension_scores', [])
            if dimension_scores:
                print(f"\n  维度评分 ({len(dimension_scores)}个):")
                for dim in dimension_scores:
                    dim_name = dim.get('dimension_name', 'N/A')
                    dim_score = dim.get('score', 0)
                    print(f"    - {dim_name}: {dim_score} 分")
            
            highlights = report.get('highlights', [])
            if highlights:
                print(f"\n  表现亮点 ({len(highlights)}个):")
                for i, h in enumerate(highlights[:3], 1):
                    print(f"    {i}. {h}")
            
            improvements = report.get('improvements', [])
            if improvements:
                print(f"\n  改进建议 ({len(improvements)}个):")
                for i, imp in enumerate(improvements[:3], 1):
                    print(f"    {i}. {imp}")
        except:
            print(f"  [WARN] 报告格式错误，无法解析")
    else:
        print(f"\n[WARN] 无评估报告")
    
    # 检查SOP结果
    sop_result = record.get('sop_result')
    if sop_result:
        print(f"\n[OK] SOP质检结果存在")
        try:
            sop_data = json.loads(sop_result)
            print(f"\n  SOP质检结果:")
            print(f"    总分: {sop_data.get('score', 'N/A')}")
            print(f"    质检项总数: {sop_data.get('total_items', 0)}")
            print(f"    通过: {sop_data.get('passed_count', 0)}")
            print(f"    未通过: {sop_data.get('failed_count', 0)}")
            
            details = sop_data.get('details', [])
            if details:
                print(f"\n  详细结果:")
                for item in details:
                    status = '[PASS]' if item.get('passed') else '[FAIL]'
                    print(f"    {status} {item.get('item_name', 'N/A')} ({item.get('check_type', 'N/A')})")
                    if not item.get('passed'):
                        print(f"         建议: {item.get('suggestion', 'N/A')}")
            
            summary = sop_data.get('summary', '')
            if summary:
                print(f"\n  总结: {summary}")
        except:
            print(f"  [WARN] SOP结果格式错误，无法解析")
    else:
        print(f"\n[WARN] 无SOP质检结果")
    
    # 检查AI建议
    ai_advise = record.get('ai_advise')
    if ai_advise:
        print(f"\n[OK] AI建议存在 ({len(ai_advise)} 字符)")
        print(f"\n  AI建议预览:")
        print(f"  {ai_advise[:200]}...")
    else:
        print(f"\n[WARN] 无AI建议")
    
    # 检查对话内容
    word_content = record.get('word_content')
    if word_content:
        print(f"\n[OK] 对话内容存在 ({len(word_content)} 字符)")
        print(f"\n  对话内容预览:")
        print(f"  {word_content[:300]}...")
    else:
        print(f"\n[WARN] 无对话内容")
    
    print(f"\n{'='*80}")
    print(f"检查完成")
    print(f"{'='*80}\n")
    
    return True


def list_records(limit=10):
    """列出最近的记录"""
    print(f"\n{'='*80}")
    print(f"最近的训练记录")
    print(f"{'='*80}\n")
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """   
                SELECT 
                    session_id,
                    scene_id,
                    call_duration,
                    score,
                    CASE 
                        WHEN ai_evaluate IS NOT NULL THEN 'YES'
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
            
            print(f"共 {len(records)} 条记录:\n")
            print(f"{'序号':<5} {'Session ID':<40} {'场景':<8} {'时长':<8} {'评分':<8} {'有评估':<10} {'创建时间'}")
            print("─" * 120)
            
            for idx, record in enumerate(records, 1):
                print(f"{idx:<5} {record['session_id']:<40} {record['scene_id']:<8} {record['call_duration'] or 0:<8} {record['score'] or '-':<8} {record['has_evaluate']:<10} {record['created_time']}")
            
            print("\n用法: python tests/test_check_assessment.py <session_id>")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python tests/test_check_assessment.py <session_id>")
        print("      python tests/test_check_assessment.py <session_id> --sop  (重新生成SOP评估)")
        print("      python tests/test_check_assessment.py --list\n")
        list_records(10)
        sys.exit(1)
    
    if sys.argv[1] in ['--list', '-l']:
        list_records(20)
        sys.exit(0)
    
    session_id = sys.argv[1]
    regenerate_sop_flag = '--sop' in sys.argv or '-s' in sys.argv
    
    try:
        if regenerate_sop_flag:
            # 重新生成SOP评估
            success = regenerate_sop_evaluation(session_id)
            if success:
                print(f"\n提示: 使用以下命令查看完整结果:")
                print(f"  python tests/test_check_assessment.py {session_id}")
        else:
            # 检查现有评估数据
            check_assessment_by_session_id(session_id)
            
            # 如果没有SOP结果，自动生成
            record = get_coach_record_by_session_id(session_id)
            if record and not record.get('sop_result'):
                print("\n[INFO] 检测到无SOP评估，自动生成...")
                regenerate_sop_evaluation(session_id)
                
    except KeyboardInterrupt:
        print("\n中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
