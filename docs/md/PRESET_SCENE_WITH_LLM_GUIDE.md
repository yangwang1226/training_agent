# 预设场景 + LLM 生成方案 - 使用指南

## 📊 方案架构

本方案结合了三种内容来源，形成完整的场景提示词：

```
完整场景提示词
├── 手工模板（骨架，固定不变）
│   ├── ✅ 对话控制机制（强制提问队列、顺序控制）
│   ├── ✅ 结束流程（根据意愿选择结束语）
│   ├── ✅ 关联问题触发规则
│   └── ✅ 防御性对话设计
│
├── LLM 生成（血肉，动态生成）
│   ├── ✅ 融合用户背景的背景信息
│   ├── ✅ 个性化的主问题列表
│   ├── ✅ 个性化的关联问题和触发词
│   └── ✅ 角色情绪画像
│
└── 预设场景（基础，保底数据）
    ├── ✅ 行业、角色、场景基本信息
    ├── ✅ 默认主问题（LLM失败时的兜底）
    ├── ✅ 默认关联问题（LLM失败时的兜底）
    └── ✅ 默认考核维度
```

## 🚀 快速开始

### 步骤总结

基于**汽车销售预设场景 `auto_first_visit`** 的完整流程：

1. **确保数据库已初始化**（运行 `python scripts/insert_preset_scenes.py`）
2. **启动应用**（`python app.py`）
3. **调用 API 生成场景**（见下方示例）
4. **开始语音对练**（自动跳转到 `/realtime/{scene_id}`）

---

### API 调用示例

#### 示例 1：基于预设场景直接生成

```bash
curl -X POST http://localhost:5000/api/scene/generate-from-preset \
  -H "Content-Type: application/json" \
  -d '{
    "scene_code": "auto_first_visit"
  }'
```

**返回：**
```json
{
  "success": true,
  "scene_id": 123,
  "scene_name": "automobile_想看车的客户_场景",
  "redirect_url": "/realtime/123",
  "message": "场景生成成功！准备开始对练"
}
```

---

#### 示例 2：添加用户背景信息

```bash
curl -X POST http://localhost:5000/api/scene/generate-from-preset \
  -H "Content-Type: application/json" \
  -d '{
    "scene_code": "auto_first_visit",
    "user_background": "客户35岁，预算20-30万，关注SUV，家庭使用，注重安全",
    "custom_requirements": "客户必须询问：1.安全配置 2.新能源续航 3.价格优惠"
  }'
```

---

## 📋 预设场景列表

### 汽车销售（5个场景）

| 场景代码 | 场景名称 | 难度 |
|---------|---------|------|
| `auto_first_visit` | 客户首次到店接待 | 简单 |
| `auto_test_drive` | 试驾邀约与跟进 | 中等 |
| `auto_price_nego` | 价格谈判与促成 | 困难 |
| `auto_competitor` | 竞品对比应对 | 中等 |
| `auto_followup` | 潜客电话回访 | 简单 |

---

## 🧪 运行测试

```bash
python test_preset_scene_service.py
```

测试脚本会：
1. 加载预设场景 `auto_first_visit`
2. 使用 LLM 生成个性化内容
3. 结合手工模板构建完整提示词
4. 保存到文件 `scene_prompt/auto_first_visit_generated.txt`

---

## 📞 技术支持

如有问题，请查看：
1. 后端日志（`app.py` 输出）
2. 数据库记录（`ai_coach_preset_scene` 表）
3. 测试脚本输出

---

**祝使用愉快！** 🎉