# 场景创建与语音对练使用指南

## 🎯 功能说明

本系统支持**场景智能创建**和**语音实时对练**两大核心功能：

1. **场景创建**：通过对话式交互，AI 智能体帮你生成定制化的培训场景
2. **语音对练**：使用 Qwen-Omni 实时语音模型，进行沉浸式销售对练

## 📱 完整使用流程

### 第一步：访问场景创建页面

```
http://localhost:5000/scene/create/
```

页面会自动初始化对话，显示欢迎消息。

### 第二步：对话收集信息

#### 示例对话：

**AI**: 你好！我是场景创建助手。请告诉我你想创建什么行业的培训场景？比如"我想创建一个汽车销售的培训场景"。

**你**: 我想创建一个汽车销售的培训场景

**AI**: 好的！请问您希望 AI 模拟什么角色呢？比如"客户"、"销售经理"等。

**你**: 模拟一个想看车的客户

**AI**: 明白了。请问这个客户有什么特点吗？比如预算、关注的车型、购车需求等。

**你**: 客户预算 20-30 万，关注 SUV 车型，主要是家庭使用，有两个孩子

**你**: 客户比较挑剔，注重安全，正在对比传统豪华燃油车与新能源车

继续提供更多信息，直到**状态面板全部变绿**：
- 🏢 行业：汽车
- 👤 角色：客户
- 📝 背景信息：已收集足够信息

### 第三步：自动生成场景内容

当信息收集完成后，AI 会自动生成完整的场景内容，包括：
- ✅ 场景背景信息
- ✅ 主问题列表（3-5 个）
- ✅ 关联问题分组
- ✅ 考核维度（3-4 个）
- ✅ 情绪画像

此时会显示 AI 回复：

```
🎉 场景内容已生成完成！

包括背景信息、问题列表、关联问题和考核维度。

请点击下方「保存并开始对练」按钮，进入语音实时对练界面！
```

**底部操作栏会自动显示**：
- ✅ 场景内容生成成功！
- [查看生成的内容] [**保存并开始对练**]

### 第四步：进入语音对练

#### 方式 1：直接开始对练（推荐）

点击 **"保存并开始对练"** 按钮：
1. 系统自动保存场景到数据库
2. 显示成功提示："场景保存成功！正在跳转到对练页面..."
3. 自动跳转到语音对练页面：`http://localhost:5000/realtime/{scene_id}`

#### 方式 2：先预览再对练

1. 点击 **"查看生成的内容"** 按钮
2. 在模态框中预览完整场景内容：
   - 📍 场景背景
   - ❓ 主问题列表
   - 🔗 关联问题分组
   - 📊 考核维度
   - 😊 情绪画像
3. 点击模态框中的 **"开始对练"** 按钮
4. 跳转到语音对练页面

### 第五步：语音实时对练

在对练页面：

1. **点击"开始对话"按钮**
   - 系统会请求麦克风权限
   - 允许后开始语音交互

2. **进行语音对话**
   - 对着麦克风说话
   - AI 会实时语音回复
   - 文字内容同步显示在聊天区

3. **查看实时数据**
   - 通话时长
   - 交互轮数
   - 音频波形可视化

4. **结束对话**
   - 点击"结束对话"按钮
   - 系统自动保存录音和对话
   - 生成 AI 评估报告

### 第六步：查看评估报告

对练完成后，系统自动生成评估报告：
- 📊 综合得分
- 📈 各维度得分和反馈
- ✨ 亮点分析
- 💡 改进建议
- 🎯 关键时刻分析
- 💬 金句摘录

## 🎨 界面优化

### Markdown 渲染

AI 回复内容支持 Markdown 格式，显示更清晰：

```markdown
# 标题
**粗体** 重点内容
- 列表项
> 引用内容
```

### Toast 提示

操作反馈更友好：
- ✅ 成功提示（绿色）
- ❌ 错误提示（红色）
- ⏳ 加载状态提示

### 按钮状态

- 正常状态：可点击
- 禁用状态：灰色，显示"生成中..."或"保存中..."
- 悬停效果：放大和阴影

## 🔧 技术实现

### 前端关键功能

#### 1. Markdown 渲染
```javascript
function renderMarkdown(text) {
    // 支持标题、粗体、斜体、列表、引用等
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // ... 更多格式支持
}
```

#### 2. Toast 提示
```javascript
function showToast(message, type = 'info') {
    // 自动消失的提示框
    // 支持 success 和 error 两种类型
}
```

#### 3. 保存并跳转
```javascript
async function saveAndStartTraining() {
    // 1. 保存场景
    const response = await fetch('/api/scene/generate', {
        method: 'POST'
    });
    
    // 2. 显示提示
    showToast('场景保存成功！正在跳转到对练页面...', 'success');
    
    // 3. 延迟跳转
    setTimeout(() => {
        window.location.href = `/realtime/${currentSceneId}`;
    }, 1000);
}
```

### 后端接口

