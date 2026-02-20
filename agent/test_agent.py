import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)

from agent import (
    PromptGeneratorAgent,
    generate_prompt,
    async_generate_prompt
)


def test_sync_generate():
    print("=" * 50)
    print("测试同步生成提示词")
    print("=" * 50)
    
    conversation = """
    老师：家长您好，我是小明的数学老师。
    家长：您好，老师。
    老师：小明最近数学成绩有些下滑，从上次的85分降到了70分。
    家长：是吗？他在家做作业倒是挺认真的。
    老师：作业完成情况是不错，但是课堂专注度不够，经常走神。
    """
    
    custom_requirements = """
    学生是初二学生，数学成绩中等偏上，最近有下滑趋势。
    家长比较关心孩子的学习状态和方法。
    """
    
    result = generate_prompt(
        conversation=conversation,
        template_name="training_teacher",
        custom_requirements=custom_requirements
    )
    
    if result.success:
        print("\n生成成功！")
        print("\n" + "=" * 50)
        print("完整提示词:")
        print("=" * 50)
        print(result.full_prompt)
    else:
        print(f"生成失败: {result.error_message}")


async def test_async_generate():
    print("\n" + "=" * 50)
    print("测试异步生成提示词")
    print("=" * 50)
    
    conversation = """
    老师：家长您好，我是小红班的班主任。
    家长：老师好，孩子最近表现怎么样？
    老师：小红学习很认真，但是英语成绩不太稳定。
    """
    
    result = await async_generate_prompt(
        conversation=conversation,
        template_name="training_teacher"
    )
    
    if result.success:
        print("\n生成成功！")
        print("\n" + "=" * 50)
        print("完整提示词:")
        print("=" * 50)
        print(result.full_prompt)
    else:
        print(f"生成失败: {result.error_message}")


def test_agent_class():
    print("\n" + "=" * 50)
    print("测试Agent类使用方式")
    print("=" * 50)
    
    agent = PromptGeneratorAgent(template_name="training_teacher")
    
    print(f"可用模板: {agent.get_available_templates()}")
    
    conversation = "老师反映孩子上课注意力不集中，作业完成质量下降。"
    
    result = agent.generate(conversation=conversation)
    
    if result.success:
        print("\n生成成功！")
        print("\n" + "=" * 50)
        print("完整提示词:")
        print("=" * 50)
        print(result.full_prompt)
    else:
        print(f"生成失败: {result.error_message}")


if __name__ == "__main__":
    test_sync_generate()
    
    asyncio.run(test_async_generate())
    
    test_agent_class()
