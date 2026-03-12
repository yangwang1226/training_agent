"""测试新的评估数据结构"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json

def test_data_structure():
    """测试新的数据结构"""
    print("\n" + "="*80)
    print("测试新的评估数据结构")
    print("="*80)
    
    # 模拟评估报告数据
    mock_report = {
        "overall_score": 85,
        "summary": "整体表现良好，沟通能力突出。",
        "dimension_scores": [
            {
                "dimension_name": "沟通能力",
                "score": 88,
                "feedback": "表达清晰，逻辑连贯。"
            },
            {
                "dimension_name": "专业知识",
                "score": 82,
                "feedback": "产品知识掌握较好。"
            }
        ],
        "highlights": [
            "开场白自然亲切",
            "产品介绍专业"
        ],
        "improvements": [
            "需求挖掘可以更深入",
            "异议处理需要加强"
        ],
        "golden_sentences": [
            "您的需求我理解了"
        ],
        "key_moments": []
    }
    
    print("\n1. 原始评估报告:")
    print(json.dumps(mock_report, ensure_ascii=False, indent=2))
    
    # 拆分为新的字段结构
    ai_score = mock_report.get("overall_score", 0)
    ai_summary = mock_report.get("summary", "")
    
    dimension_result = {
        "dimension_scores": mock_report.get("dimension_scores", []),
        "highlights": mock_report.get("highlights", []),
        "improvements": mock_report.get("improvements", []),
        "golden_sentences": mock_report.get("golden_sentences", []),
        "key_moments": mock_report.get("key_moments", [])
    }
    
    print("\n2. 拆分后的字段:")
    print(f"\nai_score (INT): {ai_score}")
    print(f"\nai_summary (TEXT):\n{ai_summary}")
    print(f"\ndimension_result (JSON):\n{json.dumps(dimension_result, ensure_ascii=False, indent=2)}")
    
    # 模拟数据库保存参数
    print("\n3. save_coach_record 调用参数:")
    print(f"  - session_id: 'test_session_123'")
    print(f"  - scene_id: 14")
    print(f"  - user_id: 1")
    print(f"  - ai_score: {ai_score}")
    print(f"  - ai_summary: '{ai_summary}'")
    print(f"  - dimension_result: (JSON字符串，{len(json.dumps(dimension_result))} 字符)")
    print(f"  - ai_advise: '【亮点】...【改进建议】...'")
    print(f"  - sop_result: (JSON字符串)")
    
    print("\n4. API 返回数据结构:")
    api_response = {
        "success": True,
        "data": {
            "session_id": "test_session_123",
            "scene_id": 14,
            "scene_name": "汽车销售场景",
            "ai_score": ai_score,
            "ai_summary": ai_summary,
            "dimension_result": dimension_result,
            "call_duration": 180,
            "ai_advise": "改进建议文本",
            "sop_result": {
                "score": 75,
                "total_items": 3,
                "passed_count": 2,
                "failed_count": 1
            }
        }
    }
    print(json.dumps(api_response, ensure_ascii=False, indent=2))
    
    print("\n5. 前端读取路径:")
    print("  - 综合评分: data.ai_score")
    print("  - 评估总结: data.ai_summary")
    print("  - 维度评分: data.dimension_result.dimension_scores[]")
    print("  - 表现亮点: data.dimension_result.highlights[]")
    print("  - 改进建议: data.dimension_result.improvements[]")
    print("  - 雷达图数据: data.dimension_result.dimension_scores[]")
    
    print("\n" + "="*80)
    print("✅ 数据结构测试完成")
    print("="*80)
    print("\n下一步:")
    print("1. 执行数据库迁移 SQL")
    print("2. 重启服务")
    print("3. 进行一次新的训练对话")
    print("4. 查看评估报告页面")
    print()

if __name__ == '__main__':
    test_data_structure()