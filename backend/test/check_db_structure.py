#!/usr/bin/env python3
"""
데이터베이스 테이블 구조 확인 스크립트
"""

import psycopg2
from app.config import settings

def check_organizations_table():
    """organizations 테이블 구조를 확인합니다."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        
        # organizations 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'organizations'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print('📊 organizations 테이블 구조:')
        if columns:
            for col in columns:
                print(f'  - {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}')
        else:
            print('  ❌ organizations 테이블이 존재하지 않습니다.')
        
        # 모든 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print('\n📋 현재 데이터베이스의 모든 테이블:')
        for table in tables:
            print(f'  - {table[0]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ 오류: {e}')

if __name__ == "__main__":
    check_organizations_table()