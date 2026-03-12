-- 检查最近的训练记录

-- 1. 查看最新的5条记录
SELECT 
    session_id,
    scene_id,
    user_id,
    call_duration,
    oss_file_path,
    LEFT(word_content, 50) as word_content_preview,
    score,
    created_time
FROM ai_coach_record
WHERE is_delete = 0
ORDER BY created_time DESC
LIMIT 5;

-- 2. 统计今天的记录数
SELECT COUNT(*) as today_count
FROM ai_coach_record
WHERE DATE(created_time) = CURDATE()
AND is_delete = 0;

-- 3. 检查是否有评估分数的记录
SELECT 
    COUNT(*) as total_records,
    COUNT(score) as records_with_score,
    COUNT(overall_score) as records_with_overall_score
FROM ai_coach_record
WHERE is_delete = 0;

-- 4. 查看表结构
DESC ai_coach_record;
