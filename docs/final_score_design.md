# 综合评分（final_score）设计文档

## 概述

`final_score` 是对销售训练会话的综合评分，通过加权平均的方式结合 AI 维度评分和 SOP 流程评分，提供一个统一的评估标准。

## 计算公式

```
final_score = ai_score × 0.4 + sop_score × 0.6
```

### 权重说明

- **AI 维度评分（40%）**：评估销售人员的软技能
  - 沟通能力
  - 情绪管理
  - 产品知识
  - 需求挖掘
  - 异议处理

- **SOP 流程评分（60%）**：评估流程规范执行情况
  - 必做项完成度
  - 禁止项规避情况
  - 标准话术使用
  - 流程完整性

### 权重设计理由

1. **SOP 占比更高（60%）**：
   - 流程规范是销售的基础
   - 标准化操作保证服务质量
   - 企业合规要求

2. **AI 评分也重要（40%）**：
   - 软技能决定销售上限
   - 个人能力差异化
   - 客户体验关键

## 数据库结构

### ai_coach_record 表字段

```sql
CREATE TABLE ai_coach_record (
    -- ... 其他字段 ...
    ai_score INT DEFAULT 0 COMMENT 'AI维度评分(0-100)',
    sop_score INT DEFAULT 0 COMMENT 'SOP质检总分(0-100)',
    final_score INT DEFAULT 0 COMMENT '综合评分(0-100)，由AI评分和SOP评分加权计算',
    -- ... 其他字段 ...
);
```

## 使用方式

### 1. 自动计算（推荐）

在保存训练记录时，`final_score` 会自动计算：

```python
from database.record_dao import save_coach_record

save_coach_record(
    session_id="session_123",
    scene_id=1,
    user_id=1,
    ai_score=80,      # AI 评分
    sop_score=90,     # SOP 评分
    # final_score 会自动计算为 86
    # ... 其他参数 ...
)
```

### 2. 更新评分时自动重算

更新 `ai_score` 或 `sop_score` 时，`final_score` 会自动重新计算：

```python
from database.record_dao import update_coach_record

# 更新 AI 评分
update_coach_record(
    session_id="session_123",
    ai_score=85  # final_score 会自动重新计算
)

# 更新 SOP 评分
update_coach_record(
    session_id="session_123",
    sop_score=95  # final_score 会自动重新计算
)
```

### 3. 手动计算

如果需要预览或验证评分：

```python
from database.record_dao import calculate_final_score

# 计算综合评分
final = calculate_final_score(ai_score=80, sop_score=90)
print(f"综合评分: {final}")  # 输出: 86
```

## API 返回示例

### 评估报告接口

```json
{
  "success": true,
  "data": {
    "session_id": "session_123",
    "ai_score": 80,
    "sop_score": 90,
    "final_score": 86,
    "dimension_result": { ... },
    "sop_result": { ... }
  }
}
```

## 评分等级划分

建议的评分等级：

| 综合评分 | 等级 | 说明 |
|---------|------|------|
| 90-100  | 优秀 | 表现出色，可作为标杆 |
| 80-89   | 良好 | 表现良好，有提升空间 |
| 70-79   | 合格 | 达到基本要求 |
| 60-69   | 待提升 | 需要加强训练 |
| 0-59    | 不合格 | 需要重点培训 |

## 数据迁移

### 添加 final_score 字段

```bash
# 执行迁移脚本
mysql -u your_user -p your_database < scripts/migration_add_final_score.sql
```

### 回填历史数据

```sql
-- 更新现有记录的 final_score
UPDATE ai_coach_record
SET final_score = ROUND(COALESCE(ai_score, 0) * 0.4 + COALESCE(sop_score, 0) * 0.6)
WHERE is_delete = 0;
```

## 测试

运行测试脚本验证功能：

```bash
python tests/test_final_score.py
```

### 预期输出

```
=== 测试综合评分计算 ===

✓ AI=80, SOP=90 => final_score=86 (预期: 86)
✓ AI=100, SOP=100 => final_score=100 (预期: 100)
✓ AI=0, SOP=0 => final_score=0 (预期: 0)
...

总计: 8 个测试用例
通过: 8
失败: 0

=== 测试权重分配 ===

AI=100, SOP=0 => 40 (应该是 40，即 AI 权重)
AI=0, SOP=100 => 60 (应该是 60，即 SOP 权重)

权重验证: ✓ 通过
AI 权重 40%, SOP 权重 60%
```

## 注意事项

1. **空值处理**：如果 `ai_score` 或 `sop_score` 为 `None`，会被视为 0
2. **四舍五入**：最终评分会四舍五入到整数
3. **自动计算**：无需手动指定 `final_score`，系统会自动计算
4. **更新触发**：更新任一评分字段时，`final_score` 会自动重新计算

## 未来优化方向

1. **可配置权重**：支持不同场景使用不同的权重配置
2. **动态权重**：根据行业、岗位、经验等因素动态调整权重
3. **多维度综合**：考虑加入更多评估维度（如客户满意度、成交率等）
4. **历史趋势**：追踪用户的综合评分变化趋势