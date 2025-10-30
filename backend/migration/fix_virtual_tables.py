#!/usr/bin/env python3
"""
Virtual 테이블 정리 스크립트

이 스크립트는 마이그레이션 중 발생한 virtual_domains, virtual_users, virtual_aliases 테이블 의존성 문제를 해결합니다.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """데이터베이스 연결을 생성합니다."""
    try:
        # 설정에서 데이터베이스 URL 가져오기
        db_url = settings.DATABASE_URL
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return None

def check_table_exists(conn, table_name):
    """테이블이 존재하는지 확인합니다."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"테이블 존재 확인 실패 ({table_name}): {e}")
        return False

def drop_virtual_tables(conn):
    """Virtual 테이블들을 의존성 순서에 따라 삭제합니다."""
    tables_to_drop = [
        'virtual_aliases',  # 먼저 aliases 삭제
        'virtual_users',    # 그 다음 users 삭제
        'virtual_domains'   # 마지막에 domains 삭제
    ]
    
    for table_name in tables_to_drop:
        try:
            if check_table_exists(conn, table_name):
                logger.info(f"🗑️ {table_name} 테이블 삭제 중...")
                with conn.cursor() as cur:
                    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                logger.info(f"✅ {table_name} 테이블 삭제 완료")
            else:
                logger.info(f"ℹ️ {table_name} 테이블이 존재하지 않음")
        except Exception as e:
            logger.error(f"❌ {table_name} 테이블 삭제 실패: {e}")

def main():
    """메인 함수"""
    logger.info("🚀 Virtual 테이블 정리 스크립트 시작")
    
    # 데이터베이스 연결
    conn = get_db_connection()
    if not conn:
        logger.error("❌ 데이터베이스 연결 실패")
        sys.exit(1)
    
    try:
        # Virtual 테이블들 삭제
        drop_virtual_tables(conn)
        
        logger.info("✅ Virtual 테이블 정리 완료")
        
    except Exception as e:
        logger.error(f"❌ 스크립트 실행 중 오류 발생: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            logger.info("🔌 데이터베이스 연결 종료")

if __name__ == "__main__":
    main()