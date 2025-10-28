#!/usr/bin/env python3
"""
contacts 테이블 존재 여부 확인 스크립트
"""

import psycopg2
from app.config import settings

def check_contacts_table():
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print('📋 현재 데이터베이스 테이블 목록:')
        for table in tables:
            print(f'   - {table[0]}')
        
        # contacts 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'contacts'
            )
        """)
        contacts_exists = cursor.fetchone()[0]
        
        print(f'\n🔍 contacts 테이블 존재 여부: {contacts_exists}')
        
        # addressbook 관련 테이블들 확인
        addressbook_tables = ['contacts', 'departments', 'groups', 'contact_groups']
        print('\n📊 addressbook 관련 테이블 상태:')
        for table_name in addressbook_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
            exists = cursor.fetchone()[0]
            status = "✅ 존재" if exists else "❌ 누락"
            print(f'   - {table_name}: {status}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ 데이터베이스 연결 오류: {e}')

if __name__ == "__main__":
    check_contacts_table()