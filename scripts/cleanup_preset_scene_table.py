#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理 ai_coach_preset_scene 表
1. 删除冗余字段
2. 添加字段注释
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 要删除的冗余字段
FIELDS_TO_DROP = [
    # 未使用的模板字段（TEXT格式）
    'background_template',
    'main_questions_template',
    'trigger_groups_template',
    'dimensions_template',
    'emotion_template',
    
    # 未使用的默认字段（JSON/TEXT格式）
    'default_params',
    'default_questions',
    'default_triggers',
    'default_background',
    'default_dimensions',
    'emotion_settings',
    
    # 可能有用但不必要的字段
    'scene_tag',
    'estimated_duration',
    'display_order',
]

# 字段注释映射
FIELD_COMMENTS = {
    'id': '主键ID',
    'industry_code': '行业代码（如：automobile, education）',
    'scene_code': '场景唯一代码（如：auto_first_visit）',
    'scene_name': '场景名称',
    'scene_description': '场景描述',
    'ai_role': 'AI扮演的角色（如：想看车的客户）',
    'user_role': '用户扮演的角色（如：汽车销售顾问）',
    'difficulty': '难度等级（easy/medium/hard）',
    'opening_line': 'AI开场白',
    'is_active': '是否启用（1=启用，0=禁用）',
    'usage_count': '使用次数统计',
    'created_time': '创建时间',
    'updated_time': '更新时间',
    'default_sop_checklist': '默认SOP质检项列表（JSON格式，全局模板）',
}

def check_field_exists(cursor, table_name, field_name):
    """检查字段是否存在"""
    cursor.execute(f"""
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{field_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0

def drop_fields():
    """删除冗余字段"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("开始删除冗余字段...")
        dropped_count = 0
        
        for field in FIELDS_TO_DROP:
            if check_field_exists(cursor, 'ai_coach_preset_scene', field):
                logger.info(f"  删除字段: {field}")
                cursor.execute(f"ALTER TABLE ai_coach_preset_scene DROP COLUMN `{field}`")
                dropped_count += 1
            else:
                logger.info(f"  字段 {field} 不存在，跳过")
        
        conn.commit()
        logger.info(f"✓ 成功删除 {dropped_count} 个冗余字段")
        return True
        
    except Exception as e:
        logger.error(f"✗ 删除字段失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_comments():
    """添加字段注释"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("\n开始添加字段注释...")
        
        # 获取当前字段信息
        cursor.execute("DESCRIBE ai_coach_preset_scene")
        current_fields = {row['Field']: row for row in cursor.fetchall()}
        
        for field_name, comment in FIELD_COMMENTS.items():
            if field_name not in current_fields:
                logger.info(f"  字段 {field_name} 不存在，跳过")
                continue
            
            field_info = current_fields[field_name]
            field_type = field_info['Type']
            null_clause = 'NULL' if field_info['Null'] == 'YES' else 'NOT NULL'
            
            # 处理默认值
            default_clause = ''
            if field_info['Default'] is not None:
                if field_info['Default'] == 'CURRENT_TIMESTAMP':
                    default_clause = 'DEFAULT CURRENT_TIMESTAMP'
                else:
                    default_clause = f"DEFAULT '{field_info['Default']}'"
            
            # 处理 auto_increment
            auto_increment = 'AUTO_INCREMENT' if 'auto_increment' in field_info['Extra'] else ''
            
            # 处理 on update
            on_update = ''
            if 'on update CURRENT_TIMESTAMP' in field_info['Extra']:
                on_update = 'ON UPDATE CURRENT_TIMESTAMP'
            
            sql = f"""
                ALTER TABLE ai_coach_preset_scene 
                MODIFY COLUMN `{field_name}` {field_type} {null_clause} {default_clause} {auto_increment} {on_update}
                COMMENT '{comment}'
            """
            
            logger.info(f"  添加注释: {field_name} - {comment}")
            cursor.execute(sql)
        
        conn.commit()
        logger.info(f"✓ 成功添加 {len(FIELD_COMMENTS)} 个字段注释")
        return True
        
    except Exception as e:
        logger.error(f"✗ 添加注释失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_result():
    """验证结果"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("\n验证结果...")
        
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ai_coach_preset_scene'
            ORDER BY ORDINAL_POSITION
        """)
        
        fields = cursor.fetchall()
        
        logger.info(f"\n当前表结构（共 {len(fields)} 个字段）：")
        logger.info("="*80)
        for field in fields:
            name = field['COLUMN_NAME']
            type_ = field['COLUMN_TYPE']
            comment = field['COLUMN_COMMENT'] or '(无注释)'
            logger.info(f"{name:30} {type_:30} {comment}")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 验证失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    logger.info("="*80)
    logger.info("ai_coach_preset_scene 表清理脚本")
    logger.info("="*80)
    
    # 步骤1: 删除冗余字段
    if not drop_fields():
        logger.error("删除字段失败，停止执行")
        sys.exit(1)
    
    # 步骤2: 添加字段注释
    if not add_comments():
        logger.error("添加注释失败")
        sys.exit(1)
    
    # 步骤3: 验证结果
    verify_result()
    
    logger.info("\n" + "="*80)
    logger.info("✓ 清理完成！")
    logger.info("="*80)
    sys.exit(0)