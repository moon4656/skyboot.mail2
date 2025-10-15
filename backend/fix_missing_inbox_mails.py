#!/usr/bin/env python3
"""
누락된 메일들을 admin의 INBOX에 추가하는 스크립트
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.model.mail_model import Mail, MailRecipient, MailInFolder, MailFolder, MailUser
from app.model.user_model import User
from app.config import settings

def fix_missing_inbox_mails():
    """
    누락된 메일들을 admin의 INBOX에 추가
    """
    print("=" * 60)
    print("🔧 누락된 메일들을 admin INBOX에 추가")
    print("=" * 60)
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Admin 사용자 정보 조회
        print("1️⃣ Admin 사용자 정보 조회")
        print("-" * 30)
        
        admin_user = db.query(User).filter(User.email == "admin@skyboot.mail").first()
        if not admin_user:
            print("❌ Admin 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ Admin 사용자 발견: {admin_user.user_uuid}")
        
        # 2. Admin MailUser 정보 조회
        admin_mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == admin_user.user_uuid
        ).first()
        
        if not admin_mail_user:
            print("❌ Admin MailUser를 찾을 수 없습니다.")
            return
        
        print(f"✅ Admin MailUser 발견: {admin_mail_user.user_uuid}")
        
        # 3. Admin의 INBOX 폴더 조회
        print("\n2️⃣ Admin INBOX 폴더 조회")
        print("-" * 30)
        
        admin_inbox = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == admin_mail_user.user_uuid,
                MailFolder.folder_type == "inbox"
            )
        ).first()
        
        if not admin_inbox:
            print("❌ Admin INBOX 폴더를 찾을 수 없습니다.")
            return
        
        print(f"✅ Admin INBOX 폴더 발견: {admin_inbox.folder_uuid}")
        
        # 4. 누락된 메일 UUID 목록
        print("\n3️⃣ 누락된 메일들을 INBOX에 추가")
        print("-" * 30)
        
        missing_mail_uuids = [
            "20251015_205433_97594a81b93d",
            "20251015_211940_baf049f3cfd1", 
            "20251015_215948_7c1976b43c60"
        ]
        
        added_count = 0
        
        for mail_uuid in missing_mail_uuids:
            print(f"\n📧 처리 중: {mail_uuid}")
            
            # 메일이 존재하는지 확인
            mail = db.query(Mail).filter(Mail.mail_uuid == mail_uuid).first()
            if not mail:
                print(f"   ❌ 메일을 찾을 수 없음: {mail_uuid}")
                continue
            
            # 이미 INBOX에 할당되어 있는지 확인
            existing_relation = db.query(MailInFolder).filter(
                and_(
                    MailInFolder.mail_uuid == mail_uuid,
                    MailInFolder.folder_uuid == admin_inbox.folder_uuid,
                    MailInFolder.user_uuid == admin_mail_user.user_uuid
                )
            ).first()
            
            if existing_relation:
                print(f"   ⚠️ 이미 INBOX에 할당됨: {mail_uuid}")
                continue
            
            # INBOX에 메일 할당
            try:
                mail_in_folder = MailInFolder(
                    mail_uuid=mail_uuid,
                    folder_uuid=admin_inbox.folder_uuid,
                    user_uuid=admin_mail_user.user_uuid,
                    is_read=False  # 새 메일은 읽지 않음 상태
                )
                db.add(mail_in_folder)
                db.commit()
                
                print(f"   ✅ INBOX에 추가 완료: {mail_uuid}")
                print(f"      제목: {mail.subject}")
                print(f"      상태: {mail.status}")
                print(f"      발송일: {mail.sent_at}")
                added_count += 1
                
            except Exception as e:
                print(f"   ❌ INBOX 추가 실패: {mail_uuid} - {str(e)}")
                db.rollback()
        
        print(f"\n4️⃣ 작업 완료")
        print("-" * 30)
        print(f"📊 총 처리된 메일: {len(missing_mail_uuids)}개")
        print(f"✅ 성공적으로 추가된 메일: {added_count}개")
        
        # 5. 최종 확인
        print(f"\n5️⃣ 최종 확인")
        print("-" * 30)
        
        # INBOX에 할당된 총 메일 수 확인
        total_inbox_mails = db.query(MailInFolder).filter(
            MailInFolder.folder_uuid == admin_inbox.folder_uuid
        ).count()
        
        print(f"📊 Admin INBOX에 할당된 총 메일 수: {total_inbox_mails}개")
        
        # 수신자 테이블의 총 메일 수 확인
        total_recipient_mails = db.query(MailRecipient).filter(
            MailRecipient.recipient_email == "admin@skyboot.mail"
        ).count()
        
        print(f"📊 mail_recipients 테이블의 admin 수신 메일 수: {total_recipient_mails}개")
        
        if total_inbox_mails == total_recipient_mails:
            print("✅ 데이터 일치: INBOX와 수신자 테이블의 메일 수가 일치합니다!")
        else:
            print("⚠️ 데이터 불일치: INBOX와 수신자 테이블의 메일 수가 다릅니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        db.rollback()
    finally:
        db.close()
    
    print(f"\n⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    fix_missing_inbox_mails()