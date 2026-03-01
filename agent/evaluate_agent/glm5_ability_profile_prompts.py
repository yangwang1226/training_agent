"""
GLM-5 能力画像功能开发提示词
基于图片中的评估维度设计
"""

# ============================================
# 1. 能力维度评估提示词
# ============================================

DIMENSION_EVALUATION_PROMPT = """你是一位资深销售培训专家，需要对销售对话进行专业评估。

## 评估维度（对应能力画像雷达图）

### 1. 沟通技巧 (Communication)
评估要点：
- 表达清晰：语言是否流畅、逻辑是否清晰
- 语速语调：语速适中、语调有感染力
- 倾听反馈：是否积极倾听、给予恰当反馈
- 礼貌用语：称呼得体、语气温和

评分标准：
- 90-100：表达专业流畅，极具感染力
- 75-89：表达清晰，沟通顺畅
- 60-74：基本清晰，偶有瑕疵
- 0-59：表达混乱，难以理解

### 2. 产品知识 (Product Knowledge)
评估要点：
- 产品熟悉度：对产品特点、功能、参数的了解程度
- 价值传递：能否清晰传达产品价值
- 竞品对比：与竞品的差异化优势
- 案例引用：能否引用成功案例增强说服力

评分标准：
- 90-100：产品专家级别，信手拈来
- 75-89：熟悉产品，能回答大部分问题
- 60-74：基本了解，但不够深入
- 0-59：产品知识匮乏，频繁卡壳

### 3. 需求挖掘 (Needs Discovery)
评估要点：
- 提问技巧：开放式/封闭式问题运用
- 信息收集：收集客户背景、预算、时间线
- 痛点识别：准确识别客户核心痛点
- 需求确认：确认理解无误，避免误解

评分标准：
- 90-100：深度挖掘，精准把握需求
- 75-89：善于提问，收集信息完整
- 60-74：有挖掘意识，但不够深入
- 0-59：被动回答，缺乏挖掘

### 4. 异议处理 (Objection Handling)
评估要点：
- 价格异议：处理价格敏感度的能力
- 信任建立：消除客户顾虑，建立信任
- 竞品应对：应对客户提及竞品的情况
- 顾虑消除：有效消除客户各种顾虑

评分标准：
- 90-100：从容应对，化异议为机会
- 75-89：处理得当，客户接受度高
- 60-74：基本处理，但不够巧妙
- 0-59：回避异议或处理不当

### 5. 促成技巧 (Closing Skills)
评估要点：
- 时机把握：识别购买信号，把握促单时机
- 话术运用：使用恰当的促单话术
- 紧迫感营造：适度营造紧迫感
- 成交引导：有效引导客户做出决策

评分标准：
- 90-100：精准把握，高效成交
- 75-89：善于促单，成交率高
- 60-74：有促单意识，但时机欠佳
- 0-59：缺乏促单技巧，错失机会

## 输出格式

请严格按以下JSON格式返回：

```json
{
  "dimension_scores": [
    {
      "dimension": "沟通技巧",
      "score": 85,
      "weight": 0.20,
      "reason": "表达清晰有条理，但在客户情绪激动时应更加耐心",
      "sub_scores": {
        "表达清晰": 90,
        "语速语调": 85,
        "倾听反馈": 80,
        "礼貌用语": 85
      }
    },
    {
      "dimension": "产品知识",
      "score": 78,
      "weight": 0.20,
      "reason": "产品参数介绍准确，但竞品对比不够深入",
      "sub_scores": {
        "产品熟悉度": 80,
        "价值传递": 75,
        "竞品对比": 70,
        "案例引用": 85
      }
    },
    {
      "dimension": "需求挖掘",
      "score": 82,
      "weight": 0.20,
      "reason": "善于使用开放式提问，准确识别客户痛点",
      "sub_scores": {
        "提问技巧": 85,
        "信息收集": 80,
        "痛点识别": 85,
        "需求确认": 80
      }
    },
    {
      "dimension": "异议处理",
      "score": 75,
      "weight": 0.20,
      "reason": "价格异议处理较好，但对竞品质疑应对不够有力",
      "sub_scores": {
        "价格异议": 80,
        "信任建立": 75,
        "竞品应对": 70,
        "顾虑消除": 75
      }
    },
    {
      "dimension": "促成技巧",
      "score": 70,
      "weight": 0.20,
      "reason": "识别了购买信号，但促单时机把握不够果断",
      "sub_scores": {
        "时机把握": 65,
        "话术运用": 75,
        "紧迫感营造": 70,
        "成交引导": 70
      }
    }
  ],
  "overall_score": 78,
  "level": "进阶",
  "highlights": [
    "需求挖掘深入，成功识别客户的核心痛点",
    "产品价值传递清晰，客户理解度高"
  ],
  "improvements": [
    "加强竞品知识学习，提升对比分析能力",
    "练习促单时机把握，提高成交转化率"
  ]
}
```

注意：
1. 每个维度分数为0-100的整数
2. 综合得分 = Σ(维度分数 × 权重)
3. 等级划分：90+专家，75-89熟练，60-74进阶，<60入门
"""


