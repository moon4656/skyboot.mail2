#!/usr/bin/env python3
"""
users 테이블 구조 확인 스크립트

실제 users 테이블의 컬럼 구조와 데이터를 확인합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_users_table_structure():
    """users 테이블 구조 확인"""
    print("🔍 users 테이블 구조 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # 1. 테이블 구조 확인
        print("📋 users 테이블 컬럼 정보:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        for column in columns:
            print(f"  - {column[0]} ({column[1]}) - Nullable: {column[2]} - Default: {column[3]}")
        
        print()
        
        # 2. 실제 데이터 확인 (모든 컬럼)
        print("📋 users 테이블 데이터 (처음 5개):")
        result = db.execute(text("SELECT * FROM users LIMIT 5;"))
        
        users = result.fetchall()
        if users:
            # 컬럼 이름 가져오기
            column_names = result.keys()
            print(f"  컬럼: {list(column_names)}")
            print()
            
            for i, user in enumerate(users):
                print(f"  사용자 {i+1}:")
                for j, value in enumerate(user):
                    print(f"    {column_names[j]}: {value}")
                print()
        else:
            print("  데이터가 없습니다.")
        
        # 3. user01 관련 사용자 찾기
        print("📋 user01 관련 사용자 찾기:")
        result = db.execute(text("SELECT * FROM users WHERE email LIKE '%user01%' OR email LIKE '%user%';"))
        
        user01_users = result.fetchall()
        if user01_users:
            column_names = result.keys()
            for i, user in enumerate(user01_users):
                print(f"  사용자 {i+1}:")
                for j, value in enumerate(user):
                    print(f"    {column_names[j]}: {value}")
                print()
        else:
            print("  user01 관련 사용자를 찾을 수 없습니다.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    """메인 함수"""
    print("🔍 users 테이블 구조 및 데이터 확인")
    print("=" * 60)
    
    check_users_table_structure()
    
    print("=" * 60)
    print("🔍 users 테이블 확인 완료")

if __name__ == "__main__":
    main()