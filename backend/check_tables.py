#!/usr/bin/env python3
"""
데이터베이스 테이블 목록을 확인하는 스크립트
"""

import psycopg2
from app.config import settings

def check_database_tables():
    """데이터베이스에 있는 모든 테이블을 조회합니다."""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cur = conn.cursor()
        
        print(f"데이터베이스 연결 성공: {settings.DB_NAME}")
        print(f"호스트: {settings.DB_HOST}:{settings.DB_PORT}")
        print("-" * 50)
        
        # 모든 테이블 조회
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f'데이터베이스에 있는 테이블 목록 (총 {len(tables)}개):')
        
        if tables:
            for table in tables:
                print(f'- {table[0]}')
        else:
            print("테이블이 없습니다.")
        
        print("-" * 50)
        
        # users 테이블이 있는지 특별히 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        users_exists = cur.fetchone()[0]
        print(f"users 테이블 존재 여부: {'있음' if users_exists else '없음'}")
        
        # Alembic 버전 테이블 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        
        alembic_exists = cur.fetchone()[0]
        print(f"alembic_version 테이블 존재 여부: {'있음' if alembic_exists else '없음'}")
        
        if alembic_exists:
            cur.execute("SELECT version_num FROM alembic_version;")
            version = cur.fetchone()
            if version:
                print(f"현재 Alembic 버전: {version[0]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f'데이터베이스 연결 오류: {e}')
        print(f'설정 정보:')
        print(f'- HOST: {settings.DB_HOST}')
        print(f'- PORT: {settings.DB_PORT}')
        print(f'- DATABASE: {settings.DB_NAME}')
        print(f'- USER: {settings.DB_USER}')

if __name__ == "__main__":
    check_database_tables()