#!/usr/bin/env python3
"""
메일 폴더 생성 상태를 확인하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
from app.model.mail_model import MailUser, MailFolder

def check_mail_folders():
    """메일 폴더 생성 상태를 확인합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        print("🔍 메일 폴더 생성 상태 확인 중...")
        
        # 1. 사용자 정보 확인
        user = db.query(User).filter(User.user_id == "testadmin").first()
        if not user:
            print("❌ testadmin 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 사용자 발견: {user.user_id} ({user.email})")
        print(f"   - 사용자 UUID: {user.user_uuid}")
        print(f"   - 조직 ID: {user.org_id}")
        
        # 2. 조직 정보 확인
        organization = db.query(Organization).filter(Organization.org_id == user.org_id).first()
        if organization:
            print(f"✅ 조직 발견: {organization.name} ({organization.org_id})")
        
        # 3. MailUser 확인
        mail_user = db.query(MailUser).filter(MailUser.user_uuid == user.user_uuid).first()
        if not mail_user:
            print("❌ MailUser 레코드를 찾을 수 없습니다.")
            return
        
        print(f"✅ MailUser 발견: {mail_user.email}")
        print(f"   - MailUser UUID: {mail_user.user_uuid}")
        print(f"   - 조직 ID: {mail_user.org_id}")
        
        # 4. 메일 폴더 확인
        folders = db.query(MailFolder).filter(MailFolder.user_uuid == user.user_uuid).all()
        
        if not folders:
            print("❌ 메일 폴더가 생성되지 않았습니다.")
            return
        
        print(f"✅ 메일 폴더 {len(folders)}개 발견:")
        for folder in folders:
            print(f"   - {folder.folder_type.value}: {folder.name}")
            print(f"     UUID: {folder.folder_uuid}")
            print(f"     조직 ID: {folder.org_id}")
        
        # 5. Inbox 폴더 특별 확인
        from app.model.mail_model import FolderType
        inbox_folder = db.query(MailFolder).filter(
            MailFolder.user_uuid == user.user_uuid,
            MailFolder.folder_type == FolderType.INBOX
        ).first()
        
        if inbox_folder:
            print(f"✅ Inbox 폴더 확인됨: {inbox_folder.name}")
            print(f"   - UUID: {inbox_folder.folder_uuid}")
        else:
            print("❌ Inbox 폴더를 찾을 수 없습니다!")
        
        print("\n📊 전체 통계:")
        print(f"   - 총 사용자 수: {db.query(User).count()}")
        print(f"   - 총 조직 수: {db.query(Organization).count()}")
        print(f"   - 총 MailUser 수: {db.query(MailUser).count()}")
        print(f"   - 총 MailFolder 수: {db.query(MailFolder).count()}")

if __name__ == "__main__":
    try:
        check_mail_folders()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()