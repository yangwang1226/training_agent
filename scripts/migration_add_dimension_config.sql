-- 能力画像维度动态化 - 数据库迁移脚本
-- 执行前请备份数据库

-- 为 ai_coach_scene 表新增维度配置相关字段
ALTER TABLE ai_coach_scene
ADD COLUMN dimension_config TEXT COMMENT '维度配置JSON' AFTER scene_prompt,
ADD COLUMN role_type VARCHAR(100) COMMENT 'AI模拟角色类型' AFTER dimension_config,
ADD COLUMN role_description TEXT COMMENT '角色描述' AFTER role_type,
ADD COLUMN industry VARCHAR(100) COMMENT '行业' AFTER role_description,
ADD COLUMN training_goal TEXT COMMENT '培训目标' AFTER industry,
ADD COLUMN full_evaluation_prompt TEXT COMMENT '完整评估提示词' AFTER training_goal;

-- 查看表结构确认
DESCRIBE ai_coach_scene;
