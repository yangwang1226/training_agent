-- ============================================
-- 从 ai_coach_record 表删除 sop_checklist 字段
-- 日期: 2024-03-15
-- 说明: 记录表不再存储 SOP 快照，直接引用场景表
-- ============================================

-- 1. 检查当前表结构
DESC ai_coach_record;

-- 2. 查看是否存在 sop_checklist 字段
SHOW COLUMNS FROM ai_coach_record LIKE 'sop_checklist';

-- 3. 删除 sop_checklist 字段（如果存在）
ALTER TABLE ai_coach_record
DROP COLUMN IF EXISTS sop_checklist;

-- 4. 验证删除后的表结构
DESC ai_coach_record;

-- 5. 确认字段列表
SHOW FULL COLUMNS FROM ai_coach_record;

-- ============================================
-- 说明
-- ============================================
-- sop_checklist 字段已从记录表中删除
-- SOP 质检项现在只存储在场景表 (ai_coach_scene) 中
-- 评估时从场景表读取，质检结果存储在 sop_result 字段
-- ============================================