#!/usr/bin/env python3
"""
사용자 ID 확인 스크립트

데이터베이스에 등록된 사용자들의 user_id 값을 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization

def main():
    """메인 함수"""
    print("=" * 60)
    print("🔍 사용자 ID 확인")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 모든 사용자 조회
        users = db.query(User).all()
        
        print(f"📊 총 {len(users)}명의 사용자가 등록되어 있습니다.")
        print()
        
        for i, user in enumerate(users, 1):
            # 조직 정보 조회
            org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
            org_name = org.name if org else "Unknown"
            
            print(f"{i}. 사용자 정보:")
            print(f"   - user_id: {user.user_id}")
            print(f"   - 이메일: {user.email}")
            print(f"   - 사용자명: {user.username}")
            print(f"   - 사용자 UUID: {user.user_uuid}")
            print(f"   - 역할: {user.role}")
            print(f"   - 조직: {org_name} ({user.org_id})")
            print(f"   - 활성화 상태: {'활성' if user.is_active else '비활성'}")
            print(f"   - 생성일: {user.created_at}")
            print()
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return
    
    print("=" * 60)
    print("✅ 사용자 ID 확인 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()