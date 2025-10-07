#!/usr/bin/env python3
"""
사용자를 위한 기본 메일 폴더 생성 스크립트

이 스크립트는 테스트 사용자를 위해 기본 메일 폴더들(받은편지함, 보낸편지함, 임시보관함, 휴지통)을 생성합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailFolder, FolderType, MailUser
import uuid

def create_default_folders():
    """테스트 사용자를 위한 기본 메일 폴더들을 생성합니다."""
    try:
        db: Session = next(get_db())
        
        print("📁 기본 메일 폴더 생성 시작...")
        
        # 테스트 사용자 조회
        test_user = db.query(User).filter(User.email == "testuser_folder@example.com").first()
        if not test_user:
            print("❌ 테스트 사용자를 찾을 수 없습니다.")
            return
            
        # MailUser 조회
        mail_user = db.query(MailUser).filter(MailUser.email == "testuser_folder@example.com").first()
        if not mail_user:
            print("❌ MailUser를 찾을 수 없습니다.")
            return
            
        print(f"✅ 사용자 발견: {mail_user.email}")
        print(f"   - 사용자 UUID: {mail_user.user_uuid}")
        print(f"   - 조직 ID: {mail_user.org_id}")
        
        # 기본 폴더 정의
        default_folders = [
            {"name": "받은편지함", "folder_type": FolderType.INBOX},
            {"name": "보낸편지함", "folder_type": FolderType.SENT},
            {"name": "임시보관함", "folder_type": FolderType.DRAFT},
            {"name": "휴지통", "folder_type": FolderType.TRASH},
        ]
        
        created_count = 0
        
        for folder_info in default_folders:
            # 이미 존재하는지 확인
            existing_folder = db.query(MailFolder).filter(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.folder_type == folder_info["folder_type"]
            ).first()
            
            if existing_folder:
                print(f"⚠️ {folder_info['name']} 폴더가 이미 존재합니다.")
                continue
            
            # 새 폴더 생성
            new_folder = MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=mail_user.user_uuid,
                org_id=mail_user.org_id,
                name=folder_info["name"],
                folder_type=folder_info["folder_type"],
                is_system=True  # 시스템 기본 폴더로 설정
            )
            
            db.add(new_folder)
            created_count += 1
            print(f"✅ {folder_info['name']} 폴더 생성됨")
        
        # 변경사항 저장
        db.commit()
        print(f"\n🎉 총 {created_count}개의 기본 폴더가 생성되었습니다!")
        
        # 생성된 폴더들 확인
        print("\n📋 생성된 폴더 목록:")
        user_folders = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid
        ).all()
        
        for folder in user_folders:
            print(f"   - {folder.name} ({folder.folder_type.value})")
            print(f"     UUID: {folder.folder_uuid}")
            print(f"     시스템 폴더: {folder.is_system}")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    create_default_folders()