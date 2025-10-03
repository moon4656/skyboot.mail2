#!/usr/bin/env python3
"""
조직 사용량 테이블 직접 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime, timedelta

def check_organization_usage():
    """조직 사용량 테이블을 직접 확인합니다."""
    print("🔍 조직 사용량 테이블 확인")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 1. 조직 정보 확인
        print("📊 조직 정보:")
        org_query = text("""
            SELECT org_id, name, domain, is_active, created_at 
            FROM organizations 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        org_result = db.execute(org_query)
        for row in org_result:
            print(f"  - 조직 ID: {row.org_id}, 이름: {row.name}, 도메인: {row.domain}")
        
        # 2. organization_usage 테이블 전체 확인
        print("\n📈 조직 사용량 데이터:")
        usage_query = text("""
            SELECT org_id, usage_date, current_users, current_storage_gb, 
                   emails_sent_today, emails_received_today, 
                   total_emails_sent, total_emails_received, 
                   created_at, updated_at
            FROM organization_usage 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)
        usage_result = db.execute(usage_query)
        
        usage_found = False
        for row in usage_result:
            usage_found = True
            print(f"  - 조직 ID: {row.org_id}")
            print(f"    날짜: {row.usage_date}")
            print(f"    현재 사용자: {row.current_users}")
            print(f"    현재 저장 공간: {row.current_storage_gb}GB")
            print(f"    오늘 발송 메일: {row.emails_sent_today}")
            print(f"    오늘 수신 메일: {row.emails_received_today}")
            print(f"    총 발송 메일: {row.total_emails_sent}")
            print(f"    총 수신 메일: {row.total_emails_received}")
            print(f"    생성: {row.created_at}")
            print(f"    수정: {row.updated_at}")
            print("    " + "-" * 40)
        
        if not usage_found:
            print("  ❌ 조직 사용량 데이터가 없습니다.")
        
        # 3. 최근 메일 발송 기록 확인
        print("\n📧 최근 메일 발송 기록:")
        mail_query = text("""
            SELECT mail_uuid, sender_uuid, org_id, subject, sent_at, status
            FROM mails 
            WHERE sent_at >= :recent_time
            ORDER BY sent_at DESC 
            LIMIT 5
        """)
        recent_time = datetime.now() - timedelta(hours=1)
        mail_result = db.execute(mail_query, {"recent_time": recent_time})
        
        mail_found = False
        for row in mail_result:
            mail_found = True
            print(f"  - 메일 UUID: {row.mail_uuid}")
            print(f"    조직 ID: {row.org_id}")
            print(f"    제목: {row.subject}")
            print(f"    발송 시간: {row.sent_at}")
            print(f"    상태: {row.status}")
            print("    " + "-" * 30)
        
        if not mail_found:
            print("  ❌ 최근 1시간 내 메일 발송 기록이 없습니다.")
        
        # 4. 특정 조직의 오늘 사용량 확인
        print("\n🎯 특정 조직 (3856a8c1-84a4-4019-9133-655cacab4bc9) 오늘 사용량:")
        today_query = text("""
            SELECT org_id, usage_date, total_emails_sent, total_emails_received, updated_at
            FROM organization_usage 
            WHERE org_id = :org_id
            AND usage_date = CURRENT_DATE
        """)
        today_result = db.execute(today_query, {"org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9"})
        
        today_found = False
        for row in today_result:
            today_found = True
            print(f"  - 조직 ID: {row.org_id}")
            print(f"    날짜: {row.usage_date}")
            print(f"    발송 메일: {row.total_emails_sent}")
            print(f"    수신 메일: {row.total_emails_received}")
            print(f"    마지막 업데이트: {row.updated_at}")
        
        if not today_found:
            print("  ❌ 해당 조직의 오늘 사용량 데이터가 없습니다.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_organization_usage()