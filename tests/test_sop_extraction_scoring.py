"""
测试 SOP 智能提取和评分功能
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

BASE_URL = "http://localhost:5000"


def test_extract_with_scoring():
    """
    测试文本智能提取 + 自动评分
    """
    print("\n" + "="*80)
    print("测试：文本智能提取 + 自动评分")
    print("="*80)
    
    # 测试数据：房地产销售场景的SOP文档
    test_text = """
    房地产销售标准操作流程（SOP）
    
    一、开场阶段
    1. 必须在30秒内主动向客户问好，使用标准问候语："您好，欢迎光临，我是置业顾问XXX"
    2. 必须主动递上名片，展现专业形象
    3. 建议使用开放式问题了解客户来访目的
    
    二、需求分析阶段
    1. 必须询问客户的购房预算范围
    2. 必须了解客户的户型需求（几室几厅）
    3. 必须确认客户的入住时间要求
    4. 建议了解客户的工作地点，推荐合适的地段
    
    三、产品介绍阶段
    1. 必须根据客户需求精准推荐户型
    2. 禁止一次性推荐超过3个户型，避免客户混淆
    3. 必须介绍小区的核心卖点（地段、配套、品牌）
    4. 建议使用类比法说明房屋价值
    
    四、异议处理阶段
    1. 禁止贬低竞品楼盘
    2. 禁止虚假承诺或夸大宣传
    3. 必须真实回答客户疑问
    4. 建议使用成交案例增强说服力
    
    五、促成阶段
    1. 必须主动询问客户是否需要预约看房
    2. 必须说明当前优惠政策
    3. 建议制造紧迫感（限时优惠、仅剩几套等）
    
    六、合规要求
    1. 严禁虚假宣传，必须如实告知房屋信息
    2. 必须明确告知客户贷款政策和购房流程
    3. 禁止承诺不符合实际的交付时间
    """
    
    url = f"{BASE_URL}/api/sop/extract-with-scoring"
    
    data = {
        "scene_code": "real_estate_sales",
        "text_content": test_text,
        "scene_description": "房地产销售场景，需要专业的置业顾问与客户沟通，完成从接待到促成的全流程",
        "extract_must_do": True,
        "extract_must_not": True,
        "extract_should_do": True,
        "auto_scoring": True,
        "target_total": 100
    }
    
    print("\n发送请求...")
    print(f"场景：{data['scene_code']}")
    print(f"文本长度：{len(test_text)} 字符")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n✅ 提取成功！\n")
                
                items = result.get('items', [])
                summary = result.get('scoring_summary', {})
                
                # 显示评分摘要
                print("📊 评分摘要：")
                print(f"  总分：{summary.get('total_score', 0)} 分")
                print(f"  必须项(must_do)：{summary.get('must_do_score', 0)} 分")
                print(f"  禁止项(must_not_do)：{summary.get('must_not_score', 0)} 分")
                print(f"  建议项(should_do)：{summary.get('should_do_score', 0)} 分")
                print(f"")
                print(f"  关键项数量：{summary.get('critical_count', 0)}")
                print(f"  重要项数量：{summary.get('high_count', 0)}")
                print(f"  一般项数量：{summary.get('medium_count', 0)}")
                print(f"  加分项数量：{summary.get('low_count', 0)}")
                print(f"  总质检项：{summary.get('total_items', 0)}")
                
                # 按重要性分组显示
                print("\n📋 质检项列表（按重要性分组）：\n")
                
                importance_groups = {
                    'critical': [],
                    'high': [],
                    'medium': [],
                    'low': []
                }
                
                for item in items:
                    importance = item.get('importance_level', 'medium')
                    importance_groups[importance].append(item)
                
                importance_labels = {
                    'critical': '⭐⭐⭐ 关键项',
                    'high': '⭐⭐ 重要项',
                    'medium': '⭐ 一般项',
                    'low': '💡 加分项'
                }
                
                for level in ['critical', 'high', 'medium', 'low']:
                    group_items = importance_groups[level]
                    if group_items:
                        total_score = sum(item.get('final_score', 0) for item in group_items)
                        print(f"\n{importance_labels[level]} ({len(group_items)}项，{total_score}分)")
                        print("-" * 80)
                        
                        for item in group_items:
                            print(f"\n[{item.get('item_id')}] {item.get('item_name')}")
                            print(f"  类型：{item.get('check_type')} | 分类：{item.get('category')} | 分数：{item.get('final_score')}分")
                            print(f"  重要性：{item.get('importance_level')}")
                            print(f"  关键词：{', '.join(item.get('keywords', []))}")
                            print(f"  描述：{item.get('item_desc', '无')}")
                            print(f"  评分依据：{item.get('score_reason', '无')}")
                
                # 保存结果到文件
                output_file = "test_output_sop_extraction.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 完整结果已保存到：{output_file}")
                
                return True
            else:
                print(f"\n❌ 提取失败：{result.get('error')}")
                return False
        else:
            print(f"\n❌ 请求失败，状态码：{response.status_code}")
            print(f"响应内容：{response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 异常：{e}")
        return False


def test_scoring_rules():
    """
    测试获取评分规则
    """
    print("\n" + "="*80)
    print("测试：获取评分规则")
    print("="*80)
    
    url = f"{BASE_URL}/api/sop/scoring-rules"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n✅ 获取成功！\n")
                
                rules = result.get('rules', {})
                
                print("📐 评分规则说明：")
                print(f"\n公式：{rules.get('formula', '无')}")
                
                print("\n1️⃣ 重要性等级基础分：")
                for level, score in rules.get('importance_scores', {}).items():
                    print(f"  {level}: {score}分")
                
                print("\n2️⃣ 质检类型系数：")
                for type_name, weight in rules.get('type_weights', {}).items():
                    print(f"  {type_name}: {weight}")
                
                print("\n3️⃣ 分类权重：")
                for category, weight in rules.get('category_weights', {}).items():
                    print(f"  {category}: {weight}")
                
                print(f"\n是否可自定义：{rules.get('customizable', False)}")
                
                return True
            else:
                print(f"\n❌ 获取失败：{result.get('error')}")
                return False
        else:
            print(f"\n❌ 请求失败，状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 异常：{e}")
        return False


def test_adjust_score():
    """
    测试调整质检项分数
    """
    print("\n" + "="*80)
    print("测试：调整质检项分数")
    print("="*80)
    
    # 先读取之前提取的结果
    try:
        with open("test_output_sop_extraction.json", 'r', encoding='utf-8') as f:
            prev_result = json.load(f)
            checklist = prev_result.get('items', [])
    except:
        print("\n❌ 请先运行 test_extract_with_scoring()")
        return False
    
    if not checklist:
        print("\n❌ 质检项列表为空")
        return False
    
    # 选择第一个质检项进行调整
    target_item = checklist[0]
    print(f"\n调整目标：{target_item.get('item_name')}")
    print(f"当前分数：{target_item.get('final_score')} 分")
    print(f"当前重要性：{target_item.get('importance_level')}")
    
    url = f"{BASE_URL}/api/sop/adjust-score"
    
    # 测试1：直接修改分数
    print("\n测试1：直接修改分数为 35 分")
    data = {
        "item_id": target_item.get('item_id'),
        "new_score": 35,
        "checklist": checklist
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ 调整成功！")
                updated_item = result.get('updated_item', {})
                print(f"新分数：{updated_item.get('final_score')} 分")
                
                rebalanced = result.get('rebalanced_checklist', [])
                total = sum(item.get('final_score', 0) for item in rebalanced)
                print(f"重新平衡后总分：{total} 分")
                
                return True
            else:
                print(f"❌ 调整失败：{result.get('error')}")
                return False
        else:
            print(f"❌ 请求失败，状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 异常：{e}")
        return False


def test_rebalance_scores():
    """
    测试重新平衡分数
    """
    print("\n" + "="*80)
    print("测试：重新平衡分数")
    print("="*80)
    
    # 先读取之前提取的结果
    try:
        with open("test_output_sop_extraction.json", 'r', encoding='utf-8') as f:
            prev_result = json.load(f)
            checklist = prev_result.get('items', [])
    except:
        print("\n❌ 请先运行 test_extract_with_scoring()")
        return False
    
    if not checklist:
        print("\n❌ 质检项列表为空")
        return False
    
    print(f"\n当前总分：{sum(item.get('final_score', 0) for item in checklist)} 分")
    print("目标总分：100 分")
    
    url = f"{BASE_URL}/api/sop/rebalance-scores"
    
    data = {
        "checklist": checklist,
        "target_total": 100
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n✅ 平衡成功！\n")
                
                rebalanced = result.get('rebalanced_checklist', [])
                summary = result.get('scoring_summary', {})
                
                print("📊 平衡后摘要：")
                print(f"  总分：{summary.get('total_score', 0)} 分")
                print(f"  必须项：{summary.get('must_do_score', 0)} 分")
                print(f"  禁止项：{summary.get('must_not_score', 0)} 分")
                print(f"  建议项：{summary.get('should_do_score', 0)} 分")
                
                return True
            else:
                print(f"\n❌ 平衡失败：{result.get('error')}")
                return False
        else:
            print(f"\n❌ 请求失败，状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 异常：{e}")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("SOP 智能提取和评分功能测试套件")
    print("="*80)
    print("\n请确保：")
    print("1. Flask 应用正在运行 (python app.py)")
    print("2. 已配置 DASHSCOPE_API_KEY 环境变量")
    print("\n开始测试...\n")
    
    # 运行测试
    results = []
    
    # 测试1：智能提取 + 评分
    results.append(("智能提取+评分", test_extract_with_scoring()))
    
    # 测试2：获取评分规则
    results.append(("获取评分规则", test_scoring_rules()))
    
    # 测试3：调整分数
    results.append(("调整分数", test_adjust_score()))
    
    # 测试4：重新平衡
    results.append(("重新平衡", test_rebalance_scores()))
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
