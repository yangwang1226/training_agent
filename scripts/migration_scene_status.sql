-- =========================================
-- 场景状态管理迁移脚本
-- 创建时间: 2025-01-09
-- 说明: 为场景表添加状态管理功能
-- =========================================

-- 1. 为 status 字段添加详细注释
ALTER TABLE ai_coach_scene 
MODIFY COLUMN status INT DEFAULT 0 
COMMENT '场景状态：0=草稿 1=预设模板 2=已定制 9=已归档';

-- 2. 将现有的可用场景标记为"已定制"状态
-- （假设 status=0 且 deleted=0 的是正常使用的场景）
UPDATE ai_coach_scene 
SET status = 2 
WHERE status = 0 
  AND deleted = 0
  AND scene_name IS NOT NULL 
  AND scene_prompt IS NOT NULL;

-- 3. 创建索引以提升查询性能
CREATE INDEX idx_scene_status_deleted 
ON ai_coach_scene(status, deleted);

-- 4. 查看迁移结果
SELECT 
    status,
    CASE status
        WHEN 0 THEN '草稿'
        WHEN 1 THEN '预设模板'
        WHEN 2 THEN '已定制'
        WHEN 9 THEN '已归档'
        ELSE '未知'
    END as status_name,
    COUNT(*) as count
FROM ai_coach_scene
WHERE deleted = 0
GROUP BY status
ORDER BY status;

-- 5. 验证查询（确保能正确获取可用场景）
SELECT id, scene_name, status, created_time
FROM ai_coach_scene
WHERE deleted = 0 
  AND status IN (1, 2)  -- 只显示模板和定制场景
ORDER BY created_time DESC
LIMIT 10;