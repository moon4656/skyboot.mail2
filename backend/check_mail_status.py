#!/usr/bin/env python3
"""
메일 발송 상태 확인 스크립트

데이터베이스에 저장된 메일 정보를 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.mail_model import Mail, MailRecipient, MailUser
from app.model.user_model import User
from app.model.organization_model import Organization
from datetime import datetime

def main():
    """메인 함수"""
    print("=" * 60)
    print("📧 메일 발송 상태 확인")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 최근 메일 조회 (최근 10개)
        mails = db.query(Mail).order_by(desc(Mail.created_at)).limit(10).all()
        
        print(f"📊 최근 {len(mails)}개의 메일이 있습니다.")
        print()
        
        for i, mail in enumerate(mails, 1):
            # 발송자 정보 조회
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보 조회
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            recipient_emails = [r.recipient_email for r in recipients]
            
            print(f"{i}. 메일 정보:")
            print(f"   - 메일 UUID: {mail.mail_uuid}")
            print(f"   - 제목: {mail.subject}")
            print(f"   - 발송자: {sender_email}")
            print(f"   - 수신자: {', '.join(recipient_emails)}")
            print(f"   - 상태: {mail.status}")
            print(f"   - 우선순위: {mail.priority}")
            print(f"   - 임시보관함: {'예' if mail.is_draft else '아니오'}")
            print(f"   - 생성일: {mail.created_at}")
            print(f"   - 발송일: {mail.sent_at if mail.sent_at else '미발송'}")
            print(f"   - 조직 ID: {mail.org_id}")
            print()
        
        # 메일 사용자 정보 확인
        print("📋 메일 사용자 정보:")
        print("-" * 30)
        mail_users = db.query(MailUser).all()
        for mail_user in mail_users:
            print(f"   - {mail_user.email} (UUID: {mail_user.user_uuid}, 조직: {mail_user.org_id})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return
    
    print()
    print("=" * 60)
    print("✅ 메일 상태 확인 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()