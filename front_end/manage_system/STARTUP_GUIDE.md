# 🚀 AI教练后台管理系统 - 启动向导

## 📋 目录
- [系统概述](#系统概述)
- [快速开始](#快速开始)
- [功能说明](#功能说明)
- [常见问题](#常见问题)
- [技术架构](#技术架构)

---

## 🎯 系统概述

AI教练后台管理系统是一个基于 Flask + SQLite 的后台管理平台，用于管理训练场景、查看统计数据等。

### 核心功能
- ✅ 场景管理（预设场景、自定义场景、草稿）
- ✅ 统计数据展示
- ✅ 场景详情查看
- ✅ 场景删除（软删除）
- ✅ 实时搜索和筛选

---

## 🚀 快速开始

### 步骤 1: 环境检查

确保已安装以下环境：
```bash
# Python 3.8+
python --version

# 依赖包
pip install flask flask-cors
```

### 步骤 2: 启动应用

在项目根目录执行：

```bash
# Windows
python app.py

# Linux/Mac
python3 app.py
```

### 步骤 3: 访问系统

启动成功后，在浏览器访问：

```
http://localhost:5000/manage_system/
```

**默认端口**: 5000

如果5000端口被占用，可以修改 `app.py` 中的端口配置。

---

## 📱 功能说明

### 1. 仪表盘（Dashboard）

**访问地址**: `/manage_system/`

显示系统统计数据：
- 全部场景数量
- 预设场景数量
- 自定义场景数量
- 草稿数量

### 2. 场景管理

**访问地址**: `/manage_system/scenes`

#### 2.1 场景列表
- 显示所有场景的基本信息
- 支持按状态筛选（全部/预设/自定义/草稿）
- 支持场景名称搜索
- 分页显示

#### 2.2 状态说明
| 状态 | 说明 | status值 |
|------|------|---------|
| 预设场景 | 系统预设的标准场景 | 1 |
| 自定义场景 | 用户创建的场景 | 2 |
| 草稿 | 未发布的场景 | 0 |

#### 2.3 操作功能
- 🔍 **查看详情**: 查看场景完整信息
- ✏️ **编辑**: 修改场景配置
- 🗑️ **删除**: 软删除场景（不会真实删除数据）
- ➕ **创建场景**: 跳转到场景创建页面

### 3. API 接口

#### 获取场景列表
```http
GET /manage_system/api/scenes
```

响应示例：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "scene_name": "销售场景",
      "industry": "零售",
      "status": 1,
      "training_count": 0,
      "created_at": "2024-01-01 10:00:00"
    }
  ]
}
```

#### 获取场景详情
```http
GET /manage_system/api/scenes/<scene_id>
```

#### 删除场景
```http
DELETE /manage_system/api/scenes/<scene_id>
```

#### 获取统计数据
```http
GET /manage_system/api/stats/overview
```

---

## ❓ 常见问题

### Q1: 页面显示404错误

**解决方法**:
1. 检查 Flask 应用是否正常启动
2. 确认 `manage_bp` 已在 `app.py` 中注册：
   ```python
   from routes.manage_routes import manage_bp
   app.register_blueprint(manage_bp)
   ```
3. 检查访问URL是否正确（必须包含 `/manage_system/` 前缀）

### Q2: 静态资源加载失败（CSS/JS）

**可能原因**:
- 静态文件路径配置错误
- 文件不存在

**解决方法**:
1. 确认文件存在：
   ```
   front_end/manage_system/static/css/scenes.css
   front_end/manage_system/static/js/scenes.js
   ```
2. 检查 Blueprint 配置：
   ```python
   manage_bp = Blueprint(
       'manage',
       __name__,
       url_prefix='/manage_system',
       template_folder='...',
       static_folder='...'
   )
   ```

### Q3: 场景列表为空

**可能原因**:
- 数据库中没有场景数据
- API请求失败

**解决方法**:
1. 打开浏览器开发者工具（F12）查看控制台错误
2. 检查网络请求是否成功
3. 检查数据库中是否有数据：
   ```bash
   sqlite3 ai_coach.db "SELECT * FROM scenes WHERE deleted_at IS NULL;"
   ```

### Q4: 创建场景按钮点击无反应

**解决方法**:
1. 检查 `scenes.js` 中的 `createScene()` 函数
2. 确认场景创建页面路由存在：`/scene/create/`
3. 查看浏览器控制台是否有 JavaScript 错误

### Q5: 搜索或筛选不工作

**解决方法**:
1. 检查 JavaScript 是否正确加载
2. 查看控制台是否有错误
3. 确认 `handleSearch()` 和 `filterByStatus()` 函数存在

---

## 🏗️ 技术架构

### 后端技术栈
- **Flask**: Web 框架
- **SQLite**: 数据库
- **Python 3.8+**: 编程语言

### 前端技术栈
- **HTML5**: 页面结构
- **CSS3**: 样式设计
- **JavaScript (ES6+)**: 交互逻辑
- **Jinja2**: 模板引擎

### 目录结构
```
front_end/manage_system/
├── templates/              # 模板文件
│   ├── layout.html        # 基础布局
│   ├── dashboard.html     # 仪表盘
│   └── scenes/
│       └── index.html     # 场景管理页面
├── static/                # 静态资源
│   ├── css/              # 样式文件
│   │   ├── common.css
│   │   ├── layout.css
│   │   └── scenes.css
│   └── js/               # JavaScript 文件
│       ├── common.js
│       └── scenes.js
└── README.md             # 文档

routes/
└── manage_routes.py       # 后端路由
```

### 数据库表结构

**scenes 表** (场景表)
```sql
CREATE TABLE scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_name TEXT NOT NULL,           -- 场景名称
    scene_prompt TEXT,                  -- 场景提示词
    industry TEXT,                      -- 行业
    status INTEGER DEFAULT 0,           -- 状态：0草稿 1预设 2自定义
    created_at TIMESTAMP,               -- 创建时间
    updated_at TIMESTAMP,               -- 更新时间
    deleted_at TIMESTAMP,               -- 软删除时间
    -- 其他字段...
);
```

---

## 🔧 开发调试

### 启用调试模式

修改 `app.py`：
```python
if __name__ == '__main__':
    app.run(
        debug=True,           # 启用调试模式
        host='0.0.0.0',
        port=5000
    )
```

**注意**: 生产环境请关闭调试模式！

### 查看日志

日志会输出到控制台，包含：
- API 请求信息
- 数据库操作
- 错误堆栈

### 使用浏览器开发者工具

1. 按 `F12` 打开开发者工具
2. **Console**: 查看 JavaScript 错误
3. **Network**: 查看 API 请求/响应
4. **Elements**: 检查 DOM 结构

---

## 📝 最佳实践

### 1. 场景状态管理

- 新建场景默认为草稿（status=0）
- 测试通过后改为自定义场景（status=2）
- 预设场景（status=1）由管理员创建

### 2. 软删除机制

- 删除场景时不会真正删除数据
- 只是设置 `deleted_at` 字段
- 可以实现数据恢复功能

### 3. 性能优化

- 场景列表使用分页加载
- 搜索使用防抖处理
- 静态资源使用浏览器缓存

---

## 🆘 获取帮助

### 问题报告

如遇到问题，请提供以下信息：

1. **错误信息**: 浏览器控制台的错误日志
2. **操作步骤**: 如何重现问题
3. **环境信息**: Python版本、操作系统
4. **截图**: 如有必要

### 联系方式

- **项目地址**: [GitHub仓库地址]
- **文档**: 查看项目 README.md

---

## 📄 更新日志

### v1.0.0 (2024-01-01)
- ✅ 初始版本发布
- ✅ 场景管理功能
- ✅ 统计数据展示
- ✅ 搜索和筛选功能

---

## 📜 许可证

本项目采用 MIT 许可证。

---

**祝您使用愉快！** 🎉

如有问题，请随时查阅本文档或联系技术支持。
```