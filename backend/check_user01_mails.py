#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
user01 사용자의 메일 데이터 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import Mail, MailUser, MailRecipient

def check_user01_mails():
    """user01 사용자의 메일 데이터를 확인합니다."""
    print("=" * 60)
    print("user01 사용자 메일 데이터 확인")
    print("=" * 60)
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # 1. user01 사용자 확인
        user = db.query(User).filter(User.user_id == "user01").first()
        if not user:
            print("❌ user01 사용자를 찾을 수 없습니다")
            return
            
        print(f"✅ 사용자 발견: {user.user_id} ({user.email})")
        print(f"   - UUID: {user.user_uuid}")
        print(f"   - 조직 ID: {user.org_id}")
        
        # 2. MailUser 확인
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == user.user_uuid
        ).first()
        
        if mail_user:
            print(f"✅ MailUser 발견: {mail_user.email}")
            print(f"   - 조직 ID: {mail_user.org_id}")
        else:
            print("❌ MailUser를 찾을 수 없습니다")
            
        # 3. 발송한 메일 확인 (sender_uuid 기준)
        sent_mails = db.query(Mail).filter(Mail.sender_uuid == user.user_uuid).all()
        print(f"📤 발송한 메일: {len(sent_mails)}개")
        
        for i, mail in enumerate(sent_mails[:5]):  # 최대 5개만 표시
            print(f"   {i+1}. {mail.mail_uuid} - {mail.subject} ({mail.sent_at})")
            
        # 4. 수신한 메일 확인 (recipients 테이블 기준)
        received_mails = db.query(Mail).join(MailRecipient).filter(
            MailRecipient.recipient_email == user.email
        ).all()
        print(f"📥 수신한 메일: {len(received_mails)}개")
        
        for i, mail in enumerate(received_mails[:5]):  # 최대 5개만 표시
            print(f"   {i+1}. {mail.mail_uuid} - {mail.subject} ({mail.sent_at})")
            
        # 5. 전체 메일 확인 (조직 기준)
        if user.org_id:
            org_mails = db.query(Mail).filter(
                Mail.org_id == user.org_id
            ).all()
            print(f"🏢 조직 전체 메일: {len(org_mails)}개")
            
        # 6. 백업 대상 메일 확인 (백업 로직과 동일)
        # 발송자이거나 수신자인 메일
        backup_mails = db.query(Mail).filter(
            (Mail.sender_uuid == user.user_uuid) |
            (Mail.mail_uuid.in_(
                db.query(MailRecipient.mail_uuid).filter(
                    MailRecipient.recipient_email == user.email
                )
            ))
        ).all()
        print(f"💾 백업 대상 메일: {len(backup_mails)}개")
        
        if len(backup_mails) > 0:
            print("백업 대상 메일 상세:")
            for i, mail in enumerate(backup_mails[:3]):  # 최대 3개만 표시
                recipients = db.query(MailRecipient).filter(
                    MailRecipient.mail_uuid == mail.mail_uuid
                ).all()
                recipient_emails = [r.recipient_email for r in recipients]
                print(f"   {i+1}. ID: {mail.mail_uuid}")
                print(f"      제목: {mail.subject}")
                print(f"      발송자 UUID: {mail.sender_uuid}")
                print(f"      수신자: {recipient_emails}")
                print(f"      발송 시간: {mail.sent_at}")
                print(f"      상태: {mail.status}")
                print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user01_mails()