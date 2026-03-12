-- ============================================
-- 添加综合评分字段
-- 日期: 2024-03-15
-- 说明: 在 ai_coach_record 表中添加 final_score 字段
--       final_score = ai_score * 0.4 + sop_score * 0.6
-- ============================================

-- 1. 检查当前表结构
DESC ai_coach_record;

-- 2. 添加 final_score 字段
ALTER TABLE ai_coach_record
ADD COLUMN final_score INT DEFAULT 0 COMMENT '综合评分(0-100)，由AI评分和SOP评分加权计算' AFTER sop_score;

-- 3. 验证字段添加成功
DESC ai_coach_record;

-- 4. 更新现有记录的 final_score（回填数据）
UPDATE ai_coach_record
SET final_score = ROUND(COALESCE(ai_score, 0) * 0.4 + COALESCE(sop_score, 0) * 0.6)
WHERE is_delete = 0;

-- 5. 查看更新后的示例数据
SELECT 
    session_id,
    ai_score,
    sop_score,
    final_score,
    created_time
FROM ai_coach_record
WHERE is_delete = 0
ORDER BY created_time DESC
LIMIT 10;

-- 6. 验证计算公式
SELECT 
    session_id,
    ai_score,
    sop_score,
    final_score,
    ROUND(COALESCE(ai_score, 0) * 0.4 + COALESCE(sop_score, 0) * 0.6) as calculated_score,
    (final_score = ROUND(COALESCE(ai_score, 0) * 0.4 + COALESCE(sop_score, 0) * 0.6)) as is_correct
FROM ai_coach_record
WHERE is_delete = 0
LIMIT 10;

-- ============================================
-- 执行完毕
-- ============================================