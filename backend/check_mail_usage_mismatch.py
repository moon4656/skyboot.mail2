#!/usr/bin/env python3
"""
메일 발송 기록과 조직 사용량 불일치 문제 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime, timedelta

def check_mail_usage_mismatch():
    """메일 발송 기록과 조직 사용량 불일치 문제를 확인합니다."""
    print("🔍 메일 발송 기록 vs 조직 사용량 불일치 확인")
    print("=" * 80)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 1. 오늘 날짜 설정
        today = datetime.now().date()
        print(f"📅 확인 날짜: {today}")
        
        # 2. mails 테이블에서 오늘 발송된 메일 수 확인
        print("\n📧 mails 테이블 - 오늘 발송된 메일:")
        mails_query = text("""
            SELECT 
                org_id,
                COUNT(*) as mail_count,
                MIN(sent_at) as first_sent,
                MAX(sent_at) as last_sent
            FROM mails 
            WHERE DATE(sent_at) = CURRENT_DATE
            AND status = 'sent'
            GROUP BY org_id
            ORDER BY mail_count DESC
        """)
        mails_result = db.execute(mails_query)
        
        mail_counts_by_org = {}
        total_mails_today = 0
        
        for row in mails_result:
            org_id = row.org_id
            mail_count = row.mail_count
            mail_counts_by_org[org_id] = mail_count
            total_mails_today += mail_count
            
            print(f"  - 조직 ID: {org_id}")
            print(f"    발송 메일 수: {mail_count}")
            print(f"    첫 발송: {row.first_sent}")
            print(f"    마지막 발송: {row.last_sent}")
            print()
        
        print(f"📊 총 발송 메일 수 (mails 테이블): {total_mails_today}")
        
        # 3. organization_usage 테이블에서 오늘 기록된 사용량 확인
        print("\n📈 organization_usage 테이블 - 오늘 기록된 사용량:")
        usage_query = text("""
            SELECT 
                org_id,
                emails_sent_today,
                total_emails_sent,
                usage_date,
                updated_at
            FROM organization_usage 
            WHERE DATE(usage_date) = CURRENT_DATE
            ORDER BY emails_sent_today DESC
        """)
        usage_result = db.execute(usage_query)
        
        usage_counts_by_org = {}
        total_usage_today = 0
        
        for row in usage_result:
            org_id = row.org_id
            emails_sent = row.emails_sent_today
            usage_counts_by_org[org_id] = emails_sent
            total_usage_today += emails_sent
            
            print(f"  - 조직 ID: {org_id}")
            print(f"    기록된 발송량: {emails_sent}")
            print(f"    총 발송량: {row.total_emails_sent}")
            print(f"    사용량 날짜: {row.usage_date}")
            print(f"    마지막 업데이트: {row.updated_at}")
            print()
        
        print(f"📊 총 기록된 사용량: {total_usage_today}")
        
        # 4. 불일치 분석
        print("\n🔍 불일치 분석:")
        print(f"실제 발송 메일 수: {total_mails_today}")
        print(f"기록된 사용량: {total_usage_today}")
        print(f"차이: {total_mails_today - total_usage_today}")
        
        if total_mails_today != total_usage_today:
            print("❌ 불일치 발견!")
            
            # 조직별 상세 비교
            print("\n📋 조직별 상세 비교:")
            all_orgs = set(mail_counts_by_org.keys()) | set(usage_counts_by_org.keys())
            
            for org_id in all_orgs:
                actual_count = mail_counts_by_org.get(org_id, 0)
                recorded_count = usage_counts_by_org.get(org_id, 0)
                
                if actual_count != recorded_count:
                    print(f"  🚨 조직 {org_id}:")
                    print(f"    실제 발송: {actual_count}")
                    print(f"    기록된 사용량: {recorded_count}")
                    print(f"    차이: {actual_count - recorded_count}")
                    print()
        else:
            print("✅ 일치함!")
        
        # 5. 특정 조직의 상세 메일 기록 확인 (가장 많이 발송한 조직)
        if mail_counts_by_org:
            top_org = max(mail_counts_by_org.keys(), key=lambda x: mail_counts_by_org[x])
            print(f"\n🎯 가장 많이 발송한 조직 ({top_org}) 상세 기록:")
            
            detail_query = text("""
                SELECT 
                    mail_uuid,
                    subject,
                    sent_at,
                    status
                FROM mails 
                WHERE org_id = :org_id
                AND DATE(sent_at) = CURRENT_DATE
                ORDER BY sent_at DESC
                LIMIT 10
            """)
            detail_result = db.execute(detail_query, {"org_id": top_org})
            
            for row in detail_result:
                print(f"  - {row.sent_at}: {row.subject[:50]}... ({row.status})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_mail_usage_mismatch()