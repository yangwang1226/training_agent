# 🚀 快速启动功能部署检查清单

## 📋 部署前检查

### 1. 代码文件确认

- [x] `database/scene_dao.py` - 已添加 SceneStatus 枚举和更新函数
- [x] `database/preset_scene_dao.py` - 已添加 create_scene_from_preset 和 build_preset_prompt
- [x] `database/__init__.py` - 已导出新函数
- [x] `routes/preset_scene_routes.py` - 已添加 /quick-start API
- [x] `scripts/migration_scene_status.sql` - 数据库迁移脚本已创建
- [x] `scripts/test_quick_start.py` - 测试脚本已创建

### 2. 依赖检查

```bash
# 检查 Python 环境
python --version  # 应该 >= 3.8

# 检查必要的包
pip list | grep -E "flask|pymysql|requests"
```

## 🔧 部署步骤

### 步骤 1: 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p ai_coach > backup_$(date +%Y%m%d_%H%M%S).sql

# 或者只备份场景表
mysqldump -u root -p ai_coach ai_coach_scene > backup_scene_$(date +%Y%m%d_%H%M%S).sql
```

### 步骤 2: 执行数据库迁移

```bash
# 方式 1: 直接执行 SQL 文件
mysql -u root -p ai_coach < scripts/migration_scene_status.sql

# 方式 2: 使用 MySQL 客户端
mysql -u root -p
use ai_coach;
source scripts/migration_scene_status.sql;
```

**预期结果：**
```
Query OK, X rows affected  # 更新 status 字段
Query OK, 0 rows affected  # 添加索引
```

### 步骤 3: 验证数据库迁移

```sql
-- 1. 检查字段注释
SHOW FULL COLUMNS FROM ai_coach_scene WHERE Field = 'status';

-- 2. 检查索引
SHOW INDEX FROM ai_coach_scene WHERE Key_name = 'idx_scene_status_deleted';

-- 3. 检查数据状态分布
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

**预期输出：**
```
+--------+-------------+-------+
| status | status_name | count |
+--------+-------------+-------+
|      2 | 已定制      |   X   |  # 所有现有场景都应该是 2
+--------+-------------+-------+
```

### 步骤 4: 重启应用

```bash
# 如果使用 systemd
sudo systemctl restart training_agent

# 或者手动重启
# 1. 停止当前进程
pkill -f "python app.py"

# 2. 启动新进程
nohup python app.py > app.log 2>&1 &

# 3. 查看日志
tail -f app.log
```

### 步骤 5: 验证 API 端点

```bash
# 测试 API 是否正常响应
curl -X POST http://localhost:5000/api/preset-scene/quick-start/auto_first_visit \
  -H "Content-Type: application/json" \
  -d '{}'

# 预期返回
{
  "success": true,
  "scene_id": 123,
  "redirect_url": "/realtime/123",
  "message": "场景已准备就绪！"
}
```

### 步骤 6: 运行测试脚本

```bash
python scripts/test_quick_start.py
```

**预期输出：**
```
开始测试快速启动功能...

=== 测试1: 不带背景信息的快速启动 ===
状态码: 200
响应: {
  "success": true,
  "scene_id": 123,
  ...
}

=== 测试2: 带背景信息的快速启动 ===
状态码: 200
响应: {
  "success": true,
  "scene_id": 124,
  ...
}

=== 测试完成 ===
✅ 测试1通过 - 场景ID: 123
✅ 测试2通过 - 场景ID: 124
```

## ✅ 功能验证

### 1. 数据库验证

```sql
-- 检查快速启动创建的场景
SELECT 
    id,
    scene_name,
    status,
    created_time
FROM ai_coach_scene
WHERE status = 1  -- PRESET_TEMPLATE
ORDER BY created_time DESC
LIMIT 5;
```

### 2. API 功能验证

#### 测试用例 1: 不带背景
```bash
curl -X POST http://localhost:5000/api/preset-scene/quick-start/auto_first_visit \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 测试用例 2: 带背景
```bash
curl -X POST http://localhost:5000/api/preset-scene/quick-start/auto_first_visit \
  -H "Content-Type: application/json" \
  -d '{"background_hint": "客户是30岁女性，预算25-30万"}'
