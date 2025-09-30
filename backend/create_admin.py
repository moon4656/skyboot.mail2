#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스에 관리자 계정 생성
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
from app.service.auth_service import get_password_hash
import uuid

def create_admin_account():
    """관리자 계정 생성"""
    print("🔧 관리자 계정 생성 중...")
    
    # 엔진 및 세션 생성
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 기본 조직 생성
        org = session.query(Organization).filter_by(domain="skyboot.com").first()
        if not org:
            org_uuid = str(uuid.uuid4())
            org = Organization(
                org_id=org_uuid,
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
            print("✅ 기본 조직 생성 완료")
        else:
            print("ℹ️ 기본 조직이 이미 존재합니다")
        
        # 관리자 계정 생성
        admin = session.query(User).filter_by(email="admin@skyboot.com").first()
        if not admin:
            user_uuid = str(uuid.uuid4())
            admin = User(
                user_id="admin_skyboot",
                user_uuid=user_uuid,
                email="admin@skyboot.com",
                username="admin_skyboot",
                hashed_password=get_password_hash("admin123"),
                org_id=org.org_id,
                is_active=True,
                is_email_verified=True,
                role="admin"
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print("✅ 관리자 계정 생성 완료")
            print(f"📧 이메일: {admin.email}")
            print(f"🔑 비밀번호: admin123")
            print(f"🏢 조직: {org.name}")
        else:
            # 기존 관리자 비밀번호 업데이트
            admin.hashed_password = get_password_hash("admin123")
            admin.org_id = org.org_id  # 조직 ID 업데이트
            session.commit()
            print("✅ 기존 관리자 계정 업데이트 완료")
            print(f"📧 이메일: {admin.email}")
            print(f"🔑 비밀번호: admin123")
            print(f"🏢 조직: {org.name}")
        
    except Exception as e:
        print(f"❌ 관리자 계정 생성 실패: {e}")
        session.rollback()
        return False
    finally:
        session.close()
    
    print("🎯 관리자 계정 생성 완료!")
    return True

if __name__ == "__main__":
    success = create_admin_account()
    if not success:
        exit(1)