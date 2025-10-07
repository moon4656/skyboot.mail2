#!/usr/bin/env python3
"""
메일 상태 디버깅

메일 이동 후 실제 상태를 자세히 분석합니다.
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

def check_mails_table_structure():
    """mails 테이블 구조 확인"""
    print("🔍 mails 테이블 구조 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # 테이블 구조 확인
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'mails'
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        print("📋 mails 테이블 컬럼:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        db.close()
        return [col[0] for col in columns]
        
    except Exception as e:
        print(f"❌ mails 테이블 구조 확인 오류: {e}")
        return []

def debug_mail_in_folders():
    """mail_in_folders 테이블 상세 분석"""
    print(f"\n🔍 mail_in_folders 테이블 상세 분석")
    print("=" * 60)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # user01의 모든 mail_in_folders 레코드 확인
        result = db.execute(text("""
            SELECT 
                mif.id,
                mif.mail_uuid,
                mif.folder_uuid,
                mif.user_uuid,
                mif.is_read,
                mif.read_at,
                mif.created_at,
                mf.name as folder_name,
                mf.folder_type
            FROM mail_in_folders mif
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mif.user_uuid = :user_uuid
            ORDER BY mif.created_at DESC
            LIMIT 10;
        """), {"user_uuid": user_uuid})
        
        records = result.fetchall()
        print(f"📋 user01의 최근 mail_in_folders 레코드 (최대 10개):")
        
        for record in records:
            record_id = record[0]
            mail_uuid = record[1][:8]
            folder_uuid = record[2][:8]
            user_uuid_short = record[3][:8] if record[3] else 'None'
            is_read = record[4]
            read_at = record[5]
            created_at = record[6]
            folder_name = record[7]
            folder_type = record[8]
            
            print(f"  ID: {record_id}")
            print(f"    메일: {mail_uuid}..., 폴더: {folder_name} ({folder_type})")
            print(f"    사용자: {user_uuid_short}..., 읽음: {is_read}, 읽은시간: {read_at}")
            print(f"    생성시간: {created_at}")
            print()
        
        # 폴더별 집계
        result = db.execute(text("""
            SELECT 
                mf.name as folder_name,
                mf.folder_type,
                COUNT(mif.mail_uuid) as total_count,
                COUNT(CASE WHEN mif.is_read = true THEN 1 END) as read_count,
                COUNT(CASE WHEN mif.is_read = false THEN 1 END) as unread_count,
                COUNT(CASE WHEN mif.is_read IS NULL THEN 1 END) as null_count
            FROM mail_folders mf
            LEFT JOIN mail_in_folders mif ON mf.folder_uuid = mif.folder_uuid AND mif.user_uuid = :user_uuid
            WHERE mf.user_uuid = :user_uuid
            GROUP BY mf.folder_uuid, mf.name, mf.folder_type
            ORDER BY mf.folder_type;
        """), {"user_uuid": user_uuid})
        
        folders = result.fetchall()
        print(f"📊 폴더별 상세 집계:")
        for folder in folders:
            folder_name = folder[0]
            folder_type = folder[1]
            total = folder[2]
            read = folder[3]
            unread = folder[4]
            null_read = folder[5]
            
            print(f"  - {folder_name} ({folder_type}): 총 {total}개")
            print(f"    읽음: {read}개, 읽지않음: {unread}개, NULL: {null_read}개")
        
        db.close()
        
    except Exception as e:
        print(f"❌ mail_in_folders 분석 오류: {e}")

def debug_mails_table_with_correct_columns(columns):
    """올바른 컬럼명으로 mails 테이블 분석"""
    print(f"\n📧 mails 테이블 분석 (올바른 컬럼명)")
    print("=" * 60)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # 사용 가능한 컬럼 확인
        sender_column = None
        if 'sender_email' in columns:
            sender_column = 'sender_email'
        elif 'from_email' in columns:
            sender_column = 'from_email'
        elif 'sender' in columns:
            sender_column = 'sender'
        
        # 기본 쿼리 (sender 컬럼 없이)
        base_query = """
            SELECT 
                m.mail_uuid,
                m.subject,
                m.status,
                m.created_at
        """
        
        if sender_column:
            base_query += f", m.{sender_column}"
        
        if 'sent_at' in columns:
            base_query += ", m.sent_at"
        
        base_query += """
            FROM mails m
            WHERE m.sender_uuid = :user_uuid
            ORDER BY m.created_at DESC
            LIMIT 5;
        """
        
        result = db.execute(text(base_query), {"user_uuid": user_uuid})
        
        sent_mails = result.fetchall()
        print(f"📤 user01이 발송한 최근 메일 (5개):")
        for mail in sent_mails:
            mail_uuid = mail[0][:8]
            subject = mail[1]
            status = mail[2]
            created_at = mail[3]
            
            print(f"  - {mail_uuid}... | {subject}")
            print(f"    상태: {status}, 생성: {created_at}")
            
            if sender_column and len(mail) > 4:
                sender = mail[4]
                print(f"    발송자: {sender}")
            
            if 'sent_at' in columns and len(mail) > 5:
                sent_at = mail[5] if len(mail) > 5 else mail[4]
                print(f"    발송: {sent_at}")
            print()
        
        db.close()
        
    except Exception as e:
        print(f"❌ mails 테이블 분석 오류: {e}")

def check_unread_query_logic_fixed():
    """읽지 않은 메일 쿼리 로직 확인 (수정된 버전)"""
    print(f"\n🔍 읽지 않은 메일 쿼리 로직 확인 (수정된 버전)")
    print("=" * 60)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # API에서 사용하는 것과 유사한 쿼리 실행 (sender_email 제외)
        result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                mif.is_read,
                mf.name as folder_name,
                mf.folder_type
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = :user_uuid 
            AND mf.folder_type = 'inbox'
            AND mif.is_read = false
            ORDER BY m.created_at DESC;
        """), {"user_uuid": user_uuid})
        
        unread_mails = result.fetchall()
        print(f"📧 읽지 않은 메일 쿼리 결과: {len(unread_mails)}개")
        
        for mail in unread_mails:
            mail_uuid = mail[0][:8]
            subject = mail[1]
            created_at = mail[2]
            is_read = mail[3]
            folder_name = mail[4]
            folder_type = mail[5]
            
            print(f"  - {mail_uuid}... | {subject}")
            print(f"    폴더: {folder_name} ({folder_type})")
            print(f"    읽음상태: {is_read}, 생성시간: {created_at}")
            print()
        
        # 모든 INBOX 메일 확인 (읽음 상태 무관)
        result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                mif.is_read,
                mif.created_at as moved_at
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = :user_uuid 
            AND mf.folder_type = 'inbox'
            ORDER BY mif.created_at DESC;
        """), {"user_uuid": user_uuid})
        
        all_inbox_mails = result.fetchall()
        print(f"\n📥 INBOX의 모든 메일: {len(all_inbox_mails)}개")
        
        for mail in all_inbox_mails:
            mail_uuid = mail[0][:8]
            subject = mail[1]
            is_read = mail[2]
            moved_at = mail[3]
            
            print(f"  - {mail_uuid}... | {subject} | 읽음: {is_read} | 이동: {moved_at}")
        
        db.close()
        return len(unread_mails)
        
    except Exception as e:
        print(f"❌ 읽지 않은 메일 쿼리 확인 오류: {e}")
        return 0

def main():
    """메인 함수"""
    print("🔧 메일 상태 디버깅 (수정된 버전)")
    print("=" * 60)
    
    # 1. mails 테이블 구조 확인
    columns = check_mails_table_structure()
    
    # 2. mail_in_folders 테이블 상세 분석
    debug_mail_in_folders()
    
    # 3. mails 테이블 분석 (올바른 컬럼명)
    if columns:
        debug_mails_table_with_correct_columns(columns)
    
    # 4. 읽지 않은 메일 쿼리 로직 확인
    unread_count = check_unread_query_logic_fixed()
    
    print(f"\n🎯 디버깅 결과 요약:")
    print(f"   데이터베이스 읽지 않은 메일 수: {unread_count}개")
    
    print("\n" + "=" * 60)
    print("🔧 메일 상태 디버깅 완료")

if __name__ == "__main__":
    main()