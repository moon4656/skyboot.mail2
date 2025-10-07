#!/usr/bin/env python3
"""
로그인용 사용자 테이블 확인 스크립트
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import SaaSSettings

def check_login_users():
    """로그인용 사용자 테이블 확인"""
    try:
        settings = SaaSSettings()
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # 로그인용 사용자 정보 조회
        query = text("""
            SELECT 
                user_id,
                user_uuid,
                org_id,
                email,
                username,
                is_active,
                role,
                created_at
            FROM users
            ORDER BY created_at
        """)
        
        results = session.execute(query).fetchall()
        session.close()
        
        print("📋 로그인용 사용자 테이블 (users):")
        print("-" * 60)
        
        if results:
            for result in results:
                print(f"   사용자 ID: {result.user_id}")
                print(f"   UUID: {result.user_uuid}")
                print(f"   조직 ID: {result.org_id}")
                print(f"   이메일: {result.email}")
                print(f"   사용자명: {result.username}")
                print(f"   활성화: {result.is_active}")
                print(f"   역할: {result.role}")
                print(f"   생성일: {result.created_at}")
                print()
        else:
            print("   ❌ 로그인용 사용자가 없습니다!")
        
        return results
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {str(e)}")
        return []

if __name__ == "__main__":
    check_login_users()