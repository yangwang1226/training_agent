# 预设场景功能实现文档

## 📋 功能概述

本次更新实现了从数据库动态加载预设场景的功能，替代了原有的前端硬编码数据。用户在行业选择页面看到的所有场景都来自数据库表 `ai_coach_preset_scene`。

## 🗄️ 数据库结构

### 1. 预设行业表 (ai_coach_preset_industry)

存储行业基本信息：

```sql
CREATE TABLE ai_coach_preset_industry (
    id INT PRIMARY KEY AUTO_INCREMENT,
    industry_code VARCHAR(50) UNIQUE NOT NULL,  -- 行业代码（如 'automobile'）
    industry_name VARCHAR(100) NOT NULL,         -- 行业名称（如 '汽车销售'）
    industry_icon VARCHAR(50) NOT NULL,          -- 图标标识
    description VARCHAR(500),                    -- 行业描述
    display_order INT DEFAULT 0,                 -- 显示顺序
    is_active TINYINT(1) DEFAULT 1,             -- 是否激活
    scene_count INT DEFAULT 0,                   -- 场景数量（冗余字段）
    total_usage INT DEFAULT 0,                   -- 总使用次数
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. 预设场景表 (ai_coach_preset_scene)

存储具体场景信息：

```sql
CREATE TABLE ai_coach_preset_scene (
    id INT PRIMARY KEY AUTO_INCREMENT,
    industry_code VARCHAR(50) NOT NULL,          -- 关联行业代码
    scene_code VARCHAR(50) UNIQUE NOT NULL,      -- 场景代码（如 'auto_first_visit'）
    scene_name VARCHAR(100) NOT NULL,            -- 场景名称
    scene_description VARCHAR(300) NOT NULL,     -- 场景描述
    scene_tag VARCHAR(100),                      -- 标签（如 'hot'）
    ai_role VARCHAR(100) NOT NULL,               -- AI扮演角色
    user_role VARCHAR(100) NOT NULL,             -- 用户角色
    difficulty ENUM('easy','medium','hard') DEFAULT 'medium',  -- 难度
    estimated_duration INT DEFAULT 300,          -- 预计时长（秒）
    default_params TEXT,                         -- 默认参数（JSON）
    background_template TEXT,                    -- 背景信息模板
    main_questions_template TEXT,                -- 主问题模板
    trigger_groups_template TEXT,                -- 触发问题组模板
    dimensions_template TEXT,                    -- 评估维度模板
    emotion_template TEXT,                       -- 情绪画像模板
    display_order INT DEFAULT 0,                 -- 显示顺序
    is_active TINYINT(1) DEFAULT 1,             -- 是否激活
    usage_count INT DEFAULT 0,                   -- 使用次数
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (industry_code) REFERENCES ai_coach_preset_industry(industry_code) ON DELETE CASCADE
);
```

## 🔧 后端实现

### 1. DAO层 (database/preset_scene_dao.py)

新增数据访问方法：

```python
def get_preset_scenes_by_industry(industry_code: str) -> List[Dict[str, Any]]:
    """根据行业代码获取预设场景列表"""

def get_preset_scene_by_code(scene_code: str) -> Optional[Dict[str, Any]]:
    """根据场景代码获取完整预设场景信息（包含模板）"""

def get_all_active_preset_scenes() -> List[Dict[str, Any]]:
    """获取所有激活的预设场景"""

def increment_usage_count(scene_code: str) -> bool:
    """增加场景使用次数"""

def get_industries_with_scene_count() -> List[Dict[str, Any]]:
    """获取所有行业及其场景数量"""
```

### 2. API路由 (routes/preset_scene_routes.py)

新增 RESTful API 接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/preset-scene/industries` | GET | 获取所有行业及场景数量 |
| `/api/preset-scene/industry/<industry_code>` | GET | 获取指定行业的场景列表 |
| `/api/preset-scene/detail/<scene_code>` | GET | 获取场景详情（含模板） |
| `/api/preset-scene/all` | GET | 获取所有激活场景 |
| `/api/preset-scene/use/<scene_code>` | POST | 增加场景使用次数 |

#### API 响应示例

**获取行业列表**
```json
GET /api/preset-scene/industries

{
    "success": true,
    "count": 2,
    "industries": [
        {"industry_code": "automobile", "scene_count": 5},
        {"industry_code": "education", "scene_count": 5}
    ]
}
```

