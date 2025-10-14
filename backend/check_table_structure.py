#!/usr/bin/env python3
"""
데이터베이스 테이블 구조를 확인하는 스크립트
"""

import psycopg2
from app.config import SaaSSettings

def check_table_structure():
    """mail_recipients 테이블 구조를 확인합니다."""
    settings = SaaSSettings()
    
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # mail_recipients 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_recipients'
            ORDER BY ordinal_position;
        """)
        
        print('📋 mail_recipients 테이블 구조:')
        columns = cursor.fetchall()
        if columns:
            for row in columns:
                print(f'  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})')
        else:
            print('  테이블이 존재하지 않거나 컬럼이 없습니다.')
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mail_recipients'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        print(f'\n📊 mail_recipients 테이블 존재 여부: {table_exists}')
        
        cursor.close()
        conn.close()
        print('✅ 테이블 구조 확인 완료')
        
    except Exception as e:
        print(f'❌ 오류: {e}')

if __name__ == "__main__":
    check_table_structure()