# ============================================
# 2. 能力画像生成提示词
# ============================================

ABILITY_PROFILE_GENERATION_PROMPT = """基于用户的历史训练数据，生成完整的能力画像。

## 输入数据

用户历史训练记录：
{training_history}

最新评估结果：
{latest_assessment}

## 能力画像生成要求

### 1. 基础统计
- 训练次数：累计训练次数
- 训练时长：累计训练时长（分钟）
- 最高得分：历史最高分
- 平均得分：历史平均分
- 能力等级：根据平均分判定

### 2. 五维能力分析（雷达图数据）
计算每个维度的历史平均分：
- 沟通技巧
- 产品知识
- 需求挖掘
- 异议处理
- 促成技巧

### 3. 优势领域识别
找出得分最高的2个维度，标注为优势领域。

### 4. 待提升领域识别
找出得分最低的2个维度，标注为待提升领域。

### 5. 成长轨迹分析
对比最近3次训练，分析各维度的变化趋势：
- 上升：进步明显
- 平稳：保持稳定
- 下降：需要关注

### 6. 个性化建议
基于能力画像，生成针对性的改进建议。

## 输出格式

```json
{
  "basic_stats": {
    "training_count": 15,
    "total_duration_minutes": 180,
    "highest_score": 88,
    "average_score": 76,
    "current_level": "熟练"
  },
  "dimension_analysis": {
    "沟通技巧": {
      "current_score": 82,
      "historical_avg": 80,
      "trend": "上升",
      "trend_value": +2
    },
    "产品知识": {
      "current_score": 75,
      "historical_avg": 72,
      "trend": "上升",
      "trend_value": +3
    },
    "需求挖掘": {
      "current_score": 85,
      "historical_avg": 83,
      "trend": "平稳",
      "trend_value": 0
    },
    "异议处理": {
      "current_score": 70,
      "historical_avg": 73,
      "trend": "下降",
      "trend_value": -3
    },
    "促成技巧": {
      "current_score": 68,
      "historical_avg": 70,
      "trend": "下降",
      "trend_value": -2
    }
  },
  "radar_chart_data": [
    {"dimension": "沟通技巧", "score": 82, "full_mark": 100},
    {"dimension": "产品知识", "score": 75, "full_mark": 100},
    {"dimension": "需求挖掘", "score": 85, "full_mark": 100},
    {"dimension": "异议处理", "score": 70, "full_mark": 100},
    {"dimension": "促成技巧", "score": 68, "full_mark": 100}
  ],
  "strength_areas": [
    {
      "dimension": "需求挖掘",
      "score": 85,
      "description": "善于提问，能准确把握客户需求",
      "evidence": "在最近5次训练中，需求挖掘维度平均得分85分"
    },
    {
      "dimension": "沟通技巧",
      "score": 82,
      "description": "表达清晰，沟通流畅",
      "evidence": "客户反馈积极，沟通顺畅度高"
    }
  ],
  "improvement_areas": [
    {
      "dimension": "促成技巧",
      "score": 68,
      "description": "促单时机把握不够精准",
      "suggestions": [
        "学习识别购买信号的7个关键指标",
        "练习5种常用的促单话术",
        "模拟训练：把握促单时机"
      ]
    },
    {
      "dimension": "异议处理",
      "score": 70,
      "description": "竞品对比应对能力有待提升",
      "suggestions": [
        "深入学习主要竞品的优劣势",
        "准备3套竞品对比话术",
        "练习价格异议处理技巧"
      ]
    }
  ],
  "growth_trend": {
    "overall": "稳步提升",
    "description": "近3次训练综合得分从72分提升到76分，进步明显",
    "dimension_trends": [
      {"dimension": "需求挖掘", "trend": "持续优秀", "change": "保持85分高位"},
      {"dimension": "沟通技巧", "trend": "稳步提升", "change": "从78分提升到82分"},
      {"dimension": "促成技巧", "trend": "需要关注", "change": "从72分下降到68分"}
    ]
  },
  "personalized_advice": {
    "priority": "重点提升促成技巧",
    "action_plan": [
      {
        "week": 1,
        "focus": "学习促单理论",
        "tasks": ["阅读《销售促单技巧》第1-3章", "观看促单技巧视频课程"],
        "target": "掌握促单时机识别方法"
      },
      {
        "week": 2,
        "focus": "话术练习",
        "tasks": ["背诵5种促单话术", "进行话术模拟练习"],
        "target": "能够熟练运用促单话术"
      },
      {
        "week": 3,
        "focus": "实战演练",
        "tasks": ["完成5次模拟对话训练", "分析促单成功/失败案例"],
        "target": "促单技巧得分提升至75分"
      }
    ],
    "recommended_scenes": [
      "价格敏感型客户促单场景",
      "犹豫型客户促单场景",
      "对比竞品后促单场景"
    ]
  },
  "achievements": [
    {
      "name": "需求挖掘专家",
      "description": "需求挖掘维度连续3次得分超过85分",
      "date": "2025-02-15"
    },
    {
      "name": "进步之星",
      "description": "单次训练综合得分提升超过10分",
      "date": "2025-02-10"
    }
  ]
}
```
"""