**获取行业场景**
```json
GET /api/preset-scene/industry/automobile

{
    "success": true,
    "industry_code": "automobile",
    "count": 5,
    "scenes": [
        {
            "id": 1,
            "scene_code": "auto_first_visit",
            "scene_name": "客户首次到店接待",
            "scene_description": "模拟客户首次进入4S店的接待场景",
            "scene_tag": "hot",
            "ai_role": "想看车的客户",
            "user_role": "汽车销售顾问",
            "difficulty": "easy",
            "estimated_duration": 300,
            "usage_count": 0
        },
        ...
    ]
}
```

## 🎨 前端实现

### 1. 数据加载流程

```javascript
// 页面加载时自动调用
document.addEventListener('DOMContentLoaded', async () => {
    initEventListeners();
    await loadIndustryData();  // 从 API 加载数据
    renderIndustryCards();     // 渲染卡片
});
```

### 2. 核心函数

#### loadIndustryData()
从后端 API 加载行业和场景数据：

```javascript
async function loadIndustryData() {
    // 1. 获取行业列表
    const industriesResponse = await fetch('/api/preset-scene/industries');
    const industriesData = await industriesResponse.json();
    
    // 2. 为每个行业加载场景
    for (const industryInfo of industriesData.industries) {
        const industryCode = industryInfo.industry_code;
        const scenesResponse = await fetch(`/api/preset-scene/industry/${industryCode}`);
        const scenesData = await scenesResponse.json();
        
        // 3. 转换并存储数据
        INDUSTRY_DATA.push({...});
    }
}
```

#### getSceneIcon(sceneCode)
根据场景代码智能匹配 SVG 图标：

```javascript
function getSceneIcon(sceneCode) {
    if (sceneCode.includes('visit')) return SCENE_ICON_MAP.user_group;
    if (sceneCode.includes('price')) return SCENE_ICON_MAP.dollar;
    // ... 更多匹配规则
    return SCENE_ICON_MAP.user_group; // 默认图标
}
```

#### selectScene(industryId, sceneId)
用户选择场景时：
1. 调用 API 增加使用次数
2. 跳转到场景创建页面并传递参数

```javascript
async function selectScene(industryId, sceneId) {
    // 增加使用次数
    await fetch(`/api/preset-scene/use/${sceneId}`, { method: 'POST' });
    
    // 跳转并传递参数
    const params = new URLSearchParams({
        industry: industry.name,
        scene: scene.name,
        scene_desc: scene.desc,
        scene_code: sceneId
    });
    window.location.href = `/scene/create/?${params.toString()}`;
}
```

### 3. 前端配置

#### 行业配置 (INDUSTRY_CONFIG)

```javascript
const INDUSTRY_CONFIG = {
    'automobile': {
        icon: '<svg>...</svg>',
        name: '汽车销售',
        tag: { type: 'hot', text: '热门' }
    },
    'education': {
        icon: '<svg>...</svg>',
        name: '教育培训',
        tag: null
    }
};
```

#### 场景图标映射 (SCENE_ICON_MAP)

```javascript
const SCENE_ICON_MAP = {
    'user_group': '<svg>...</svg>',
    'dollar': '<svg>...</svg>',
    'phone': '<svg>...</svg>',
    // ... 更多图标
};
```

## 📦 数据初始化

### 使用初始化脚本

运行 `scripts/insert_preset_scenes.py` 插入初始数据：

```bash
python scripts/insert_preset_scenes.py
```

脚本会：
1. 清空现有预设数据
2. 插入 2 个行业（汽车销售、教育培训）
3. 插入 10 个预设场景（每个行业 5 个）

### 预设场景列表

#### 汽车销售 (5个)
1. 客户首次到店接待 (easy)
2. 试驾邀约与跟进 (medium)
3. 价格谈判与促成 (hard)
4. 竞品对比应对 (medium)
5. 潜客电话回访 (easy)

#### 教育培训 (5个)
1. 课程咨询接待 (easy)
2. 试听课邀约 (easy)
3. 学习需求诊断 (medium)
4. 价格异议处理 (hard)
5. 续费挽留沟通 (medium)

## 🔄 完整流程

### 用户操作流程

