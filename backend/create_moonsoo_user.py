#!/usr/bin/env python3
"""
moonsoo 테스트 사용자 생성 스크립트
외부 메일 발송 테스트를 위한 사용자 계정 생성
"""

import sys
import os
import uuid
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import Base
from app.service.auth_service import AuthService

# PostgreSQL 데이터베이스 설정
DATABASE_URL = "postgresql://skyboot_user:skyboot_password@localhost:5432/skyboot_mail"

def create_moonsoo_user():
    """moonsoo 테스트 사용자 생성"""
    try:
        # 데이터베이스 연결
        engine = create_engine(
            DATABASE_URL,
            connect_args={
                "client_encoding": "utf8",
                "options": "-c timezone=UTC"
            },
            echo=False
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("🔧 moonsoo 테스트 사용자 생성 중...")
        
        # SkyBoot 조직 확인
        skyboot_org = session.query(Organization).filter(
            Organization.org_code == "SKYBOOT"
        ).first()
        
        if not skyboot_org:
            print("🏢 SkyBoot 조직을 생성합니다...")
            skyboot_org = Organization(
                org_id="skyboot_org",
                org_code="SKYBOOT",
                name="SkyBoot",
                subdomain="skyboot",
                domain="skyboot.com",
                admin_email="admin@skyboot.com",
                max_users=1000,
                is_active=True
            )
            session.add(skyboot_org)
            session.commit()
            session.refresh(skyboot_org)
        
        print(f"✅ SkyBoot 조직 확인: {skyboot_org.name}")
        
        # 기존 moonsoo 사용자 확인
        existing_user = session.query(User).filter(
            User.email == "moonsoo@skyboot.com"
        ).first()
        
        if existing_user:
            print("⚠️ moonsoo 사용자가 이미 존재합니다. 비밀번호를 업데이트합니다.")
            existing_user.hashed_password = AuthService.get_password_hash("test")
            existing_user.is_active = True
            existing_user.is_email_verified = True
            session.commit()
            print("✅ moonsoo 사용자 비밀번호 업데이트 완료")
            return True
        
        # 새 moonsoo 사용자 생성
        moonsoo_user = User(
            user_id="moonsoo_test",
            user_uuid=str(uuid.uuid4()),
            username="moonsoo",
            email="moonsoo@skyboot.com",
            hashed_password=AuthService.get_password_hash("test"),
            org_id=skyboot_org.org_id,
            is_active=True,
            is_email_verified=True,
            role="user",
            created_at=datetime.utcnow()
        )
        
        session.add(moonsoo_user)
        session.commit()
        session.refresh(moonsoo_user)
        
        print("✅ moonsoo 테스트 사용자 생성 완료")
        print(f"   - 이메일: {moonsoo_user.email}")
        print(f"   - 비밀번호: test")
        print(f"   - 조직: {skyboot_org.name}")
        print(f"   - 사용자 ID: {moonsoo_user.user_id}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ 사용자 생성 실패: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    print("🚀 moonsoo 테스트 사용자 생성 시작")
    success = create_moonsoo_user()
    
    if success:
        print("\n✅ 모든 작업이 완료되었습니다!")
        print("📧 이제 moonsoo@skyboot.com 계정으로 로그인하여 메일 발송 테스트를 진행할 수 있습니다.")
    else:
        print("\n❌ 사용자 생성에 실패했습니다.")
        sys.exit(1)