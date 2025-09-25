#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트: MailUser.id 참조를 MailUser.user_id로 변경

이 스크립트는 다음 작업을 수행합니다:
1. MailFolder 테이블의 user_id 필드를 MailUser.id에서 MailUser.user_id로 업데이트
2. MailRecipient 테이블의 recipient_id 필드를 MailUser.id에서 MailUser.user_id로 업데이트  
3. Mail 테이블의 sender_uuid 필드를 MailUser.id에서 MailUser.user_id로 업데이트

실행 전 반드시 데이터베이스 백업을 수행하세요!
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def create_backup_tables(session):
    """
    백업 테이블을 생성합니다.
    """
    print("📦 백업 테이블 생성 중...")
    
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # MailFolder 백업
    session.execute(text(f"""
        CREATE TABLE mail_folders_backup_{backup_timestamp} AS 
        SELECT * FROM mail_folders;
    """))
    
    # MailRecipient 백업
    session.execute(text(f"""
        CREATE TABLE mail_recipients_backup_{backup_timestamp} AS 
        SELECT * FROM mail_recipients;
    """))
    
    # Mail 백업
    session.execute(text(f"""
        CREATE TABLE mails_backup_{backup_timestamp} AS 
        SELECT * FROM mails;
    """))
    
    session.commit()
    print(f"✅ 백업 테이블 생성 완료 (타임스탬프: {backup_timestamp})")
    return backup_timestamp

def update_mail_folder_user_ids(session):
    """
    MailFolder 테이블의 user_id를 MailUser.user_id로 업데이트
    """
    print("📁 MailFolder 테이블 업데이트 중...")
    
    # 1. 임시 컬럼 추가
    session.execute(text("""
        ALTER TABLE mail_folders 
        ADD COLUMN IF NOT EXISTS user_id_temp character varying;
    """))
    
    # 2. 임시 컬럼에 mail_users.user_id 값 설정
    result = session.execute(text("""
        UPDATE mail_folders 
        SET user_id_temp = mail_users.user_id
        FROM mail_users 
        WHERE mail_folders.user_id = mail_users.id
        AND mail_users.user_id IS NOT NULL;
    """))
    
    # 3. 기존 user_id 컬럼 삭제
    session.execute(text("""
        ALTER TABLE mail_folders DROP COLUMN user_id;
    """))
    
    # 4. 임시 컬럼을 user_id로 이름 변경
    session.execute(text("""
        ALTER TABLE mail_folders RENAME COLUMN user_id_temp TO user_id;
    """))
    
    # 5. NOT NULL 제약 조건 추가
    session.execute(text("""
        ALTER TABLE mail_folders ALTER COLUMN user_id SET NOT NULL;
    """))
    
    session.commit()
    updated_count = result.rowcount
    print(f"   ✅ {updated_count}개 레코드 업데이트 완료")
    
    return updated_count

def update_mail_recipient_user_ids(session):
    """
    MailRecipient 테이블의 recipient_id를 MailUser.user_id로 업데이트
    """
    print("👥 MailRecipient 테이블 업데이트 중...")
    
    # 1. 임시 컬럼 추가
    session.execute(text("""
        ALTER TABLE mail_recipients 
        ADD COLUMN IF NOT EXISTS recipient_id_temp character varying;
    """))
    
    # 2. 임시 컬럼에 mail_users.user_id 값 설정
    result = session.execute(text("""
        UPDATE mail_recipients 
        SET recipient_id_temp = mail_users.user_id
        FROM mail_users 
        WHERE mail_recipients.recipient_id = mail_users.id
        AND mail_users.user_id IS NOT NULL;
    """))
    
    # 3. 기존 recipient_id 컬럼 삭제
    session.execute(text("""
        ALTER TABLE mail_recipients DROP COLUMN recipient_id;
    """))
    
    # 4. 임시 컬럼을 recipient_id로 이름 변경
    session.execute(text("""
        ALTER TABLE mail_recipients RENAME COLUMN recipient_id_temp TO recipient_id;
    """))
    
    # 5. NOT NULL 제약 조건 추가
    session.execute(text("""
        ALTER TABLE mail_recipients ALTER COLUMN recipient_id SET NOT NULL;
    """))
    
    session.commit()
    updated_count = result.rowcount
    print(f"   ✅ {updated_count}개 레코드 업데이트 완료")
    
    return updated_count

def update_mail_sender_uuids(session):
    """
    Mail 테이블의 sender_uuid를 MailUser.user_id로 업데이트
    """
    print("📧 Mail 테이블 업데이트 중...")
    
    # 1. 임시 컬럼 추가
    session.execute(text("""
        ALTER TABLE mails 
        ADD COLUMN IF NOT EXISTS sender_uuid_temp character varying;
    """))
    
    # 2. 임시 컬럼에 mail_users.user_id 값 설정
    result = session.execute(text("""
        UPDATE mails 
        SET sender_uuid_temp = mail_users.user_id
        FROM mail_users 
        WHERE mails.sender_uuid = mail_users.id
        AND mail_users.user_id IS NOT NULL;
    """))
    
    # 3. 기존 sender_uuid 컬럼 삭제
    session.execute(text("""
        ALTER TABLE mails DROP COLUMN sender_uuid;
    """))
    
    # 4. 임시 컬럼을 sender_uuid로 이름 변경
    session.execute(text("""
        ALTER TABLE mails RENAME COLUMN sender_uuid_temp TO sender_uuid;
    """))
    
    # 5. NOT NULL 제약 조건 추가
    session.execute(text("""
        ALTER TABLE mails ALTER COLUMN sender_uuid SET NOT NULL;
    """))
    
    session.commit()
    updated_count = result.rowcount
    print(f"   ✅ {updated_count}개 레코드 업데이트 완료")
    
    return updated_count

