#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 ai_coach_scene 表添加 sop_checklist 字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


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


def add_sop_checklist_field():
    """添加 sop_checklist 字段到 ai_coach_scene 表"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("检查 sop_checklist 字段是否存在...")
        
        if check_field_exists(cursor, 'ai_coach_scene', 'sop_checklist'):
            logger.info("✓ sop_checklist 字段已存在，跳过创建")
            return True
        
        logger.info("添加 sop_checklist 字段到 ai_coach_scene 表...")
        cursor.execute("""
            ALTER TABLE ai_coach_scene
            ADD COLUMN sop_checklist JSON
            COMMENT 'SOP质检项列表（从预设场景复制而来，用户可修改）'
            AFTER full_evaluation_prompt
        """)
        
        conn.commit()
        logger.info("✓ sop_checklist 字段添加成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ 添加字段失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("开始数据库迁移：为 ai_coach_scene 添加 sop_checklist 字段")
    logger.info("="*60)
    
    success = add_sop_checklist_field()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("✓ 迁移成功完成！")
        logger.info("="*60)
        sys.exit(0)
    else:
        logger.error("\n" + "="*60)
        logger.error("✗ 迁移失败")
        logger.error("="*60)
        sys.exit(1)