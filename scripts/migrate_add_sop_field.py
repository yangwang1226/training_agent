#!/usr/bin/env python3
"""
数据库迁移脚本：添加 SOP 质检项字段
为 ai_coach_preset_scene 表添加 default_sop_checklist 字段
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_field_exists(cursor, table_name, field_name):
    """
    检查字段是否存在
    """
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
    """
    添加 default_sop_checklist 字段
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("检查 default_sop_checklist 字段是否存在...")
        
        if check_field_exists(cursor, 'ai_coach_preset_scene', 'default_sop_checklist'):
            logger.info("✓ default_sop_checklist 字段已存在，跳过创建")
            return True
        
        logger.info("添加 default_sop_checklist 字段...")
        cursor.execute("""
            ALTER TABLE ai_coach_preset_scene
            ADD COLUMN default_sop_checklist JSON
            COMMENT '默认SOP质检项列表'
        """)
        
        conn.commit()
        logger.info("✓ default_sop_checklist 字段添加成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ 添加字段失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def add_updated_time_field():
    """
    添加 updated_time 字段（如果不存在）
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("检查 updated_time 字段是否存在...")
        
        if check_field_exists(cursor, 'ai_coach_preset_scene', 'updated_time'):
            logger.info("✓ updated_time 字段已存在，跳过创建")
            return True
        
        logger.info("添加 updated_time 字段...")
        cursor.execute("""
            ALTER TABLE ai_coach_preset_scene
            ADD COLUMN updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            COMMENT '更新时间'
        """)
        
        conn.commit()
        logger.info("✓ updated_time 字段添加成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ 添加字段失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def verify_migration():
    """
    验证迁移结果
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("\n验证表结构...")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ai_coach_preset_scene'
            AND COLUMN_NAME IN ('default_sop_checklist', 'updated_time')
        """)
        
        results = cursor.fetchall()
        
        if results:
            logger.info("\n表结构信息：")
            for row in results:
                logger.info(f"  - {row['COLUMN_NAME']}: {row['DATA_TYPE']} ({row['COLUMN_COMMENT']})")
            return True
        else:
            logger.error("✗ 未找到字段，迁移可能失败")
            return False
            
    except Exception as e:
        logger.error(f"✗ 验证失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    logger.info("="*60)
    logger.info("SOP 质检项字段迁移脚本")
    logger.info("="*60)
    
    # 执行迁移
    success = True
    
    if not add_sop_checklist_field():
        success = False
    
    if not add_updated_time_field():
        success = False
    
    # 验证迁移
    if success:
        verify_migration()
    
    logger.info("\n" + "="*60)
    if success:
        logger.info("✓ 迁移完成")
        logger.info("\n下一步：")
        logger.info("1. 运行测试脚本: python test_sop_config.py")
        logger.info("2. 启动应用: python app.py")
        logger.info("3. 访问页面: http://localhost:5000/sop/config")
        return 0
    else:
        logger.error("✗ 迁移失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
