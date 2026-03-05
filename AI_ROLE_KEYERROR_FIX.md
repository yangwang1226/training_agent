# ai_role KeyError 修复说明

## 🐛 问题描述

**错误信息**:
```
KeyError: 'ai_role'
```

**错误位置**: `agent/service/scene/agent.py` 第 135 行

**堆栈跟踪**:
```python
File "D:\workspace\training_agent\agent\service\scene\agent.py", line 135, in _extract_info
    prompt = INFO_EXTRACTION_PROMPT.format(
        ...
        ai_role=self.state.ai_role  # ← 这里报错
    )
```

## 🔍 问题分析

### 根本原因

在 `INFO_EXTRACTION_PROMPT` 中添加了 `{ai_role}` 占位符：

```python
INFO_EXTRACTION_PROMPT = """从用户输入中提取信息。

当前已收集信息:
- 行业：{industry}
- 用户角色：{role_type}
- AI 扮演角色：{ai_role}  # ← 新增的占位符
- 角色描述：{role_description}
- 延展信息：{extended_info}
...
"""
```

但在 `_extract_info` 方法中调用 `format()` 时，忘记传入 `ai_role` 参数：

```python
# 错误的代码
prompt = INFO_EXTRACTION_PROMPT.format(
    user_input=user_input,
    industry=self.state.industry or '未收集',
    role_type=self.state.role_type or '未收集',
    role_description=self.state.role_description or '未收集',  # ← 缺少 ai_role
    extended_info=self.state.get_extended_info_summary()
)
```

### Python format() 机制

当字符串中包含 `{key}` 占位符时，必须在 `format()` 中提供对应的参数，否则会抛出 `KeyError`。

## ✅ 修复方案

### 修复代码

**文件**: [`agent/service/scene/agent.py`](file:///d:\workspace\training_agent\agent\service\scene\agent.py#L133-L152)

**修复前**:
```python
def _extract_info(self, user_input: str) -> Dict[str, Any]:
    """从用户输入中提取信息"""
    prompt = INFO_EXTRACTION_PROMPT.format(
        user_input=user_input,
        industry=self.state.industry or '未收集',
        role_type=self.state.role_type or '未收集',
        role_description=self.state.role_description or '未收集',
        extended_info=self.state.get_extended_info_summary()
    )
```

**修复后**:
```python
def _extract_info(self, user_input: str) -> Dict[str, Any]:
    """从用户输入中提取信息"""
    prompt = INFO_EXTRACTION_PROMPT.format(
        user_input=user_input,
        industry=self.state.industry or '未收集',
        role_type=self.state.role_type or '未收集',
        ai_role=self.state.ai_role or '未确认',  # ← 新增
        role_description=self.state.role_description or '未收集',
        extended_info=self.state.get_extended_info_summary()
    )
```

### 修改说明

1. **添加参数**: `ai_role=self.state.ai_role or '未确认'`
2. **位置**: 在 `role_type` 和 `role_description` 之间
3. **默认值**: 如果 `ai_role` 为空，使用 `'未确认'` 作为默认值

## 📊 完整的 format() 参数列表

现在 `INFO_EXTRACTION_PROMPT.format()` 包含以下参数：

```python
prompt = INFO_EXTRACTION_PROMPT.format(
    user_input=user_input,                          # 用户输入
    industry=self.state.industry or '未收集',       # 行业
    role_type=self.state.role_type or '未收集',     # 用户角色
    ai_role=self.state.ai_role or '未确认',         # AI 扮演角色 ← 新增
    role_description=self.state.role_description or '未收集',  # 角色描述
    extended_info=self.state.get_extended_info_summary()       # 延展信息
)
```

对应 `INFO_EXTRACTION_PROMPT` 中的占位符：

```python
当前已收集信息:
- 行业：{industry}
- 用户角色：{role_type}
- AI 扮演角色：{ai_role}
- 角色描述：{role_description}
- 延展信息：{extended_info}
```

## ✅ 测试验证

### 1. 启动应用
```bash
python app.py
```

**预期输出**:
```
Loaded .env from: ...
INFO - Registered realtime blueprint
INFO - Registering WebSocket routes
INFO - 评估服务初始化完成，使用模型：qwen3.5-flash
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### 2. 访问场景创建页面
```
http://localhost:5000/scene/create/
```

**预期**:
- ✅ 页面正常加载
- ✅ 不再报 KeyError 错误
- ✅ AI 显示初始对话

### 3. 发送第一条消息
```
用户：我想创建一个汽车销售的培训场景，AI 模拟一个想看车的客户
```

**预期**:
- ✅ 正常提取信息
- ✅ 更新状态面板
- ✅ AI 回复简洁明了

## 📝 最佳实践

### 1. 使用 format() 的注意事项

**规则**: 字符串中的所有 `{key}` 都必须在 `format()` 中有对应参数

**正确示例**:
```python
template = "你好，{name}！你今年{age}岁了。"
result = template.format(name="小明", age=18)
```

**错误示例**:
```python
template = "你好，{name}！你今年{age}岁了。"
result = template.format(name="小明")  # ← KeyError: 'age'
```

### 2. 提供默认值

使用 `or` 操作符提供默认值，避免 `None` 导致的问题：

```python
ai_role=self.state.ai_role or '未确认'
```

这样即使 `self.state.ai_role` 是空字符串或 `None`，也会使用默认值 `'未确认'`。

### 3. 检查占位符匹配

在修改 template 字符串后，务必检查所有使用 `format()` 的地方：

```python
# 1. 检查 template 中的占位符
print(template)  # 查看所有 {key}

# 2. 检查 format() 的参数
format(key1=value1, key2=value2, ...)

# 3. 确保一一对应
```

## 🎯 相关修改

这次修复涉及的文件：

1. ✅ [`agent/service/scene/prompts.py`](file:///d:\workspace\training_agent\agent\service\scene\prompts.py)
   - 添加 `{ai_role}` 占位符到 `INFO_EXTRACTION_PROMPT`

2. ✅ [`agent/service/scene/models.py`](file:///d:\workspace\training_agent\agent\service\scene\models.py)
   - 添加 `ai_role` 字段到 `ConversationState`

3. ✅ [`agent/service/scene/agent.py`](file:///d:\workspace\training_agent\agent\service\scene\agent.py)
   - **本次修复**: 在 `_extract_info` 中添加 `ai_role` 参数
   - 在 `_update_state` 中更新 `ai_role`
   - 在 `_get_state` 中返回 `ai_role`

4. ✅ [`routes/scene_create_routes.py`](file:///d:\workspace\training_agent\routes\scene_create_routes.py)
   - 修改初始对话，询问 AI 角色

## 🎉 修复效果

**修复前**:
```
❌ 访问页面即报错：KeyError: 'ai_role'
❌ 无法使用场景创建功能
❌ 终端显示完整堆栈跟踪
```

**修复后**:
```
✅ 页面正常加载
✅ 可以正常使用场景创建
✅ AI 正常对话和提取信息
✅ 状态面板正常更新
```

## 📚 总结

这是一个典型的 **format() 参数缺失** 错误：

1. **原因**: 在 template 中添加了新占位符 `{ai_role}`，但忘记在 `format()` 中添加对应参数
2. **修复**: 在 `_extract_info` 方法的 `format()` 调用中添加 `ai_role` 参数
3. **验证**: 重启应用，访问页面，确认不再报错

现在场景创建功能可以正常使用了！🎉
