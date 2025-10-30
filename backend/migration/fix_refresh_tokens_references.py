#!/usr/bin/env python3
"""
refresh_tokens 테이블의 잘못된 외래키 참조를 정리하는 스크립트

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

def check_orphaned_refresh_tokens(conn):
    """users에 존재하지 않는 user_uuid를 가진 refresh_tokens 레코드를 확인합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM refresh_tokens rt 
            LEFT JOIN users u ON rt.user_uuid = u.user_uuid 
            WHERE u.user_uuid IS NULL
        """)
        count = cursor.fetchone()[0]
        logger.info(f"📊 고아 상태의 refresh_tokens 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"고아 refresh_tokens 확인 실패: {str(e)}")
        return 0

def show_orphaned_refresh_tokens(conn):
    """고아 상태의 refresh_tokens 레코드들을 조회합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rt.id, rt.user_uuid, rt.created_at, rt.expires_at
            FROM refresh_tokens rt 
            LEFT JOIN users u ON rt.user_uuid = u.user_uuid 
            WHERE u.user_uuid IS NULL
            ORDER BY rt.created_at DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        
        if records:
            logger.info("🔍 고아 상태의 refresh_tokens 레코드들:")
            for record in records:
                logger.info(f"  ID: {record[0]}, User UUID: {record[1]}, Created: {record[2]}, Expires: {record[3]}")
        
        return records
    except Exception as e:
        logger.error(f"고아 refresh_tokens 조회 실패: {str(e)}")
        return []

def delete_orphaned_refresh_tokens(conn):
    """고아 상태의 refresh_tokens 레코드들을 삭제합니다."""
    try:
        cursor = conn.cursor()
        
        # 삭제 전 백업
        logger.info("💾 고아 refresh_tokens 레코드들을 백업 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens_orphaned_backup AS 
            SELECT rt.* 
            FROM refresh_tokens rt 
            LEFT JOIN users u ON rt.user_uuid = u.user_uuid 
            WHERE u.user_uuid IS NULL
        """)
        
        # 고아 레코드 삭제
        logger.info("🗑️ 고아 refresh_tokens 레코드들을 삭제 중...")
        cursor.execute("""
            DELETE FROM refresh_tokens 
            WHERE user_uuid NOT IN (SELECT user_uuid FROM users WHERE user_uuid IS NOT NULL)
        """)
        deleted_count = cursor.rowcount
        
        logger.info(f"✅ {deleted_count}개의 고아 refresh_tokens 레코드가 삭제되었습니다.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"고아 refresh_tokens 레코드 삭제 실패: {str(e)}")
        return 0

def clean_expired_refresh_tokens(conn):
    """만료된 refresh_tokens도 함께 정리합니다."""
    try:
        cursor = conn.cursor()
        
        # 만료된 토큰 수 확인
        cursor.execute("SELECT COUNT(*) FROM refresh_tokens WHERE expires_at < NOW()")
        expired_count = cursor.fetchone()[0]
        
        if expired_count > 0:
            logger.info(f"📊 만료된 refresh_tokens 레코드 수: {expired_count}")
            
            # 만료된 토큰 삭제
            logger.info("🗑️ 만료된 refresh_tokens 레코드들을 삭제 중...")
            cursor.execute("DELETE FROM refresh_tokens WHERE expires_at < NOW()")
            deleted_expired = cursor.rowcount
            
            logger.info(f"✅ {deleted_expired}개의 만료된 refresh_tokens 레코드가 삭제되었습니다.")
            return deleted_expired
        else:
            logger.info("✅ 만료된 refresh_tokens 레코드가 없습니다.")
            return 0
        
    except Exception as e:
        logger.error(f"만료된 refresh_tokens 정리 실패: {str(e)}")
        return 0

def main():
    """메인 실행 함수"""
    logger.info("🚀 refresh_tokens 외래키 참조 정리 스크립트 시작")
    
    # 데이터베이스 연결
    conn = get_db_connection()
    if not conn:
        logger.error("❌ 데이터베이스 연결 실패")
        return False
    
    try:
        # 1. 고아 refresh_tokens 레코드 확인
        orphaned_count = check_orphaned_refresh_tokens(conn)
        
        if orphaned_count > 0:
            # 2. 고아 레코드들 조회
            show_orphaned_refresh_tokens(conn)
            
            # 3. 고아 레코드들 삭제
            delete_orphaned_refresh_tokens(conn)
        else:
            logger.info("✅ 고아 상태의 refresh_tokens 레코드가 없습니다.")
        
        # 4. 만료된 토큰들도 정리
        clean_expired_refresh_tokens(conn)
        
        # 5. 정리 후 확인
        remaining_count = check_orphaned_refresh_tokens(conn)
        
        if remaining_count == 0:
            logger.info("✅ refresh_tokens 외래키 참조 정리 완료")
            return True
        else:
            logger.warning(f"⚠️ {remaining_count}개의 고아 refresh_tokens 레코드가 여전히 남아있습니다.")
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