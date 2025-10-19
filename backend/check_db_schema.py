#!/usr/bin/env python3
"""
데이터베이스 스키마 확인 스크립트
"""

import psycopg2
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_database_schema():
    """데이터베이스 스키마를 확인합니다."""
    try:
        print("🔍 데이터베이스 스키마 확인 시작...")
        
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        
        # 1. 모든 테이블 목록 조회
        print("1️⃣ 테이블 목록:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            print(f"   - {table[0]}")
        
        # 2. organizations 테이블 구조 확인
        print("\n2️⃣ organizations 테이블 구조:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'organizations' 
            ORDER BY ordinal_position
        """)
        org_columns = cursor.fetchall()
        
        if org_columns:
            for col in org_columns:
                print(f"   - {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
        else:
            print("   ⚠️ organizations 테이블이 존재하지 않습니다.")
        
        # 3. users 테이블 구조 확인
        print("\n3️⃣ users 테이블 구조:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        user_columns = cursor.fetchall()
        
        if user_columns:
            for col in user_columns:
                print(f"   - {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
        else:
            print("   ⚠️ users 테이블이 존재하지 않습니다.")
        
        # 4. contacts 테이블 구조 확인
        print("\n4️⃣ contacts 테이블 구조:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'contacts' 
            ORDER BY ordinal_position
        """)
        contact_columns = cursor.fetchall()
        
        if contact_columns:
            for col in contact_columns:
                print(f"   - {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
        else:
            print("   ⚠️ contacts 테이블이 존재하지 않습니다.")
        
        # 5. 기존 사용자 데이터 확인
        print("\n5️⃣ 기존 사용자 데이터:")
        if user_columns:
            # 컬럼명 확인 후 적절한 쿼리 실행
            column_names = [col[0] for col in user_columns]
            
            if 'user_id' in column_names:
                cursor.execute("SELECT user_id, email FROM users LIMIT 10")
            elif 'username' in column_names:
                cursor.execute("SELECT username, email FROM users LIMIT 10")
            else:
                cursor.execute("SELECT * FROM users LIMIT 5")
            
            users = cursor.fetchall()
            for user in users:
                print(f"   - {user}")
        
        cursor.close()
        conn.close()
        print("\n🎉 스키마 확인 완료!")
        
        return True
        
    except Exception as e:
        print(f"❌ 스키마 확인 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_database_schema()
    if not success:
        sys.exit(1)