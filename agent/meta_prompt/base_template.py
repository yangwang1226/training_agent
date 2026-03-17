"""
元提示词基础模板
"""


class BaseMetaPromptTemplate:
    """元提示词基础模板"""
    
    COMMON_STRUCTURE = """
你是一个专业的AI提示词工程师，为{scene_type_cn}对练场景设计提示词。

【场景信息】
- 场景类型：{scene_type_cn}
- AI角色：{ai_role}
- 用户角色：{user_role}
- 行业背景：{industry}
- 场景描述：{scene_description}

【客户基本信息】
{background_info}

{scene_specific_instructions}

【输出要求】
1. 提示词让AI表现得像真实{ai_role}
2. 对话控制隐式嵌入角色设定中
3. 针对realtime语音模型优化
4. 字数控制在1500-2500字

【特别注意】
- 避免程序化指令
- 使用角色化描述
- 考虑真实对话中的情绪、打断、重复

请直接输出完整的场景提示词，不要包含任何其他说明。
"""
    
    def generate(self, scene_data: dict) -> str:
        """生成元提示词"""
        raise NotImplementedError("子类必须实现 generate 方法")
    
    def _format_question_list(self, questions: list) -> str:
        """格式化问题列表"""
        if not questions:
            return "无"
        return "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    def _format_trigger_rules(self, trigger_rules: dict) -> str:
        """格式化关联问题规则"""
        if not trigger_rules:
            return "无关联问题规则"
        
        formatted = []
        for group_name, rules in trigger_rules.items():
            keywords = rules.get('keywords', [])
            questions = rules.get('questions', [])
            
            formatted.append(f"分组 {group_name}:")
            formatted.append(f"  触发关键词：{', '.join(keywords)}")
            formatted.append(f"  触发问题：")
            for i, q in enumerate(questions, 1):
                formatted.append(f"    {i}. {q}")
        
        return "\n".join(formatted)
    
    def _format_additional_concerns(self, concerns: list) -> str:
        """格式化额外关注点（服务场景用）"""
        if not concerns:
            return "无额外关注点"
        return "\n".join([f"- {concern}" for concern in concerns])