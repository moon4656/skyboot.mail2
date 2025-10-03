#!/usr/bin/env python3
"""
기존 메일 데이터를 기반으로 조직 사용량을 재계산하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime, timedelta

def fix_organization_usage():
    """기존 메일 데이터를 기반으로 조직 사용량을 재계산합니다."""
    print("🔧 조직 사용량 재계산 및 수정")
    print("=" * 80)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 1. 조직별 일별 메일 발송 통계 계산
        print("📊 조직별 일별 메일 발송 통계 계산 중...")
        
        stats_query = text("""
            SELECT 
                org_id,
                DATE(sent_at) as send_date,
                COUNT(*) as emails_sent,
                MIN(sent_at) as first_sent,
                MAX(sent_at) as last_sent
            FROM mails 
            WHERE status = 'sent'
            AND sent_at IS NOT NULL
            GROUP BY org_id, DATE(sent_at)
            ORDER BY org_id, send_date DESC
        """)
        
        stats_result = db.execute(stats_query)
        daily_stats = []
        
        for row in stats_result:
            daily_stats.append({
                'org_id': row.org_id,
                'send_date': row.send_date,
                'emails_sent': row.emails_sent,
                'first_sent': row.first_sent,
                'last_sent': row.last_sent
            })
        
        print(f"📈 발견된 일별 통계: {len(daily_stats)}개")
        
        # 2. 각 조직의 총 발송량 계산
        print("\n📊 조직별 총 발송량 계산 중...")
        
        total_stats_query = text("""
            SELECT 
                org_id,
                COUNT(*) as total_emails_sent
            FROM mails 
            WHERE status = 'sent'
            AND sent_at IS NOT NULL
            GROUP BY org_id
            ORDER BY total_emails_sent DESC
        """)
        
        total_stats_result = db.execute(total_stats_query)
        total_stats = {}
        
        for row in total_stats_result:
            total_stats[row.org_id] = row.total_emails_sent
            print(f"  - 조직 {row.org_id}: 총 {row.total_emails_sent}개")
        
        # 3. organization_usage 테이블 업데이트/삽입
        print("\n🔄 organization_usage 테이블 업데이트 중...")
        
        updated_count = 0
        inserted_count = 0
        
        for stat in daily_stats:
            org_id = stat['org_id']
            send_date = stat['send_date']
            emails_sent = stat['emails_sent']
            
            # 해당 날짜의 총 발송량 계산 (그 날짜까지의 누적)
            cumulative_query = text("""
                SELECT COUNT(*) as cumulative_total
                FROM mails 
                WHERE org_id = :org_id
                AND status = 'sent'
                AND sent_at IS NOT NULL
                AND DATE(sent_at) <= :send_date
            """)
            
            cumulative_result = db.execute(cumulative_query, {
                "org_id": org_id,
                "send_date": send_date
            })
            cumulative_total = cumulative_result.scalar()
            
            # 기존 레코드 확인
            existing_query = text("""
                SELECT id, emails_sent_today, total_emails_sent
                FROM organization_usage 
                WHERE org_id = :org_id
                AND DATE(usage_date) = :send_date
            """)
            
            existing_result = db.execute(existing_query, {
                "org_id": org_id,
                "send_date": send_date
            })
            existing_record = existing_result.fetchone()
            
            if existing_record:
                # 업데이트
                if (existing_record.emails_sent_today != emails_sent or 
                    existing_record.total_emails_sent != cumulative_total):
                    
                    update_query = text("""
                        UPDATE organization_usage 
                        SET 
                            emails_sent_today = :emails_sent,
                            total_emails_sent = :total_emails_sent,
                            updated_at = NOW()
                        WHERE id = :record_id
                    """)
                    
                    db.execute(update_query, {
                        "emails_sent": emails_sent,
                        "total_emails_sent": cumulative_total,
                        "record_id": existing_record.id
                    })
                    
                    updated_count += 1
                    print(f"  ✅ 업데이트: {org_id} - {send_date} ({emails_sent}개 -> 누적 {cumulative_total}개)")
            else:
                # 삽입
                insert_query = text("""
                    INSERT INTO organization_usage (
                        org_id, 
                        usage_date, 
                        emails_sent_today, 
                        total_emails_sent,
                        current_users,
                        current_storage_gb,
                        emails_received_today,
                        total_emails_received,
                        created_at,
                        updated_at
                    ) VALUES (
                        :org_id,
                        :usage_date,
                        :emails_sent,
                        :total_emails_sent,
                        0,
                        0,
                        0,
                        0,
                        NOW(),
                        NOW()
                    )
                """)
                
                db.execute(insert_query, {
                    "org_id": org_id,
                    "usage_date": send_date,
                    "emails_sent": emails_sent,
                    "total_emails_sent": cumulative_total
                })
                
                inserted_count += 1
                print(f"  ➕ 삽입: {org_id} - {send_date} ({emails_sent}개 -> 누적 {cumulative_total}개)")
        
        # 트랜잭션 커밋
        db.commit()
        
        print(f"\n✅ 완료!")
        print(f"📊 업데이트된 레코드: {updated_count}개")
        print(f"📊 삽입된 레코드: {inserted_count}개")
        
        # 4. 결과 확인
        print("\n🔍 수정 결과 확인:")
        
        verification_query = text("""
            SELECT 
                org_id,
                DATE(usage_date) as usage_date,
                emails_sent_today,
                total_emails_sent,
                updated_at
            FROM organization_usage 
            WHERE DATE(usage_date) = CURRENT_DATE
            ORDER BY total_emails_sent DESC
        """)
        
        verification_result = db.execute(verification_query)
        
        for row in verification_result:
            print(f"  - 조직 {row.org_id}: 오늘 {row.emails_sent_today}개, 총 {row.total_emails_sent}개")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
            db.close()

if __name__ == "__main__":
    fix_organization_usage()