#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 ai_coach_scene 表添加性能优化索引
"""

import sys
import os
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_index_exists(cursor, table_name, index_name):
    """检查索引是否存在"""
    cursor.execute(f"""
        SELECT COUNT(*) as count
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND INDEX_NAME = '{index_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0

def add_indexes():
    """添加性能优化索引"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        indexes = [
            # 状态 + deleted（常用查询条件）
            ('idx_status_deleted', 'CREATE INDEX idx_status_deleted ON ai_coach_scene(status, deleted)'),
            
            # 创建时间（排序）
            ('idx_created_time', 'CREATE INDEX idx_created_time ON ai_coach_scene(created_time DESC)'),
            
            # 行业（分类查询）
            ('idx_industry', 'CREATE INDEX idx_industry ON ai_coach_scene(industry)'),
        ]
        
        for index_name, create_sql in indexes:
            if check_index_exists(cursor, 'ai_coach_scene', index_name):
                logger.info(f"索引 {index_name} 已存在，跳过")
            else:
                logger.info(f"创建索引: {index_name}")
                cursor.execute(create_sql)
                logger.info(f"✓ 索引 {index_name} 创建成功")
        
        conn.commit()
        logger.info("\n✓ 所有索引已创建")
        return True
        
    except Exception as e:
        logger.error(f"✗ 创建索引失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("添加 ai_coach_scene 表索引")
    logger.info("="*60)
    
    if add_indexes():
        sys.exit(0)
    else:
        sys.exit(1)