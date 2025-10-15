#!/usr/bin/env python3
"""
현재 데이터베이스의 모든 사용자를 조회하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.model.user_model import User
from app.model.organization_model import Organization
from app.config import settings

def check_all_users():
    """
    데이터베이스의 모든 사용자를 조회하고 출력합니다.
    """
    print("=" * 60)
    print("🔍 현재 데이터베이스의 모든 사용자 조회")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # 모든 사용자 조회 (조직 정보와 함께)
        users = session.query(User).join(Organization, User.org_id == Organization.org_id).all()
        
        if not users:
            print("❌ 등록된 사용자가 없습니다.")
            return
        
        print(f"📊 총 {len(users)}명의 사용자가 등록되어 있습니다.\n")
        
        # 사용자 정보 출력
        for i, user in enumerate(users, 1):
            organization = session.query(Organization).filter(Organization.org_id == user.org_id).first()
            org_name = organization.name if organization else "알 수 없음"
            
            print(f"{i}. 사용자 정보:")
            print(f"   - 이메일: {user.email}")
            print(f"   - 사용자 UUID: {user.user_uuid}")
            print(f"   - 역할: {user.role}")
            print(f"   - 조직: {org_name} ({user.org_id})")
            print(f"   - 활성화 상태: {'활성' if user.is_active else '비활성'}")
            print(f"   - 생성일: {user.created_at}")
            print(f"   - 현재 패스워드 해시: {user.hashed_password[:50]}...")
            print()
        
        session.close()
        
        print("=" * 60)
        print("✅ 사용자 조회 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_users()