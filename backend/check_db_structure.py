#!/usr/bin/env python3
"""
데이터베이스 테이블 구조 확인 스크립트
"""

from sqlalchemy import create_engine, text
from app.config import settings

def check_db_structure():
    """데이터베이스 테이블 구조를 확인합니다."""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 모든 테이블 목록 조회
            print("📋 데이터베이스 테이블 목록:")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
            
            print("\n🏢 organizations 테이블 구조:")
            if any('organizations' in str(table[0]) for table in tables):
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'organizations'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            else:
                print("  ❌ organizations 테이블이 존재하지 않습니다.")
            
            print("\n👥 users 테이블 구조:")
            if any('users' in str(table[0]) for table in tables):
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            else:
                print("  ❌ users 테이블이 존재하지 않습니다.")
                
    except Exception as e:
        print(f"❌ 데이터베이스 구조 확인 실패: {e}")

if __name__ == "__main__":
    check_db_structure()