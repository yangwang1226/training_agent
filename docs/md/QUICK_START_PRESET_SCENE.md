# 🚀 汽车销售预设场景 - 快速开始指南

## 📌 方案总结

基于您的需求，我已经实现了一个**预设场景 + LLM 生成**的完整方案：

```
完整场景提示词 = 手工模板（骨架） + LLM生成（血肉） + 预设场景（兜底）
```

### 核心优势

✅ **手工模板固定不变**：对话控制、结束流程、触发规则、防御性设计  
✅ **LLM 动态生成**：融合用户背景，生成个性化问题和情绪  
✅ **预设场景兜底**：LLM 失败时使用默认内容，保证可用性

---

## 🎯 快速开始（3 步）

### 步骤 1：初始化数据库

```bash
python scripts/insert_preset_scenes.py
```

**作用**：插入汽车销售的 5 个预设场景到数据库

---

### 步骤 2：启动应用

```bash
python app.py
```

**访问**：http://localhost:5000

---

### 步骤 3：生成场景

#### 方式 A：通过 API（推荐）

```bash
curl -X POST http://localhost:5000/api/scene/generate-from-preset \
  -H "Content-Type: application/json" \
  -d '{
    "scene_code": "auto_first_visit",
    "user_background": "客户35岁，预算20-30万，关注SUV，家庭使用",
    "custom_requirements": "客户必须询问安全配置和价格优惠"
  }'
```

**返回示例**：
```json
{
  "success": true,
  "scene_id": 123,
  "redirect_url": "/realtime/123"
}
```

然后访问 `http://localhost:5000/realtime/123` 开始语音对练。

---

#### 方式 B：通过测试脚本

```bash
python test_preset_scene_service.py
```

**输出**：
- 在控制台显示生成的完整内容
- 自动保存到 `scene_prompt/auto_first_visit_generated.txt`

---

## 📁 关键文件

| 文件 | 说明 |
|------|------|
| `agent/service/scene/preset_scene_service.py` | 核心服务类 |
| `routes/scene_agent_routes.py` | API 路由（已添加 2 个新接口） |
| `test_preset_scene_service.py` | 测试脚本 |
| `scripts/insert_preset_scenes.py` | 数据初始化脚本 |
| `md/PRESET_SCENE_WITH_LLM_GUIDE.md` | 完整使用指南 |

---

## 🔄 完整数据流

```
1. 用户调用 API: /api/scene/generate-from-preset
   ↓
2. PresetSceneService.generate_from_preset()
   ├── 从数据库加载预设场景 (auto_first_visit)
   ├── LLM 生成背景信息（融合用户背景）
   ├── LLM 生成主问题列表（个性化）
   ├── LLM 生成关联问题分组（个性化触发词）
   ├── 解析预设考核维度
   └── LLM 生成情绪画像
   ↓
3. PresetSceneService.build_full_prompt()
   ├── 结合手工模板（对话控制机制）
   ├── 结合 LLM 生成内容
   └── 输出完整提示词
   ↓
4. 保存到数据库 (ai_coach_scene 表)
   ↓
5. 返回 scene_id 和跳转 URL
   ↓
6. 前端跳转到 /realtime/{scene_id}
   ↓
7. 开始语音对练
```

---

## 💡 使用示例

### 示例 1：最简单的调用（无用户背景）

```python
from agent.service.scene.preset_scene_service import PresetSceneService

service = PresetSceneService()
scene_content = service.generate_from_preset(scene_code="auto_first_visit")
full_prompt = service.build_full_prompt(scene_content)
print(full_prompt)
```

**效果**：
- 使用预设场景的默认信息
- LLM 生成通用的背景和问题
- 保证基本可用

---

### 示例 2：添加用户背景（推荐）

```python
service = PresetSceneService()
scene_content = service.generate_from_preset(
    scene_code="auto_first_visit",
    user_background="客户35岁，预算20-30万，关注SUV，家庭使用，注重安全",
    custom_requirements="客户必须询问：1.安全配置 2.新能源续航 3.价格优惠"
)
full_prompt = service.build_full_prompt(scene_content)
```

**效果**：
- LLM 融合用户背景，生成更真实的场景
- 问题更有针对性，符合实际业务需求
- 培训效果更好

---

## 📊 生成内容对比

### 无用户背景（通用版）

```
背景信息：
你是一位想看车的客户，今天来到4S店咨询购车。

主问题：
1. 你好，我想看看车
2. 这款车多少钱？
3. 有什么优惠吗？
```

### 有用户背景（个性化版）

```
背景信息：
你是李先生，35岁的公司中层管理人员，家有两个孩子（8岁和5岁）。
今天下午，你带着对家庭用车的期待，第一次走进了这家汽车4S店。
你的购车预算在20-30万之间，目标锁定在SUV车型上...

主问题：
1. 你好，我想看看SUV，你们这边有哪些推荐的车型吗？
2. 这款车的安全配置怎么样？有没有自动刹车、车道保持这些功能？
3. 我看中了这款车，但是也在考虑新能源车，你觉得我应该怎么选？
4. 这个价位的车，跟其他品牌比起来，你们的优势在哪里？
5. 如果我今天订车，有什么优惠活动吗？
```

**区别显而易见**：个性化版本更真实、更有针对性！

---

## 🔍 查看生成结果

### 方式 1：运行测试脚本

```bash
python test_preset_scene_service.py
```

控制台会显示完整的生成内容，并保存到文件。

---

### 方式 2：查看数据库

```sql
SELECT scene_id, scene_name, scene_prompt 
FROM ai_coach_scene 
ORDER BY created_time DESC 
LIMIT 1;
```

---

### 方式 3：通过 API

```bash
# 先生成场景，获得 scene_id
curl -X POST http://localhost:5000/api/scene/generate-from-preset \
  -H "Content-Type: application/json" \
  -d '{"scene_code": "auto_first_visit"}'

# 然后查看场景详情
curl http://localhost:5000/api/scene/{scene_id}
```

---

## ⚡ 性能说明

| 步骤 | 耗时 | 说明 |
|------|------|------|
| 加载预设场景 | <50ms | 从数据库读取 |
| LLM 生成背景 | 2-3秒 | 调用 Qwen API |
| LLM 生成问题 | 2-3秒 | 调用 Qwen API |
| LLM 生成触发分组 | 2-3秒 | 调用 Qwen API |
| LLM 生成情绪 | 2-3秒 | 调用 Qwen API |
| 构建完整提示词 | <100ms | 本地拼接 |
| 保存到数据库 | <100ms | 写入数据库 |
| **总耗时** | **约 10-15秒** | 主要是 LLM 调用 |

**优化建议**：
- 可以并行调用 LLM（减少到 3-5 秒）
- 缓存常用场景（瞬间返回）
- 异步生成，前端显示进度

---

## 🎯 下一步

1. **测试基本功能**  
   ```bash
   python test_preset_scene_service.py
   ```

2. **通过 API 生成场景**  
   使用上面的 curl 命令测试

3. **开始语音对练**  
   访问返回的 `redirect_url`

4. **查看评估报告**  
   对练完成后自动生成

---

## 📞 需要帮助？

- 查看完整文档：`md/PRESET_SCENE_WITH_LLM_GUIDE.md`
- 查看测试脚本：`test_preset_scene_service.py`
- 查看核心代码：`agent/service/scene/preset_scene_service.py`

---

**现在可以开始使用了！** 🎉

运行 `python test_preset_scene_service.py` 体验完整流程！
</contents>