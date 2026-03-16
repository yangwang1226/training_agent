-- 更新预设场景的 SOP 质检项，添加 item_name 和 item_score 字段
-- 场景：客户首次进店接待 (auto_first_visit)

UPDATE ai_coach_preset_scene 
SET default_sop_checklist = '[
    {
        "category": "greeting",
        "check_point": "开场问候",
        "item_name": "开场问候",
        "item_score": 10,
        "check_criteria": "是否主动热情招呼客户，第一时间建立良好印象",
        "check_type": "must_do"
    },
    {
        "category": "need_analysis",
        "check_point": "需求挖掘",
        "item_name": "需求挖掘",
        "item_score": 15,
        "check_criteria": "是否通过提问了解客户购车用途、预算、关注点等核心需求",
        "check_type": "must_do"
    },
    {
        "category": "product_intro",
        "check_point": "产品介绍",
        "item_name": "产品介绍",
        "item_score": 15,
        "check_criteria": "是否根据客户需求，有针对性地介绍车型配置和卖点",
        "check_type": "must_do"
    },
    {
        "category": "objection_handling",
        "check_point": "异议处理",
        "item_name": "异议处理",
        "item_score": 15,
        "check_criteria": "面对客户疑虑和异议，是否给予专业、耐心的解答",
        "check_type": "must_do"
    },
    {
        "category": "test_drive",
        "check_point": "试驾邀约",
        "item_name": "试驾邀约",
        "item_score": 10,
        "check_criteria": "是否主动邀请客户试驾，强调试驾的重要性和价值",
        "check_type": "must_do"
    },
    {
        "category": "value_proposition",
        "check_point": "价值塑造",
        "item_name": "价值塑造",
        "item_score": 15,
        "check_criteria": "是否充分展示车辆和服务的价值，而非仅仅谈价格",
        "check_type": "must_do"
    },
    {
        "category": "professionalism",
        "check_point": "专业形象",
        "item_name": "专业形象",
        "item_score": 10,
        "check_criteria": "全程保持专业、自信的沟通态度和措辞",
        "check_type": "must_do"
    },
    {
        "category": "closing",
        "check_point": "促成跟进",
        "item_name": "促成跟进",
        "item_score": 10,
        "check_criteria": "对话结束时是否明确下一步行动，留下联系方式",
        "check_type": "must_do"
    },
    {
        "category": "forbidden",
        "check_point": "禁止过早报价",
        "item_name": "禁止过早报价",
        "item_score": 0,
        "check_criteria": "在未充分了解需求前，不应直接报底价",
        "check_type": "must_not"
    },
    {
        "category": "forbidden",
        "check_point": "禁止贬低竞品",
        "item_name": "禁止贬低竞品",
        "item_score": 0,
        "check_criteria": "不得使用负面语言贬低竞争对手品牌或产品",
        "check_type": "must_not"
    }
]'
WHERE scene_code = 'auto_first_visit';

-- 验证更新
SELECT 
    scene_code,
    scene_name,
    JSON_LENGTH(default_sop_checklist) as sop_count,
    default_sop_checklist
FROM ai_coach_preset_scene
WHERE scene_code = 'auto_first_visit';