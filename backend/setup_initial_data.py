#!/usr/bin/env python3
"""
초기 데이터 및 테스트 사용자 생성 스크립트
기본 조직, 관리자 사용자, 테스트 사용자를 생성합니다.
"""

import sys
import os
from pathlib import Path
import uuid
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.schemas.auth_schema import UserRole
from app.model.organization_model import Organization, OrganizationSettings
from app.model.mail_model import MailUser, MailFolder, FolderType
from app.service.auth_service import AuthService

def setup_initial_data():
    """초기 데이터를 설정합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🏢 기본 조직 생성 중...")
        
        # 기본 조직 생성
        default_org = Organization(
            org_id=str(uuid.uuid4()),
            org_code="default",
            name="SkyBoot Mail",
            subdomain="skyboot",
            domain="skyboot.mail",
            admin_email="admin@skyboot.mail",
            admin_name="System Administrator",
            max_users=1000,
            is_active=True
        )
        db.add(default_org)
        db.flush()  # ID 생성을 위해 flush
        
        # 조직 설정 생성 (개별 설정들)
        settings_list = [
            {
                "setting_key": "mail_server_enabled",
                "setting_value": "true",
                "setting_type": "boolean",
                "description": "메일 서버 활성화 여부"
            },
            {
                "setting_key": "max_mailbox_size_mb",
                "setting_value": "1000",
                "setting_type": "number",
                "description": "최대 메일박스 크기(MB)"
            },
            {
                "setting_key": "max_attachment_size_mb",
                "setting_value": "25",
                "setting_type": "number",
                "description": "최대 첨부파일 크기(MB)"
            },
            {
                "setting_key": "smtp_enabled",
                "setting_value": "true",
                "setting_type": "boolean",
                "description": "SMTP 서버 활성화"
            },
            {
                "setting_key": "imap_enabled",
                "setting_value": "true",
                "setting_type": "boolean",
                "description": "IMAP 서버 활성화"
            }
        ]
        
        for setting in settings_list:
            org_setting = OrganizationSettings(
                org_id=default_org.org_id,
                setting_key=setting["setting_key"],
                setting_value=setting["setting_value"],
                setting_type=setting["setting_type"],
                description=setting["description"],
                is_public=False
            )
            db.add(org_setting)
        
        print(f"✅ 기본 조직 생성 완료: {default_org.name} (ID: {default_org.org_id})")
        
        print("\n👤 관리자 사용자 생성 중...")
        
        # 관리자 사용자 생성
        admin_user = User(
            user_id="admin",
            user_uuid=str(uuid.uuid4()),
            email="admin@skyboot.mail",
            username="admin",
            hashed_password=AuthService.get_password_hash("test"),
            org_id=default_org.org_id,
            role=UserRole.ORG_ADMIN.value,
            is_active=True
        )
        db.add(admin_user)
        db.flush()
        
        # 관리자 메일 사용자 생성
        admin_mail_user = MailUser(
            user_id=admin_user.user_id,
            user_uuid=admin_user.user_uuid,
            email=admin_user.email,
            password_hash=admin_user.hashed_password,
            org_id=default_org.org_id,
            is_active=True
        )
        db.add(admin_mail_user)
        
        # 관리자 기본 메일 폴더 생성
        admin_folders = [
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=admin_user.user_uuid,
                org_id=default_org.org_id,
                name="INBOX",
                folder_type=FolderType.INBOX,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=admin_user.user_uuid,
                org_id=default_org.org_id,
                name="Sent",
                folder_type=FolderType.SENT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=admin_user.user_uuid,
                org_id=default_org.org_id,
                name="Drafts",
                folder_type=FolderType.DRAFT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=admin_user.user_uuid,
                org_id=default_org.org_id,
                name="Trash",
                folder_type=FolderType.TRASH,
                is_system=True
            )
        ]
        for folder in admin_folders:
            db.add(folder)
        
        print(f"✅ 관리자 사용자 생성 완료: {admin_user.email}")
        
        print("\n👥 테스트 사용자들 생성 중...")
        
        # 테스트 사용자 1
        test_user1 = User(
            user_id="user01",
            user_uuid=str(uuid.uuid4()),
            email="user01@skyboot.mail",
            username="user01",
            hashed_password=AuthService.get_password_hash("user123!"),
            org_id=default_org.org_id,
            role=UserRole.USER.value,
            is_active=True
        )
        db.add(test_user1)
        db.flush()
        
        # 테스트 사용자 1 메일 사용자 생성
        test_mail_user1 = MailUser(
            user_id=test_user1.user_id,
            user_uuid=test_user1.user_uuid,
            email=test_user1.email,
            password_hash=test_user1.hashed_password,
            org_id=default_org.org_id,
            is_active=True
        )
        db.add(test_mail_user1)
        
        # 테스트 사용자 1 기본 메일 폴더 생성
        user1_folders = [
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user1.user_uuid,
                org_id=default_org.org_id,
                name="INBOX",
                folder_type=FolderType.INBOX,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user1.user_uuid,
                org_id=default_org.org_id,
                name="Sent",
                folder_type=FolderType.SENT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user1.user_uuid,
                org_id=default_org.org_id,
                name="Drafts",
                folder_type=FolderType.DRAFT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user1.user_uuid,
                org_id=default_org.org_id,
                name="Trash",
                folder_type=FolderType.TRASH,
                is_system=True
            )
        ]
        for folder in user1_folders:
            db.add(folder)
        
        # 테스트 사용자 2
        test_user2 = User(
            user_id="testuser",
            user_uuid=str(uuid.uuid4()),
            email="testuser@skyboot.mail",
            username="testuser",
            hashed_password=AuthService.get_password_hash("test123!"),
            org_id=default_org.org_id,
            role=UserRole.USER.value,
            is_active=True
        )
        db.add(test_user2)
        db.flush()
        
        # 테스트 사용자 2 메일 사용자 생성
        test_mail_user2 = MailUser(
            user_id=test_user2.user_id,
            user_uuid=test_user2.user_uuid,
            email=test_user2.email,
            password_hash=test_user2.hashed_password,
            org_id=default_org.org_id,
            is_active=True
        )
        db.add(test_mail_user2)
        
        # 테스트 사용자 2 기본 메일 폴더 생성
        user2_folders = [
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user2.user_uuid,
                org_id=default_org.org_id,
                name="INBOX",
                folder_type=FolderType.INBOX,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user2.user_uuid,
                org_id=default_org.org_id,
                name="Sent",
                folder_type=FolderType.SENT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user2.user_uuid,
                org_id=default_org.org_id,
                name="Drafts",
                folder_type=FolderType.DRAFT,
                is_system=True
            ),
            MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=test_user2.user_uuid,
                org_id=default_org.org_id,
                name="Trash",
                folder_type=FolderType.TRASH,
                is_system=True
            )
        ]
        for folder in user2_folders:
            db.add(folder)
        
        print(f"✅ 테스트 사용자 생성 완료:")
        print(f"  - {test_user1.email} (비밀번호: user123!)")
        print(f"  - {test_user2.email} (비밀번호: test123!)")
        
        # 모든 변경사항 커밋
        db.commit()
        
        print("\n📊 생성된 데이터 요약:")
        print(f"  - 조직: 1개 ({default_org.name})")
        print(f"  - 사용자: 3명 (관리자 1명, 일반 사용자 2명)")
        print(f"  - 메일 사용자: 3명")
        print(f"  - 메일 폴더: 15개 (사용자당 5개씩)")
        
        return True
        
    except Exception as e:
        print(f"❌ 초기 데이터 생성 중 오류 발생: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SkyBoot Mail 초기 데이터 설정 시작")
    print("=" * 60)
    
    success = setup_initial_data()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 초기 데이터 설정이 완료되었습니다!")
        print("=" * 60)
        print("\n📋 로그인 정보:")
        print("  관리자: admin@skyboot.mail / admin123!")
        print("  사용자1: user01@skyboot.mail / user123!")
        print("  사용자2: testuser@skyboot.mail / test123!")
    else:
        print("\n" + "=" * 60)
        print("❌ 초기 데이터 설정에 실패했습니다.")
        print("=" * 60)
        sys.exit(1)