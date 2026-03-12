import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import uuid
from database.record_dao import save_coach_record, get_coach_record_by_session_id

def test_save_coach_record():
    session_id = str(uuid.uuid4())
    scene_id = 1
    user_id = 1
    
    word_content = json.dumps([
        {"role": "trainer", "content": "你好", "timestamp": "10:00:00"},
        {"role": "ai", "content": "您好，请问有什么可以帮助您的？", "timestamp": "10:00:05"}
    ], ensure_ascii=False)
    
    oss_file_path = "audio_file/test_20260312.wav"
    call_duration = 60
    
    ai_score = 85
    ai_summary = "本次对话表现良好，沟通技巧有待提升。"
    
    dimension_result = json.dumps({
        "dimension_scores": [
            {"name": "沟通能力", "score": 80},
            {"name": "专业知识", "score": 90}
        ],
        "highlights": ["表达清晰", "逻辑性强"],
        "improvements": ["需要更多互动"]
    }, ensure_ascii=False)
    
    ai_advise = "建议加强沟通技巧训练"
    
    sop_result = json.dumps({
        "sop_score": 90,
        "passed_count": 9,
        "total_items": 10
    }, ensure_ascii=False)
    
    sop_score = 90
    
    print("=" * 60)
    print("测试 1: save_coach_record 函数 (正常字符串参数)")
    print("=" * 60)
    print(f"session_id: {session_id}")
    print(f"scene_id: {scene_id}")
    print(f"user_id: {user_id}")
    print(f"word_content type: {type(word_content)}")
    print(f"oss_file_path type: {type(oss_file_path)}")
    print(f"call_duration type: {type(call_duration)}")
    print(f"ai_score type: {type(ai_score)}")
    print(f"ai_summary type: {type(ai_summary)}")
    print(f"dimension_result type: {type(dimension_result)}")
    print(f"ai_advise type: {type(ai_advise)}")
    print(f"sop_result type: {type(sop_result)}")
    print(f"sop_score type: {type(sop_score)}")
    print("=" * 60)
    
    try:
        success = save_coach_record(
            session_id=session_id,
            scene_id=scene_id,
            user_id=user_id,
            word_content=word_content,
            oss_file_path=oss_file_path,
            call_duration=call_duration,
            ai_score=ai_score,
            ai_summary=ai_summary,
            dimension_result=dimension_result,
            ai_advise=ai_advise,
            sop_result=sop_result,
            sop_score=sop_score
        )
        print(f"\n保存结果: {'成功' if success else '失败'}")
        
        record = get_coach_record_by_session_id(session_id)
        if record:
            print(f"验证读取成功: session_id={record.get('session_id')}")
        else:
            print("验证读取失败: 未找到记录")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

def test_with_dict_parameter():
    print("\n" + "=" * 60)
    print("测试 2: 传入字典参数的情况（模拟错误场景）")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    
    dimension_result_dict = {
        "dimension_scores": [
            {"name": "沟通能力", "score": 80},
        ],
        "highlights": ["表达清晰"],
    }
    
    print(f"dimension_result_dict type: {type(dimension_result_dict)}")
    
    try:
        success = save_coach_record(
            session_id=session_id,
            scene_id=1,
            user_id=1,
            dimension_result=dimension_result_dict,
        )
        print(f"结果: {'成功' if success else '失败'}")
        
        record = get_coach_record_by_session_id(session_id)
        if record:
            print(f"验证读取成功: dimension_result={record.get('dimension_result')[:50]}...")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def test_with_mixed_types():
    print("\n" + "=" * 60)
    print("测试 3: 混合类型参数（模拟真实场景）")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    
    word_content_dict = [
        {"role": "trainer", "content": "你好"},
        {"role": "ai", "content": "您好"}
    ]
    
    ai_summary_dict = {"text": "本次对话表现良好"}
    
    dimension_result_dict = {
        "dimension_scores": [{"name": "沟通能力", "score": 80}],
        "highlights": ["表达清晰"],
    }
    
    print(f"word_content type: {type(word_content_dict)}")
    print(f"ai_summary type: {type(ai_summary_dict)}")
    print(f"dimension_result type: {type(dimension_result_dict)}")
    
    try:
        success = save_coach_record(
            session_id=session_id,
            scene_id=1,
            user_id=1,
            word_content=word_content_dict,
            ai_summary=ai_summary_dict,
            dimension_result=dimension_result_dict,
            ai_score=85,
            sop_score=90
        )
        print(f"结果: {'成功' if success else '失败'}")
        
        record = get_coach_record_by_session_id(session_id)
        if record:
            print(f"验证读取成功:")
            print(f"  word_content: {record.get('word_content')[:50]}...")
            print(f"  ai_summary: {record.get('ai_summary')[:50]}...")
            print(f"  final_score: {record.get('final_score')}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_coach_record()
    test_with_dict_parameter()
    test_with_mixed_types()
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)
