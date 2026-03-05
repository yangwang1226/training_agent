# 场景智能体重构实施计划

## 📌 项目概述

**目标**: 重构场景创建流程，不依赖提示词模板，完全依靠智能体思维链能力动态生成实时语音通话所需的提示词内容和考核维度。

**核心价值**:
- 更灵活的提示词生成机制
- 更智能的场景理解能力
- 更流畅的用户体验
- 完整的训练记录与评估闭环

---

## 🎯 需求分析

### 当前实现存在的问题

1. **依赖模板**: 当前 [ConversationalPromptAgent](file://c:\workspace\training_agent\agent\service\conversational\agent.py#L21-L767) 使用 [TemplateManager](file://c:\workspace\training_agent\agent\service\template_manager.py#L8-L92) 加载预定义模板 (`training_salse.txt`, `training_teacher.txt`)
2. **流程割裂**: 提示词生成、场景保存、对练测试是分离的步骤
3. **维度生成时机**: 考核维度在对话过程中生成，而非基于完整场景信息
4. **评估报告缺失**: 对练完成后缺少基于考核维度的详细评估报告

### 新方案设计

#### 1. 不加载提示词模板
- **移除**: `TemplateManager` 的模板加载逻辑
- **新增**: 基于思维链的结构化内容生成

#### 2. 智能体思维链生成内容
生成以下内容:
```
a. 背景信息 (background_info)
   - 行业背景
   - 场景设定
   - 角色关系
   
b. AI 模拟提出的主问题列表 (main_questions)
   - 3-5 个核心问题
   - 按逻辑顺序排列
   - 符合角色身份
   
c. 关联问题列表 (trigger_groups)
   - 话术触发关键词
   - 关联问题分组
   - 问题间的逻辑关系
   
d. 考核维度 (assessment_dimensions)
   - 基于行业特点
   - 基于场景复杂度
   - 3-4 个关键维度，每个维度 2-3 个评估要点
```

#### 3. 用户流程优化
```
信息收集 → 智能生成 → 确认开始 → 实时对练 → 评估报告
   ↓           ↓           ↓           ↓           ↓
 对话交互   思维链生成   直接跳转   qwen-omni   qwen-plus-3.5
```

#### 4. Realtime 页面改造
- **移除**: 模型选择功能
- **固定**: 使用 qwen-omni realtime 模型
- **确保**: 音频录制、文字转录正常保存

#### 5. 评估报告生成
- **触发时机**: 对练完成后自动触发
- **调用模型**: qwen-plus-3.5 (qwen3.5-plus)
- **输入**: 对话转录文字 + 考核维度
- **输出**: JSON 格式评估报告
- **保存**: 存入 `ai_coach_record` 表的 `ai_evaluate` 字段

---

## 📝 实施步骤

### 阶段一：创建新的场景智能体 (SceneAgent)

#### 1.1 创建 SceneAgent 核心类
**文件**: `agent/service/scene/scene_agent.py`

**核心功能**:
```python
class SceneAgent:
    - 通过对话收集场景信息
    - 使用思维链生成背景信息
    - 生成主问题列表
    - 生成关联问题分组
    - 生成考核维度
    - 构建完整提示词
```

**关键方法**:
- `chat(user_input: str) -> Dict` - 对话交互
- `generate_scene_content() -> SceneContent` - 生成场景内容
- `_generate_background_info() -> str` - 生成背景信息
- `_generate_main_questions() -> List[Dict]` - 生成主问题
- `_generate_trigger_groups() -> List[Dict]` - 生成关联问题
- `_generate_dimensions() -> List[Dimension]` - 生成考核维度
- `_build_prompt() -> str` - 构建提示词

#### 1.2 创建数据模型
**文件**: `agent/service/scene/models.py`

**数据类**:
```python
@dataclass
class SceneContent:
    industry: str
    role_type: str
    role_description: str
    background_info: str
    main_questions: List[Dict]
    trigger_groups: List[Dict]
    dimensions: List[Dimension]
    emotion_profile: EmotionProfile
    
@dataclass
class Dimension:
    dimension_name: str
    weight: float
    sub_criteria: Dict[str, str]
    
@dataclass
class EmotionProfile:
    emotion_type: str
    emotion_description: str
    speaking_style: str
    attitude: str
```

#### 1.3 创建思维链提示词
**文件**: `agent/service/scene/prompts.py`

**提示词设计**:
```python
# 思维链提示词示例
CHAIN_OF_THOUGHT_PROMPT = """
你是一个专业的场景设计专家。请按照以下步骤思考:

1. **分析行业特点**
   - 这个行业的典型场景是什么？
   - 从业者的主要工作职责是什么？
   - 常见的挑战和问题有哪些？

2. **构建背景信息**
   - 基于行业特点，设计一个具体的场景背景
   - 设定时间、地点、人物关系
   - 确保场景真实、接地气

3. **设计主问题列表**
   - AI 模拟的角色会提出哪些核心问题？
   - 问题应该符合角色身份和场景逻辑
   - 3-5 个问题，按对话顺序排列

4. **设计关联问题**
   - 用户说什么话会触发 AI 的特定问题？
   - 将问题分组，每组有明确的触发关键词
   - 问题要口语化、自然

5. **设计考核维度**
   - 这个场景下，哪些能力是最重要的？
   - 每个维度应该包含哪些具体的评估要点？
   - 权重分配要合理，总和为 1.0

请基于以上思考，生成结构化的场景内容。
"""
```

---

### 阶段二：创建新的路由接口

#### 2.1 重构 scene_routes.py
**文件**: `routes/scene_routes.py`

**新增接口**:
```python
# 创建场景会话
POST /api/scene/create
- 初始化场景智能体
- 返回 session_id

# 场景对话交互
POST /api/scene/chat
- 接收用户输入
- 调用 SceneAgent.chat()
- 返回对话内容和场景信息状态

# 生成场景内容
POST /api/scene/generate
- 调用 SceneAgent.generate_scene_content()
- 保存场景到数据库
- 返回场景 ID 和跳转 URL

# 获取场景详情
GET /api/scene/<scene_id>
- 返回场景完整信息
```

#### 2.2 扩展 realtime_routes.py
**文件**: `routes/realtime_routes.py`

**修改内容**:
```python
# WebSocket 连接时自动保存 record
@sock.route('/api/realtime/ws/<scene_id>')
def realtime_ws(ws, scene_id):
    # 生成 session_id
    session_id = generate_session_id()
    
    # 创建 recorder
    recorder = ConversationRecorder(scene_id, scene_name, provider)
    recorder.set_session_id(session_id)
    
    # 对练完成后，保存记录到数据库
    saved_path = recorder.save()
    
    # 触发评估报告生成
    if saved_path:
        assessment_service = AssessmentService()
        report = assessment_service.generate_report(
            session_id=session_id,
            transcript=recorder.get_transcript(),
            dimensions=scene_dimensions
        )
        
        # 保存评估报告到数据库
        save_assessment_to_db(session_id, report)
```

---

### 阶段三：评估报告生成服务

#### 3.1 扩展 AssessmentService
**文件**: `agent/evaluate_agent/assessment_service.py`

**新增方法**:
```python
class AssessmentService:
    def generate_report(
        self,
        session_id: str,
        transcript: str,
        dimensions: List[Dimension]
    ) -> AssessmentReport:
        """
        基于对话转录和考核维度生成评估报告
        
        Args:
            session_id: 训练会话 ID
            transcript: 对话转录文字
            dimensions: 考核维度列表
            
        Returns:
            AssessmentReport: 评估报告对象
        """
        # 1. 调用 qwen-plus-3.5 模型
        # 2. 解析 JSON 结果
        # 3. 返回评估报告
```

#### 3.2 创建评估提示词
**文件**: `agent/evaluate_agent/assessment_prompts.py`

**提示词设计**:
```python
ASSESSMENT_PROMPT = """
你是一个专业的培训评估专家。请根据以下信息生成详细的考核报告:

【场景信息】
- 行业：{industry}
- 角色：{role_type}
- 场景背景：{background_info}

【考核维度】
{dimensions_text}

【对话转录】
{transcript}

请按照以下 JSON 格式返回评估结果:
{{
    "overall_score": 85,
    "dimension_scores": [
        {{
            "dimension_name": "沟通能力",
            "score": 88,
            "feedback": "表达清晰，逻辑性强",
            "examples": ["具体对话示例"]
        }}
    ],
    "highlights": ["亮点 1", "亮点 2"],
    "improvements": ["改进建议 1", "改进建议 2"],
    "golden_sentences": ["金句 1", "金句 2"],
    "key_moments": [
        {{
            "turn": 5,
            "description": "关键时刻描述",
            "analysis": "分析说明"
        }}
    ],
    "summary": "综合评价总结"
}}
"""
```

#### 3.3 扩展数据库记录
**文件**: `database/record_dao.py`

**确保字段完整**:
```python
def save_coach_record(
    session_id: str,
    scene_id: int,
    user_id: int,
    word_content: str,        # JSON 格式对话内容
    oss_file_path: str,       # 音频文件路径
    call_duration: int,       # 通话时长
    ai_evaluate: str,         # AI 评估结果 (JSON)
    ai_advise: str,           # AI 建议
    score: int,               # 综合得分
    sop_result: str = None,
    audio_analysis: str = None
) -> bool
```

---

### 阶段四：前端页面改造

#### 4.1 创建场景创建页面
**文件**: `front_end/scene/create.html` (新建)

**页面功能**:
- 对话式交互界面
- 实时显示收集的信息
- 生成进度展示
- 成功提示 + 开始对练按钮

**关键逻辑**:
```javascript
// 对话交互
async function chat(message) {
    const response = await fetch('/api/scene/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
    });
    const data = await response.json();
    
    // 显示 AI 回复
    displayMessage(data.response);
    
    // 更新状态
    updateState(data.state);
}

// 生成场景
async function generate() {
    const response = await fetch('/api/scene/generate', {
        method: 'POST'
    });
    const data = await response.json();
    
    if (data.success) {
        // 显示成功提示
        showSuccess('场景生成成功！');
        
        // 询问是否开始对练
        if (confirm('是否开始对练测试？')) {
            // 跳转到 realtime 页面
            window.location.href = `/realtime/${data.scene_id}`;
        }
    }
}
```

#### 4.2 修改 realtime.html
**文件**: `front_end/realtime/templates/realtime.html`

**修改内容**:
- 移除模型选择下拉框
- 固定使用 qwen-omni 模型
- 确保"开始对练"按钮直接启动 WebSocket 连接

**关键代码**:
```javascript
// 移除模型选择逻辑
// const provider = document.getElementById('provider-select').value;
const provider = 'qwen'; // 固定使用 qwen

// 开始对练按钮
document.getElementById('start-btn').addEventListener('click', () => {
    connectWebSocket(sceneId, provider);
});
```

---

### 阶段五：数据流整合

#### 5.1 确保数据流完整性

**数据流向**:
```
场景创建 → 场景保存 → 对练 → 录音保存 → 转录 → 评估 → 报告保存
   ↓          ↓         ↓        ↓         ↓       ↓        ↓
SceneAgent  DB.insert  WS    recorder  whisper  LLM    DB.update
```

**关键检查点**:
1. ✅ SceneAgent 生成的内容正确保存到 `ai_coach_scene` 表
2. ✅ Realtime 页面正确加载场景提示词
3. ✅ WebSocket 连接时创建 session_id
4. ✅ 对练过程中录音和转录正常进行
5. ✅ 对练结束后保存到 `ai_coach_record` 表
6. ✅ 评估报告生成并更新到数据库

#### 5.2 Session 管理
**文件**: `app.py`

**确保 session_id 传递**:
```python
@app.before_request
def before_request():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
```

---

## 🔍 关键技术点

### 1. 思维链提示词设计
**核心思路**: 引导 LLM 按步骤思考，生成结构化内容

**示例**:
```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": f"我想创建一个{industry}行业的培训场景，角色是{role_type}"}
]

# 第一步：分析行业特点
messages.append({
    "role": "assistant",
    "content": "好的，让我先分析一下{industry}行业的特点..."
})

# 第二步：生成背景信息
messages.append({
    "role": "user",
    "content": "请基于行业特点，生成一个具体的场景背景"
})

# 第三步：生成问题列表
# 第四步：生成考核维度
# ...
```

### 2. JSON 输出稳定性
**技巧**:
- 使用 LangChain 的 `JsonOutputParser`
- 提供详细的格式说明
- 添加输出示例
- 使用 `_extract_json()` 方法提取 JSON

### 3. 评估报告调用时机
**方案**: 同步调用 (对练结束后立即生成)

**理由**:
- 用户体验更好，无需等待
- 数据一致性强
- 实现简单

**代码**:
```python
@sock.route('/api/realtime/ws/<scene_id>')
def realtime_ws(ws, scene_id):
    try:
        # ... WebSocket 通信 ...
    finally:
        # 保存录音
        saved_path = recorder.save()
        
        # 生成评估报告
        if saved_path:
            report = generate_assessment(
                session_id=recorder.session_id,
                transcript=recorder.get_transcript(),
                dimensions=scene_dimensions
            )
            
            # 保存到数据库
            save_assessment_to_db(recorder.session_id, report)
```

### 4. 错误处理
**关键点**:
- LLM 调用失败时使用默认值
- 数据库操作失败时回滚
- WebSocket 异常时优雅关闭
- 评估报告生成失败不影响录音保存

---

## 📊 数据库表结构确认

### ai_coach_scene 表
```sql
CREATE TABLE ai_coach_scene (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scene_name VARCHAR(200) NOT NULL,
    scene_prompt TEXT NOT NULL,
    dimension_config TEXT COMMENT '维度配置 JSON',
    role_type VARCHAR(100),
    role_description TEXT,
    industry VARCHAR(100),
    training_goal TEXT,
    full_evaluation_prompt TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);
```

### ai_coach_record 表
```sql
CREATE TABLE ai_coach_record (
    session_id VARCHAR(100) PRIMARY KEY,
    scene_id INT NOT NULL,
    user_id INT NOT NULL,
    word_content TEXT COMMENT '对话内容 JSON',
    oss_file_path VARCHAR(500),
    call_duration INT,
    ai_evaluate TEXT COMMENT 'AI 评估结果 JSON',
    ai_advise TEXT,
    score INT,
    sop_result TEXT,
    audio_analysis TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_delete INT DEFAULT 0
);
```

---

## ✅ 验证清单

### 功能验证
- [ ] 场景智能体能正确收集行业、角色信息
- [ ] 能生成背景信息、主问题列表、关联问题列表
- [ ] 能生成合理的考核维度
- [ ] 生成成功后显示确认对话框
- [ ] 点击确认后跳转到 realtime 页面
- [ ] Realtime 页面不显示模型选择
- [ ] 点击"开始对练"能正常连接 WebSocket
- [ ] 对练过程中录音正常
- [ ] 对练结束后保存音频文件
- [ ] 对练结束后保存转录文字
- [ ] 调用 qwen-plus-3.5 生成评估报告
- [ ] 评估报告 JSON 格式正确
- [ ] 评估报告保存到数据库

### 代码质量
- [ ] 无语法错误
- [ ] 无类型错误
- [ ] 异常处理完善
- [ ] 日志记录完整
- [ ] 代码符合项目规范

---

## 🚀 实施顺序

1. **阶段一**: 创建 SceneAgent 核心类 (2-3 小时)
2. **阶段二**: 创建路由接口 (1-2 小时)
3. **阶段三**: 评估报告服务 (2-3 小时)
4. **阶段四**: 前端页面改造 (2-3 小时)
5. **阶段五**: 数据流整合与测试 (2-3 小时)

**总预计时间**: 9-14 小时

---

## 💡 建议与优化

### 短期优化
1. **缓存机制**: 对同一行业的场景，缓存思维链生成的中间结果
2. **进度反馈**: 生成过程中显示进度条，提升用户体验
3. **预览功能**: 生成后允许用户预览和微调内容

### 长期优化
1. **场景模板库**: 积累优质场景，形成可复用的模板
2. **用户反馈**: 收集用户评分，优化生成质量
3. **A/B 测试**: 测试不同提示词的效果

---

## 📌 总结

你的设计方案**完全可行**，核心优势在于:
1. ✅ 去模板化，更灵活
2. ✅ 思维链生成，更智能
3. ✅ 流程优化，体验更好
4. ✅ 完整闭环，数据可追溯

实施过程中需要重点关注:
1. ⚠️ 思维链提示词的设计质量
2. ⚠️ JSON 输出的稳定性
3. ⚠️ 数据流的完整性
4. ⚠️ 异常情况的处理

现在开始实施吗？
