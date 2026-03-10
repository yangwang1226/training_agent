# AI 角色定位优化说明

## 🐛 问题描述

**症状**: 
- 用户说"模拟一个想看车的客户"
- 但生成的提示词却让 AI 扮演销售顾问
- 角色定位完全相反

**根本原因**:
1. 对话开始时没有明确确认 AI 应该扮演什么角色
2. 信息提取时没有专门提取 AI 角色
3. 状态管理中没有 AI 角色的字段

## ✅ 解决方案

### 核心设计原则

**系统定位**: 
- 主要用于训练**客服、销售、服务人员**等
- AI 扮演**客户、访客、顾客**等社会自然人
- 用户扮演**服务人员**进行对练

### 1. 修改系统提示词

**文件**: [`agent/service/scene/prompts.py`](file:///d:\workspace\training_agent\agent\service\scene\prompts.py#L7-L27)

**新增内容**:
```python
SYSTEM_PROMPT = """你是一个专业的场景设计专家，专门帮助用户创建 AI 培训教练场景。

**重要：角色定位确认**
在对话开始时，你必须明确确认：用户希望 AI 扮演什么角色？
- 如果用户说"模拟客户"、"模拟访客"等 → AI 扮演客户/访客（用户是销售/服务人员）
- 如果用户说"模拟销售"、"模拟客服"等 → AI 扮演销售/客服（用户是客户/访客）

**典型场景说明**：
- 销售培训：AI 模拟客户，用户扮演销售（最常见）
- 客服培训：AI 模拟客户/访客，用户扮演客服
- 服务培训：AI 模拟顾客，用户扮演服务人员

你的工作流程：
1. **首先确认角色定位**：明确 AI 要扮演什么角色
2. 通过对话收集用户的行业、具体角色等基本信息
3. 深入了解场景背景和具体需求
4. 使用思维链能力生成完整的场景内容
5. 确认无误后保存到数据库
"""
```

### 2. 优化初始对话

**文件**: [`routes/scene_create_routes.py`](file:///d:\workspace\training_agent\routes\scene_create_routes.py#L37-L55)

**修改前**:
```python
response = agent.chat("你好，我想创建一个培训场景")
```

**修改后**:
```python
initial_message = """你好！我是场景创建助手，专门帮你设计 AI 培训教练场景。

在开始之前，我需要先确认一个关键问题：

**你希望 AI 扮演什么角色？**

常见场景：
- 🎯 **销售培训**：AI 模拟客户，你扮演销售（最常见）
- 💁 **客服培训**：AI 模拟客户/访客，你扮演客服
- 🏪 **服务培训**：AI 模拟顾客，你扮演服务人员
- 其他：你可以自定义任何角色

请告诉我：
1. 你想创建什么行业的培训场景？
2. **你希望 AI 扮演什么角色**？（比如"模拟客户"、"模拟访客"等）

例如："我想创建一个汽车销售的培训场景，AI 模拟一个想看车的客户" """

response = agent.chat(initial_message)
```

### 3. 添加 AI 角色字段

**文件**: [`agent/service/scene/models.py`](file:///d:\workspace\training_agent\agent\service\scene\models.py#L170-L220)

**ConversationState 新增字段**:
```python
@dataclass
class ConversationState:
    industry: str = ""
    role_type: str = ""  # 用户的角色（销售、客服等）
    ai_role: str = ""    # AI 应该扮演的角色（客户、访客等）
    role_description: str = ""
    # ... 其他字段
    
    collected_info: Dict[str, bool] = field(default_factory=lambda: {
        "industry": False,
        "role": False,
        "ai_role": False,  # 新增：AI 角色是否确认
        "intent": False,
        "questions": False
    })
    
    def is_ready_for_generation(self) -> bool:
        """检查是否可以开始生成场景内容"""
        return (
            self.collected_info.get("industry", False) and
            self.collected_info.get("role", False) and
            self.collected_info.get("ai_role", False) and  # 必须确认 AI 角色
            self.extended_info_sufficient
        )
```

### 4. 更新信息提取逻辑

**文件**: [`agent/service/scene/prompts.py`](file:///d:\workspace\training_agent\agent\service\scene\prompts.py#L18-L65)

**INFO_EXTRACTION_PROMPT 新增内容**:
```python
INFO_EXTRACTION_PROMPT = """从用户输入中提取信息。

当前已收集信息:
- 行业：{industry}
- 用户角色：{role_type}
- AI 扮演角色：{ai_role}  # 新增
- 角色描述：{role_description}
- 延展信息：{extended_info}

**重要：AI 角色定位**
- 如果用户说"模拟客户"、"模拟访客"等 → AI 扮演客户/访客
- 如果用户说"模拟销售"、"模拟客服"等 → AI 扮演销售/客服

请返回 JSON 格式的提取结果，格式如下:
{{
    "industry": "提取的行业，如果没有则为 null",
    "role_type": "提取的用户角色，如果没有则为 null",
    "ai_role": "提取的 AI 角色（客户/访客/销售/客服等），如果没有则为 null",  # 新增
    "role_description": "角色描述，如果没有则为 null",
    "extended_info": {{...}},
    "additional_requirements": "额外需求，如果没有则为 null"
}}

注意:
1. extended_info 用于提取行业相关的背景信息
2. **ai_role 是关键信息**，必须准确提取用户希望 AI 扮演的角色  # 新增
3. 只有当用户明确提到新信息时才更新
4. 保持已有信息不变
"""
```

### 5. 更新状态管理

**文件**: [`agent/service/scene/agent.py`](file:///d:\workspace\training_agent\agent\service\scene\agent.py#L154-L182)

**_update_state 新增逻辑**:
```python
def _update_state(self, extraction_result: Dict[str, Any]):
    """更新状态"""
    # ... 其他更新逻辑
    
    # 更新 AI 角色（新增）
    if extraction_result.get("ai_role"):
        self.state.ai_role = extraction_result["ai_role"]
        self.state.collected_info["ai_role"] = True
    
    # ... 其他更新逻辑
```

**_get_state 新增返回**:
```python
def _get_state(self) -> Dict[str, Any]:
    """获取当前状态"""
    return {
        "industry": self.state.industry,
        "role_type": self.state.role_type,
        "ai_role": self.state.ai_role,  # 新增：AI 扮演的角色
        "role_description": self.state.role_description,
        # ... 其他字段
    }
```

### 6. 前端状态面板优化

**文件**: [`front_end/scene/templates/create.html`](file:///d:\workspace\training_agent\front_end\scene\templates\create.html#L38-L60)

**新增 AI 角色状态项**:
```html
<div class="status-items">
    <div class="status-item" id="status-industry">
        <span class="status-icon">🏢</span>
        <span class="status-label">行业</span>
        <span class="status-value" id="industry-value">-</span>
        <span class="status-indicator"></span>
    </div>
    <div class="status-item" id="status-role">
        <span class="status-icon">👤</span>
        <span class="status-label">你的角色</span>
        <span class="status-value" id="role-value">-</span>
        <span class="status-indicator"></span>
    </div>
    <div class="status-item" id="status-ai-role">  <!-- 新增 -->
        <span class="status-icon">🤖</span>
        <span class="status-label">AI 扮演</span>
        <span class="status-value" id="ai-role-value">-</span>
        <span class="status-indicator"></span>
    </div>
    <div class="status-item" id="status-extended">
        <span class="status-icon">📝</span>
        <span class="status-label">背景信息</span>
        <span class="status-value" id="extended-value">-</span>
        <span class="status-indicator"></span>
    </div>
</div>
```

**JavaScript 更新逻辑**:
```javascript
function updateStatus(state) {
    // ... 其他更新逻辑
    
    // 更新 AI 角色状态（新增）
    const aiRoleEl = document.getElementById('status-ai-role');
    const aiRoleValue = document.getElementById('ai-role-value');
    if (state.ai_role) {
        aiRoleEl.classList.add('completed');
        aiRoleEl.classList.remove('in-progress');
        aiRoleValue.textContent = state.ai_role;
    }
    
    // ... 其他更新逻辑
}
```

## 📊 修改文件清单

1. ✅ [`agent/service/scene/prompts.py`](file:///d:\workspace\training_agent\agent\service\scene\prompts.py)
   - 修改 SYSTEM_PROMPT，增加角色定位说明
   - 修改 INFO_EXTRACTION_PROMPT，增加 AI 角色提取

2. ✅ [`routes/scene_create_routes.py`](file:///d:\workspace\training_agent\routes\scene_create_routes.py)
   - 优化初始对话，主动询问 AI 角色

3. ✅ [`agent/service/scene/models.py`](file:///d:\workspace\training_agent\agent\service\scene\models.py)
   - ConversationState 增加 ai_role 字段
   - collected_info 增加 ai_role 状态
   - is_ready_for_generation 增加 ai_role 检查

4. ✅ [`agent/service/scene/agent.py`](file:///d:\workspace\training_agent\agent\service\scene\agent.py)
   - _update_state 增加 AI 角色更新
   - _get_state 增加 AI 角色返回

5. ✅ [`front_end/scene/templates/create.html`](file:///d:\workspace\training_agent\front_end\scene\templates\create.html)
   - 新增 AI 角色状态面板

6. ✅ [`front_end/scene/static/js/create.js`](file:///d:\workspace\training_agent\front_end\scene\static\js\create.js)
   - updateStatus 增加 AI 角色更新逻辑

## 🎯 新的使用流程

### 步骤 1: 访问场景创建页面
```
http://localhost:5000/scene/create/
```

### 步骤 2: AI 主动询问角色定位
```
AI: 你好！我是场景创建助手，专门帮你设计 AI 培训教练场景。

在开始之前，我需要先确认一个关键问题：

**你希望 AI 扮演什么角色？**

常见场景：
- 🎯 销售培训：AI 模拟客户，你扮演销售（最常见）
- 💁 客服培训：AI 模拟客户/访客，你扮演客服
- 🏪 服务培训：AI 模拟顾客，你扮演服务人员
- 其他：你可以自定义任何角色

请告诉我：
1. 你想创建什么行业的培训场景？
2. **你希望 AI 扮演什么角色**？（比如"模拟客户"、"模拟访客"等）

例如："我想创建一个汽车销售的培训场景，AI 模拟一个想看车的客户"
```

### 步骤 3: 用户回答
```
用户：我想创建一个汽车销售的培训场景，AI 模拟一个想看车的客户
```

### 步骤 4: 状态面板更新
```
📊 信息收集状态
🏢 行业：汽车 ✅
👤 你的角色：销售顾问 ✅
🤖 AI 扮演：客户 ✅
📝 背景信息：已收集足够信息 ✅
```

### 步骤 5: 继续收集其他信息
AI 会继续询问：
- 客户的特点（预算、需求等）
- 场景背景
- 其他细节

### 步骤 6: 生成场景内容
所有信息收集完成后（状态面板全绿），自动生成场景内容。

## ✅ 优化效果

### 修复前
```
❌ 用户：模拟一个想看车的客户
❌ AI 生成的提示词：你是一名汽车行业的销售
❌ 角色完全相反，无法使用
```

### 修复后
```
✅ 用户：模拟一个想看车的客户
✅ AI 确认：AI 扮演"客户"，用户扮演"销售"
✅ 生成的提示词：客户（AI）刚刚体验完车辆外观...
✅ 角色定位准确，可以正常对练
```

## 📝 最佳实践

### 1. 明确角色定位
在对话开始时就必须确认：
- AI 扮演什么角色？
- 用户扮演什么角色？

### 2. 典型场景说明
给用户提供参考：
- 销售培训：AI 模拟客户（最常见）
- 客服培训：AI 模拟客户/访客
- 服务培训：AI 模拟顾客

### 3. 状态可视化
前端状态面板清晰显示：
- 🏢 行业
- 👤 你的角色
- 🤖 AI 扮演
- 📝 背景信息

### 4. 强制确认
必须确认 AI 角色后才能生成场景：
```python
def is_ready_for_generation(self) -> bool:
    return (
        self.collected_info.get("industry", False) and
        self.collected_info.get("role", False) and
        self.collected_info.get("ai_role", False) and  # 必须确认
        self.extended_info_sufficient
    )
```

## 🚀 测试验证

### 测试对话
```
AI: 你好！我是场景创建助手...你希望 AI 扮演什么角色？

用户：我想创建一个汽车销售的培训场景，AI 模拟一个想看车的客户

AI: 好的！我理解了：
- 行业：汽车
- 你的角色：销售顾问
- AI 扮演：想看车的客户

请问这个客户有什么特点吗？比如预算、关注的车型等。

用户：客户预算 20-30 万，关注 SUV 车型，主要是家庭使用

AI: 明白了。请问客户的性格特点如何？比如温和、挑剔等。

用户：客户比较挑剔，注重安全

AI: 场景内容已生成完成！请点击下方「保存并开始对练」按钮...

[状态面板全绿]
🏢 行业：汽车 ✅
👤 你的角色：销售顾问 ✅
🤖 AI 扮演：客户 ✅
📝 背景信息：已收集足够信息 ✅
```

### 验证要点
1. ✅ AI 主动询问角色定位
2. ✅ 准确提取 AI 角色信息
3. ✅ 状态面板显示 AI 角色
4. ✅ 必须确认 AI 角色后才能生成
5. ✅ 生成的提示词中 AI 角色正确

## 📚 相关文档

- [场景创建使用指南](SCENE_CREATE_GUIDE.md)
- [场景创建流程说明](SCENE_CREATE_FLOW.md)
- [WebSocket 修复说明](WEBSOCKET_FIX.md)
- [Blueprint 修复说明](BLUEPRINT_FIX.md)