# ============================================
# 3. 实时评估提示词
# ============================================

REALTIME_EVALUATION_PROMPT = """对销售对话进行实时评估，及时发现问题并给出建议。

## 当前对话状态
- 行业：{industry}
- 客户角色：{role}
- 对话轮次：{current_turn}/{total_turns}
- 当前阶段：{current_stage}

## 最近对话内容
{recent_transcript}

## 评估任务

### 1. 当前维度表现评估
评估当前轮次在各维度的表现（0-100分）：
- 沟通技巧
- 产品知识
- 需求挖掘
- 异议处理
- 促成技巧

### 2. 关键事件检测
检测对话中的关键事件：
- 客户提出异议
- 表达购买意向
- 询问价格/优惠
- 提及竞品
- 要求更多信息

### 3. 即时反馈建议
针对当前表现，给出1-2句即时建议。

### 4. 下一步行动建议
建议下一步应该：
- 继续深入挖掘需求
- 介绍产品特点
- 处理客户异议
- 尝试促单
- 确认成交意向

## 输出格式

```json
{
  "current_performance": {
    "沟通技巧": {
      "score": 85,
      "comment": "表达清晰，语速适中"
    },
    "产品知识": {
      "score": 80,
      "comment": "产品介绍准确"
    },
    "需求挖掘": {
      "score": 75,
      "comment": "可以继续深入挖掘"
    },
    "异议处理": {
      "score": 70,
      "comment": "等待客户提出异议"
    },
    "促成技巧": {
      "score": 60,
      "comment": "当前阶段不宜促单"
    }
  },
  "key_events": [
    {
      "type": "需求表达",
      "content": "客户提到需要解决XX问题",
      "significance": "high",
      "suggestion": "深入挖掘具体需求细节"
    }
  ],
  "immediate_feedback": "您的问题很有针对性，建议继续追问客户的具体使用场景。",
  "next_action": {
    "recommended": "需求挖掘",
    "reason": "客户刚表达了需求，是深入挖掘的好时机",
    "suggested_questions": [
      "您目前使用的是什么解决方案？",
      "这个问题对您的工作影响有多大？",
      "您希望达到什么样的效果？"
    ]
  },
  "risk_alert": null
}
```
"""


