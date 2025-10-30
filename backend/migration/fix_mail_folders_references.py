#!/usr/bin/env python3
"""
mail_folders 테이블의 잘못된 외래키 참조를 정리하는 스크립트

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

def check_orphaned_mail_folders(conn):
    """mail_users에 존재하지 않는 user_uuid를 가진 mail_folders 레코드를 확인합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mail_folders mf 
            LEFT JOIN mail_users mu ON mf.user_uuid = mu.user_uuid 
            WHERE mu.user_uuid IS NULL
        """)
        count = cursor.fetchone()[0]
        logger.info(f"📊 고아 상태의 mail_folders 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"고아 mail_folders 확인 실패: {str(e)}")
        return 0

def show_orphaned_records(conn):
    """고아 상태의 mail_folders 레코드들을 조회합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mf.id, mf.user_uuid, mf.folder_name, mf.created_at
            FROM mail_folders mf 
            LEFT JOIN mail_users mu ON mf.user_uuid = mu.user_uuid 
            WHERE mu.user_uuid IS NULL
            ORDER BY mf.created_at DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        
        if records:
            logger.info("🔍 고아 상태의 mail_folders 레코드들:")
            for record in records:
                logger.info(f"  ID: {record[0]}, User UUID: {record[1]}, Folder: {record[2]}, Created: {record[3]}")
        
        return records
    except Exception as e:
        logger.error(f"고아 레코드 조회 실패: {str(e)}")
        return []

def delete_orphaned_mail_folders(conn):
    """고아 상태의 mail_folders 레코드들을 삭제합니다."""
    try:
        cursor = conn.cursor()
        
        # 삭제 전 백업
        logger.info("💾 고아 mail_folders 레코드들을 백업 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_folders_orphaned_backup AS 
            SELECT mf.* 
            FROM mail_folders mf 
            LEFT JOIN mail_users mu ON mf.user_uuid = mu.user_uuid 
            WHERE mu.user_uuid IS NULL
        """)
        
        # 고아 레코드 삭제
        logger.info("🗑️ 고아 mail_folders 레코드들을 삭제 중...")
        cursor.execute("""
            DELETE FROM mail_folders 
            WHERE user_uuid NOT IN (SELECT user_uuid FROM mail_users)
        """)
        deleted_count = cursor.rowcount
        
        logger.info(f"✅ {deleted_count}개의 고아 mail_folders 레코드가 삭제되었습니다.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"고아 mail_folders 레코드 삭제 실패: {str(e)}")
        return 0

def check_orphaned_mail_in_folders(conn):
    """mail_folders에 존재하지 않는 folder_id를 가진 mail_in_folders 레코드를 확인합니다."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mail_in_folders mif 
            LEFT JOIN mail_folders mf ON mif.folder_id = mf.id 
            WHERE mf.id IS NULL
        """)
        count = cursor.fetchone()[0]
        logger.info(f"📊 고아 상태의 mail_in_folders 레코드 수: {count}")
        return count
    except Exception as e:
        logger.error(f"고아 mail_in_folders 확인 실패: {str(e)}")
        return 0

def delete_orphaned_mail_in_folders(conn):
    """고아 상태의 mail_in_folders 레코드들을 삭제합니다."""
    try:
        cursor = conn.cursor()
        
        # 삭제 전 백업
        logger.info("💾 고아 mail_in_folders 레코드들을 백업 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_in_folders_orphaned_backup AS 
            SELECT mif.* 
            FROM mail_in_folders mif 
            LEFT JOIN mail_folders mf ON mif.folder_id = mf.id 
            WHERE mf.id IS NULL
        """)
        
        # 고아 레코드 삭제
        logger.info("🗑️ 고아 mail_in_folders 레코드들을 삭제 중...")
        cursor.execute("""
            DELETE FROM mail_in_folders 
            WHERE folder_id NOT IN (SELECT id FROM mail_folders)
        """)
        deleted_count = cursor.rowcount
        
        logger.info(f"✅ {deleted_count}개의 고아 mail_in_folders 레코드가 삭제되었습니다.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"고아 mail_in_folders 레코드 삭제 실패: {str(e)}")
        return 0

def main():
    """메인 실행 함수"""
    logger.info("🚀 mail_folders 외래키 참조 정리 스크립트 시작")
    
    # 데이터베이스 연결
    conn = get_db_connection()
    if not conn:
        logger.error("❌ 데이터베이스 연결 실패")
        return False
    
    try:
        # 1. 고아 mail_folders 레코드 확인 및 정리
        orphaned_folders_count = check_orphaned_mail_folders(conn)
        
        if orphaned_folders_count > 0:
            show_orphaned_records(conn)
            delete_orphaned_mail_folders(conn)
        else:
            logger.info("✅ 고아 상태의 mail_folders 레코드가 없습니다.")
        
        # 2. 고아 mail_in_folders 레코드 확인 및 정리
        orphaned_in_folders_count = check_orphaned_mail_in_folders(conn)
        
        if orphaned_in_folders_count > 0:
            delete_orphaned_mail_in_folders(conn)
        else:
            logger.info("✅ 고아 상태의 mail_in_folders 레코드가 없습니다.")
        
        # 3. 정리 후 확인
        remaining_folders = check_orphaned_mail_folders(conn)
        remaining_in_folders = check_orphaned_mail_in_folders(conn)
        
        if remaining_folders == 0 and remaining_in_folders == 0:
            logger.info("✅ mail_folders 외래키 참조 정리 완료")
            return True
        else:
            logger.warning(f"⚠️ 여전히 고아 레코드가 남아있습니다. (folders: {remaining_folders}, in_folders: {remaining_in_folders})")
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