# 场景创建与对练流程说明

## 📋 完整流程

### 1. 访问场景创建页面
```
http://localhost:5000/scene/create/
```

### 2. 对话式信息收集

系统会自动初始化对话，用户需要回答以下问题：

#### 第一步：指定行业
```
用户：我想创建一个汽车销售的培训场景
```

#### 第二步：指定 AI 模拟角色
```
用户：AI 模拟一个想看车的客户
```

#### 第三步：提供角色背景信息
```
用户：客户预算 20-30 万，关注 SUV 车型，主要是家庭使用
```

可以继续提供更多细节：
- 客户性格特点（温和、挑剔、犹豫等）
- 关注重点（价格、性能、外观等）
- 购车需求（代步、商务、家庭等）

### 3. 自动生成场景内容

当信息收集完成后（状态面板全部变绿），系统会自动：
- ✅ 生成场景背景信息
- ✅ 生成主问题列表（3-5 个）
- ✅ 生成关联问题分组
- ✅ 生成考核维度（3-4 个）
- ✅ 生成情绪画像

此时底部会出现**操作栏**，显示两个按钮：
- **查看生成的内容** - 预览生成的场景内容
- **保存并开始对练** - 保存场景并跳转到实时对练页面

### 4. 查看生成的内容（可选）

点击 **"查看生成的内容"** 按钮：
- 调用 `/api/scene/generate` 接口
- 生成场景内容并保存到数据库
- 在模态框中显示完整场景内容：
  - 📍 场景背景
  - ❓ 主问题列表
  - 🔗 关联问题分组
  - 📊 考核维度
  - 😊 情绪画像

### 5. 保存并开始对练

点击 **"保存并开始对练"** 按钮：
- 如果之前没有保存，会先调用生成接口保存场景
- 获取 `scene_id`
- 自动跳转到实时对练页面：`/realtime/{scene_id}`

### 6. 实时对练

在 realtime 页面：
- 使用 **Qwen-Omni** 实时语音模型
- 语音对话交互
- 自动录音和转录
- WebSocket 实时通信

### 7. 查看评估报告

对练完成后：
- 自动保存到数据库
- 生成 AI 评估报告
- 显示综合得分
- 各维度得分和反馈
- 亮点和改进建议

## 🔧 技术实现

### 前端关键代码

#### 显示操作栏
```javascript
// 当后端返回 is_ready: true 时
if (data.is_ready) {
    showActionBar();  // 显示底部操作栏
}
```

#### 保存并开始对练
```javascript
async function saveAndStartTraining() {
    // 1. 调用生成接口保存场景
    const response = await fetch('/api/scene/generate', {
        method: 'POST'
    });
    
    const data = await response.json();
    
    if (data.success) {
        currentSceneId = data.scene_id;
        
        // 2. 跳转到 realtime 页面
        window.location.href = `/realtime/${currentSceneId}`;
    }
}
```

### 后端关键代码

#### 场景生成接口
```python
@scene_create_bp.route('/generate', methods=['POST'])
def generate_scene():
    # 1. 生成场景内容
    scene_content = agent.generate_scene_content()
    
    # 2. 构建完整提示词
    full_prompt = agent.build_prompt()
    
    # 3. 准备场景数据
    scene_name = f"{scene_content.industry}_{scene_content.role_type}_场景"
    dimension_config = json.dumps({...})
    
    # 4. 保存到数据库
    scene_id = db_module.save_scene(
        scene_name=scene_name,
        scene_prompt=full_prompt,
        dimension_config=dimension_config,
        role_type=scene_content.role_type,
        role_description=scene_content.role_description,
        industry=scene_content.industry,
        training_goal=f"提升{scene_content.role_type}的沟通能力",
        full_evaluation_prompt=full_prompt,
        status=0
    )
    
    # 5. 返回场景信息和跳转 URL
    return jsonify({
        'success': True,
        'scene_id': scene_id,
        'scene_name': scene_name,
        'redirect_url': f'/realtime/{scene_id}',
        'scene_content': agent.get_scene_content_dict()
    })
```

