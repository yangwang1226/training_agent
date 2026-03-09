# 预设场景快速启动功能

## 📋 功能概述

实现了从预设场景快速创建用户场景的功能，用户可以：
1. 跳过对话式创建流程
2. 可选填写简单的背景信息
3. 快速生成场景并开始对练

## 🎯 场景状态管理

### 状态枚举（SceneStatus）

| 状态值 | 状态名 | 说明 | 使用场景 |
|--------|--------|------|----------|
| `0` | DRAFT | 草稿 | 用户在对话创建中，但还未生成完整场景 |
| `1` | PRESET_TEMPLATE | 预设模板 | 用户点击"跳过"，直接用预设场景数据生成（无个性化背景） |
| `2` | CUSTOMIZED | 已定制 | 用户提供了背景信息，AI 融合生成的个性化场景 |
| `9` | ARCHIVED | 已归档 | 场景被禁用或删除 |

### 状态流转

```
【预设场景快速启动】
  用户点击"跳过，直接开始"
          ↓
  后端用预设数据生成 scene
          ↓
  status = 1 (PRESET_TEMPLATE)
          ↓
  跳转 /realtime/{scene_id}

【对话式创建】
  用户进入 /scene/create/
          ↓
  (可选) 创建草稿记录
  status = 0 (DRAFT)
          ↓
  对话收集信息...
          ↓
  生成完整场景
  status = 2 (CUSTOMIZED)
          ↓
  跳转 /realtime/{scene_id}
```

## 🔧 核心实现

### 1. 数据库层 (database/)

#### scene_dao.py
```python
class SceneStatus:
    DRAFT = 0
    PRESET_TEMPLATE = 1
    CUSTOMIZED = 2
    ARCHIVED = 9

# 默认状态改为 CUSTOMIZED
def save_scene(..., status: int = SceneStatus.CUSTOMIZED)

# 获取可用场景（排除草稿和归档）
def get_active_scenes() -> List[Dict[str, Any]]
```

#### preset_scene_dao.py
```python
# 构建预设场景提示词
def build_preset_prompt(preset: Dict, background_hint: Optional[str]) -> str

# 从预设场景快速创建
def create_scene_from_preset(
    preset_scene_code: str,
    background_hint: Optional[str] = None,
    ...
) -> Optional[int]
```

### 2. API 层 (routes/)

#### preset_scene_routes.py

**新增端点：快速启动**
```
POST /api/preset-scene/quick-start/<scene_code>

Request Body:
{
    "background_hint": "客户是30岁女性..." (可选)
}

Response:
{
    "success": true,
    "scene_id": 123,
    "redirect_url": "/realtime/123",
    "message": "场景已准备就绪！"
}
```

### 3. 数据库迁移 (scripts/)

```sql
-- 为 status 字段添加注释
ALTER TABLE ai_coach_scene 
MODIFY COLUMN status INT DEFAULT 0 
COMMENT '场景状态：0=草稿 1=预设模板 2=已定制 9=已归档';

-- 将现有场景标记为"已定制"
UPDATE ai_coach_scene 
SET status = 2 
WHERE status = 0 AND deleted = 0;

-- 创建索引
CREATE INDEX idx_scene_status_deleted 
ON ai_coach_scene(status, deleted);
```

## 📡 API 使用示例

### 示例 1: 不带背景信息快速启动

```javascript
fetch('/api/preset-scene/quick-start/auto_first_visit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect_url;
    }
});
```

### 示例 2: 带背景信息快速启动

```javascript
fetch('/api/preset-scene/quick-start/auto_first_visit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        background_hint: '客户是一位30岁的女性，想购买SUV，预算25-30万'
    })
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        console.log('场景ID:', data.scene_id);
        window.location.href = data.redirect_url;
    }
});
```

### 示例 3: 带用户信息（如果有登录系统）

```javascript
fetch('/api/preset-scene/quick-start/auto_first_visit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        background_hint: '客户想看SUV',
        org_id: 1,
        creator_id: 123,
        create_name: '张三'
    })
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect_url;
    }
});
```

## 🧪 测试

### 运行测试脚本

```bash
python scripts/test_quick_start.py
```

### 手动测试步骤

1. **运行数据库迁移**
   ```bash
   # 在 MySQL 客户端中执行
   mysql -u root -p ai_coach < scripts/migration_scene_status.sql
   ```

2. **启动服务器**
   ```bash
   python app.py
   ```

3. **测试快速启动 API**
   ```bash
   curl -X POST http://localhost:5000/api/preset-scene/quick-start/auto_first_visit \
     -H "Content-Type: application/json" \
     -d '{"background_hint": "测试背景信息"}'
   ```

4. **验证场景创建**
   - 检查返回的 `scene_id`
   - 访问 `/realtime/{scene_id}` 确认可以正常对练

## 📊 数据验证

### 查询场景状态分布

```sql
SELECT 
    status,
    CASE status
        WHEN 0 THEN '草稿'
        WHEN 1 THEN '预设模板'
        WHEN 2 THEN '已定制'
        WHEN 9 THEN '已归档'
    END as status_name,
    COUNT(*) as count
FROM ai_coach_scene
WHERE deleted = 0
GROUP BY status;
```

### 查询最近创建的预设模板场景

```sql
SELECT id, scene_name, status, created_time
FROM ai_coach_scene
WHERE status = 1  -- PRESET_TEMPLATE
ORDER BY created_time DESC
LIMIT 10;
```

## ⚠️ 注意事项

1. **场景名称唯一性**
   - 使用时间戳后缀避免重复：`场景名_1704844800`

2. **背景信息处理**
   - 如果用户提供了 `background_hint`，会追加到预设模板中
   - 如果未提供，直接使用预设模板

3. **使用次数统计**
   - 每次快速启动会自动增加预设场景的 `usage_count`

4. **状态管理**
   - 快速启动的场景状态为 `PRESET_TEMPLATE (1)`
   - 对话创建的场景状态为 `CUSTOMIZED (2)`
   - 可通过状态区分场景来源，便于后续数据分析

## 🔄 后续扩展

1. **增强背景融合**
   - 使用 AI 将用户背景更自然地融入预设模板
   - 支持更复杂的背景参数配置

2. **场景收藏功能**
   - 用户可以收藏常用的预设场景
   - 快速访问历史创建的场景

3. **数据分析**
   - 统计哪些预设场景最受欢迎
   - 分析用户是否更倾向于快速启动还是定制创建

4. **场景模板优化**
   - 根据使用数据优化预设模板内容
   - 动态调整推荐的预设场景

## 📝 变更日志

### 2025-01-09
- ✅ 实现场景状态枚举（DRAFT, PRESET_TEMPLATE, CUSTOMIZED, ARCHIVED）
- ✅ 新增 `create_scene_from_preset()` 函数
- ✅ 新增 `/api/preset-scene/quick-start/<scene_code>` API
- ✅ 更新 `list_scenes()` 只返回可用场景
- ✅ 创建数据库迁移脚本
- ✅ 添加测试脚本

## 🤝 贡献指南

如需修改或扩展此功能，请：
1. 更新相关代码文件
2. 更新本文档
3. 添加或更新测试用例
4. 运行测试确保功能正常