```

#### 测试用例 3: 无效场景代码
```bash
curl -X POST http://localhost:5000/api/preset-scene/quick-start/invalid_code \
  -H "Content-Type: application/json" \
  -d '{}'
```

**预期返回：**
```json
{
  "success": false,
  "error": "场景创建失败，请检查场景代码是否正确"
}
```

### 3. 端到端验证

1. **访问行业选择页面**
   ```
   http://localhost:5000/industry/
   ```

2. **选择行业和场景**
   - 选择一个行业（如汽车销售）
   - 选择一个场景（如客户首次到店）

3. **填写背景信息（可选）**
   - 可以填写背景
   - 也可以留空

4. **点击"开始训练"**
   - 应该看到加载提示
   - 自动跳转到 `/realtime/{scene_id}`

5. **验证对练页面**
   - 场景信息正确显示
   - AI 角色正确
   - 可以正常开始对话

## 🔍 故障排查

### 问题 1: API 返回 500 错误

**检查步骤：**
```bash
# 查看应用日志
tail -f app.log

# 检查 Python 进程
ps aux | grep python

# 检查数据库连接
mysql -u root -p -e "SELECT 1;"
```

### 问题 2: 场景创建失败

**可能原因：**
1. 预设场景不存在
2. 数据库连接失败
3. 字段值过长或格式错误

**调试方法：**
```python
# 在 Python 中测试
import db as db_module

# 检查预设场景是否存在
preset = db_module.get_preset_scene_by_code('auto_first_visit')
print(preset)

# 测试创建场景
scene_id = db_module.create_scene_from_preset('auto_first_visit')
print(f"Scene ID: {scene_id}")
```

### 问题 3: 迁移脚本执行失败

**检查权限：**
```sql
SHOW GRANTS FOR CURRENT_USER();
```

**手动执行每条语句：**
```sql
-- 一条一条执行，看哪条失败
ALTER TABLE ai_coach_scene 
MODIFY COLUMN status INT DEFAULT 0 
COMMENT '场景状态：0=草稿 1=预设模板 2=已定制 9=已归档';
```

## 📊 监控指标

### 关键指标

1. **场景创建成功率**
   ```sql
   SELECT 
       DATE(created_time) as date,
       COUNT(*) as total_created,
       SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as preset_count,
       SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as custom_count
   FROM ai_coach_scene
   WHERE deleted = 0
   GROUP BY DATE(created_time)
   ORDER BY date DESC
   LIMIT 7;
   ```

2. **预设场景使用排名**
   ```sql
   SELECT 
       scene_code,
       scene_name,
       usage_count
   FROM ai_coach_preset_scene
   WHERE is_active = 1
   ORDER BY usage_count DESC
   LIMIT 10;
   ```

3. **平均创建时间**
   - 在应用日志中记录创建耗时
   - 监控数据库查询性能

## 🔄 回滚方案

如果出现严重问题，可以回滚：

### 1. 恢复数据库
```bash
# 使用之前的备份
mysql -u root -p ai_coach < backup_YYYYMMDD_HHMMSS.sql
```

### 2. 回滚代码
```bash
# 使用 git 回退
git checkout HEAD~1  # 回退到上一个提交

# 或者恢复特定文件
git checkout HEAD~1 -- database/scene_dao.py
git checkout HEAD~1 -- routes/preset_scene_routes.py
```

### 3. 重启服务
```bash
sudo systemctl restart training_agent
```

## ✨ 部署完成确认

- [ ] 数据库迁移成功执行
- [ ] 索引创建成功
- [ ] 现有场景状态正确更新
- [ ] 应用成功重启，无错误日志
- [ ] API 端点正常响应
- [ ] 测试脚本全部通过
- [ ] 创建的场景状态为 PRESET_TEMPLATE (1)
- [ ] 可以正常跳转到对练页面
- [ ] 前端页面功能正常

## 📝 部署记录

**部署日期：** _____________
**部署人员：** _____________
**部署环境：** □ 开发环境  □ 测试环境  □ 生产环境
**备份文件：** _____________

**测试结果：**
- API 测试：□ 通过  □ 失败
- 功能验证：□ 通过  □ 失败
- 性能测试：□ 通过  □ 失败

**问题记录：**
```

```

**解决方案：**
```

```

---

**部署完成签字：** _____________  **日期：** _____________