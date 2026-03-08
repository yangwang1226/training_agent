import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db

# 预设行业数据
PRESET_INDUSTRIES = [
    {
        'industry_code': 'automobile',
        'industry_name': '汽车销售',
        'industry_icon': 'car',
        'description': '汽车4S店销售培训场景',
        'display_order': 1
    },
    {
        'industry_code': 'education',
        'industry_name': '教育培训',
        'industry_icon': 'graduation',
        'description': '教育培训机构销售场景',
        'display_order': 2
    }
]

# 预设场景数据
PRESET_SCENES = [
    # 汽车销售场景
    {
        'industry_code': 'automobile',
        'scene_code': 'auto_first_visit',
        'scene_name': '客户首次到店接待',
        'scene_description': '模拟客户首次进入4S店的接待场景',
        'scene_tag': 'hot',
        'ai_role': '想看车的客户',
        'user_role': '汽车销售顾问',
        'difficulty': 'easy',
        'estimated_duration': 300,
        'display_order': 1
    },
    {
        'industry_code': 'automobile',
        'scene_code': 'auto_test_drive',
        'scene_name': '试驾邀约与跟进',
        'scene_description': '邀请客户试驾并做好试驾后跟进',
        'scene_tag': None,
        'ai_role': '考虑试驾的客户',
        'user_role': '汽车销售顾问',
        'difficulty': 'medium',
        'estimated_duration': 400,
        'display_order': 2
    },
    {
        'industry_code': 'automobile',
        'scene_code': 'auto_price_nego',
        'scene_name': '价格谈判与促成',
        'scene_description': '处理客户价格异议并促成成交',
        'scene_tag': None,
        'ai_role': '对价格敏感的客户',
        'user_role': '汽车销售顾问',
        'difficulty': 'hard',
        'estimated_duration': 600,
        'display_order': 3
    },
    {
        'industry_code': 'automobile',
        'scene_code': 'auto_competitor',
        'scene_name': '竞品对比应对',
        'scene_description': '客户拿竞品对比时的专业应对',
        'scene_tag': None,
        'ai_role': '对比竞品的客户',
        'user_role': '汽车销售顾问',
        'difficulty': 'medium',
        'estimated_duration': 500,
        'display_order': 4
    },
    {
        'industry_code': 'automobile',
        'scene_code': 'auto_followup',
        'scene_name': '潜客电话回访',
        'scene_description': '对意向客户进行电话跟进回访',
        'scene_tag': None,
        'ai_role': '潜在购车客户',
        'user_role': '汽车销售顾问',
        'difficulty': 'easy',
        'estimated_duration': 300,
        'display_order': 5
    },
    # 教育培训场景
    {
        'industry_code': 'education',
        'scene_code': 'edu_consult',
        'scene_name': '课程咨询接待',
        'scene_description': '家长来电或到访咨询课程信息',
        'scene_tag': None,
        'ai_role': '咨询课程的家长',
        'user_role': '课程顾问',
        'difficulty': 'easy',
        'estimated_duration': 300,
        'display_order': 1
    },
    {
        'industry_code': 'education',
        'scene_code': 'edu_trial',
        'scene_name': '试听课邀约',
        'scene_description': '邀请家长带孩子参加试听课',
        'scene_tag': None,
        'ai_role': '考虑试听的家长',
        'user_role': '课程顾问',
        'difficulty': 'easy',
        'estimated_duration': 300,
        'display_order': 2
    },
    {
        'industry_code': 'education',
        'scene_code': 'edu_needs',
        'scene_name': '学习需求诊断',
        'scene_description': '深入了解学生学习情况并给出建议',
        'scene_tag': None,
        'ai_role': '关心孩子学习的家长',
        'user_role': '课程顾问',
        'difficulty': 'medium',
        'estimated_duration': 500,
        'display_order': 3
    },
    {
        'industry_code': 'education',
        'scene_code': 'edu_price',
        'scene_name': '价格异议处理',
        'scene_description': '家长对课程价格提出异议时的应对',
        'scene_tag': None,
        'ai_role': '对价格有顾虑的家长',
        'user_role': '课程顾问',
        'difficulty': 'hard',
        'estimated_duration': 400,
        'display_order': 4
    },
    {
        'industry_code': 'education',
        'scene_code': 'edu_renew',
        'scene_name': '续费挽留沟通',
        'scene_description': '课程到期时与家长沟通续费',
        'scene_tag': None,
        'ai_role': '课程即将到期的家长',
        'user_role': '课程顾问',
        'difficulty': 'medium',
        'estimated_duration': 400,
        'display_order': 5
    }
]

def insert_preset_industries():
    """插入预设行业数据"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            print("插入预设行业数据...")
            
            # 清空现有数据
            cursor.execute("DELETE FROM ai_coach_preset_scene")
            cursor.execute("DELETE FROM ai_coach_preset_industry")
            
            sql = """
                INSERT INTO ai_coach_preset_industry 
                (industry_code, industry_name, industry_icon, description, display_order)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for industry in PRESET_INDUSTRIES:
                cursor.execute(sql, (
                    industry['industry_code'],
                    industry['industry_name'],
                    industry['industry_icon'],
                    industry['description'],
                    industry['display_order']
                ))
                print(f"  [OK] 插入行业: {industry['industry_name']}")
            
            conn.commit()
            print(f"[SUCCESS] 成功插入 {len(PRESET_INDUSTRIES)} 个行业!\n")

def insert_preset_scenes():
    """插入预设场景数据"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            print("插入预设场景数据...")
            
            # 插入新数据
            print(f"准备插入 {len(PRESET_SCENES)} 条预设场景数据...")
            
            sql = """
                INSERT INTO ai_coach_preset_scene 
                (industry_code, scene_code, scene_name, scene_description, scene_tag,
                 ai_role, user_role, difficulty, estimated_duration, display_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for scene in PRESET_SCENES:
                cursor.execute(sql, (
                    scene['industry_code'],
                    scene['scene_code'],
                    scene['scene_name'],
                    scene['scene_description'],
                    scene['scene_tag'],
                    scene['ai_role'],
                    scene['user_role'],
                    scene['difficulty'],
                    scene['estimated_duration'],
                    scene['display_order']
                ))
                print(f"  [OK] 插入: {scene['scene_name']}")
            
            conn.commit()
            print(f"\n[SUCCESS] 成功插入 {len(PRESET_SCENES)} 条预设场景数据!")

if __name__ == '__main__':
    # 先插入行业，再插入场景
    insert_preset_industries()
    insert_preset_scenes()