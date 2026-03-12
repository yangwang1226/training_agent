-- ============================================
-- 添加 SOP 质检分数字段
-- 日期: 2024-03-15
-- 说明: 在 ai_coach_record 表中添加 sop_score 字段
-- ============================================

-- 1. 检查当前表结构
DESC ai_coach_record;

-- 2. 添加 sop_score 字段
ALTER TABLE ai_coach_record
ADD COLUMN sop_score INT DEFAULT 0 COMMENT 'SOP质检总分(0-100)' AFTER sop_result;

-- 3. 验证字段添加成功
DESC ai_coach_record;

-- 4. 查看示例数据
SELECT 
    session_id,
    ai_score,
    sop_score,
    sop_result,
    created_time
FROM ai_coach_record
WHERE is_delete = 0
ORDER BY created_time DESC
LIMIT 3;

-- ============================================
-- SOP 分数规则说明
-- ============================================
-- must_do (必须项):    每项 30 分
-- should_do (建议项):  每项 15 分
-- must_not_do (禁止项): 违反扣 30 分
--
-- 计算公式:
--   sop_score = (实际得分 / 总可得分) × 100
--
-- 示例:
--   3个 must_do (3×30=90分)
--   2个 should_do (2×15=30分)
--   总分 120 分
--   通过了 2个 must_do + 1个 should_do = 60+15=75分
--   sop_score = (75/120) × 100 = 62.5 ≈ 63分
-- ============================================