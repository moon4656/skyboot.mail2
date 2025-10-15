#!/usr/bin/env python3
"""
user01 계정의 메일 발송 내역과 admin 계정의 수신 내역을 확인하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database.user import engine
from app.model.user_model import User
from app.model.organization_model import Organization
from app.model.mail_model import MailUser, Mail, MailRecipient, MailFolder, MailInFolder
from datetime import datetime

def main():
    """user01과 admin의 메일 데이터를 조회합니다."""
    
    # 데이터베이스 세션 생성
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("📧 user01 및 admin 메일 데이터 조회")
        print("=" * 60)
        
        # 1. user01 사용자 정보 조회
        print("\n1️⃣ user01 사용자 정보 조회")
        user01 = db.query(User).filter(User.email == "user01@skyboot.mail").first()
        if user01:
            print(f"✅ user01 사용자 발견:")
            print(f"   - ID: {user01.user_id}")
            print(f"   - UUID: {user01.user_uuid}")
            print(f"   - 이메일: {user01.email}")
            print(f"   - 조직 ID: {user01.org_id}")
            print(f"   - 활성화: {user01.is_active}")
            
            # user01의 MailUser 정보 조회
            user01_mail_user = db.query(MailUser).filter(MailUser.user_id == user01.user_id).first()
            if user01_mail_user:
                print(f"   - MailUser UUID: {user01_mail_user.user_uuid}")
                print(f"   - 조직 ID: {user01_mail_user.org_id}")
            else:
                print("   ❌ MailUser 정보 없음")
        else:
            print("❌ user01 사용자를 찾을 수 없습니다.")
            return
        
        # 2. admin 사용자 정보 조회
        print("\n2️⃣ admin 사용자 정보 조회")
        admin = db.query(User).filter(User.email == "admin@skyboot.mail").first()
        if admin:
            print(f"✅ admin 사용자 발견:")
            print(f"   - ID: {admin.user_id}")
            print(f"   - UUID: {admin.user_uuid}")
            print(f"   - 이메일: {admin.email}")
            print(f"   - 조직 ID: {admin.org_id}")
            
            # admin의 MailUser 정보 조회
            admin_mail_user = db.query(MailUser).filter(MailUser.user_id == admin.user_id).first()
            if admin_mail_user:
                print(f"   - MailUser UUID: {admin_mail_user.user_uuid}")
                print(f"   - 조직 ID: {admin_mail_user.org_id}")
            else:
                print("   ❌ MailUser 정보 없음")
        else:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 3. user01이 발송한 메일 조회 (최근 10개)
        print("\n3️⃣ user01이 발송한 메일 조회 (최근 10개)")
        if user01_mail_user:
            sent_mails = db.query(Mail).filter(
                Mail.sender_uuid == user01_mail_user.user_uuid
            ).order_by(Mail.sent_at.desc()).limit(10).all()
            
            if sent_mails:
                print(f"✅ user01이 발송한 메일 {len(sent_mails)}개 발견:")
                for i, mail in enumerate(sent_mails, 1):
                    print(f"   {i}. 메일 ID: {mail.mail_uuid}")
                    print(f"      제목: {mail.subject}")
                    print(f"      발송 시간: {mail.sent_at}")
                    print(f"      상태: {mail.status}")
                    print(f"      조직 ID: {mail.org_id}")
                    
                    # 수신자 정보 조회
                    recipients = db.query(MailRecipient).filter(
                        MailRecipient.mail_uuid == mail.mail_uuid
                    ).all()
                    if recipients:
                        print(f"      수신자:")
                        for recipient in recipients:
                            print(f"        - {recipient.recipient_email} ({recipient.recipient_type})")
                    print()
            else:
                print("❌ user01이 발송한 메일이 없습니다.")
        
        # 4. admin이 수신한 메일 조회 (최근 10개)
        print("\n4️⃣ admin이 수신한 메일 조회 (최근 10개)")
        admin_received_mails = db.query(MailRecipient).filter(
            MailRecipient.recipient_email == "admin@skyboot.mail"
        ).order_by(MailRecipient.id.desc()).limit(10).all()
        
        if admin_received_mails:
            print(f"✅ admin이 수신한 메일 {len(admin_received_mails)}개 발견:")
            for i, recipient in enumerate(admin_received_mails, 1):
                # 메일 정보 조회
                mail = db.query(Mail).filter(Mail.mail_uuid == recipient.mail_uuid).first()
                if mail:
                    print(f"   {i}. 메일 ID: {mail.mail_uuid}")
                    print(f"      제목: {mail.subject}")
                    print(f"      발송 시간: {mail.sent_at}")
                    print(f"      상태: {mail.status}")
                    print(f"      수신 타입: {recipient.recipient_type}")
                    
                    # 발송자 정보 조회
                    sender_mail_user = db.query(MailUser).filter(
                        MailUser.user_uuid == mail.sender_uuid
                    ).first()
                    if sender_mail_user:
                        sender_user = db.query(User).filter(
                            User.user_id == sender_mail_user.user_id
                        ).first()
                        if sender_user:
                            print(f"      발송자: {sender_user.email}")
                    print()
        else:
            print("❌ admin이 수신한 메일이 없습니다.")
        
        # 5. admin의 INBOX 폴더 메일 조회
        print("\n5️⃣ admin의 INBOX 폴더 메일 조회")
        if admin_mail_user:
            # admin의 INBOX 폴더 찾기
            inbox_folder = db.query(MailFolder).filter(
                MailFolder.user_uuid == admin_mail_user.user_uuid,
                MailFolder.folder_type == "inbox"
            ).first()
            
            if inbox_folder:
                print(f"✅ admin INBOX 폴더 발견: {inbox_folder.name}")
                
                # INBOX에 할당된 메일 조회
                inbox_mails = db.query(MailInFolder).filter(
                    MailInFolder.folder_uuid == inbox_folder.folder_uuid
                ).order_by(MailInFolder.id.desc()).limit(10).all()
                
                if inbox_mails:
                    print(f"✅ INBOX에 할당된 메일 {len(inbox_mails)}개:")
                    for i, mail_in_folder in enumerate(inbox_mails, 1):
                        # 메일 정보 조회
                        mail = db.query(Mail).filter(
                            Mail.mail_uuid == mail_in_folder.mail_uuid
                        ).first()
                        if mail:
                            print(f"   {i}. 메일 ID: {mail.mail_uuid}")
                            print(f"      제목: {mail.subject}")
                            print(f"      발송 시간: {mail.sent_at}")
                            print(f"      읽음 상태: {'읽음' if mail_in_folder.is_read else '읽지 않음'}")
                            
                            # 발송자 정보 조회
                            sender_mail_user = db.query(MailUser).filter(
                                MailUser.user_uuid == mail.sender_uuid
                            ).first()
                            if sender_mail_user:
                                sender_user = db.query(User).filter(
                                    User.user_id == sender_mail_user.user_id
                                ).first()
                                if sender_user:
                                    print(f"      발송자: {sender_user.email}")
                            print()
                else:
                    print("❌ INBOX에 할당된 메일이 없습니다.")
            else:
                print("❌ admin의 INBOX 폴더를 찾을 수 없습니다.")
        
        # 6. 최근 발송된 메일 중 user01 -> admin 메일 찾기
        print("\n6️⃣ 최근 user01 -> admin 메일 찾기")
        if user01_mail_user and admin:
            recent_user01_to_admin = db.query(Mail).join(
                MailRecipient, Mail.mail_uuid == MailRecipient.mail_uuid
            ).filter(
                Mail.sender_uuid == user01_mail_user.user_uuid,
                MailRecipient.recipient_email == "admin@skyboot.mail"
            ).order_by(Mail.sent_at.desc()).limit(5).all()
            
            if recent_user01_to_admin:
                print(f"✅ user01 -> admin 메일 {len(recent_user01_to_admin)}개 발견:")
                for i, mail in enumerate(recent_user01_to_admin, 1):
                    print(f"   {i}. 메일 ID: {mail.mail_uuid}")
                    print(f"      제목: {mail.subject}")
                    print(f"      발송 시간: {mail.sent_at}")
                    print(f"      상태: {mail.status}")
                    
                    # admin의 INBOX에 할당되었는지 확인
                    if inbox_folder:
                        in_inbox = db.query(MailInFolder).filter(
                            MailInFolder.mail_uuid == mail.mail_uuid,
                            MailInFolder.folder_uuid == inbox_folder.folder_uuid
                        ).first()
                        print(f"      INBOX 할당: {'예' if in_inbox else '아니오'}")
                        if in_inbox:
                            print(f"      읽음 상태: {'읽음' if in_inbox.is_read else '읽지 않음'}")
                    print()
            else:
                print("❌ user01 -> admin 메일을 찾을 수 없습니다.")
        
        print("=" * 60)
        print("✅ 메일 데이터 조회 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()