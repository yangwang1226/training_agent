import os
import logging
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ai_coach_test'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


@contextmanager
def get_db():
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
