#!/usr/bin/env python3
"""
testuser1@example.com 사용자의 메일 계정 초기화 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.model.user_model import User
from app.model.organization_model import Organization
from app.model.mail_model import MailUser, MailFolder, FolderType
from app.config import settings
import uuid
from datetime import datetime

def create_mail_user():
    """testuser1@example.com 사용자의 MailUser 생성"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔍 testuser1@example.com 사용자 조회...")
        
        # 사용자 조회
        user = db.query(User).filter(User.email == "testuser1@example.com").first()
        
        if not user:
            print("❌ testuser1@example.com 사용자를 찾을 수 없습니다.")
            return False
        
        print(f"✅ User 발견:")
        print(f"   - user_uuid: {user.user_uuid}")
        print(f"   - email: {user.email}")
        print(f"   - org_id: {user.org_id}")
        
        # 기존 MailUser 확인
        existing_mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == user.user_uuid,
            MailUser.org_id == user.org_id
        ).first()
        
        if existing_mail_user:
            print(f"✅ MailUser가 이미 존재합니다:")
            print(f"   - user_uuid: {existing_mail_user.user_uuid}")
            print(f"   - email: {existing_mail_user.email}")
            return True
        
        # 새 MailUser 생성
        print("\n📧 새 MailUser 생성 중...")
        
        mail_user = MailUser(
            user_id=str(user.user_uuid),  # user_id 필드에 user_uuid 값 설정
            user_uuid=user.user_uuid,
            org_id=user.org_id,
            email=user.email,
            password_hash=user.hashed_password,
            display_name=user.username,
            is_active=True,
            storage_used_mb=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(mail_user)
        db.commit()
        db.refresh(mail_user)
        
        print(f"✅ MailUser 생성 완료:")
        print(f"   - user_uuid: {mail_user.user_uuid}")
        print(f"   - email: {mail_user.email}")
        print(f"   - org_id: {mail_user.org_id}")
        
        # 기본 폴더 생성
        print("\n📁 기본 폴더 생성 중...")
        
        default_folders = [
            {"name": "받은편지함", "folder_type": FolderType.INBOX, "is_system": True},
            {"name": "보낸편지함", "folder_type": FolderType.SENT, "is_system": True},
            {"name": "임시보관함", "folder_type": FolderType.DRAFT, "is_system": True},
            {"name": "휴지통", "folder_type": FolderType.TRASH, "is_system": True}
        ]
        
        for folder_info in default_folders:
            folder = MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=mail_user.user_uuid,
                org_id=mail_user.org_id,
                name=folder_info["name"],
                folder_type=folder_info["folder_type"],
                is_system=folder_info["is_system"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(folder)
        
        db.commit()
        print("✅ 기본 폴더 생성 완료")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("📧 testuser1@example.com 메일 계정 초기화 시작")
    
    if create_mail_user():
        print("\n🎉 메일 계정 초기화 완료!")
    else:
        print("\n❌ 메일 계정 초기화 실패!")
        sys.exit(1)