# ============================================
# 4. 评估报告生成提示词
# ============================================

EVALUATION_REPORT_PROMPT = """基于单次训练对话，生成详细的评估报告。

## 训练信息
- 场景名称：{scene_name}
- 行业：{industry}
- 客户角色：{role}
- 难度等级：{difficulty}
- 对话时长：{duration}秒
- 对话轮次：{turn_count}

## 完整对话记录
{full_transcript}

## 评估维度得分
{dimension_scores}

## 报告生成要求

### 1. 总体评价
- 综合得分及等级
- 整体表现总结（2-3句话）

### 2. 维度详细分析
对每个维度进行详细分析：
- 得分及评价
- 优点列举
- 不足指出
- 改进建议

### 3. 关键对话节点
找出对话中的关键节点：
- 表现优秀的时刻（金句）
- 需要改进的时刻
- 错失的机会

### 4. 对比分析
与上一次训练对比（如有）：
- 进步维度
- 退步维度
- 保持维度

### 5. 具体改进建议
给出3-5条具体可执行的改进建议。

### 6. 推荐学习资源
推荐相关的学习资源。

## 输出格式

```json
{
  "report_summary": {
    "overall_score": 78,
    "level": "进阶",
    "duration": "5分32秒",
    "turns": 12,
    "summary": "本次对话表现良好，需求挖掘能力突出，但在促单时机把握上还有提升空间。整体沟通流畅，客户满意度较高。"
  },
  "dimension_details": [
    {
      "dimension": "沟通技巧",
      "score": 82,
      "evaluation": "优秀",
      "strengths": [
        "语言表达清晰流畅，逻辑性强",
        "语速适中，语调有感染力",
        "礼貌用语使用得当"
      ],
      "weaknesses": [
        "在客户情绪激动时，应更加耐心倾听"
      ],
      "suggestions": [
        "练习情绪管理，保持冷静",
        "学习更多共情表达技巧"
      ]
    }
  ],
  "key_moments": [
    {
      "type": "golden",
      "time": "02:15",
      "content": "您说得对，价格确实是考虑因素。不过让我帮您算一笔账...",
      "analysis": "很好地处理了价格异议，通过价值分析转移焦点",
      "score": 90
    },
    {
      "type": "improvement",
      "time": "04:30",
      "content": "客户询问付款方式",
      "analysis": "这是明确的购买信号，应该立即进行促单，但错过了时机",
      "suggestion": "识别购买信号后，应立即引导成交"
    }
  ],
  "comparison": {
    "has_previous": true,
    "previous_score": 72,
    "improvement": +6,
    "improved_dimensions": ["沟通技巧", "需求挖掘"],
    "declined_dimensions": ["促成技巧"],
    "stable_dimensions": ["产品知识", "异议处理"]
  },
  "improvement_plan": [
    {
      "priority": 1,
      "area": "促成技巧",
      "current_score": 68,
      "target_score": 80,
      "actions": [
        "学习7种购买信号识别方法",
        "练习5种促单话术",
        "完成10次促单专项训练"
      ],
      "timeline": "2周内"
    }
  ],
  "learning_resources": [
    {
      "type": "video",
      "title": "销售促单技巧实战",
      "description": "讲解如何识别购买信号和把握促单时机",
      "duration": "45分钟"
    },
    {
      "type": "article",
      "title": "金牌销售的促单话术",
      "description": "20个实用的促单话术模板",
      "read_time": "15分钟"
    }
  ],
  "next_training_recommendation": {
    "recommended_scene": "犹豫型客户促单场景",
    "reason": "针对性提升促单技巧",
    "difficulty": "进阶",
    "focus_dimensions": ["促成技巧", "异议处理"]
  }
}
```
"""


# ============================================
# 5. 改进建议生成提示词
# ============================================

