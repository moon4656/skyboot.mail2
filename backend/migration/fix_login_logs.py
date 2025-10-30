#!/usr/bin/env python3
"""
login_logs 테이블의 NULL user_id 값을 정리하는 스크립트

SkyBoot Mail SaaS 프로젝트에서 마이그레이션 전 데이터 정리를 위한 스크립트입니다.
"""

import sys
import os
import logging
import psycopg2
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

def check_null_user_ids(conn):
    """NULL user_id 값이 있는 레코드 수를 확인합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM login_logs WHERE user_id IS NULL")
        count = cursor.fetchone()[0]
        logger.info(f"📊 NULL user_id를 가진 login_logs 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"NULL user_id 확인 실패: {str(e)}")
        return 0

def show_null_records(conn):
    """NULL user_id를 가진 레코드들을 조회합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, ip_address, user_agent, login_time, success 
            FROM login_logs 
            WHERE user_id IS NULL 
            ORDER BY login_time DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        
        if records:
            logger.info("🔍 NULL user_id를 가진 최근 레코드들:")
            for record in records:
                logger.info(f"  ID: {record[0]}, Email: {record[1]}, IP: {record[2]}, Time: {record[4]}, Success: {record[5]}")
        
        return records
    except Exception as e:
        logger.error(f"NULL 레코드 조회 실패: {str(e)}")
        return []

def delete_null_user_id_records(conn):
    """NULL user_id를 가진 레코드들을 삭제합니다."""
    try:
        cursor = conn.cursor()
        
        # 삭제 전 백업 (선택사항)
        logger.info("💾 NULL user_id 레코드들을 백업 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs_null_backup AS 
            SELECT * FROM login_logs WHERE user_id IS NULL
        """)
        
        # NULL user_id 레코드 삭제
        logger.info("🗑️ NULL user_id 레코드들을 삭제 중...")
        cursor.execute("DELETE FROM login_logs WHERE user_id IS NULL")
        deleted_count = cursor.rowcount
        
        logger.info(f"✅ {deleted_count}개의 NULL user_id 레코드가 삭제되었습니다.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"NULL user_id 레코드 삭제 실패: {str(e)}")
        return 0

def main():
    """메인 실행 함수"""
    logger.info("🚀 login_logs 테이블 NULL user_id 정리 스크립트 시작")
    
    # 데이터베이스 연결
    conn = get_db_connection()
    if not conn:
        logger.error("❌ 데이터베이스 연결 실패")
        return False
    
    try:
        # 1. NULL user_id 레코드 수 확인
        null_count = check_null_user_ids(conn)
        
        if null_count == 0:
            logger.info("✅ NULL user_id를 가진 레코드가 없습니다.")
            return True
        
        # 2. NULL 레코드들 조회
        show_null_records(conn)
        
        # 3. NULL user_id 레코드들 삭제
        deleted_count = delete_null_user_id_records(conn)
        
        # 4. 삭제 후 확인
        remaining_count = check_null_user_ids(conn)
        
        if remaining_count == 0:
            logger.info("✅ login_logs 테이블 NULL user_id 정리 완료")
            return True
        else:
            logger.warning(f"⚠️ {remaining_count}개의 NULL user_id 레코드가 여전히 남아있습니다.")
            return False
            
    except Exception as e:
        logger.error(f"❌ 스크립트 실행 중 오류 발생: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
            logger.info("🔌 데이터베이스 연결 종료")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)