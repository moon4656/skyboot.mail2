#!/usr/bin/env python3
"""
user01의 받은편지함 폴더 할당 문제를 조사하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.mail_model import MailUser, Mail, MailFolder, MailInFolder, FolderType
from app.model.organization_model import Organization

def main():
    print("🔍 user01 받은편지함 폴더 할당 문제 조사")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # 1. user01 정보 확인
        user01 = db.query(User).filter(User.user_id == "user01").first()
        if not user01:
            print("❌ user01 계정을 찾을 수 없습니다.")
            return
        
        print(f"✅ user01 정보:")
        print(f"   - 이메일: {user01.email}")
        print(f"   - UUID: {user01.user_uuid}")
        print(f"   - 조직 ID: {user01.org_id}")
        
        # 2. user01의 메일 폴더 확인
        print(f"\n📁 user01의 메일 폴더 목록:")
        folders = db.query(MailFolder).filter(MailFolder.user_uuid == user01.user_uuid).all()
        print(f"총 폴더 수: {len(folders)}개")
        
        inbox_folder = None
        for folder in folders:
            print(f"   - {folder.name} ({folder.folder_type})")
            print(f"     UUID: {folder.folder_uuid}")
            print(f"     시스템 폴더: {folder.is_system}")
            if folder.folder_type == FolderType.INBOX:
                inbox_folder = folder
        
        if not inbox_folder:
            print("❌ 받은편지함 폴더를 찾을 수 없습니다!")
            return
        
        print(f"\n📥 받은편지함 폴더 정보:")
        print(f"   - 폴더명: {inbox_folder.name}")
        print(f"   - UUID: {inbox_folder.folder_uuid}")
        print(f"   - 타입: {inbox_folder.folder_type}")
        print(f"   - 시스템 폴더: {inbox_folder.is_system}")
        print(f"   - 생성일: {inbox_folder.created_at}")
        
        # 3. 받은편지함에 할당된 메일 확인
        print(f"\n📧 받은편지함에 할당된 메일:")
        assigned_mails = db.query(MailInFolder).filter(
            MailInFolder.folder_uuid == inbox_folder.folder_uuid
        ).all()
        print(f"할당된 메일 수: {len(assigned_mails)}개")
        
        for mail_in_folder in assigned_mails:
            print(f"   - 메일 UUID: {mail_in_folder.mail_uuid}")
            print(f"     할당 시간: {mail_in_folder.created_at}")
        
        # 4. user01이 수신한 모든 메일 확인
        print(f"\n📨 user01이 수신한 모든 메일:")
        received_query = text("""
            SELECT m.mail_uuid, m.subject, m.sent_at, mr.recipient_type
            FROM mails m
            JOIN mail_recipients mr ON m.mail_uuid = mr.mail_uuid
            WHERE mr.recipient_email = :email
            ORDER BY m.sent_at DESC
        """)
        received_mails = db.execute(received_query, {"email": user01.email}).fetchall()
        print(f"수신한 메일 수: {len(received_mails)}개")
        
        # 5. 할당되지 않은 메일 찾기
        print(f"\n🔍 할당되지 않은 메일 찾기:")
        assigned_mail_uuids = {mail.mail_uuid for mail in assigned_mails}
        unassigned_mails = []
        
        for mail in received_mails:
            if mail.mail_uuid not in assigned_mail_uuids:
                unassigned_mails.append(mail)
        
        print(f"할당되지 않은 메일: {len(unassigned_mails)}개")
        for mail in unassigned_mails:
            print(f"   - {mail.mail_uuid}: {mail.subject}")
            print(f"     발송 시간: {mail.sent_at}")
            print(f"     수신 타입: {mail.recipient_type}")
        
        # 6. 메일 할당 규칙 확인
        print(f"\n📋 메일 할당 규칙 확인:")
        print("받은편지함에 할당되어야 하는 메일:")
        print("- recipient_type이 'to'인 메일")
        print("- 해당 사용자의 이메일로 수신된 메일")
        
        # 7. 자동 할당 테스트
        if unassigned_mails:
            print(f"\n🔧 자동 할당 테스트 (실제 할당하지 않음):")
            for mail in unassigned_mails[:3]:  # 처음 3개만 테스트
                print(f"할당 대상: {mail.mail_uuid} - {mail.subject}")
                # 실제 할당은 하지 않고 로그만 출력
        
        # 8. 최근 메일 할당 로그 확인
        print(f"\n📊 최근 메일 할당 활동:")
        recent_assignments = db.query(MailInFolder).filter(
            MailInFolder.folder_uuid == inbox_folder.folder_uuid
        ).order_by(MailInFolder.created_at.desc()).limit(5).all()
        
        print(f"최근 할당 기록: {len(recent_assignments)}개")
        for assignment in recent_assignments:
            print(f"   - {assignment.mail_uuid} (할당: {assignment.created_at})")

if __name__ == "__main__":
    main()