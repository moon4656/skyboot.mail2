#!/usr/bin/env python3
"""
user01 계정의 메일 데이터 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.mail_model import MailUser
from app.model.mail_model import Mail, MailFolder, MailInFolder
from app.model.organization_model import Organization

def main():
    print("🔍 user01 계정 메일 데이터 확인 시작")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. user01 계정 정보 확인
        print("\n📋 1. user01 계정 정보 확인")
        user01 = db.query(User).filter(User.user_id == "user01").first()
        if not user01:
            print("❌ user01 계정을 찾을 수 없습니다.")
            return
        
        print(f"✅ user01 계정 발견:")
        print(f"   - ID: {user01.user_id}")
        print(f"   - UUID: {user01.user_uuid}")
        print(f"   - 이메일: {user01.email}")
        print(f"   - 조직 ID: {user01.org_id}")
        print(f"   - 활성화: {user01.is_active}")
        print(f"   - 생성일: {user01.created_at}")
        
        # 2. 조직 정보 확인
        print(f"\n🏢 2. 조직 정보 확인")
        org = db.query(Organization).filter(Organization.org_id == user01.org_id).first()
        if org:
            print(f"✅ 조직 정보:")
            print(f"   - ID: {org.org_id}")
            print(f"   - 이름: {org.name}")
            print(f"   - 도메인: {org.domain}")
            print(f"   - 활성화: {org.is_active}")
        else:
            print("❌ 조직 정보를 찾을 수 없습니다.")
        
        # 3. MailUser 정보 확인
        print(f"\n📧 3. MailUser 정보 확인")
        mail_user = db.query(MailUser).filter(MailUser.user_id == user01.user_id).first()
        if mail_user:
            print(f"✅ MailUser 정보:")
            print(f"   - ID: {mail_user.user_id}")
            print(f"   - UUID: {mail_user.user_uuid}")
            print(f"   - 이메일: {mail_user.email}")
            print(f"   - 조직 ID: {mail_user.org_id}")
            print(f"   - 활성화: {mail_user.is_active}")
        else:
            print("❌ MailUser 정보를 찾을 수 없습니다.")
        
        # 4. user01과 관련된 모든 메일 확인
        print(f"\n📬 4. user01과 관련된 메일 확인")
        
        # 발송한 메일
        sent_mails = db.query(Mail).filter(Mail.sender_uuid == user01.user_uuid).all()
        print(f"📤 발송한 메일: {len(sent_mails)}개")
        for mail in sent_mails[:5]:  # 최근 5개만 표시
            print(f"   - {mail.mail_uuid}: {mail.subject} ({mail.sent_at})")
        
        # 수신한 메일 (recipients 테이블에서 확인)
        received_query = text("""
            SELECT m.mail_uuid, m.subject, m.sent_at, mr.recipient_type
            FROM mails m
            JOIN mail_recipients mr ON m.mail_uuid = mr.mail_uuid
            WHERE mr.recipient_email = :email
            ORDER BY m.sent_at DESC
            LIMIT 10
        """)
        received_mails = db.execute(received_query, {"email": user01.email}).fetchall()
        print(f"📥 수신한 메일: {len(received_mails)}개")
        for mail in received_mails:
            print(f"   - {mail.mail_uuid}: {mail.subject} ({mail.recipient_type})")
        
        # 5. 메일 폴더 확인
        print(f"\n📁 5. user01의 메일 폴더 확인")
        if mail_user:
            folders = db.query(MailFolder).filter(MailFolder.user_id == mail_user.id).all()
            print(f"📂 총 폴더 수: {len(folders)}개")
            for folder in folders:
                print(f"   - {folder.folder_uuid}: {folder.name} ({folder.folder_type})")
                
                # 각 폴더의 메일 할당 확인
                assignments = db.query(MailInFolder).filter(
                    MailInFolder.folder_uuid == folder.folder_uuid
                ).count()
                print(f"     └─ 할당된 메일: {assignments}개")
        
        # 6. 받은편지함 폴더의 메일 할당 상세 확인
        print(f"\n📥 6. 받은편지함 폴더 상세 확인")
        if mail_user:
            inbox_folder = db.query(MailFolder).filter(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == "inbox"
            ).first()
            
            if inbox_folder:
                print(f"✅ 받은편지함 폴더 발견:")
                print(f"   - UUID: {inbox_folder.folder_uuid}")
                print(f"   - 이름: {inbox_folder.name}")
                
                # 할당된 메일 상세 조회
                assignment_query = text("""
                    SELECT mif.mail_uuid, m.subject, m.sent_at, mif.created_at
                    FROM mail_in_folders mif
                    JOIN mails m ON mif.mail_uuid = m.mail_uuid
                    WHERE mif.folder_uuid = :folder_uuid
                    ORDER BY mif.created_at DESC
                    LIMIT 10
                """)
                assignments = db.execute(assignment_query, {"folder_uuid": inbox_folder.folder_uuid}).fetchall()
                print(f"📧 받은편지함에 할당된 메일: {len(assignments)}개")
                for assignment in assignments:
                    print(f"   - {assignment.mail_uuid}: {assignment.subject} (할당: {assignment.created_at})")
            else:
                print("❌ 받은편지함 폴더를 찾을 수 없습니다.")
        
        # 7. 최근 메일 발송 로그 확인
        print(f"\n📊 7. 최근 메일 활동 확인")
        recent_mails_query = text("""
            SELECT mail_uuid, subject, sent_at, status
            FROM mails
            WHERE org_id = :org_id
            ORDER BY sent_at DESC
            LIMIT 5
        """)
        recent_mails = db.execute(recent_mails_query, {"org_id": org.org_id if org else None}).fetchall()
        print(f"🕒 최근 조직 메일 활동: {len(recent_mails)}개")
        for mail in recent_mails:
            print(f"   - {mail.mail_uuid}: {mail.subject} ({mail.sent_at}) - {mail.status}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n✅ user01 메일 데이터 확인 완료")

if __name__ == "__main__":
    main()