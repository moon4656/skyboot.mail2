#!/usr/bin/env python3
"""
사용자 생성 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
import uuid
import bcrypt

def test_user_creation():
    """사용자 생성 테스트"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 조직 찾기 (SkyBoot 조직 사용)
        org = db.query(Organization).filter(Organization.org_code == "A003").first()
        if not org:
            print("❌ SkyBoot 조직을 찾을 수 없습니다.")
            return
        
        print(f"✅ 조직 찾음: {org.name} (ID: {org.org_id})")
        
        # 기존 사용자 확인
        existing_user = db.query(User).filter(
            User.email == "testadmin@skyboot.com",
            User.org_id == org.org_id
        ).first()
        
        if existing_user:
            print(f"⚠️ 사용자가 이미 존재합니다: {existing_user.email}")
            return
        
        # 비밀번호 해시
        password = "test"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 새 사용자 생성
        new_user = User(
            user_id="testadmin",
            user_uuid=str(uuid.uuid4()),
            org_id=org.org_id,
            email="testadmin@skyboot.com",
            username="testadmin",
            hashed_password=hashed_password,
            role="user",
            permissions="read,write",
            is_active=True,
            is_email_verified=False
        )
        
        print(f"📝 사용자 객체 생성: {new_user.email}")
        print(f"   - user_id: {new_user.user_id}")
        print(f"   - org_id: {new_user.org_id}")
        print(f"   - email: {new_user.email}")
        
        # 데이터베이스에 추가
        db.add(new_user)
        db.commit()
        
        print("✅ 사용자 생성 성공!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_creation()