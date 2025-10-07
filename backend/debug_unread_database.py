#!/usr/bin/env python3
"""
데이터베이스에서 직접 읽지 않은 메일 상태 확인

SkyBoot Mail SaaS 시스템의 읽지 않은 메일 데이터를 직접 확인합니다.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import SaaSSettings
from datetime import datetime

def get_db_session():
    """데이터베이스 세션 생성"""
    settings = SaaSSettings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_user01_mail_data():
    """user01의 메일 데이터 확인"""
    print(f"\n🔍 user01의 메일 데이터 확인")
    print("=" * 60)
    
    db = get_db_session()
    
    try:
        # 1. user01의 기본 정보 확인
        print(f"\n1️⃣ user01 기본 정보 확인")
        print("-" * 40)
        
        user_result = db.execute(text("""
            SELECT user_uuid, email, org_id 
            FROM users 
            WHERE user_id = 'user01'
        """))
        user_data = user_result.fetchone()
        
        if user_data:
            user_uuid, email, org_id = user_data
            print(f"✅ user01 정보:")
            print(f"   UUID: {user_uuid}")
            print(f"   Email: {email}")
            print(f"   Org ID: {org_id}")
        else:
            print(f"❌ user01을 찾을 수 없습니다.")
            return
        
        # 2. mail_users 테이블에서 user01 확인
        print(f"\n2️⃣ mail_users 테이블에서 user01 확인")
        print("-" * 40)
        
        mail_user_result = db.execute(text("""
            SELECT user_uuid, email, org_id, is_active
            FROM mail_users 
            WHERE user_uuid = :user_uuid
        """), {"user_uuid": user_uuid})
        mail_user_data = mail_user_result.fetchone()
        
        if mail_user_data:
            print(f"✅ mail_users에서 user01 정보:")
            print(f"   UUID: {mail_user_data[0]}")
            print(f"   Email: {mail_user_data[1]}")
            print(f"   Org ID: {mail_user_data[2]}")
            print(f"   Active: {mail_user_data[3]}")
        else:
            print(f"❌ mail_users에서 user01을 찾을 수 없습니다.")
            return
        
        # 3. user01의 받은편지함 폴더 확인
        print(f"\n3️⃣ user01의 받은편지함 폴더 확인")
        print("-" * 40)
        
        folder_result = db.execute(text("""
            SELECT folder_uuid, name, folder_type, org_id
            FROM mail_folders 
            WHERE user_uuid = :user_uuid AND folder_type = 'inbox'
        """), {"user_uuid": user_uuid})
        folder_data = folder_result.fetchone()
        
        if folder_data:
            folder_uuid, folder_name, folder_type, folder_org_id = folder_data
            print(f"✅ 받은편지함 폴더:")
            print(f"   UUID: {folder_uuid}")
            print(f"   Name: {folder_name}")
            print(f"   Type: {folder_type}")
            print(f"   Org ID: {folder_org_id}")
        else:
            print(f"❌ 받은편지함 폴더를 찾을 수 없습니다.")
            return
        
        # 4. 받은편지함의 모든 메일 확인
        print(f"\n4️⃣ 받은편지함의 모든 메일 확인")
        print("-" * 40)
        
        all_mails_result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                m.org_id as mail_org_id,
                mif.is_read,
                mif.user_uuid as mif_user_uuid,
                mif.folder_uuid as mif_folder_uuid
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            WHERE mif.folder_uuid = :folder_uuid
            ORDER BY m.created_at DESC
        """), {"folder_uuid": folder_uuid})
        all_mails = all_mails_result.fetchall()
        
        print(f"📧 받은편지함 총 메일 수: {len(all_mails)}개")
        
        if all_mails:
            print(f"\n📋 받은편지함 메일 목록:")
            for i, mail in enumerate(all_mails, 1):
                mail_uuid = str(mail[0])[:8]
                subject = mail[1] or "No Subject"
                created_at = mail[2]
                mail_org_id = mail[3]
                is_read = mail[4]
                mif_user_uuid = mail[5]
                mif_folder_uuid = mail[6]
                
                print(f"   {i}. {subject}")
                print(f"      Mail UUID: {mail_uuid}...")
                print(f"      Created: {created_at}")
                print(f"      Mail Org ID: {mail_org_id}")
                print(f"      Is Read: {is_read}")
                print(f"      MIF User UUID: {str(mif_user_uuid)[:8]}...")
                print(f"      MIF Folder UUID: {str(mif_folder_uuid)[:8]}...")
                print()
        
        # 5. 읽지 않은 메일만 확인
        print(f"\n5️⃣ 읽지 않은 메일만 확인")
        print("-" * 40)
        
        unread_mails_result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                m.org_id as mail_org_id,
                mif.is_read
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            WHERE mif.folder_uuid = :folder_uuid
            AND mif.is_read = false
            ORDER BY m.created_at DESC
        """), {"folder_uuid": folder_uuid})
        unread_mails = unread_mails_result.fetchall()
        
        print(f"📧 읽지 않은 메일 수: {len(unread_mails)}개")
        
        if unread_mails:
            print(f"\n📋 읽지 않은 메일 목록:")
            for i, mail in enumerate(unread_mails, 1):
                mail_uuid = str(mail[0])[:8]
                subject = mail[1] or "No Subject"
                created_at = mail[2]
                mail_org_id = mail[3]
                is_read = mail[4]
                
                print(f"   {i}. {subject}")
                print(f"      Mail UUID: {mail_uuid}...")
                print(f"      Created: {created_at}")
                print(f"      Mail Org ID: {mail_org_id}")
                print(f"      Is Read: {is_read}")
                print()
        
        # 6. 조직별 필터링 확인
        print(f"\n6️⃣ 조직별 필터링 확인")
        print("-" * 40)
        
        org_filtered_result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.org_id as mail_org_id,
                mif.is_read
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            WHERE mif.folder_uuid = :folder_uuid
            AND mif.is_read = false
            AND m.org_id = :org_id
            ORDER BY m.created_at DESC
        """), {"folder_uuid": folder_uuid, "org_id": org_id})
        org_filtered_mails = org_filtered_result.fetchall()
        
        print(f"📧 조직별 필터링된 읽지 않은 메일 수: {len(org_filtered_mails)}개")
        print(f"   (조직 ID: {org_id})")
        
        if org_filtered_mails:
            print(f"\n📋 조직별 필터링된 읽지 않은 메일 목록:")
            for i, mail in enumerate(org_filtered_mails, 1):
                mail_uuid = str(mail[0])[:8]
                subject = mail[1] or "No Subject"
                mail_org_id = mail[2]
                is_read = mail[3]
                
                print(f"   {i}. {subject}")
                print(f"      Mail UUID: {mail_uuid}...")
                print(f"      Mail Org ID: {mail_org_id}")
                print(f"      Is Read: {is_read}")
                print()
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {e}")
    finally:
        db.close()

def main():
    """메인 함수"""
    print("🔍 읽지 않은 메일 데이터베이스 직접 확인")
    print("=" * 60)
    print(f"시작 시간: {datetime.now()}")
    
    check_user01_mail_data()
    
    print(f"\n🏁 확인 완료")
    print("=" * 60)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()