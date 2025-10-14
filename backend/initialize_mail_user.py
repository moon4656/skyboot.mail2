#!/usr/bin/env python3
"""
메일 사용자 및 기본 폴더 초기화 스크립트

testadmin 사용자의 메일 사용자 계정과 기본 폴더들을 생성합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.model.organization_model import Organization
from app.model.mail_model import MailUser, MailFolder, FolderType
import uuid
from datetime import datetime

def initialize_mail_user():
    """메일 사용자 및 기본 폴더 초기화"""
    
    # 데이터베이스 세션 생성
    db = next(get_db())
    
    try:
        # testadmin 사용자 조회
        user = db.query(User).filter(User.email == "testadmin@skyboot.com").first()
        if not user:
            print("❌ testadmin 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 사용자 조회 성공: {user.email} (UUID: {user.user_uuid})")
        
        # 조직 조회
        organization = db.query(Organization).filter(Organization.org_id == user.org_id).first()
        if not organization:
            print("❌ 조직을 찾을 수 없습니다.")
            return
        
        print(f"✅ 조직 조회 성공: {organization.name} (UUID: {organization.org_id})")
        
        # 메일 사용자 확인/생성
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == user.user_uuid,
            MailUser.org_id == organization.org_id
        ).first()
        
        if not mail_user:
            # 메일 사용자 생성
            mail_user = MailUser(
                user_uuid=user.user_uuid,
                email=user.email,
                hashed_password=user.hashed_password,
                org_id=organization.org_id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(mail_user)
            db.commit()
            db.refresh(mail_user)
            print(f"✅ 메일 사용자 생성 완료: {mail_user.email}")
        else:
            print(f"✅ 메일 사용자 이미 존재: {mail_user.email}")
        
        # 기본 폴더들 생성
        folder_types = [
            (FolderType.INBOX, "받은편지함"),
            (FolderType.SENT, "보낸편지함"),
            (FolderType.DRAFT, "임시보관함"),
            (FolderType.TRASH, "휴지통")
        ]
        
        for folder_type, folder_name in folder_types:
            existing_folder = db.query(MailFolder).filter(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == organization.org_id,
                MailFolder.folder_type == folder_type
            ).first()
            
            if not existing_folder:
                folder = MailFolder(
                    folder_uuid=str(uuid.uuid4()),
                    user_uuid=mail_user.user_uuid,
                    org_id=organization.org_id,
                    name=folder_name,
                    folder_type=folder_type,
                    is_system=True,
                    created_at=datetime.utcnow()
                )
                db.add(folder)
                print(f"✅ {folder_name} 폴더 생성 완료")
            else:
                print(f"✅ {folder_name} 폴더 이미 존재")
        
        db.commit()
        print("✅ 모든 초기화 작업이 완료되었습니다.")
        
        # 생성된 폴더 목록 확인
        folders = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid,
            MailFolder.org_id == organization.org_id
        ).all()
        
        print("\n📁 생성된 폴더 목록:")
        for folder in folders:
            print(f"  - {folder.name} ({folder.folder_type.value}) - UUID: {folder.folder_uuid}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 메일 사용자 및 폴더 초기화 시작...")
    initialize_mail_user()