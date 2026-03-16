# AI教练后台管理系统

## 📋 概述

AI教练后台管理系统是一个用于管理训练场景、查看训练记录、分析数据的综合管理平台。

## 🎯 已实现功能

### 1. 场景管理 ✅

#### 功能列表
- ✅ 场景列表展示（包含预设场景和自定义场景）
- ✅ 场景统计（总数、预设、自定义、草稿）
- ✅ 场景筛选（按状态筛选）
- ✅ 场景搜索（按名称/行业搜索）
- ✅ 场景详情查看
  - 基本信息（名称、状态、行业、训练目标等）
  - 角色设定（AI角色类型、角色描述）
  - 场景背景
  - 评估维度配置
  - SOP质检清单
- ✅ 场景删除（软删除）
- ✅ 分页展示

#### 页面路由
- `/manage_system/` - 仪表盘
- `/manage_system/scenes` - 场景管理主页
- `/manage_system/scenes/preset` - 预设场景（待实现）
- `/manage_system/scenes/custom` - 自定义场景（待实现）
- `/manage_system/scenes/edit/<scene_id>` - 编辑场景（待实现）

#### API接口
- `GET /manage_system/api/scenes` - 获取场景列表
- `GET /manage_system/api/scenes/<scene_id>` - 获取场景详情
- `DELETE /manage_system/api/scenes/<scene_id>` - 删除场景
- `PUT /manage_system/api/scenes/<scene_id>` - 更新场景（待实现）
- `GET /manage_system/api/stats/overview` - 获取统计概览

## 🚀 快速开始

### 1. 启动应用

```bash
python app.py
```

### 2. 访问后台

在浏览器中访问：`http://localhost:5000/manage_system/`

### 3. 运行测试

```bash
python tests/test_manage_system.py
```

## 📁 文件结构

```
front_end/manage_system/
├── static/
│   ├── css/
│   │   ├── layout.css       # 布局样式
│   │   ├── common.css       # 通用组件样式
│   │   └── scenes.css       # 场景管理样式
│   └── js/
│       ├── common.js        # 通用工具函数
│       └── scenes.js        # 场景管理逻辑
├── templates/
│   ├── layout.html          # 基础布局模板
│   ├── dashboard.html       # 仪表盘
│   └── scenes/
│       └── index.html       # 场景管理主页
└── README.md                # 本文件

routes/
└── manage_routes.py         # 后台管理路由

database/
└── scene_dao.py             # 场景数据访问（新增函数）
```

## 🎨 UI特性

### 设计风格
- 现代化的卡片式布局
- 渐变色主题（蓝紫色系）
- 响应式设计，支持移动端
- 流畅的动画效果

### 组件
- 侧边栏导航（可折叠）
- 统计卡片
- 数据表格
- 模态框
- Toast提示
- 加载状态
- 空状态提示

## 🔧 技术栈

### 前端
- 原生 JavaScript（无框架依赖）
- HTML5 + CSS3
- Flexbox + Grid 布局

### 后端
- Flask（Python Web框架）
- MySQL（数据库）
- Blueprint（路由模块化）

## 📊 数据结构

### 场景表 (ai_coach_scene)

主要字段：
- `id` - 场景ID
- `scene_name` - 场景名称
- `scene_prompt` - 场景提示词
- `status` - 状态（0=草稿, 1=预设, 2=自定义, 9=归档）
- `industry` - 所属行业
- `role_type` - AI角色类型
- `role_description` - 角色描述
- `training_goal` - 训练目标
- `dimension_config` - 维度配置（JSON）
- `sop_checklist` - SOP清单（JSON）
- `background_hint` - 场景背景
- `deleted` - 是否删除（软删除标记）
- `created_time` - 创建时间

## 🎯 待实现功能

### 场景管理
- [ ] 场景编辑功能
- [ ] 场景复制功能
- [ ] 批量操作（批量删除、批量导出）
- [ ] 场景排序
- [ ] 场景标签管理

### 其他模块
- [ ] 训练记录管理
- [ ] 用户管理
- [ ] 评估配置
- [ ] 数据分析
- [ ] 系统设置

## 🐛 调试

### 常见问题

1. **页面访问404**
   - 确保 Flask 应用已启动
   - 检查 `manage_bp` 是否在 `app.py` 中注册

2. **API返回500错误**
   - 查看终端错误日志
   - 检查数据库连接
   - 确认函数已在 `db.py` 和 `database/__init__.py` 中正确导出

3. **静态文件加载失败**
   - 检查文件路径是否正确
   - 确认 `static_folder` 配置正确

### 日志查看

```python
import logging
logger = logging.getLogger(__name__)
logger.info("调试信息")
```

## 📝 开发规范

### 代码风格
- Python: PEP 8
- JavaScript: Standard Style
- CSS: BEM命名规范

### 提交规范
- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试

## 📞 联系方式

如有问题或建议，请联系开发团队。

## 📄 许可证

内部项目，保留所有权利。