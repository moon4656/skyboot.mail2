#!/usr/bin/env python3
"""
사용자 메일 폴더 상태 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailFolder, FolderType, MailUser

def debug_user_folders():
    """사용자의 메일 폴더 상태를 디버깅합니다."""
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("🔍 사용자 메일 폴더 디버깅 시작...")
        
        # 테스트 사용자 조회 (User 테이블에서)
        test_user = db.query(User).filter(User.email == "testuser_folder@example.com").first()
        if not test_user:
            print("❌ 테스트 사용자를 찾을 수 없습니다.")
            return
            
        print(f"✅ 테스트 사용자 발견: {test_user.email}")
        print(f"   - 사용자 ID: {test_user.user_id}")
        print(f"   - 사용자 UUID: {test_user.user_uuid}")
        print(f"   - 조직 ID: {test_user.org_id}")
        
        # MailUser 테이블에서도 조회
        mail_user = db.query(MailUser).filter(MailUser.email == "testuser_folder@example.com").first()
        if mail_user:
            print(f"✅ MailUser 발견: {mail_user.email}")
            print(f"   - 사용자 ID: {mail_user.user_id}")
            print(f"   - 사용자 UUID: {mail_user.user_uuid}")
            print(f"   - 조직 ID: {mail_user.org_id}")
        else:
            print("❌ MailUser를 찾을 수 없습니다.")
            return
        
        # 사용자의 모든 폴더 조회 (MailUser의 UUID 사용)
        user_folders = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid
        ).all()
        
        print(f"\n📁 사용자 폴더 목록 (총 {len(user_folders)}개):")
        for folder in user_folders:
            print(f"   - 폴더 ID: {folder.id}")
            print(f"     이름: {folder.name}")
            print(f"     타입: {folder.folder_type}")
            print(f"     사용자 UUID: {folder.user_uuid}")
            print(f"     조직 ID: {folder.org_id}")
            print(f"     생성일: {folder.created_at}")
            print()
        
        # 특별히 보낸편지함 폴더 확인
        sent_folder = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid,
            MailFolder.folder_type == FolderType.SENT
        ).first()
        
        if sent_folder:
            print(f"✅ 보낸편지함 폴더 발견:")
            print(f"   - 폴더 ID: {sent_folder.id}")
            print(f"   - 이름: {sent_folder.name}")
            print(f"   - 타입: {sent_folder.folder_type}")
        else:
            print("❌ 보낸편지함 폴더를 찾을 수 없습니다!")
            
            # 기본 폴더들 확인
            print("\n📋 기본 폴더 타입별 확인:")
            for folder_type in [FolderType.INBOX, FolderType.SENT, FolderType.DRAFT, FolderType.TRASH]:
                folder = db.query(MailFolder).filter(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.folder_type == folder_type
                ).first()
                
                if folder:
                    print(f"   ✅ {folder_type.value}: {folder.name}")
                else:
                    print(f"   ❌ {folder_type.value}: 없음")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_user_folders()