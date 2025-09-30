#!/usr/bin/env python3
"""
SQLite 테스트 데이터베이스에 관리자 계정 생성
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.user import Base
from app.model.user_model import User
from app.model.organization_model import Organization
from app.service.auth_service import get_password_hash

# 테스트 데이터베이스 URL
TEST_DATABASE_URL = "sqlite:///./test_skyboot_mail.db"

def setup_test_admin():
    """테스트 관리자 계정 설정"""
    print("🔧 테스트 관리자 계정 설정 중...")
    
    # 엔진 및 세션 생성
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 테스트 테이블 생성 완료")
    
    session = SessionLocal()
    
    try:
        # 기본 조직 생성
        org = session.query(Organization).filter_by(org_id="bbf43d4b-3862-4ab0-9a03-522213ccb7a2").first()
        if not org:
            org = Organization(
                org_id="bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
                org_code="SKYBOOT",
                name="SkyBoot",
                subdomain="skyboot",
                domain="skyboot.com",
                admin_email="admin@skyboot.com",
                is_active=True,
                max_users=100
            )
            session.add(org)
            session.commit()
            session.refresh(org)
            print("✅ 테스트 조직 생성 완료")
        else:
            print("ℹ️ 테스트 조직이 이미 존재합니다")
        
        # 관리자 계정 생성
        admin = session.query(User).filter_by(email="admin@skyboot.com").first()
        if not admin:
            admin = User(
                user_id="admin_skyboot",
                user_uuid="441eb65c-bed0-4e75-9cdd-c95425e635a0",
                email="admin@skyboot.com",
                username="admin_skyboot",
                hashed_password=get_password_hash("admin123"),  # 테스트에서 사용하는 비밀번호
                org_id=org.org_id,
                is_active=True,
                is_email_verified=True,
                role="admin"
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print("✅ 테스트 관리자 계정 생성 완료")
            print(f"📧 이메일: {admin.email}")
            print(f"🔑 비밀번호: admin123")
        else:
            # 기존 관리자 비밀번호 업데이트
            admin.hashed_password = get_password_hash("admin123")
            session.commit()
            print("✅ 기존 관리자 계정 비밀번호 업데이트 완료")
            print(f"📧 이메일: {admin.email}")
            print(f"🔑 비밀번호: admin123")
        
    except Exception as e:
        print(f"❌ 테스트 관리자 계정 설정 실패: {e}")
        session.rollback()
        return False
    finally:
        session.close()
    
    print("🎯 테스트 관리자 계정 설정 완료!")
    return True

if __name__ == "__main__":
    success = setup_test_admin()
    if not success:
        sys.exit(1)