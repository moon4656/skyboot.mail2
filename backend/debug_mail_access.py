#!/usr/bin/env python3
"""
메일 읽기 권한 문제 디버깅 스크립트
403 Access denied 오류 원인 분석
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
from app.model.mail_model import MailUser, Mail, MailRecipient, MailInFolder

def main():
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔍 메일 읽기 권한 문제 디버깅")
        print("=" * 50)
        
        # 1. user01 정보 확인
        user01 = db.query(User).filter(User.email == "user01@skyboot.com").first()
        if not user01:
            print("❌ user01@skyboot.com 사용자를 찾을 수 없습니다")
            return
        
        print(f"✅ 사용자 정보:")
        print(f"   - ID: {user01.id}")
        print(f"   - UUID: {user01.user_uuid}")
        print(f"   - Email: {user01.email}")
        print(f"   - Organization ID: {user01.organization_id}")
        
        # 2. 조직 정보 확인
        org = db.query(Organization).filter(Organization.id == user01.organization_id).first()
        if org:
            print(f"✅ 조직 정보:")
            print(f"   - ID: {org.id}")
            print(f"   - Name: {org.name}")
            print(f"   - Domain: {org.domain}")
        
        # 3. MailUser 확인
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == user01.user_uuid,
            MailUser.org_id == str(user01.organization_id)
        ).first()
        
        if not mail_user:
            print("❌ user01의 MailUser 엔트리를 찾을 수 없습니다")
            print("   이것이 403 오류의 주요 원인일 수 있습니다")
            
            # MailUser 생성 제안
            print("\n💡 해결 방법:")
            print("   POST /api/v1/mail/setup-mail-account 엔드포인트를 호출하여")
            print("   MailUser와 기본 폴더를 생성하세요")
            return
        else:
            print(f"✅ MailUser 정보:")
            print(f"   - User UUID: {mail_user.user_uuid}")
            print(f"   - Email: {mail_user.email}")
            print(f"   - Org ID: {mail_user.org_id}")
            print(f"   - Is Active: {mail_user.is_active}")
        
        # 4. 문제의 메일 확인 (20251030_152652_2e376deddacc)
        mail_uuid = "20251030_152652_2e376deddacc"
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == str(user01.organization_id)
        ).first()
        
        if not mail:
            print(f"❌ 메일 {mail_uuid}을 찾을 수 없습니다")
            return
        
        print(f"\n✅ 메일 정보:")
        print(f"   - UUID: {mail.mail_uuid}")
        print(f"   - Subject: {mail.subject}")
        print(f"   - Sender UUID: {mail.sender_uuid}")
        print(f"   - Sender Email: {mail.sender_email}")
        print(f"   - Org ID: {mail.org_id}")
        
        # 5. 권한 확인
        print(f"\n🔒 권한 확인:")
        
        # 발송자인지 확인
        is_sender = mail.sender_uuid == mail_user.user_uuid
        print(f"   - 발송자 여부: {is_sender}")
        if is_sender:
            print(f"     (메일 발송자 UUID: {mail.sender_uuid})")
            print(f"     (사용자 UUID: {mail_user.user_uuid})")
        
        # 수신자인지 확인
        recipient = db.query(MailRecipient).filter(
            MailRecipient.mail_uuid == mail.mail_uuid,
            MailRecipient.recipient_uuid == mail_user.user_uuid
        ).first()
        
        is_recipient = recipient is not None
        print(f"   - 수신자 여부: {is_recipient}")
        
        if recipient:
            print(f"     (수신자 UUID: {recipient.recipient_uuid})")
            print(f"     (수신자 Email: {recipient.recipient_email})")
            print(f"     (수신자 타입: {recipient.recipient_type})")
        
        # 6. 모든 수신자 목록 확인
        all_recipients = db.query(MailRecipient).filter(
            MailRecipient.mail_uuid == mail.mail_uuid
        ).all()
        
        print(f"\n📧 모든 수신자 목록:")
        for i, r in enumerate(all_recipients, 1):
            print(f"   {i}. {r.recipient_email} ({r.recipient_type})")
            print(f"      UUID: {r.recipient_uuid}")
        
        # 7. MailInFolder 확인
        mail_in_folder = db.query(MailInFolder).filter(
            MailInFolder.mail_uuid == mail.mail_uuid,
            MailInFolder.user_uuid == mail_user.user_uuid
        ).first()
        
        print(f"\n📁 MailInFolder 정보:")
        if mail_in_folder:
            print(f"   - 폴더 타입: {mail_in_folder.folder_type}")
            print(f"   - 읽음 상태: {mail_in_folder.is_read}")
            print(f"   - 읽은 시간: {mail_in_folder.read_at}")
        else:
            print("   ❌ MailInFolder 레코드를 찾을 수 없습니다")
        
        # 8. 결론
        print(f"\n📊 권한 분석 결과:")
        has_access = is_sender or is_recipient
        print(f"   - 접근 권한: {'✅ 있음' if has_access else '❌ 없음'}")
        
        if not has_access:
            print(f"\n❌ 403 오류 원인:")
            print(f"   user01이 해당 메일의 발송자도 수신자도 아닙니다")
            print(f"   - 발송자 UUID: {mail.sender_uuid}")
            print(f"   - 사용자 UUID: {mail_user.user_uuid}")
            print(f"   - 수신자 목록에 user01 없음")
        else:
            print(f"✅ 권한은 정상입니다. 다른 원인을 확인해야 합니다")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()