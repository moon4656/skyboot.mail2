#!/usr/bin/env python3
"""
mail_logs 테이블의 NULL org_id 값을 정리하는 스크립트

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

def check_null_org_ids(conn):
    """NULL org_id 값이 있는 mail_logs 레코드 수를 확인합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mail_logs WHERE org_id IS NULL")
        count = cursor.fetchone()[0]
        logger.info(f"📊 NULL org_id를 가진 mail_logs 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"NULL org_id 확인 실패: {str(e)}")
        return 0

def show_null_org_id_records(conn):
    """NULL org_id를 가진 레코드들을 조회합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, mail_id, action, user_id, created_at 
            FROM mail_logs 
            WHERE org_id IS NULL 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        
        if records:
            logger.info("🔍 NULL org_id를 가진 최근 mail_logs 레코드들:")
            for record in records:
                logger.info(f"  ID: {record[0]}, Mail ID: {record[1]}, Action: {record[2]}, User ID: {record[3]}, Created: {record[4]}")
        
        return records
    except Exception as e:
        logger.error(f"NULL org_id 레코드 조회 실패: {str(e)}")
        return []

def try_update_org_id_from_users(conn):
    """user_id를 통해 org_id를 업데이트 시도합니다."""
    try:
        cursor = conn.cursor()
        
        # user_id가 있는 경우 users 테이블에서 org_id 가져오기
        logger.info("🔄 user_id를 통해 org_id 업데이트 시도 중...")
        cursor.execute("""
            UPDATE mail_logs 
            SET org_id = u.org_id 
            FROM users u 
            WHERE mail_logs.user_id = u.id 
            AND mail_logs.org_id IS NULL 
            AND u.org_id IS NOT NULL
        """)
        updated_count = cursor.rowcount
        
        logger.info(f"✅ {updated_count}개의 mail_logs 레코드의 org_id가 업데이트되었습니다.")
        return updated_count
        
    except Exception as e:
        logger.error(f"org_id 업데이트 실패: {str(e)}")
        return 0

def try_update_org_id_from_mails(conn):
    """mail_id를 통해 org_id를 업데이트 시도합니다."""
    try:
        cursor = conn.cursor()
        
        # mail_id가 있는 경우 mails 테이블에서 org_id 가져오기
        logger.info("🔄 mail_id를 통해 org_id 업데이트 시도 중...")
        cursor.execute("""
            UPDATE mail_logs 
            SET org_id = m.org_id 
            FROM mails m 
            WHERE mail_logs.mail_id = m.mail_id 
            AND mail_logs.org_id IS NULL 
            AND m.org_id IS NOT NULL
        """)
        updated_count = cursor.rowcount
        
        logger.info(f"✅ {updated_count}개의 mail_logs 레코드의 org_id가 업데이트되었습니다.")
        return updated_count
        
    except Exception as e:
        logger.error(f"mail_id를 통한 org_id 업데이트 실패: {str(e)}")
        return 0

def delete_null_org_id_records(conn):
    """여전히 NULL org_id를 가진 레코드들을 삭제합니다."""
    try:
        cursor = conn.cursor()
        
        # 삭제 전 백업
        logger.info("💾 NULL org_id 레코드들을 백업 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_logs_null_org_backup AS 
            SELECT * FROM mail_logs WHERE org_id IS NULL
        """)
        
        # NULL org_id 레코드 삭제
        logger.info("🗑️ NULL org_id 레코드들을 삭제 중...")
        cursor.execute("DELETE FROM mail_logs WHERE org_id IS NULL")
        deleted_count = cursor.rowcount
        
        logger.info(f"✅ {deleted_count}개의 NULL org_id 레코드가 삭제되었습니다.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"NULL org_id 레코드 삭제 실패: {str(e)}")
        return 0

def main():
    """메인 실행 함수"""
    logger.info("🚀 mail_logs 테이블 NULL org_id 정리 스크립트 시작")
    
    # 데이터베이스 연결
    conn = get_db_connection()
    if not conn:
        logger.error("❌ 데이터베이스 연결 실패")
        return False
    
    try:
        # 1. NULL org_id 레코드 수 확인
        null_count = check_null_org_ids(conn)
        
        if null_count == 0:
            logger.info("✅ NULL org_id를 가진 레코드가 없습니다.")
            return True
        
        # 2. NULL 레코드들 조회
        show_null_org_id_records(conn)
        
        # 3. user_id를 통해 org_id 업데이트 시도
        try_update_org_id_from_users(conn)
        
        # 4. mail_id를 통해 org_id 업데이트 시도
        try_update_org_id_from_mails(conn)
        
        # 5. 여전히 NULL인 레코드들 확인
        remaining_count = check_null_org_ids(conn)
        
        if remaining_count > 0:
            logger.warning(f"⚠️ {remaining_count}개의 레코드가 여전히 NULL org_id를 가지고 있습니다.")
            # 6. 남은 NULL org_id 레코드들 삭제
            delete_null_org_id_records(conn)
        
        # 7. 최종 확인
        final_count = check_null_org_ids(conn)
        
        if final_count == 0:
            logger.info("✅ mail_logs 테이블 NULL org_id 정리 완료")
            return True
        else:
            logger.warning(f"⚠️ {final_count}개의 NULL org_id 레코드가 여전히 남아있습니다.")
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