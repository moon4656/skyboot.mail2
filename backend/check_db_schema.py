#!/usr/bin/env python3
"""
데이터베이스 테이블 스키마 확인 스크립트
"""

import psycopg2
from app.config import SaaSSettings

def check_table_schema():
    """mail_recipients 테이블의 스키마를 확인합니다."""
    
    settings = SaaSSettings()
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("📊 mail_recipients 테이블 스키마 확인")
        print("=" * 50)
        
        # 테이블 스키마 조회
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_recipients'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            print("❌ mail_recipients 테이블을 찾을 수 없습니다.")
        
        print("\n📊 mails 테이블 스키마 확인")
        print("=" * 50)
        
        # mails 테이블 스키마 조회
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mails'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            print("❌ mails 테이블을 찾을 수 없습니다.")
        
        print("\n📊 mail_in_folders 테이블 스키마 확인")
        print("=" * 50)
        
        # mail_in_folders 테이블 스키마 조회
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_in_folders'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            print("❌ mail_in_folders 테이블을 찾을 수 없습니다.")
        
        print("\n📊 organizations 테이블 스키마 확인")
        print("=" * 50)
        
        # organizations 테이블 스키마 조회
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'organizations'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            print("❌ organizations 테이블을 찾을 수 없습니다.")
        
        print("\n📊 mail_folders 테이블 스키마 확인")
        print("=" * 50)
        
        # mail_folders 테이블 스키마 조회
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_folders'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            print("❌ mail_folders 테이블을 찾을 수 없습니다.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")

if __name__ == "__main__":
    check_table_schema()