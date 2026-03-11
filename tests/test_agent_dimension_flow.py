"""
测试智能体维度生成流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.service.conversational_agent import ConversationalPromptAgent, ConversationState

def test_conversation_state():
    print("=" * 60)
    print("测试 ConversationState 新增方法")
    print("=" * 60)
    
    state = ConversationState()
    
    print(f"初始状态:")
    print(f"  is_ready_for_dimensions: {state.is_ready_for_dimensions()}")
    print(f"  is_dimensions_confirmed: {state.is_dimensions_confirmed()}")
    print(f"  dimensions: {state.dimensions}")
    
    state.industry = "教育"
    state.role_type = "家长"
    state.purchase_intent = "一般"
    state.collected_info = {"industry": True, "role": True, "intent": True, "questions": True}
    state.extended_info = {"学生年级": "初二", "学科": "数学"}
    state.extended_info_sufficient = True
    
    print(f"\n设置信息后:")
    print(f"  is_ready_for_dimensions: {state.is_ready_for_dimensions()}")
    
    state.dimensions = [{"dimension_name": "沟通技巧", "weight": 0.25}]
    state.dimensions_confirmed = True
    
    print(f"\n设置维度后:")
    print(f"  is_dimensions_confirmed: {state.is_dimensions_confirmed()}")


def test_dimension_generation_flow():
    print("\n" + "=" * 60)
    print("测试智能体维度生成流程")
    print("=" * 60)
    
    agent = ConversationalPromptAgent()
    
    print("\n模拟对话流程...")
    
    response = agent.chat("我想生成一个教师培训的场景")
    print(f"用户: 我想生成一个教师培训的场景")
    print(f"助手: {response['content'][:100]}...")
    print(f"选项: {response.get('options', [])}")
    
    print(f"\n当前状态:")
    state = agent.get_current_state()
    print(f"  行业: {state.industry}")
    print(f"  角色: {state.role_type}")
    print(f"  is_ready_for_dimensions: {state.is_ready_for_dimensions()}")


if __name__ == "__main__":
    test_conversation_state()
    test_dimension_generation_flow()
