#!/usr/bin/env python3
"""
메일 읽음 상태 디버깅 스크립트
특정 메일 ID의 읽음 상태를 데이터베이스에서 직접 확인
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import SaaSSettings

def check_mail_read_status():
    """특정 메일의 읽음 상태를 데이터베이스에서 확인"""
    
    print("🔍 메일 읽음 상태 디버깅 시작")
    print("=" * 60)
    print(f"시작 시간: {datetime.now()}")
    print()
    
    # 설정 로드
    settings = SaaSSettings()
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        mail_uuid = '20251005_235140_009e55f6a7f6'
        
        print(f"📧 대상 메일 ID: {mail_uuid}")
        print()
        
        # 1. 메일 기본 정보 확인
        print("1️⃣ 메일 기본 정보 확인")
        print("-" * 40)
        
        mail_query = text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.sender_uuid,
                m.created_at,
                m.org_id,
                mu.email as sender_email
            FROM mails m
            LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_uuid
            WHERE m.mail_uuid = :mail_uuid
        """)
        
        mail_result = session.execute(mail_query, {"mail_uuid": mail_uuid}).fetchone()
        
        if mail_result:
            print(f"   메일 UUID: {mail_result.mail_uuid}")
            print(f"   제목: {mail_result.subject}")
            print(f"   발송자 UUID: {mail_result.sender_uuid}")
            print(f"   발송자 이메일: {mail_result.sender_email}")
            print(f"   생성 시간: {mail_result.created_at}")
            print(f"   조직 ID: {mail_result.org_id}")
        else:
            print("   ❌ 해당 메일을 찾을 수 없습니다!")
            return
        
        print()
        
        # 2. MailInFolder 테이블에서 읽음 상태 확인
        print("2️⃣ MailInFolder 테이블 읽음 상태 확인")
        print("-" * 40)
        
        folder_query = text("""
            SELECT 
                mif.id,
                mif.mail_uuid,
                mif.user_uuid,
                mif.folder_uuid,
                mif.is_read,
                mif.read_at,
                mif.created_at,
                f.name as folder_name,
                mu.email as user_email
            FROM mail_in_folders mif
            JOIN mail_folders f ON mif.folder_uuid = f.folder_uuid
            JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            WHERE mif.mail_uuid = :mail_uuid
            ORDER BY mu.email, f.name
        """)
        
        folder_results = session.execute(folder_query, {"mail_uuid": mail_uuid}).fetchall()
        
        if folder_results:
            for result in folder_results:
                print(f"   사용자: {result.user_email}")
                print(f"   폴더: {result.folder_name}")
                print(f"   읽음 상태: {'읽음' if result.is_read else '읽지 않음'}")
                print(f"   읽은 시간: {result.read_at or '읽지 않음'}")
                print(f"   생성 시간: {result.created_at}")
                print(f"   MailInFolder ID: {result.id}")
                print()
        else:
            print("   ❌ MailInFolder에서 해당 메일을 찾을 수 없습니다!")
        
        # 3. 메일 수신자 정보 확인
        print("3️⃣ 메일 수신자 정보 확인")
        print("-" * 40)
        
        recipient_query = text("""
            SELECT 
                mr.id,
                mr.mail_uuid,
                mr.recipient_email,
                mr.recipient_type,
                mr.recipient_uuid,
                mu.email as user_email
            FROM mail_recipients mr
            LEFT JOIN mail_users mu ON mr.recipient_uuid = mu.user_uuid
            WHERE mr.mail_uuid = :mail_uuid
        """)
        
        recipient_results = session.execute(recipient_query, {"mail_uuid": mail_uuid}).fetchall()
        
        if recipient_results:
            for result in recipient_results:
                print(f"   수신자 이메일: {result.recipient_email}")
                print(f"   수신자 타입: {result.recipient_type}")
                print(f"   수신자 UUID: {result.recipient_uuid}")
                print(f"   연결된 사용자: {result.user_email or '외부 사용자'}")
                print()
        else:
            print("   ❌ 메일 수신자 정보를 찾을 수 없습니다!")
        
        # 4. 사용자별 읽음 상태 요약
        print("4️⃣ 사용자별 읽음 상태 요약")
        print("-" * 40)
        
        summary_query = text("""
            SELECT 
                mu.email,
                mu.user_uuid,
                COUNT(CASE WHEN mif.is_read = true THEN 1 END) as read_count,
                COUNT(CASE WHEN mif.is_read = false THEN 1 END) as unread_count,
                COUNT(*) as total_folders
            FROM mail_in_folders mif
            JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            WHERE mif.mail_uuid = :mail_uuid
            GROUP BY mu.email, mu.user_uuid
        """)
        
        summary_results = session.execute(summary_query, {"mail_uuid": mail_uuid}).fetchall()
        
        if summary_results:
            for result in summary_results:
                print(f"   사용자: {result.email}")
                print(f"   UUID: {result.user_uuid}")
                print(f"   읽음: {result.read_count}개 폴더")
                print(f"   읽지 않음: {result.unread_count}개 폴더")
                print(f"   총 폴더: {result.total_folders}개")
                print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        session.close()
        print("🏁 디버깅 완료")
        print("=" * 60)
        print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    check_mail_read_status()