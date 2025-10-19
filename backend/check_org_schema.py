#!/usr/bin/env python3
"""
organizations 테이블의 정확한 스키마를 확인하는 스크립트
"""

import psycopg2
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_org_schema():
    """organizations 테이블 스키마를 확인합니다."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        
        print("=== organizations 테이블 구조 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'organizations'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]} | {col[1]} | nullable: {col[2]} | default: {col[3]}")
        
        print("\n=== organizations 테이블 데이터 ===")
        cursor.execute("SELECT * FROM organizations LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        
        print("\n=== users 테이블에서 organization 관련 컬럼 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name LIKE '%org%'
            ORDER BY ordinal_position
        """)
        
        user_org_columns = cursor.fetchall()
        for col in user_org_columns:
            print(f"{col[0]} | {col[1]} | nullable: {col[2]} | default: {col[3]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 스키마 확인 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_org_schema()