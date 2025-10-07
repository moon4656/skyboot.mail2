#!/usr/bin/env python3
"""
특정 메일 UUID 디버그 스크립트
"""

import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import Mail, MailUser, MailRecipient

def debug_mail_uuid(mail_uuid: str):
    """특정 메일 UUID의 상세 정보를 확인합니다."""
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print(f"🔍 메일 UUID 디버그: {mail_uuid}")
        print("=" * 80)
        
        # 1. 메일 테이블에서 검색
        print("1️⃣ Mail 테이블에서 검색...")
        mail = db.query(Mail).filter(Mail.mail_uuid == mail_uuid).first()
        
        if mail:
            print(f"✅ 메일 발견!")
            print(f"   - 메일 UUID: {mail.mail_uuid}")
            print(f"   - 제목: {mail.subject}")
            print(f"   - 발송자 UUID: {mail.sender_uuid}")
            print(f"   - 조직 ID: {mail.org_id}")
            print(f"   - 상태: {mail.status}")
            print(f"   - 생성 시간: {mail.created_at}")
            print(f"   - 발송 시간: {mail.sent_at}")
            
            # 2. 발송자 정보 확인
            print("\n2️⃣ 발송자 정보 확인...")
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            if sender:
                print(f"✅ 발송자 발견!")
                print(f"   - 이메일: {sender.email}")
                print(f"   - 표시 이름: {sender.display_name}")
                print(f"   - 조직 ID: {sender.org_id}")
                print(f"   - 활성 상태: {sender.is_active}")
            else:
                print("❌ 발송자를 찾을 수 없습니다.")
            
            # 3. 수신자 정보 확인
            print("\n3️⃣ 수신자 정보 확인...")
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail_uuid).all()
            if recipients:
                print(f"✅ {len(recipients)}명의 수신자 발견!")
                for i, recipient in enumerate(recipients, 1):
                    print(f"   {i}. 이메일: {recipient.recipient_email}")
                    print(f"      타입: {recipient.recipient_type}")
                    print(f"      수신자 UUID: {recipient.recipient_uuid}")
            else:
                print("❌ 수신자를 찾을 수 없습니다.")
            
            # 4. 조직별 사용자 확인
            print("\n4️⃣ 조직별 사용자 확인...")
            org_users = db.query(MailUser).filter(MailUser.org_id == mail.org_id).all()
            print(f"📊 조직 {mail.org_id}의 사용자 수: {len(org_users)}")
            for user in org_users:
                print(f"   - {user.email} (UUID: {user.user_uuid}, 활성: {user.is_active})")
                
        else:
            print("❌ 해당 UUID의 메일을 찾을 수 없습니다.")
            
            # 비슷한 UUID 패턴 검색
            print("\n🔍 비슷한 UUID 패턴 검색...")
            similar_mails = db.query(Mail).filter(
                Mail.mail_uuid.like(f"%{mail_uuid[:10]}%")
            ).limit(5).all()
            
            if similar_mails:
                print(f"📋 비슷한 패턴의 메일 {len(similar_mails)}개 발견:")
                for mail in similar_mails:
                    print(f"   - {mail.mail_uuid} | {mail.subject} | {mail.created_at}")
            else:
                print("❌ 비슷한 패턴의 메일도 없습니다.")
        
        # 5. 전체 메일 통계
        print("\n5️⃣ 전체 메일 통계...")
        total_mails = db.query(Mail).count()
        print(f"📊 전체 메일 수: {total_mails}")
        
        # 최근 메일 5개
        recent_mails = db.query(Mail).order_by(Mail.created_at.desc()).limit(5).all()
        print(f"📧 최근 메일 5개:")
        for mail in recent_mails:
            print(f"   - {mail.mail_uuid} | {mail.subject} | {mail.created_at}")
            
    except Exception as e:
        print(f"❌ 디버그 중 오류: {str(e)}")
    finally:
        db.close()

def main():
    """메인 함수"""
    # 로그에서 확인된 메일 UUID
    mail_uuid = "20251005_001818_0500f18ee17c"
    
    debug_mail_uuid(mail_uuid)

if __name__ == "__main__":
    main()