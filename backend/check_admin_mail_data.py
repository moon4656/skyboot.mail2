#!/usr/bin/env python3
"""
Admin 계정의 메일 데이터를 데이터베이스에서 직접 조회하는 스크립트
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.mail_model import Mail, MailRecipient, MailInFolder, MailFolder, MailUser
from app.model.user_model import User
from app.config import settings

def check_admin_mail_data():
    """
    Admin 계정의 메일 관련 데이터를 데이터베이스에서 직접 조회
    """
    print("=" * 60)
    print("📧 Admin 메일 데이터 직접 조회")
    print("=" * 60)
    print(f"⏰ 조회 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("1️⃣ Admin 사용자 정보 조회")
        print("-" * 30)
        
        # Admin 사용자 조회
        admin_user = db.query(User).filter(User.email == "admin@skyboot.mail").first()
        if admin_user:
            print(f"✅ Admin 사용자 발견:")
            print(f"   - User ID: {admin_user.user_id}")
            print(f"   - UUID: {admin_user.user_uuid}")
            print(f"   - 이메일: {admin_user.email}")
            print(f"   - 조직 ID: {admin_user.org_id}")
        else:
            print("❌ Admin 사용자를 찾을 수 없습니다.")
            return
        
        print()
        print("2️⃣ Admin MailUser 정보 조회")
        print("-" * 30)
        
        # Admin MailUser 조회
        admin_mail_user = db.query(MailUser).filter(MailUser.email == "admin@skyboot.mail").first()
        if admin_mail_user:
            print(f"✅ Admin MailUser 발견:")
            print(f"   - User UUID: {admin_mail_user.user_uuid}")
            print(f"   - 이메일: {admin_mail_user.email}")
            print(f"   - 조직 ID: {admin_mail_user.org_id}")
        else:
            print("❌ Admin MailUser를 찾을 수 없습니다.")
            return
        
        print()
        print("3️⃣ Admin 수신 메일 (mail_recipients) 조회")
        print("-" * 30)
        
        # Admin이 수신자인 메일들 조회
        admin_recipients = db.query(MailRecipient).filter(
            MailRecipient.recipient_email == "admin@skyboot.mail"
        ).all()
        
        print(f"📊 총 {len(admin_recipients)}개의 수신 레코드 발견:")
        for i, recipient in enumerate(admin_recipients, 1):
            print(f"   {i}. 메일 UUID: {recipient.mail_uuid}")
            print(f"      수신자 타입: {recipient.recipient_type}")
            print(f"      생성일: {recipient.created_at}")
            print()
        print("4️⃣ Admin INBOX 폴더 조회")
        print("-" * 30)
        
        # Admin의 INBOX 폴더 조회
        admin_inbox = db.query(MailFolder).filter(
            MailFolder.user_uuid == admin_mail_user.user_uuid,
            MailFolder.folder_type == "inbox"
        ).first()
        
        if admin_inbox:
            print(f"✅ Admin INBOX 폴더 발견:")
            print(f"   - 폴더 UUID: {admin_inbox.folder_uuid}")
            print(f"   - 폴더명: {admin_inbox.name}")
            print(f"   - 폴더 타입: {admin_inbox.folder_type}")
        else:
            print("❌ Admin INBOX 폴더를 찾을 수 없습니다.")
            return
        
        print()
        print("5️⃣ Admin INBOX에 할당된 메일 (mail_in_folder) 조회")
        print("-" * 30)
        
        # Admin INBOX에 할당된 메일들 조회
        inbox_mails = db.query(MailInFolder).filter(
            MailInFolder.folder_uuid == admin_inbox.folder_uuid
        ).all()
        
        print(f"📊 INBOX에 할당된 메일 수: {len(inbox_mails)}개")
        for i, mail_in_folder in enumerate(inbox_mails, 1):
            print(f"   {i}. 메일 UUID: {mail_in_folder.mail_uuid}")
            print(f"      사용자 UUID: {mail_in_folder.user_uuid}")
            print(f"      생성일: {mail_in_folder.created_at}")
            print()
        
        print("6️⃣ 실제 메일 정보 조회")
        print("-" * 30)
        
        # 수신자 테이블에 있는 메일들의 실제 정보 조회
        mail_uuids = [r.mail_uuid for r in admin_recipients]
        mails = db.query(Mail).filter(Mail.mail_uuid.in_(mail_uuids)).all()
        
        print(f"📊 실제 메일 수: {len(mails)}개")
        for i, mail in enumerate(mails, 1):
            print(f"   {i}. 메일 UUID: {mail.mail_uuid}")
            print(f"      제목: {mail.subject}")
            print(f"      상태: {mail.status}")
            print(f"      발송일: {mail.sent_at}")
            print(f"      임시보관: {mail.is_draft}")
            
            # 이 메일이 INBOX에 할당되어 있는지 확인
            is_in_inbox = any(mif.mail_uuid == mail.mail_uuid for mif in inbox_mails)
            print(f"      INBOX 할당: {'✅ 예' if is_in_inbox else '❌ 아니오'}")
            print()
        
        print("7️⃣ 문제 분석")
        print("-" * 30)
        
        recipients_count = len(admin_recipients)
        inbox_assigned_count = len(inbox_mails)
        actual_mails_count = len(mails)
        
        print(f"📊 데이터 요약:")
        print(f"   - mail_recipients 테이블: {recipients_count}개")
        print(f"   - mail_in_folder (INBOX): {inbox_assigned_count}개")
        print(f"   - 실제 메일: {actual_mails_count}개")
        
        if recipients_count != inbox_assigned_count:
            print(f"⚠️ 문제 발견: 수신자 테이블({recipients_count}개)과 INBOX 할당({inbox_assigned_count}개)이 일치하지 않습니다!")
            
            # 누락된 메일 찾기
            inbox_mail_uuids = {mif.mail_uuid for mif in inbox_mails}
            recipient_mail_uuids = {r.mail_uuid for r in admin_recipients}
            missing_in_inbox = recipient_mail_uuids - inbox_mail_uuids
            
            if missing_in_inbox:
                print(f"📋 INBOX에 누락된 메일 UUID들:")
                for mail_uuid in missing_in_inbox:
                    print(f"   - {mail_uuid}")
        else:
            print("✅ 데이터 일관성: 정상")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print()
    print(f"⏰ 조회 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    check_admin_mail_data()