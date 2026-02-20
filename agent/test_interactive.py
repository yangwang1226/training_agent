import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)

from agent import (
    ConversationalPromptAgent,
    InteractivePromptAgent,
    interactive_generate_prompt
)


def print_separator():
    print("\n" + "=" * 60)


def conversational_mode():
    print_separator()
    print("欢迎使用智能提示词生成系统（对话模式）")
    print("提示：像和朋友聊天一样告诉我您的需求，我会帮您生成提示词")
    print("输入 'quit' 退出，输入 'reset' 重新开始")
    print_separator()
    
    agent = ConversationalPromptAgent()
    
    initial_response = agent.chat("你好")
    print(f"\n助手：{initial_response}")
    
    while True:
        user_input = input("\n>>> ").strip()
        
        if user_input.lower() == 'quit':
            print("再见！")
            break
        
        if user_input.lower() == 'reset':
            agent.reset()
            print("已重置对话，让我们重新开始！")
            response = agent.chat("你好")
            print(f"\n助手：{response}")
            continue
        
        if user_input in ["开始生成", "生成", "生成提示词"]:
            if agent.is_ready_to_generate():
                print("\n正在生成提示词，请稍候...")
                full_prompt = agent.generate_prompt()
                print_separator()
                print("完整提示词：")
                print_separator()
                print(full_prompt)
                print("\n输入 'reset' 可以重新开始，输入 'quit' 退出")
            else:
                state = agent.get_current_state()
                missing = state.get_missing_info()
                print(f"\n还需要以下信息才能生成：{', '.join(missing)}")
                response = agent.chat("用户想生成提示词，但信息不完整")
                print(f"\n助手：{response}")
            continue
        
        response = agent.chat(user_input)
        print(f"\n助手：{response}")
        
        if agent.is_ready_to_generate():
            state = agent.get_current_state()
            print(f"\n[当前已收集信息]")
            print(f"  行业：{state.industry}")
            print(f"  角色：{state.role_type}")
            print(f"  购买意愿：{state.purchase_intent}")
            if state.custom_questions:
                print(f"  自定义问题：{state.custom_questions}")
            print("\n信息已收集完整！输入 '开始生成' 即可生成提示词")


def quick_mode():
    print_separator()
    print("快速模式 - 使用预设参数生成提示词")
    print_separator()
    
    result = interactive_generate_prompt(
        industry="教育培训",
        role_type="家长",
        purchase_intent="感兴趣",
        custom_questions=None,
        auto_generate=True,
        additional_requirements="学生是初二学生，数学成绩中等偏上，最近有下滑趋势",
        template_name="training_salse"
    )
    
    if result.success:
        print("\n生成成功！")
        print_separator()
        print("完整提示词：")
        print_separator()
        print(result.full_prompt)
    else:
        print(f"\n生成失败：{result.error_message}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_mode()
    else:
        print("\n请选择模式：")
        print("  1. 对话模式（推荐，自然对话收集信息）")
        print("  2. 快速模式（使用预设参数）")
        
        choice = input("\n>>> ").strip()
        
        if choice == "1":
            conversational_mode()
        elif choice == "2":
            quick_mode()
        else:
            print("无效选择，使用对话模式")
            conversational_mode()
