# 场景智能体重构项目

> 🎯 基于思维链的 AI 培训场景智能生成系统

## 📖 项目简介

这是一个全新的 AI 培训场景创建系统，通过对话式交互和思维链技术，智能生成高质量的培训场景和对练评估报告。

### 核心特性

- 💬 **对话式创建** - 像聊天一样创建培训场景
- 🧠 **思维链生成** - 智能生成背景、问题、维度
- 🎙️ **实时对练** - 语音对话模拟真实场景
- 📊 **智能评估** - 多维度能力评估报告
- 🔄 **完整闭环** - 从创建到评估一站式服务

---

## 🚀 快速开始

### 方式一：一键启动 (Windows)

```bash
start_scene_agent.bat
```

### 方式二：手动启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
python app.py

# 3. 访问页面
# 首页：http://localhost:5000
# 场景创建：http://localhost:5000/scene/create/
```

---

## 📋 使用流程

### 1. 创建场景

访问 `/scene/create/`,系统会自动开始对话:

```
AI: 你好！我是场景创建助手。请告诉我你想创建什么行业的培训场景？

你：我想创建一个汽车销售的培训场景

AI: 好的！请问您希望 AI 模拟什么角色呢？

你：模拟一个想看车的客户，预算 20 万，关注 SUV

... (继续对话)

AI: 场景内容已生成完成！可以点击「开始生成」按钮保存场景并开始对练。
```

### 2. 预览内容

点击"查看生成的内容",可以看到:
- 场景背景信息
- 主问题列表 (3-5 个)
- 关联问题分组
- 考核维度 (3-4 个)
- 情绪画像

### 3. 开始对练

点击"保存并开始对练",自动跳转到实时对练页面:
- 使用 qwen-omni realtime 模型
- 语音对话交互
- 自动录音和转录

### 4. 查看评估

对练完成后自动生成评估报告:
- 综合得分
- 维度得分和反馈
- 亮点和改进建议
- 关键时刻分析

---

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Flask + Flask-Sock
- **LLM**: Qwen Plus 3.5 (思维链生成) + Qwen Omni (实时语音)
- **数据库**: MySQL
- **音频**: PyAudio (24kHz, 16bit, 单声道)

### 前端技术栈
- **原生**: HTML5 + CSS3 + JavaScript
- **通信**: WebSocket (实时音频流)

### 核心模块

```
agent/service/scene/
├── agent.py              # SceneAgent 核心类
├── models.py             # 数据模型
├── prompts.py            # 思维链提示词
└── assessment_service.py # 评估报告服务

routes/
├── scene_create_routes.py  # 场景创建路由
└── realtime_routes.py      # 实时对练路由 (含评估)

front_end/scene/
├── templates/create.html   # 场景创建页面
├── static/css/create.css   # 样式
└── static/js/create.js     # 交互逻辑
```

---

## 📊 API 接口

### 场景创建

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/scene/create` | POST | 创建场景会话 |
| `/api/scene/chat` | POST | 对话交互 |
| `/api/scene/generate` | POST | 生成场景内容 |
| `/api/scene/status` | GET | 获取状态 |
| `/api/scene/reset` | POST | 重置智能体 |

### 实时对练

| 接口 | 方法 | 说明 |
|------|------|------|
| `/realtime/<scene_id>` | GET | 对练页面 |
| `/api/realtime/ws/<scene_id>` | WebSocket | 实时音频连接 |

---

## 📁 数据库表

### ai_coach_scene (场景表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| scene_name | VARCHAR | 场景名称 |
| scene_prompt | TEXT | 场景提示词 |
| dimension_config | TEXT | 维度配置 JSON |
| industry | VARCHAR | 行业 |
| role_type | VARCHAR | 角色类型 |
| full_evaluation_prompt | TEXT | 完整评估提示词 |

### ai_coach_record (训练记录表)

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | VARCHAR | 会话 ID (主键) |
| scene_id | INT | 场景 ID |
| word_content | TEXT | 对话内容 JSON |
| oss_file_path | VARCHAR | 音频文件路径 |
| call_duration | INT | 通话时长 (秒) |
| ai_evaluate | TEXT | AI 评估结果 JSON |
| ai_advise | TEXT | AI 建议 |
| score | INT | 综合得分 |

---

## 🧪 测试

运行测试脚本:

```bash
python test_scene_agent.py
```

测试内容:
- ✅ 模块导入测试
- ✅ SceneAgent 创建测试
- ✅ 对话交互测试
- ✅ 状态检查测试

---

## 📚 文档

- **SCENE_AGENT_GUIDE.md** - 详细使用指南
- **SCENE_AGENT_IMPLEMENTATION.md** - 实施总结
- **.trae/documents/scene_agent_redesign_plan.md** - 实施计划

---

## 💡 使用技巧

### 提供详细信息
```
好：我想创建一个汽车销售场景，客户预算 20 万，关注 SUV，主要是家庭使用。
差：我想创建一个汽车销售场景。
```

### 明确角色特点
```
好：模拟一个挑剔的客户，很在意价格，会反复砍价
差：模拟一个客户
```

### 调整考核维度
如果对生成的维度不满意，可以在对话中提出:
```
"希望能增加'需求挖掘能力'这个维度"
```

---

## 🔍 故障排查

### 场景无法生成
1. 检查浏览器控制台错误
2. 查看后端日志
3. 确认信息已收集完成 (状态面板全绿)

### 评估报告未生成
1. 检查 Qwen API 密钥配置
2. 查看后端日志错误
3. 确认数据库连接正常

### 音频未保存
1. 检查 `audio_file/` 目录权限
2. 确认 WebSocket 连接正常
3. 检查浏览器麦克风权限

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 场景生成时间 | ~15 秒 |
| 评估报告生成 | ~10 秒 |
| 音频文件大小 | ~500KB/分钟 |
| 支持并发 | 10+ 会话 |

---

## 🎯 后续优化

- [ ] 场景编辑和微调功能
- [ ] 多用户协作创建
- [ ] 场景评分和推荐
- [ ] 优质场景模板库
- [ ] 移动端优化

---

## 📞 技术支持

遇到问题请检查:
1. 后端日志 (控制台输出)
2. 浏览器控制台 (F12)
3. 数据库记录

---

## 📄 许可证

本项目仅供内部使用。

---

## 🎉 更新日志

### v2.0 (2026-03-04)
- ✅ 新增 SceneAgent 核心类
- ✅ 新增思维链场景生成
- ✅ 新增对话式交互界面
- ✅ 新增评估报告自动生成
- ✅ 优化数据流整合
- ✅ 完善文档和测试

---

**开始创建你的第一个培训场景吧!** 🚀

访问：http://localhost:5000/scene/create/
