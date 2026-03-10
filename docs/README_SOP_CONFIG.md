# 🚀 SOP 质检项配置功能 - 快速启动

## ✨ 功能简介

为训练场景配置标准操作流程（SOP）质检清单，用于后续的训练评估。

## 📋 前置要求

- Python 3.8+
- MySQL 5.7+
- Flask 应用已安装依赖

## 🎯 快速开始（3 步）

### 步骤 1: 数据库迁移

```bash
python scripts/migrate_add_sop_field.py
```

**预期输出：**
```
============================================================
SOP 质检项字段迁移脚本
============================================================
INFO:root:检查 default_sop_checklist 字段是否存在...
INFO:root:添加 default_sop_checklist 字段...
INFO:root:✓ default_sop_checklist 字段添加成功
...
INFO:root:✓ 迁移完成
```

### 步骤 2: 启动应用

```bash
python app.py
```

**预期输出：**
```
 * Running on http://127.0.0.1:5000
```

### 步骤 3: 访问页面

在浏览器中打开：

```
http://localhost:5000/sop/config
```

## ✅ 验证安装

运行测试脚本：

```bash
python test_sop_config.py
```

**预期输出：**
```
============================================================
SOP 质检项配置功能测试
============================================================
✓ 服务器运行正常

=== 测试 1: 页面访问 ===
✓ 页面访问成功

=== 测试 2: 获取 SOP 质检清单 ===
✓ 成功获取质检清单

...

🎉 所有测试通过！
```

## 📖 使用示例

### 1. 选择场景

在页面顶部下拉框中选择场景，例如：
- 汽车销售 → 客户首次到店接待
- 教育培训 → 课程咨询接待

### 2. 添加质检项

点击「+ 添加质检项」，填写信息：

**示例 1: 必须做**
- 名称：`30秒内问候客户`
- 类型：`✓ 必须做`
- 关键词：`你好,欢迎,请问`
- 分类：`接待礼仪`

**示例 2: 禁止做**
- 名称：`禁止贬低竞品`
- 类型：`✗ 禁止做`
- 关键词：`垃圾,不行,差`
- 分类：`禁止行为`

### 3. 保存配置

点击右上角「💾 保存」按钮，等待提示：
```
✓ 保存成功
```

## 🗂️ 新增文件列表

```
项目根目录/
├── database/
│   └── sop_dao.py                          # 新增：数据访问层
├── routes/
│   └── sop_routes.py                       # 新增：API 路由
├── front_end/sop/                          # 新增：前端模块
│   ├── templates/
│   │   └── sop_config.html                 # 配置页面
│   └── static/
│       ├── css/
│       │   └── sop_config.css              # 样式文件
│       └── js/
│           └── sop_config.js               # 交互逻辑
├── scripts/
│   └── migrate_add_sop_field.py            # 新增：数据库迁移脚本
├── docs/
│   ├── SOP_CONFIG_GUIDE.md                 # 新增：使用指南
│   └── SOP_CONFIG_IMPLEMENTATION.md        # 新增：实现说明
├── test_sop_config.py                      # 新增：测试脚本
└── README_SOP_CONFIG.md                    # 新增：本文件
```

## 🔧 修改的文件

**app.py**
- 导入 `sop_bp`
- 注册 SOP 路由
- 添加静态文件路由
- 添加页面路由

## 🌐 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sop/checklist/{scene_code}` | 获取质检清单 |
| PUT | `/api/sop/checklist/{scene_code}` | 更新质检清单 |
| POST | `/api/sop/checklist/{scene_code}/validate` | 验证格式 |
| GET | `/api/sop/scenes` | 获取场景列表 |

## 📊 数据库变更

在 `ai_coach_preset_scene` 表中新增字段：

```sql
-- SOP 质检清单（JSON 格式）
default_sop_checklist JSON

-- 更新时间
updated_time DATETIME
```

## 💡 快速测试

### 方式 1: 使用测试脚本

```bash
python test_sop_config.py
```

### 方式 2: 使用 curl

```bash
# 获取质检清单
curl http://localhost:5000/api/sop/checklist/auto_sales_001

# 更新质检清单
curl -X PUT http://localhost:5000/api/sop/checklist/auto_sales_001 \
  -H "Content-Type: application/json" \
  -d '{"checklist":[{"item_id":"SOP001","item_name":"测试项","check_type":"must_do"}]}'
```

### 方式 3: 浏览器访问

直接访问：http://localhost:5000/sop/config

## 🐛 常见问题

### Q1: 迁移脚本报错 "字段已存在"

**答：** 这是正常的，说明字段已经添加过了，可以跳过此步骤。

### Q2: 页面显示 404

**答：** 检查 Flask 是否正确启动，确认 app.py 中已注册路由。

### Q3: 保存失败

**答：** 
1. 确认数据库字段已添加
2. 检查场景代码是否正确
3. 查看 Flask 控制台错误信息

### Q4: 前端页面样式错误

**答：** 确认静态文件路径正确，检查浏览器控制台是否有 404 错误。

## 📚 文档链接

- **使用指南**: `docs/SOP_CONFIG_GUIDE.md`
- **实现说明**: `docs/SOP_CONFIG_IMPLEMENTATION.md`
- **测试脚本**: `test_sop_config.py`

## ✨ 功能特性

✅ 场景选择（按行业分组）  
✅ 质检项管理（增删改查）  
✅ 类型设置（必须做/禁止做）  
✅ 关键词配置（辅助 AI 判断）  
✅ 分类管理（业务流程分类）  
✅ 实时保存（一键保存到数据库）  
✅ 数据验证（前后端双重验证）  
✅ 友好提示（Toast 消息提示）  

## 🎯 下一步

配置完成后，SOP 质检项将用于：

1. **训练评估**：在评估模块中使用这些质检项
2. **AI 判断**：根据关键词和对话内容自动判断
3. **报告生成**：生成详细的 SOP 执行报告

## 📞 技术支持

如有问题：

1. 查看详细文档：`docs/SOP_CONFIG_GUIDE.md`
2. 运行测试脚本定位问题
3. 检查 Flask 日志和浏览器控制台
4. 提交 Issue 附上错误信息

---

**开始使用：**

```bash
# 1. 迁移数据库
python scripts/migrate_add_sop_field.py

# 2. 启动应用
python app.py

# 3. 打开浏览器
# http://localhost:5000/sop/config
```

🎉 祝使用愉快！
