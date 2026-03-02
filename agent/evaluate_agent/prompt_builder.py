"""
评估提示词动态构建服务
根据维度配置生成评估提示词
"""
from typing import List

from .dimension_models import DimensionConfig


EVALUATION_OUTPUT_FORMAT = """
## 输出格式

请严格按以下JSON格式返回：

```json
{
  "dimension_scores": [
    {
      "dimension": "维度名称",
      "score": 85,
      "weight": 0.20,
      "reason": "评价理由",
      "sub_scores": {
        "子项1": 90,
        "子项2": 85
      }
    }
  ],
  "overall_score": 78,
  "level": "进阶",
  "highlights": [
    "亮点1",
    "亮点2"
  ],
  "improvements": [
    "改进建议1",
    "改进建议2"
  ],
  "golden_sentences": [
    "金句1"
  ],
  "key_moments": [
    {
      "turn": "第3轮",
      "type": "优秀表现/待改进/错失机会",
      "content": "对话内容",
      "handling": "处理评价",
      "suggestion": "建议"
    }
  ]
}
```

注意：
1. 每个维度分数为0-100的整数
2. 综合得分 = Σ(维度分数 × 权重)
3. 等级划分：90+专家，75-89熟练，60-74进阶，<60入门
"""


def build_evaluation_prompt(dimensions: List[DimensionConfig]) -> str:
    prompt_parts = [
        "你是一位资深培训评估专家，需要对培训对话进行专业评估。",
        "",
        "## 评估原则",
        "",
        "1. 客观公正：基于对话事实进行评估，不带主观偏见",
        "2. 具体明确：指出具体的表现，而非笼统的评价",
        "3. 建设性：提供可操作的改进建议",
        "4. 鼓励性：肯定优点，激励进步",
        "",
        "## 评估维度",
        ""
    ]
    
    for dim in dimensions:
        prompt_parts.append(f"### {dim.dimension_name} (权重: {dim.weight*100:.0f}%)")
        prompt_parts.append("")
        prompt_parts.append("评估要点：")
        for criterion, desc in dim.sub_criteria.items():
            prompt_parts.append(f"- {criterion}：{desc}")
        prompt_parts.append("")
        prompt_parts.append("评分标准：")
        for level, desc in dim.score_levels.items():
            prompt_parts.append(f"- {level}：{desc}")
        prompt_parts.append("")
    
    prompt_parts.append(EVALUATION_OUTPUT_FORMAT)
    
    return "\n".join(prompt_parts)


def build_dimension_prompt(dimensions: List[DimensionConfig]) -> str:
    prompt_parts = []
    
    for dim in dimensions:
        dim_prompt = f"""## {dim.dimension_name}评估

评估要点：
"""
        for criterion, desc in dim.sub_criteria.items():
            dim_prompt += f"- {criterion}：{desc}\n"
        
        dim_prompt += "\n评分标准：\n"
        for level, desc in dim.score_levels.items():
            dim_prompt += f"- {level}：{desc}\n"
        
        dim.evaluation_prompt = dim_prompt
        prompt_parts.append(dim_prompt)
    
    return "\n\n---\n\n".join(prompt_parts)


def build_realtime_evaluation_prompt(dimensions: List[DimensionConfig]) -> str:
    prompt_parts = [
        "对培训对话进行实时评估，及时发现问题并给出建议。",
        "",
        "## 当前对话状态",
        "- 行业：{industry}",
        "- 客户角色：{role}",
        "- 对话轮次：{current_turn}/{total_turns}",
        "- 当前阶段：{current_stage}",
        "",
        "## 最近对话内容",
        "{recent_transcript}",
        "",
        "## 评估任务",
        "",
        "### 1. 当前维度表现评估",
        "评估当前轮次在各维度的表现（0-100分）："
    ]
    
    for dim in dimensions:
        prompt_parts.append(f"- {dim.dimension_name}")
    
    prompt_parts.extend([
        "",
        "### 2. 关键事件检测",
        "检测对话中的关键事件：",
        "- 用户提出问题或表达需求",
        "- 表达积极或消极情绪",
        "- 询问具体信息",
        "- 表达疑虑或担忧",
        "",
        "### 3. 即时反馈建议",
        "针对当前表现，给出1-2句即时建议。",
        "",
        "### 4. 下一步行动建议",
        "建议下一步应该采取的行动。",
        "",
        "## 输出格式",
        "",
        "```json",
        "{",
        '  "current_performance": {'
    ])
    
    for i, dim in enumerate(dimensions):
        comma = "," if i < len(dimensions) - 1 else ""
        prompt_parts.append(f'    "{dim.dimension_name}": {{')
        prompt_parts.append('      "score": 85,')
        prompt_parts.append('      "comment": "评价"')
        prompt_parts.append(f'    }}{comma}')
    
    prompt_parts.extend([
        "  },",
        '  "key_events": [',
        "    {",
        '      "type": "事件类型",',
        '      "content": "事件内容",',
        '      "significance": "high/medium/low",',
        '      "suggestion": "建议"',
        "    }",
        "  ],",
        '  "immediate_feedback": "即时反馈",',
        '  "next_action": {',
        '    "recommended": "建议行动",',
        '    "reason": "理由"',
        "  }",
        "}",
        "```"
    ])
    
    return "\n".join(prompt_parts)


def build_improvement_prompt(dimensions: List[DimensionConfig]) -> str:
    prompt_parts = [
        "基于用户的能力画像，生成个性化改进建议和学习路径。",
        "",
        "## 用户能力画像",
        "{user_profile}",
        "",
        "## 薄弱维度详情",
        "{weak_dimensions}",
        "",
        "## 用户目标（如有）",
        "{user_goals}",
        "",
        "## 评估维度说明",
        ""
    ]
    
    for dim in dimensions:
        prompt_parts.append(f"### {dim.dimension_name} (权重: {dim.weight*100:.0f}%)")
        for criterion, desc in dim.sub_criteria.items():
            prompt_parts.append(f"- {criterion}：{desc}")
        prompt_parts.append("")
    
    prompt_parts.extend([
        "## 生成要求",
        "",
        "### 1. 优先级排序",
        "根据薄弱程度和重要性，确定改进优先级。",
        "",
        "### 2. 学习路径设计",
        "设计4周的学习路径：",
        "- 每周聚焦1-2个维度",
        "- 具体学习任务",
        "- 练习场景推荐",
        "- 预期目标",
        "",
        "### 3. 练习场景推荐",
        "推荐适合的训练场景。",
        "",
        "### 4. 关键技巧总结",
        "针对薄弱维度，总结3-5个关键技巧。"
    ])
    
    return "\n".join(prompt_parts)
