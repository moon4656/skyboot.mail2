#!/usr/bin/env python3
"""
데이터베이스 테이블 목록을 확인하는 스크립트
"""

import os
import psycopg2
from urllib.parse import urlparse

def check_database_tables():
    """데이터베이스의 모든 테이블을 조회합니다."""
    
    # DATABASE_URL 파싱
    database_url = 'postgresql://postgres:safe70%21%21@localhost:5432/skybootmail'
    parsed = urlparse(database_url)

    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        # 모든 테이블 조회
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print('=== 현재 데이터베이스 테이블 목록 ===')
        for table in tables:
            print(f'- {table[0]}')
        
        print(f'\n총 {len(tables)}개의 테이블이 존재합니다.')
        
        # 필요한 테이블들 확인
        required_tables = [
            'organizations',
            'users', 
            'mail_users',
            'mails',
            'virtual_domains',
            'virtual_users',
            'virtual_aliases'
        ]
        
        existing_tables = [table[0] for table in tables]
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print('\n=== 누락된 테이블 ===')
            for table in missing_tables:
                print(f'- {table}')
        else:
            print('\n✅ 모든 필수 테이블이 존재합니다.')
        
        cursor.close()
        conn.close()
        
        return existing_tables, missing_tables
        
    except Exception as e:
        print(f'❌ 데이터베이스 연결 오류: {e}')
        return [], []

if __name__ == "__main__":
    check_database_tables()