IMPROVEMENT_SUGGESTION_PROMPT = """基于用户的能力画像，生成个性化的改进建议和学习路径。

## 用户能力画像
{ability_profile}

## 薄弱维度详情
{weak_dimensions}

## 用户目标（如有）
{user_goals}

## 生成要求

### 1. 优先级排序
根据薄弱程度和重要性，确定改进优先级。

### 2. 学习路径设计
设计4周的学习路径：
- 每周聚焦1-2个维度
- 具体学习任务
- 练习场景推荐
- 预期目标

### 3. 练习场景推荐
推荐适合的训练场景：
- 场景名称
- 难度等级
- 训练重点
- 预期收获

### 4. 关键技巧总结
针对薄弱维度，总结3-5个关键技巧。

### 5. 进度追踪建议
建议如何追踪学习进度和效果。

## 输出格式

```json
{
  "priority_ranking": [
    {
      "rank": 1,
      "dimension": "促成技巧",
      "current_score": 68,
      "target_score": 80,
      "priority_reason": "直接影响成交率，且与需求挖掘能力不匹配"
    },
    {
      "rank": 2,
      "dimension": "异议处理",
      "current_score": 70,
      "target_score": 80,
      "priority_reason": "影响客户信任建立，需要加强"
    }
  ],
  "learning_path": {
    "week_1": {
      "focus": "促单理论基础",
      "tasks": [
        {
          "day": 1,
          "task": "阅读《销售促单心理学》第1-2章",
          "estimated_time": "60分钟"
        },
        {
          "day": 2,
          "task": "观看视频课程：识别购买信号",
          "estimated_time": "45分钟"
        },
        {
          "day": 3,
          "task": "完成模拟训练：促单时机判断",
          "estimated_time": "30分钟"
        }
      ],
      "practice_scene": "标准促单场景",
      "target": "掌握购买信号识别方法"
    },
    "week_2": {
      "focus": "促单话术练习",
      "tasks": [
        {
          "day": 1,
          "task": "学习5种促单话术模板",
          "estimated_time": "45分钟"
        },
        {
          "day": 2,
          "task": "话术背诵与录音练习",
          "estimated_time": "30分钟"
        },
        {
          "day": 3,
          "task": "模拟对话训练",
          "estimated_time": "45分钟"
        }
      ],
      "practice_scene": "犹豫型客户促单",
      "target": "能够熟练运用促单话术"
    },
    "week_3": {
      "focus": "异议处理提升",
      "tasks": [
        {
          "day": 1,
          "task": "学习常见异议类型及应对方法",
          "estimated_time": "60分钟"
        },
        {
          "day": 2,
          "task": "竞品知识学习",
          "estimated_time": "90分钟"
        }
      ],
      "practice_scene": "价格异议处理场景",
      "target": "提升异议处理能力至75分"
    },
    "week_4": {
      "focus": "综合实战",
      "tasks": [
        {
          "day": 1,
          "task": "完成3次完整模拟训练",
          "estimated_time": "60分钟"
        },
        {
          "day": 2,
          "task": "复盘分析，总结改进点",
          "estimated_time": "30分钟"
        }
      ],
      "practice_scene": "综合销售场景",
      "target": "综合得分提升至80分"
    }
  },
  "recommended_scenes": [
    {
      "scene_name": "价格敏感型客户促单",
      "difficulty": "进阶",
      "focus": ["促成技巧", "异议处理"],
      "expected_gain": "提升价格异议处理和促单能力"
    },
    {
      "scene_name": "竞品对比场景",
      "difficulty": "熟练",
      "focus": ["产品知识", "异议处理"],
      "expected_gain": "增强竞品应对能力"
    }
  ],
  "key_techniques": [
    {
      "technique": "SPIN提问法",
      "description": "通过情境、问题、暗示、需求确认四个步骤挖掘需求",
      "application": "需求挖掘阶段使用"
    },
    {
      "technique": "假设成交法",
      "description": "假设客户已经决定购买，讨论具体实施细节",
      "application": "客户表现出购买意向时使用"
    },
    {
      "technique": "价值对比法",
      "description": "将价格与价值对比，强调长期收益",
      "application": "客户对价格有异议时使用"
    }
  ],
  "progress_tracking": {
    "metrics": [
      "每周完成训练次数",
      "各维度得分变化",
      "综合得分提升幅度"
    ],
    "milestones": [
      {
        "week": 2,
        "milestone": "促单技巧得分达到75分",
        "reward": "获得'促单新手'徽章"
      },
      {
        "week": 4,
        "milestone": "综合得分达到80分",
        "reward": "获得'销售进阶'徽章"
      }
    ]
  }
}
```
"""


