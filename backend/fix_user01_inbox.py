#!/usr/bin/env python3
"""
user01 받은편지함 할당 수정 스크립트

user01의 수신 메일을 받은편지함 폴더에 할당합니다.
"""

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import Mail, MailRecipient, MailFolder, MailInFolder, FolderType
from sqlalchemy.orm import Session
from sqlalchemy import text

def fix_user01_inbox():
    """user01의 받은편지함 할당 문제 수정"""
    print("📧 user01 받은편지함 할당 수정 시작")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # 1. user01 정보 조회
        user01 = db.query(User).filter(User.user_id == "user01").first()
        if not user01:
            print("❌ user01을 찾을 수 없습니다.")
            return
        
        print(f"👤 사용자: {user01.user_id} ({user01.email})")
        print(f"🏢 조직 ID: {user01.org_id}")
        
        # 2. user01의 받은편지함 폴더 찾기
        inbox_folder = db.query(MailFolder).filter(
            MailFolder.user_uuid == user01.user_uuid,
            MailFolder.folder_type == FolderType.INBOX
        ).first()
        
        if not inbox_folder:
            print("❌ user01의 받은편지함 폴더를 찾을 수 없습니다.")
            return
        
        print(f"📁 받은편지함 폴더: {inbox_folder.name} ({inbox_folder.folder_uuid})")
        
        # 3. user01이 수신한 메일 조회 (받은편지함에 할당되지 않은 것만)
        unassigned_mails_query = text("""
            SELECT DISTINCT m.mail_uuid, m.subject, m.sent_at
            FROM mails m
            JOIN mail_recipients mr ON m.mail_uuid = mr.mail_uuid
            WHERE mr.recipient_email = :email
            AND mr.recipient_type = 'to'
            AND m.mail_uuid NOT IN (
                SELECT mif.mail_uuid 
                FROM mail_in_folders mif 
                WHERE mif.folder_uuid = :folder_uuid
            )
            ORDER BY m.sent_at DESC
        """)
        
        unassigned_mails = db.execute(unassigned_mails_query, {
            "email": user01.email,
            "folder_uuid": inbox_folder.folder_uuid
        }).fetchall()
        
        print(f"📧 할당되지 않은 수신 메일: {len(unassigned_mails)}개")
        
        if not unassigned_mails:
            print("✅ 모든 수신 메일이 이미 받은편지함에 할당되어 있습니다.")
            return
        
        # 4. 메일을 받은편지함에 할당
        assigned_count = 0
        for mail in unassigned_mails:
            try:
                # 이미 할당되어 있는지 다시 한번 확인
                existing_assignment = db.query(MailInFolder).filter(
                    MailInFolder.mail_uuid == mail.mail_uuid,
                    MailInFolder.folder_uuid == inbox_folder.folder_uuid
                ).first()
                
                if existing_assignment:
                    print(f"⚠️ 이미 할당됨: {mail.mail_uuid}")
                    continue
                
                # 새로운 할당 생성
                mail_in_folder = MailInFolder(
                    mail_uuid=mail.mail_uuid,
                    folder_uuid=inbox_folder.folder_uuid,
                    user_uuid=user01.user_uuid
                )
                
                db.add(mail_in_folder)
                assigned_count += 1
                
                print(f"✅ 할당 완료: {mail.mail_uuid} - {mail.subject}")
                
            except Exception as e:
                print(f"❌ 할당 실패: {mail.mail_uuid} - {str(e)}")
                continue
        
        # 5. 변경사항 커밋
        if assigned_count > 0:
            db.commit()
            print(f"\n🎉 총 {assigned_count}개 메일을 받은편지함에 할당했습니다.")
        else:
            print("\n⚠️ 할당된 메일이 없습니다.")
        
        # 6. 할당 결과 확인
        assigned_mails_query = text("""
            SELECT COUNT(*) as count
            FROM mail_in_folders mif
            WHERE mif.folder_uuid = :folder_uuid
        """)
        
        assigned_count_result = db.execute(assigned_mails_query, {
            "folder_uuid": inbox_folder.folder_uuid
        }).fetchone()
        
        print(f"📊 받은편지함 총 메일 수: {assigned_count_result.count}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n✅ user01 받은편지함 할당 수정 완료")

if __name__ == "__main__":
    fix_user01_inbox()