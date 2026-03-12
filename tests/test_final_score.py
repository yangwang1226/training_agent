#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试综合评分（final_score）计算功能
验证 AI 评分和 SOP 评分的加权计算
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.record_dao import calculate_final_score


def test_calculate_final_score():
    """测试综合评分计算函数"""
    print("\n=== 测试综合评分计算 ===\n")
    
    test_cases = [
        # (ai_score, sop_score, expected_final_score)
        (80, 90, 86),  # 80*0.4 + 90*0.6 = 32 + 54 = 86
        (100, 100, 100),  # 满分
        (0, 0, 0),  # 零分
        (60, 80, 72),  # 60*0.4 + 80*0.6 = 24 + 48 = 72
        (75, 85, 81),  # 75*0.4 + 85*0.6 = 30 + 51 = 81
        (None, 90, 54),  # None 视为 0，0*0.4 + 90*0.6 = 54
        (80, None, 32),  # 80*0.4 + 0*0.6 = 32
        (None, None, 0),  # 都为 None，结果为 0
    ]
    
    passed = 0
    failed = 0
    
    for ai_score, sop_score, expected in test_cases:
        result = calculate_final_score(ai_score, sop_score)
        status = "PASS" if result == expected else "FAIL"
        
        if result == expected:
            passed += 1
            print(f"[{status}] AI={ai_score}, SOP={sop_score} => final_score={result} (expected: {expected})")
        else:
            failed += 1
            print(f"[{status}] AI={ai_score}, SOP={sop_score} => final_score={result} (expected: {expected})")
    
    print(f"\nTotal: {passed + failed} test cases")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return failed == 0


def test_weight_distribution():
    """测试权重分配是否符合预期"""
    print("\n=== 测试权重分配 ===\n")
    
    # AI 满分，SOP 零分
    score1 = calculate_final_score(100, 0)
    print(f"AI=100, SOP=0 => {score1} (应该是 40，即 AI 权重)")
    
    # AI 零分，SOP 满分
    score2 = calculate_final_score(0, 100)
    print(f"AI=0, SOP=100 => {score2} (应该是 60，即 SOP 权重)")
    
    # 验证权重比例
    weight_correct = (score1 == 40 and score2 == 60)
    print(f"\nWeight verification: {'PASS' if weight_correct else 'FAIL'}")
    print(f"AI weight: 40%, SOP weight: 60%")
    
    return weight_correct


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("综合评分（final_score）功能测试")
    print("="*60)
    
    test1_passed = test_calculate_final_score()
    test2_passed = test_weight_distribution()
    
    print("\n" + "="*60)
    if test1_passed and test2_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()