def verify_migration(session):
    """
    마이그레이션 결과를 검증합니다.
    """
    print("🔍 마이그레이션 결과 검증 중...")
    
    # MailFolder에서 고아 레코드 확인
    orphaned_folders = session.execute(text("""
        SELECT COUNT(*) as count 
        FROM mail_folders mf 
        LEFT JOIN mail_users mu ON mf.user_id = mu.user_id 
        WHERE mu.user_id IS NULL;
    """)).fetchone()
    
    # MailRecipient에서 고아 레코드 확인
    orphaned_recipients = session.execute(text("""
        SELECT COUNT(*) as count 
        FROM mail_recipients mr 
        LEFT JOIN mail_users mu ON mr.recipient_id = mu.user_id 
        WHERE mu.user_id IS NULL;
    """)).fetchone()
    
    # Mail에서 고아 레코드 확인
    orphaned_mails = session.execute(text("""
        SELECT COUNT(*) as count 
        FROM mails m 
        LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_id 
        WHERE mu.user_id IS NULL;
    """)).fetchone()
    
    print(f"📊 검증 결과:")
    print(f"   - 고아 MailFolder 레코드: {orphaned_folders.count}개")
    print(f"   - 고아 MailRecipient 레코드: {orphaned_recipients.count}개")
    print(f"   - 고아 Mail 레코드: {orphaned_mails.count}개")
    
    if orphaned_folders.count == 0 and orphaned_recipients.count == 0 and orphaned_mails.count == 0:
        print("✅ 마이그레이션 검증 성공: 모든 참조가 올바르게 업데이트되었습니다.")
        return True
    else:
        print("⚠️ 마이그레이션 검증 실패: 일부 고아 레코드가 발견되었습니다.")
        return False

def rollback_migration(session, backup_timestamp):
    """
    마이그레이션을 롤백합니다.
    """
    print(f"🔄 마이그레이션 롤백 중... (백업 타임스탬프: {backup_timestamp})")
    
    try:
        # MailFolder 롤백
        session.execute(text(f"""
            DELETE FROM mail_folders;
            INSERT INTO mail_folders SELECT * FROM mail_folders_backup_{backup_timestamp};
        """))
        
        # MailRecipient 롤백
        session.execute(text(f"""
            DELETE FROM mail_recipients;
            INSERT INTO mail_recipients SELECT * FROM mail_recipients_backup_{backup_timestamp};
        """))
        
        # Mail 롤백
        session.execute(text(f"""
            DELETE FROM mails;
            INSERT INTO mails SELECT * FROM mails_backup_{backup_timestamp};
        """))
        
        session.commit()
        print("✅ 마이그레이션 롤백 완료")
        return True
    except Exception as e:
        print(f"❌ 롤백 실패: {e}")
        session.rollback()
        return False

def main():
    """
    메인 마이그레이션 함수
    """
    print("🚀 MailUser.id 참조 업데이트 마이그레이션 시작")
    print("=" * 60)
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    backup_timestamp = None
    
    try:
        # 1. 백업 테이블 생성
        backup_timestamp = create_backup_tables(session)
        
        # 2. 현재 상태 확인
        print("\n📊 마이그레이션 전 상태 확인:")
        mail_users = session.execute(text("SELECT COUNT(*) as count FROM mail_users")).fetchone()
        mail_folders = session.execute(text("SELECT COUNT(*) as count FROM mail_folders")).fetchone()
        mail_recipients = session.execute(text("SELECT COUNT(*) as count FROM mail_recipients")).fetchone()
        mails = session.execute(text("SELECT COUNT(*) as count FROM mails")).fetchone()
        
        print(f"   - MailUser: {mail_users.count}개")
        print(f"   - MailFolder: {mail_folders.count}개")
        print(f"   - MailRecipient: {mail_recipients.count}개")
        print(f"   - Mail: {mails.count}개")
        
        # 3. 마이그레이션 실행
        print("\n🔄 마이그레이션 실행:")
        folder_updates = update_mail_folder_user_ids(session)
        recipient_updates = update_mail_recipient_user_ids(session)
        mail_updates = update_mail_sender_uuids(session)
        
        # 4. 검증
        print("\n🔍 마이그레이션 검증:")
        if verify_migration(session):
            print("\n🎉 마이그레이션이 성공적으로 완료되었습니다!")
            print(f"📈 업데이트 요약:")
            print(f"   - MailFolder: {folder_updates}개 레코드 업데이트")
            print(f"   - MailRecipient: {recipient_updates}개 레코드 업데이트")
            print(f"   - Mail: {mail_updates}개 레코드 업데이트")
        else:
            print("\n⚠️ 마이그레이션 검증에 실패했습니다.")
            user_input = input("롤백을 수행하시겠습니까? (y/N): ")
            if user_input.lower() == 'y':
                rollback_migration(session, backup_timestamp)
            else:
                print("⚠️ 수동으로 데이터를 확인하고 필요시 롤백을 수행하세요.")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        session.rollback()
        
        if backup_timestamp:
            user_input = input("롤백을 수행하시겠습니까? (y/N): ")
            if user_input.lower() == 'y':
                rollback_migration(session, backup_timestamp)
        
        sys.exit(1)
    
    finally:
        session.close()
        print("\n🔚 마이그레이션 프로세스 완료")

if __name__ == "__main__":
    # 실행 전 확인
    print("⚠️ 경고: 이 스크립트는 데이터베이스를 수정합니다.")
    print("실행 전 반드시 데이터베이스 백업을 수행하세요!")
    print()
    
    user_input = input("계속 진행하시겠습니까? (y/N): ")
    if user_input.lower() != 'y':
        print("마이그레이션이 취소되었습니다.")
        sys.exit(0)
    
    main()