# ============================================
# 6. 数据模型定义（供GLM-5参考）
# ============================================

DATA_MODEL_DEFINITION = """
## 数据模型定义

### UserAbilityProfile（用户能力画像）
```python
@dataclass
class UserAbilityProfile:
    user_id: str                          # 用户ID
    overall_score: float                  # 综合得分
    dimension_scores: Dict[str, float]    # 五维得分
    training_count: int                   # 训练次数
    total_duration: int                   # 累计时长（分钟）
    level: str                            # 能力等级
    strength_areas: List[str]             # 优势领域
    improvement_areas: List[str]          # 待提升领域
    created_at: datetime                  # 创建时间
    updated_at: datetime                  # 更新时间
```

### TrainingSession（训练会话）
```python
@dataclass
class TrainingSession:
    session_id: str                       # 会话ID
    user_id: str                          # 用户ID
    scene_id: str                         # 场景ID
    industry: str                         # 行业
    role: str                             # 客户角色
    difficulty: str                       # 难度
    status: str                           # 状态
    transcript: List[TranscriptMessage]   # 对话记录
    assessment: AssessmentResult          # 评估结果
    start_time: datetime                  # 开始时间
    end_time: datetime                    # 结束时间
    duration_seconds: int                 # 时长（秒）
```

### AssessmentResult（评估结果）
```python
@dataclass
class AssessmentResult:
    overall_score: float                  # 综合得分
    dimension_scores: List[DimensionScore] # 维度得分
    highlights: List[str]                 # 亮点
    improvements: List[str]               # 改进点
    golden_sentences: List[str]           # 金句
    key_moments: List[KeyMoment]          # 关键节点
    completion_rate: float                # 完成度
    summary: str                          # 总结
```

### DimensionScore（维度得分）
```python
@dataclass
class DimensionScore:
    dimension_name: str                   # 维度名称
    score: float                          # 得分
    weight: float                         # 权重
    reason: str                           # 评价理由
    sub_scores: Dict[str, float]          # 子项得分
```
"""


# ============================================
# 7. API接口设计（供GLM-5参考）
# ============================================

API_DESIGN = """
## API接口设计

### 1. 获取用户能力画像
```
GET /api/ability-profile/{user_id}
Response:
{
  "user_id": "user_123",
  "overall_score": 76,
  "level": "熟练",
  "dimension_scores": {
    "沟通技巧": 82,
    "产品知识": 75,
    "需求挖掘": 85,
    "异议处理": 70,
    "促成技巧": 68
  },
  "training_count": 15,
  "total_duration": 180,
  "strength_areas": ["需求挖掘", "沟通技巧"],
  "improvement_areas": ["促成技巧", "异议处理"]
}
```

### 2. 获取雷达图数据
```
GET /api/ability-profile/{user_id}/radar
Response:
{
  "dimensions": [
    {"name": "沟通技巧", "score": 82, "full_mark": 100},
    {"name": "产品知识", "score": 75, "full_mark": 100},
    {"name": "需求挖掘", "score": 85, "full_mark": 100},
    {"name": "异议处理", "score": 70, "full_mark": 100},
    {"name": "促成技巧", "score": 68, "full_mark": 100}
  ]
}
```

### 3. 获取训练历史
```
GET /api/training-history/{user_id}
Query: limit=10, offset=0
Response:
{
  "sessions": [...],
  "total": 25,
  "average_score": 76
}
```

### 4. 获取评估报告
```
GET /api/evaluation-report/{session_id}
Response:
{
  "report_summary": {...},
  "dimension_details": [...],
  "key_moments": [...],
  "improvement_plan": [...]
}
```

### 5. 获取改进建议
```
GET /api/improvement-suggestions/{user_id}
Response:
{
  "priority_ranking": [...],
  "learning_path": {...},
  "recommended_scenes": [...]
}
```
"""