## ⚠️ 常见问题

### 问题 1: 操作栏不显示

**症状**: 对话完成后，底部没有出现"查看生成的内容"和"保存并开始对练"按钮

**可能原因**:
1. 信息未收集完成（状态面板未全绿）
2. 后端未返回 `is_ready: true`
3. 前端 JavaScript 错误

**解决方案**:
1. 检查状态面板，确保行业、角色、背景信息都已收集
2. 查看浏览器控制台是否有错误
3. 查看后端日志，确认 `is_ready` 返回值

### 问题 2: 保存失败

**症状**: 点击"保存并开始对练"后提示保存失败

**可能原因**:
1. 数据库连接失败
2. `save_scene()` 函数参数错误
3. 网络请求失败

**解决方案**:
1. 检查数据库连接
2. 查看后端错误日志
3. 确认参数名称正确（`scene_name`, `scene_prompt` 等）

### 问题 3: 无法跳转到 realtime 页面

**症状**: 保存成功但没有跳转

**可能原因**:
1. `scene_id` 为空
2. URL 路径错误
3. JavaScript 跳转代码未执行

**解决方案**:
1. 检查 `currentSceneId` 是否正确赋值
2. 查看浏览器控制台错误
3. 确认 `/realtime/{scene_id}` 路由存在

## 📊 数据库表结构

### ai_coach_scene 表

保存场景配置：
- `id` - 场景 ID
- `scene_name` - 场景名称
- `scene_prompt` - 场景提示词
- `dimension_config` - 维度配置 JSON
- `role_type` - AI 模拟角色类型
- `role_description` - 角色描述
- `industry` - 行业
- `training_goal` - 培训目标
- `full_evaluation_prompt` - 完整评估提示词
- `status` - 状态（0=启用，1=禁用）

### ai_coach_record 表

保存训练记录：
- `session_id` - 会话 ID（主键）
- `scene_id` - 场景 ID
- `word_content` - 对话内容 JSON
- `oss_file_path` - 音频文件路径
- `call_duration` - 通话时长（秒）
- `ai_evaluate` - AI 评估结果 JSON
- `ai_advise` - AI 建议
- `score` - 综合得分

## 🚀 快速测试

### 测试对话
```
用户：我想创建一个汽车销售的培训场景
AI: 好的！请问您希望 AI 模拟什么角色呢？

用户：模拟一个想看车的客户
AI: 明白了。请问这个客户有什么特点吗？

用户：客户预算 20-30 万，关注 SUV 车型，主要是家庭使用
AI: 好的。请问客户的性格特点如何？

用户：客户比较温和，容易沟通
AI: 场景内容已生成完成！包括背景信息、问题列表、关联问题和考核维度。
    可以点击「开始生成」按钮保存场景并开始对练。

[此时显示操作栏]
✅ 场景内容生成成功！
[查看生成的内容] [保存并开始对练]
```

### 测试 API
```bash
# 1. 创建场景会话
curl -X POST http://localhost:5000/api/scene/create

# 2. 对话交互
curl -X POST http://localhost:5000/api/scene/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想创建一个汽车销售的培训场景"}'

# 3. 生成场景内容
curl -X POST http://localhost:5000/api/scene/generate

# 4. 访问 realtime 页面
# 浏览器打开：http://localhost:5000/realtime/{scene_id}
```

## ✅ 检查清单

使用前请确认：
- [ ] 数据库连接正常
- [ ] `ai_coach_scene` 表存在
- [ ] Qwen API 密钥配置正确
- [ ] Flask 应用启动成功
- [ ] 端口 5000 未被占用
- [ ] 浏览器支持 WebSocket

## 📝 更新日志

### v2.1 - 优化场景保存流程
- ✅ 修复 `save_scene()` 参数名称错误
- ✅ 优化按钮点击逻辑，防止重复点击
- ✅ 添加加载状态提示
- ✅ 改进错误处理
- ✅ 完善流程说明文档
