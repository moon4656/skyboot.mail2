#!/usr/bin/env python3
"""
MailFolder 테이블 상태 확인 및 수정 스크립트

읽지 않은 메일 조회 문제의 근본 원인인 MailFolder 테이블 문제를 해결합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_mail_folders():
    """MailFolder 테이블 상태 확인"""
    print("🔍 MailFolder 테이블 상태 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # 1. MailFolder 테이블 구조 확인
        print("📋 MailFolder 테이블 구조:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_folders' 
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 2. 전체 MailFolder 데이터 확인
        print(f"\n📋 MailFolder 데이터 확인:")
        result = db.execute(text("""
            SELECT folder_uuid, user_uuid, folder_type, name, org_id
            FROM mail_folders
            ORDER BY created_at DESC
            LIMIT 20;
        """))
        
        folders = result.fetchall()
        print(f"  총 {len(folders)}개의 폴더 발견:")
        for folder in folders:
            print(f"    - UUID: {folder[0]} | 사용자: {folder[1]} | 타입: {folder[2]} | 이름: {folder[3]} | 조직: {folder[4]}")
        
        # 3. user01의 폴더 확인
        print(f"\n📋 user01 사용자의 폴더 확인:")
        result = db.execute(text("""
            SELECT mf.folder_uuid, mf.folder_type, mf.name, mu.email
            FROM mail_folders mf
            LEFT JOIN mail_users mu ON mf.user_uuid = mu.user_uuid
            WHERE mu.email LIKE '%user01%'
            ORDER BY mf.created_at DESC;
        """))
        
        user_folders = result.fetchall()
        print(f"  user01의 폴더 {len(user_folders)}개:")
        for folder in user_folders:
            print(f"    - UUID: {folder[0]} | 타입: {folder[1]} | 이름: {folder[2]} | 사용자: {folder[3]}")
        
        # 4. mail_in_folders와 mail_folders 연결 상태 확인
        print(f"\n📋 mail_in_folders와 mail_folders 연결 상태:")
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_mail_in_folders,
                COUNT(mf.folder_uuid) as connected_to_folders,
                COUNT(*) - COUNT(mf.folder_uuid) as orphaned_mails
            FROM mail_in_folders mif
            LEFT JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid;
        """))
        
        connection_stats = result.fetchone()
        if connection_stats:
            print(f"    - 총 mail_in_folders: {connection_stats[0]}개")
            print(f"    - mail_folders와 연결된 것: {connection_stats[1]}개")
            print(f"    - 연결되지 않은 것 (고아 메일): {connection_stats[2]}개")
        
        # 5. user01의 mail_in_folders 상태 확인
        print(f"\n📋 user01의 mail_in_folders 상태:")
        result = db.execute(text("""
            SELECT 
                mif.mail_uuid,
                mif.folder_uuid,
                mif.is_read,
                m.subject,
                mu.email
            FROM mail_in_folders mif
            LEFT JOIN mails m ON mif.mail_uuid = m.mail_uuid
            LEFT JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            WHERE mu.email LIKE '%user01%'
            ORDER BY mif.created_at DESC
            LIMIT 10;
        """))
        
        user_mail_folders = result.fetchall()
        print(f"  user01의 mail_in_folders {len(user_mail_folders)}개:")
        for mail_folder in user_mail_folders:
            print(f"    - 메일: {mail_folder[3]} | 폴더UUID: {mail_folder[1]} | 읽음: {mail_folder[2]}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def create_missing_folders():
    """누락된 기본 폴더들을 생성"""
    print("\n🔧 누락된 기본 폴더 생성")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # user01 사용자 정보 조회
        result = db.execute(text("""
            SELECT user_uuid, email, org_id
            FROM mail_users 
            WHERE email LIKE '%user01%'
            LIMIT 1;
        """))
        
        user = result.fetchone()
        if not user:
            print("❌ user01 사용자를 찾을 수 없습니다.")
            return
        
        user_uuid = user[0]
        email = user[1]
        org_id = user[2]
        
        print(f"📧 사용자 정보: {email} (UUID: {user_uuid}, 조직: {org_id})")
        
        # 기본 폴더 타입들 (실제 enum 값 사용)
        folder_types = [
            ('INBOX', '받은편지함'),
            ('SENT', '보낸편지함'),
            ('DRAFTS', '임시보관함'),
            ('TRASH', '휴지통')
        ]
        
        for folder_type, folder_name in folder_types:
            # 폴더가 이미 존재하는지 확인
            result = db.execute(text("""
                SELECT folder_uuid FROM mail_folders
                WHERE user_uuid = :user_uuid AND folder_type = :folder_type
            """), {"user_uuid": user_uuid, "folder_type": folder_type})
            
            existing_folder = result.fetchone()
            
            if existing_folder:
                print(f"✅ {folder_name} 폴더가 이미 존재합니다: {existing_folder[0]}")
            else:
                # 새 폴더 UUID 생성
                import uuid
                folder_uuid = str(uuid.uuid4())
                
                # 폴더 생성
                db.execute(text("""
                    INSERT INTO mail_folders (folder_uuid, user_uuid, org_id, folder_type, name, created_at, updated_at, is_system)
                    VALUES (:folder_uuid, :user_uuid, :org_id, :folder_type, :folder_name, NOW(), NOW(), true)
                """), {
                    "folder_uuid": folder_uuid,
                    "user_uuid": user_uuid,
                    "org_id": org_id,
                    "folder_type": folder_type,
                    "folder_name": folder_name
                })
                
                print(f"✅ {folder_name} 폴더를 생성했습니다: {folder_uuid}")
        
        # 변경사항 커밋
        db.commit()
        
        # 고아 메일들을 받은편지함으로 이동
        print(f"\n📧 고아 메일들을 받은편지함으로 이동:")
        
        # 받은편지함 폴더 UUID 조회
        result = db.execute(text("""
            SELECT folder_uuid FROM mail_folders
            WHERE user_uuid = :user_uuid AND folder_type = 'INBOX'
        """), {"user_uuid": user_uuid})
        
        inbox_folder = result.fetchone()
        if inbox_folder:
            inbox_uuid = inbox_folder[0]
            
            # 고아 메일들 업데이트
            result = db.execute(text("""
                UPDATE mail_in_folders 
                SET folder_uuid = :inbox_uuid
                WHERE user_uuid = :user_uuid AND folder_uuid IS NULL
            """), {"inbox_uuid": inbox_uuid, "user_uuid": user_uuid})
            
            updated_count = result.rowcount
            print(f"✅ {updated_count}개의 고아 메일을 받은편지함으로 이동했습니다.")
            
            # 변경사항 커밋
            db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"❌ 폴더 생성 중 오류: {e}")
        db.rollback()

def main():
    """메인 함수"""
    print("🔍 MailFolder 테이블 진단 및 수정 시작")
    
    # 1. 현재 상태 확인
    check_mail_folders()
    
    # 2. 누락된 폴더 생성
    create_missing_folders()
    
    # 3. 수정 후 상태 재확인
    print("\n🔍 수정 후 상태 재확인")
    check_mail_folders()
    
    print("\n" + "=" * 60)
    print("🔍 MailFolder 테이블 진단 및 수정 완료")

if __name__ == "__main__":
    main()