#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试保存问题"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db

print("=== 检查 ai_coach_record 表 ===")

try:
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 1. 查看表结构
            print("\n1. 表结构:")
            cursor.execute("DESC ai_coach_record")
            columns = cursor.fetchall()
            print("字段列表:")
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']}")
            
            # 2. 查看最新的5条记录
            print("\n2. 最新的5条记录:")
            cursor.execute("""
                SELECT 
                    session_id,
                    scene_id,
                    user_id,
                    call_duration,
                    LEFT(oss_file_path, 30) as audio_path,
                    score,
                    CASE 
                        WHEN ai_evaluate IS NOT NULL THEN 'YES'
                        ELSE 'NO'
                    END as has_evaluate,
                    created_time
                FROM ai_coach_record
                WHERE is_delete = 0
                ORDER BY created_time DESC
                LIMIT 5
            """)
            records = cursor.fetchall()
            
            if records:
                for idx, record in enumerate(records, 1):
                    print(f"\n记录 {idx}:")
                    for key, value in record.items():
                        print(f"  {key}: {value}")
            else:
                print("  没有找到记录！")
            
            # 3. 统计
            print("\n3. 统计信息:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(score) as with_score,
                    COUNT(ai_evaluate) as with_evaluate,
                    COUNT(oss_file_path) as with_audio
                FROM ai_coach_record
                WHERE is_delete = 0
            """)
            stats = cursor.fetchone()
            print(f"  总记录数: {stats['total']}")
            print(f"  有评分的: {stats['with_score']}")
            print(f"  有评估的: {stats['with_evaluate']}")
            print(f"  有音频的: {stats['with_audio']}")
            
            # 4. 今天的记录
            print("\n4. 今天的记录:")
            cursor.execute("""
                SELECT COUNT(*) as today_count
                FROM ai_coach_record
                WHERE DATE(created_time) = CURDATE()
                AND is_delete = 0
            """)
            today = cursor.fetchone()
            print(f"  今天创建的记录: {today['today_count']}")
            
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 检查完成 ===")