```
访问 / 
  ↓
重定向到 /industry/
  ↓
前端调用 API 加载行业和场景数据
  ↓
用户点击行业卡片
  ↓
打开场景选择弹窗
  ↓
用户选择具体场景
  ↓
调用 API 增加使用次数
  ↓
跳转到 /scene/create/?industry=...&scene=...&scene_code=...
```

### 数据流动

```
数据库 (ai_coach_preset_scene)
  ↓
DAO 层 (preset_scene_dao.py)
  ↓
API 路由 (preset_scene_routes.py)
  ↓
HTTP 响应 (JSON)
  ↓
前端 JavaScript (industry.js)
  ↓
DOM 渲染 (行业卡片 + 场景列表)
```

## ✅ 测试验证

### 1. 数据库测试

```python
import db

# 测试获取行业列表
industries = db.get_industries_with_scene_count()
print(industries)  
# [{'industry_code': 'automobile', 'scene_count': 5}, ...]

# 测试获取场景列表
scenes = db.get_preset_scenes_by_industry('automobile')
print(len(scenes))  # 5

# 测试增加使用次数
db.increment_usage_count('auto_first_visit')
```

### 2. API 测试

```bash
# 获取行业列表
curl http://localhost:5000/api/preset-scene/industries

# 获取汽车销售场景
curl http://localhost:5000/api/preset-scene/industry/automobile

# 获取场景详情
curl http://localhost:5000/api/preset-scene/detail/auto_first_visit

# 增加使用次数
curl -X POST http://localhost:5000/api/preset-scene/use/auto_first_visit
```

### 3. 前端测试

1. 启动服务器：`python app.py`
2. 访问：`http://localhost:5000/`
3. 验证：
   - ✅ 页面自动加载行业和场景数据
   - ✅ 显示 2 个行业卡片（汽车销售、教育培训）
   - ✅ 点击行业卡片弹出场景选择框
   - ✅ 显示 5 个场景（每个行业）
   - ✅ 点击场景跳转到场景创建页面
   - ✅ URL 包含正确的参数

## 📝 文件清单

### 新增文件

```
database/
  └── preset_scene_dao.py          # 预设场景 DAO

routes/
  └── preset_scene_routes.py       # 预设场景 API 路由

scripts/
  └── insert_preset_scenes.py      # 数据初始化脚本

md/
  └── PRESET_SCENE_IMPLEMENTATION.md  # 本文档
```

### 修改文件

```
database/__init__.py              # 导出新的 DAO 函数
db.py                             # 导出新的 DAO 函数
app.py                            # 注册新的 API 路由
front_end/industry/static/js/industry.js  # 改为从 API 加载数据
```

## 🎯 优势与特点

### 1. 数据驱动
- ✅ 场景数据存储在数据库，便于管理和更新
- ✅ 无需修改代码即可添加/修改场景
- ✅ 支持动态启用/禁用场景

### 2. 统计功能
- ✅ 自动记录每个场景的使用次数
- ✅ 支持按使用次数排序
- ✅ 便于分析用户偏好

### 3. 可扩展性
- ✅ 支持添加更多行业
- ✅ 支持自定义场景模板
- ✅ 预留字段用于未来功能

### 4. 用户体验
- ✅ 加载状态提示
- ✅ 错误处理和重试机制
- ✅ 平滑的动画效果

## 🚀 未来扩展

### 1. 场景模板功能
利用数据库中的模板字段：
- `background_template`
- `main_questions_template`
- `trigger_groups_template`
- `dimensions_template`
- `emotion_template`

可以实现：
- 快速生成场景内容
- 场景参数化配置
- 场景复制和变体

### 2. 用户自定义场景
- 用户可以基于预设场景创建变体
- 保存用户的场景配置
- 分享场景给其他用户

### 3. 数据分析
- 场景使用趋势分析
- 热门场景推荐
- 个性化场景推荐

### 4. 管理后台
- 可视化编辑场景
- 批量导入导出场景
- 场景版本管理

## 📞 技术支持

如有问题，请检查：
1. 数据库表是否正确创建
2. 初始数据是否已插入
3. API 路由是否正确注册
4. 前端控制台是否有错误
5. 网络请求是否成功

## 📄 相关文档

- [场景创建使用指南](./SCENE_CREATE_GUIDE.md)
- [场景智能体实现](./SCENE_AGENT_IMPLEMENTATION.md)
- [实时对练流程](./REALTIME_FLOW.md)