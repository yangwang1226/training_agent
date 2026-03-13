"""
查询数据库中包含word_content的训练记录
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db

def query_records_with_word_content():
    """查询包含word_content的记录"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    session_id,
                    scene_id,
                    user_id,
                    call_duration,
                    ai_score,
                    sop_score,
                    created_time,
                    LENGTH(word_content) as word_content_length,
                    SUBSTRING(word_content, 1, 200) as word_content_preview
                FROM ai_coach_record
                WHERE is_delete = 0
                ORDER BY created_time DESC
                LIMIT 20
            """
            cursor.execute(sql)
            records = cursor.fetchall()
            
            if not records:
                print("没有找到记录")
                return
            
            print(f"\n共找到 {len(records)} 条记录：\n")
            print(f"{'序号':<5} {'Session ID':<40} {'场景':<8} {'时长':<8} {'AI分':<8} {'SOP分':<8} {'内容长度':<10} {'创建时间'}")
            print("─" * 140)
            
            for idx, record in enumerate(records, 1):
                print(f"{idx:<5} {record['session_id']:<40} {record['scene_id']:<8} {record['call_duration'] or 0:<8} {record.get('ai_score') or '-':<8} {record.get('sop_score') or '-':<8} {record['word_content_length'] or 0:<10} {record['created_time']}")
                if record['word_content_length'] and record['word_content_length'] > 0:
                    preview = record['word_content_preview'] or ''
                    print(f"       预览: {preview[:100]}...")
                print()

if __name__ == '__main__':
    query_records_with_word_content()