#### 场景生成接口
```python
@scene_create_bp.route('/generate', methods=['POST'])
def generate_scene():
    # 1. 生成场景内容
    scene_content = agent.generate_scene_content()
    
    # 2. 保存到数据库
    scene_id = db_module.save_scene(
        scene_name=scene_name,
        scene_prompt=full_prompt,
        dimension_config=dimension_config,
        # ... 其他参数
    )
    
    # 3. 返回场景信息和跳转 URL
    return jsonify({
        'success': True,
        'scene_id': scene_id,
        'redirect_url': f'/realtime/{scene_id}'
    })
```

## ⚠️ 常见问题

### 问题 1: 操作栏不显示

**症状**: 对话完成后，底部没有出现按钮

**解决方案**:
1. 检查状态面板是否全部变绿
2. 查看浏览器控制台（F12）是否有错误
3. 刷新页面重试

### 问题 2: 点击按钮没反应

**症状**: 点击"保存并开始对练"后无响应

**解决方案**:
1. 查看浏览器控制台是否有网络请求错误
2. 检查后端日志
3. 确认数据库连接正常

### 问题 3: 跳转后页面空白

**症状**: 跳转到 realtime 页面后显示空白

**解决方案**:
1. 检查 URL 是否正确（包含 scene_id）
2. 查看浏览器控制台错误
3. 确认 realtime 路由已注册

### 问题 4: 麦克风无法使用

**症状**: 点击"开始对话"后麦克风无响应

**解决方案**:
1. 允许浏览器访问麦克风
2. 检查系统麦克风权限设置
3. 使用 Chrome 或 Edge 浏览器
4. 确保使用 HTTPS 或 localhost

## 📊 数据库表

### ai_coach_scene（场景表）
```sql
CREATE TABLE ai_coach_scene (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scene_name VARCHAR(255),
    scene_prompt TEXT,
    dimension_config TEXT,
    role_type VARCHAR(100),
    role_description TEXT,
    industry VARCHAR(100),
    training_goal TEXT,
    full_evaluation_prompt TEXT,
    status INT DEFAULT 0,
    created_time DATETIME,
    deleted INT DEFAULT 0
);
```

### ai_coach_record（训练记录表）
```sql
CREATE TABLE ai_coach_record (
    session_id VARCHAR(100) PRIMARY KEY,
    scene_id INT,
    user_id INT,
    word_content TEXT,
    oss_file_path VARCHAR(500),
    call_duration INT,
    ai_evaluate TEXT,
    ai_advise TEXT,
    score INT,
    created_time DATETIME
);
```

## 🚀 快速测试

### 测试脚本

```bash
# 1. 启动应用
python app.py

# 2. 访问页面
http://localhost:5000/scene/create/

# 3. 测试对话
# 按照上面的示例对话进行

# 4. 点击"保存并开始对练"
# 自动跳转到语音对练页面

# 5. 开始语音对练
# 点击"开始对话"，对着麦克风说话
```

### API 测试

```bash
# 创建场景会话
curl -X POST http://localhost:5000/api/scene/create

# 对话交互
curl -X POST http://localhost:5000/api/scene/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想创建一个汽车销售的培训场景"}'

# 生成场景内容
curl -X POST http://localhost:5000/api/scene/generate

# 访问 realtime 页面
# 浏览器打开返回的 redirect_url
```

## ✅ 检查清单

使用前确认：
- [ ] Python 环境配置完成
- [ ] 数据库连接正常
- [ ] Qwen API 密钥已配置
- [ ] Flask 应用启动成功
- [ ] 端口 5000 可访问
- [ ] 浏览器支持 WebSocket
- [ ] 麦克风权限已允许

## 📝 更新日志

### v2.1 - 场景创建优化
- ✅ 修复 `save_scene()` 参数名称错误
- ✅ 优化 AI 回复内容，使用 Markdown 格式
- ✅ 添加 Toast 提示，替代 alert 弹窗
- ✅ 优化按钮点击逻辑，防止重复点击
- ✅ 添加加载状态提示
- ✅ 改进错误处理
- ✅ 完善跳转逻辑，显示成功提示后跳转
- ✅ 完善使用文档

### v2.0 - 语音对练集成
- ✅ Qwen-Omni 实时语音模型
- ✅ WebSocket 实时通信
- ✅ 音频录制和转录
- ✅ AI 评估报告生成

## 🎯 最佳实践

### 1. 提供详细信息
在对话中提供越多的背景信息，生成的场景质量越高。

**好**: "我想创建一个汽车销售场景，客户预算 20 万，关注 SUV，主要是家庭使用，有两个孩子，比较注重安全。"

**差**: "我想创建一个汽车销售场景。"

### 2. 明确角色特点
描述 AI 模拟角色的特点：
- 性格特点（温和、挑剔、犹豫等）
- 关注重点（价格、性能、外观等）
- 决策风格（理性、感性、从众等）

### 3. 充分利用预览
点击"查看生成的内容"可以：
- 确认场景内容是否符合预期
- 了解 AI 会提出的问题
- 提前准备应对策略

### 4. 多次练习
同一个场景可以多次对练：
- 第一次熟悉场景
- 第二次改进话术
- 第三次挑战高分

## 📞 技术支持

如有问题，请查看：
1. 浏览器控制台（F12）
2. 后端日志
3. 数据库连接状态
4. API 密钥配置
