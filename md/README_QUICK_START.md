# 🚀 预设场景快速启动功能

## 📦 功能简介

用户可以跳过复杂的对话式场景创建流程，直接从预设场景快速生成训练场景并开始对练。

**核心优势：**
- ⚡ 快速启动 - 1秒生成场景
- 🎯 预设模板 - 专业场景配置
- ✏️ 可选定制 - 支持补充背景信息
- 📊 状态管理 - 区分场景来源便于分析

## 🎯 状态枚举

| 状态值 | 状态名 | 说明 |
|--------|--------|------|
| `0` | DRAFT | 草稿（对话创建中） |
| `1` | PRESET_TEMPLATE | 预设模板（快速启动） |
| `2` | CUSTOMIZED | 已定制（对话创建完成） |
| `9` | ARCHIVED | 已归档 |

## 🔧 快速部署

### 1. 执行数据库迁移

```bash
mysql -u root -p ai_coach < scripts/migration_scene_status.sql
```

### 2. 重启应用

```bash
python app.py
```

### 3. 测试 API

```bash
curl -X POST http://localhost:5000/api/preset-scene/quick-start/auto_first_visit \
  -H "Content-Type: application/json" \
  -d '{"background_hint": "客户是30岁女性，预算25-30万"}'
```

## 📡 API 文档

### POST /api/preset-scene/quick-start/{scene_code}

**请求参数：**
```json
{
  "background_hint": "用户补充的背景信息（可选）",
  "org_id": 1,
  "creator_id": 123,
  "create_name": "张三"
}
```

**成功响应：**
```json
{
  "success": true,
  "scene_id": 123,
  "redirect_url": "/realtime/123",
  "message": "场景已准备就绪！"
}
```

**失败响应：**
```json
{
  "success": false,
  "error": "场景创建失败，请检查场景代码是否正确"
}
```

## 📁 修改的文件

### 核心代码
- ✅ `database/scene_dao.py` - 状态枚举和查询逻辑
- ✅ `database/preset_scene_dao.py` - 快速创建函数
- ✅ `database/__init__.py` - 导出新函数
- ✅ `routes/preset_scene_routes.py` - API 端点

### 脚本和文档
- ✅ `scripts/migration_scene_status.sql` - 数据库迁移
- ✅ `scripts/test_quick_start.py` - 测试脚本
- ✅ `docs/QUICK_START_FEATURE.md` - 详细文档
- ✅ `docs/DEPLOYMENT_CHECKLIST.md` - 部署清单

## 🧪 测试

```bash
# 运行自动化测试
python scripts/test_quick_start.py
```

## 📊 验证

```sql
-- 查看场景状态分布
SELECT 
    status,
    COUNT(*) as count
FROM ai_coach_scene
WHERE deleted = 0
GROUP BY status;

-- 查看快速启动创建的场景
SELECT id, scene_name, created_time
FROM ai_coach_scene
WHERE status = 1
ORDER BY created_time DESC
LIMIT 10;
```

## ⚠️ 注意事项

1. **备份数据库** - 迁移前务必备份
2. **场景代码** - 确保预设场景存在
3. **状态管理** - 新创建的场景默认为 CUSTOMIZED (2)
4. **向后兼容** - 现有场景自动标记为已定制

## 📖 详细文档

- 完整功能说明：`docs/QUICK_START_FEATURE.md`
- 部署检查清单：`docs/DEPLOYMENT_CHECKLIST.md`
- 实现总结：`docs/IMPLEMENTATION_SUMMARY.md`

## 🎉 完成状态

✅ 所有代码已实现  
✅ 数据库迁移脚本已创建  
✅ 测试脚本已创建  
✅ 文档已完善  

**待完成：**
- 执行数据库迁移
- 部署到服务器
- 前端集成（如需要）
- 用户验收测试

---

**版本：** 1.0.0  
**创建时间：** 2025-01-09  
**状态：** ✅ 开发完成，等待部署