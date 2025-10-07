#!/usr/bin/env python3
"""
메일 상태 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_mail_status():
    """메일 상태를 확인합니다."""
    print("🔍 메일 상태 확인 시작")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 최근 발송된 메일 5개 조회
        query = text("""
            SELECT 
                mail_uuid,
                subject,
                status,
                is_draft,
                sender_uuid,
                org_id,
                sent_at,
                created_at
            FROM mails 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        result = conn.execute(query)
        mails = result.fetchall()
        
        print(f"📧 최근 메일 {len(mails)}개:")
        for mail in mails:
            print(f"   - UUID: {mail.mail_uuid}")
            print(f"     제목: {mail.subject}")
            print(f"     상태: {mail.status}")
            print(f"     임시보관: {mail.is_draft}")
            print(f"     발송자: {mail.sender_uuid}")
            print(f"     조직: {mail.org_id}")
            print(f"     발송시간: {mail.sent_at}")
            print(f"     생성시간: {mail.created_at}")
            print()
        
        # 상태별 메일 개수 조회
        status_query = text("""
            SELECT status, COUNT(*) as count
            FROM mails 
            GROUP BY status
        """)
        
        status_result = conn.execute(status_query)
        status_counts = status_result.fetchall()
        
        print("📊 상태별 메일 개수:")
        for status_count in status_counts:
            print(f"   - {status_count.status}: {status_count.count}개")

if __name__ == "__main__":
    check_mail_status()