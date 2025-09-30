#!/usr/bin/env python3
"""
데이터베이스를 완전히 삭제하고 다시 생성
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from app.config import settings
from app.database.user import Base

def recreate_database():
    """데이터베이스를 완전히 삭제하고 다시 생성"""
    print("🗑️ 기존 데이터베이스 삭제 중...")
    
    # PostgreSQL 관리자 연결 (기본 postgres 데이터베이스)
    admin_conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database="postgres"
    )
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = admin_conn.cursor()
    
    try:
        # 기존 연결 종료
        cursor.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{settings.DB_NAME}' AND pid <> pg_backend_pid()
        """)
        
        # 데이터베이스 삭제 (따옴표로 감싸서 특수문자 처리)
        cursor.execute(f'DROP DATABASE IF EXISTS "{settings.DB_NAME}"')
        print(f"✅ 데이터베이스 '{settings.DB_NAME}' 삭제 완료")
        
        # 데이터베이스 생성 (따옴표로 감싸서 특수문자 처리)
        cursor.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
        print(f"✅ 데이터베이스 '{settings.DB_NAME}' 생성 완료")
        
    except Exception as e:
        print(f"❌ 데이터베이스 재생성 실패: {e}")
        return False
    finally:
        cursor.close()
        admin_conn.close()
    
    # 새 데이터베이스에 테이블 생성
    print("📋 테이블 생성 중...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False

if __name__ == "__main__":
    success = recreate_database()
    if not success:
        exit(1)
    print("🎯 데이터베이스 재생성 완료!")