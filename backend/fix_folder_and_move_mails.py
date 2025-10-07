#!/usr/bin/env python3
"""
폴더 타입 확인 및 메일 이동

mail_folders 테이블의 folder_type 열거형 값을 확인하고
sent 폴더의 메일을 inbox로 이동합니다. (user_uuid 포함)
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

def move_mails_to_inbox_with_user_uuid():
    """user_uuid를 포함하여 메일 이동"""
    print(f"\n📦 메일 이동 (sent → inbox) - user_uuid 포함")
    print("=" * 60)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # user01의 inbox와 sent 폴더 UUID 가져오기
        result = db.execute(text("""
            SELECT folder_uuid, folder_type, name
            FROM mail_folders
            WHERE user_uuid = :user_uuid
            AND folder_type IN ('inbox', 'sent');
        """), {"user_uuid": user_uuid})
        
        folders = result.fetchall()
        inbox_uuid = None
        sent_uuid = None
        
        for folder in folders:
            if folder[1] == 'inbox':
                inbox_uuid = folder[0]
                print(f"📥 INBOX 폴더: {folder[2]} (UUID: {folder[0]})")
            elif folder[1] == 'sent':
                sent_uuid = folder[0]
                print(f"📤 SENT 폴더: {folder[2]} (UUID: {folder[0]})")
        
        if not inbox_uuid or not sent_uuid:
            print(f"❌ inbox 또는 sent 폴더를 찾을 수 없습니다.")
            return
        
        # SENT 폴더의 메일 수 확인
        result = db.execute(text("""
            SELECT COUNT(*) as mail_count
            FROM mail_in_folders
            WHERE folder_uuid = :sent_uuid;
        """), {"sent_uuid": sent_uuid})
        
        sent_count = result.fetchone()[0]
        print(f"📊 SENT 폴더의 메일 수: {sent_count}개")
        
        if sent_count == 0:
            print(f"❌ SENT 폴더에 이동할 메일이 없습니다.")
            return
        
        # SENT 폴더의 메일 중 처음 3개를 INBOX로 이동
        result = db.execute(text("""
            SELECT mail_uuid
            FROM mail_in_folders
            WHERE folder_uuid = :sent_uuid
            LIMIT 3;
        """), {"sent_uuid": sent_uuid})
        
        mails_to_move = result.fetchall()
        
        print(f"📦 {len(mails_to_move)}개 메일을 SENT에서 INBOX로 이동합니다...")
        
        moved_count = 0
        for mail in mails_to_move:
            mail_uuid = mail[0]
            
            # 이미 INBOX에 있는지 확인
            result = db.execute(text("""
                SELECT COUNT(*) 
                FROM mail_in_folders
                WHERE mail_uuid = :mail_uuid AND folder_uuid = :inbox_uuid;
            """), {"mail_uuid": mail_uuid, "inbox_uuid": inbox_uuid})
            
            if result.fetchone()[0] > 0:
                print(f"   ⚠️ 메일 {mail_uuid[:8]}... 이미 INBOX에 있음")
                continue
            
            # 기존 SENT 폴더 레코드 삭제
            db.execute(text("""
                DELETE FROM mail_in_folders
                WHERE mail_uuid = :mail_uuid AND folder_uuid = :sent_uuid;
            """), {"mail_uuid": mail_uuid, "sent_uuid": sent_uuid})
            
            # INBOX 폴더에 새 레코드 추가 (user_uuid 포함, 읽지 않음으로 설정)
            db.execute(text("""
                INSERT INTO mail_in_folders (mail_uuid, folder_uuid, user_uuid, is_read, created_at)
                VALUES (:mail_uuid, :inbox_uuid, :user_uuid, false, NOW());
            """), {
                "mail_uuid": mail_uuid, 
                "inbox_uuid": inbox_uuid, 
                "user_uuid": user_uuid
            })
            
            moved_count += 1
            print(f"   ✅ 메일 {mail_uuid[:8]}... 이동 완료")
        
        db.commit()
        print(f"✅ {moved_count}개 메일 이동 완료!")
        
        # 이동 후 폴더 상태 확인
        print(f"\n📊 이동 후 폴더 상태:")
        for folder_uuid, folder_type, folder_name in [(inbox_uuid, 'inbox', 'INBOX'), (sent_uuid, 'sent', 'SENT')]:
            result = db.execute(text("""
                SELECT COUNT(*) as mail_count,
                       COUNT(CASE WHEN is_read = false THEN 1 END) as unread_count
                FROM mail_in_folders
                WHERE folder_uuid = :folder_uuid;
            """), {"folder_uuid": folder_uuid})
            
            counts = result.fetchone()
            total_count = counts[0]
            unread_count = counts[1]
            
            print(f"  - {folder_name}: 총 {total_count}개, 읽지 않음 {unread_count}개")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 메일 이동 오류: {e}")
        if 'db' in locals():
            db.rollback()

def check_mail_in_folders_structure():
    """mail_in_folders 테이블 구조 확인"""
    print(f"\n🔍 mail_in_folders 테이블 구조 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # 테이블 구조 확인
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'mail_in_folders'
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        print("📋 mail_in_folders 테이블 컬럼:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        # 샘플 데이터 확인
        result = db.execute(text("""
            SELECT mail_uuid, folder_uuid, user_uuid, is_read, created_at
            FROM mail_in_folders
            LIMIT 3;
        """))
        
        samples = result.fetchall()
        print(f"\n📋 샘플 데이터 (처음 3개):")
        for sample in samples:
            print(f"  - Mail: {sample[0][:8]}..., Folder: {sample[1][:8]}..., User: {sample[2]}, Read: {sample[3]}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 테이블 구조 확인 오류: {e}")

def main():
    """메인 함수"""
    print("🔧 메일 이동 (user_uuid 포함)")
    print("=" * 60)
    
    # 1. mail_in_folders 테이블 구조 확인
    check_mail_in_folders_structure()
    
    # 2. 메일 이동
    move_mails_to_inbox_with_user_uuid()
    
    print("\n" + "=" * 60)
    print("🔧 메일 이동 완료")

if __name__ == "__main__":
    main()