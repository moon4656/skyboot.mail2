#!/usr/bin/env python3
"""
organization_usage 테이블의 current_users 필드를 실제 사용자 수로 업데이트하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime, date

def fix_current_users():
    """current_users 필드를 실제 사용자 수로 업데이트합니다."""
    print("🔧 current_users 필드 수정")
    print("=" * 80)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 1. 조직별 실제 활성 사용자 수 계산
        print("📊 조직별 실제 활성 사용자 수 계산 중...")
        
        actual_users_query = text("""
            SELECT 
                u.org_id,
                o.name as org_name,
                COUNT(CASE WHEN u.is_active = true THEN 1 END) as active_user_count
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.org_id
            GROUP BY u.org_id, o.name
            ORDER BY active_user_count DESC
        """)
        
        actual_users_result = db.execute(actual_users_query)
        org_user_counts = {}
        
        for row in actual_users_result:
            org_id = row.org_id
            active_count = row.active_user_count
            org_user_counts[org_id] = {
                'org_name': row.org_name,
                'active_users': active_count
            }
            print(f"  - 조직 {org_id} ({row.org_name}): {active_count}명")
        
        print(f"\n📈 총 활성 사용자 수: {sum(data['active_users'] for data in org_user_counts.values())}명")
        
        # 2. organization_usage 테이블 업데이트
        print("\n🔄 organization_usage 테이블 업데이트 중...")
        
        updated_count = 0
        inserted_count = 0
        
        for org_id, user_data in org_user_counts.items():
            active_users = user_data['active_users']
            org_name = user_data['org_name']
            
            # 오늘 날짜의 기존 레코드 확인
            today = date.today()
            existing_query = text("""
                SELECT id, current_users, emails_sent_today, total_emails_sent
                FROM organization_usage 
                WHERE org_id = :org_id
                AND DATE(usage_date) = :today
            """)
            
            existing_result = db.execute(existing_query, {
                "org_id": org_id,
                "today": today
            })
            existing_record = existing_result.fetchone()
            
            if existing_record:
                # 기존 레코드 업데이트
                if existing_record.current_users != active_users:
                    update_query = text("""
                        UPDATE organization_usage 
                        SET 
                            current_users = :active_users,
                            updated_at = NOW()
                        WHERE id = :record_id
                    """)
                    
                    db.execute(update_query, {
                        "active_users": active_users,
                        "record_id": existing_record.id
                    })
                    
                    updated_count += 1
                    print(f"  ✅ 업데이트: {org_name} - {existing_record.current_users}명 → {active_users}명")
                else:
                    print(f"  ➡️ 변경없음: {org_name} - {active_users}명")
            else:
                # 새 레코드 삽입 (오늘 날짜로)
                insert_query = text("""
                    INSERT INTO organization_usage (
                        org_id, 
                        usage_date, 
                        current_users,
                        emails_sent_today, 
                        total_emails_sent,
                        current_storage_gb,
                        emails_received_today,
                        total_emails_received,
                        created_at,
                        updated_at
                    ) VALUES (
                        :org_id,
                        :usage_date,
                        :current_users,
                        0,
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
                    "usage_date": today,
                    "current_users": active_users
                })
                
                inserted_count += 1
                print(f"  ➕ 삽입: {org_name} - {active_users}명 (새 레코드)")
        
        # 3. 과거 레코드도 업데이트 (current_users가 0인 경우)
        print("\n🔄 과거 레코드의 current_users 업데이트 중...")
        
        past_updated_count = 0
        for org_id, user_data in org_user_counts.items():
            active_users = user_data['active_users']
            org_name = user_data['org_name']
            
            # current_users가 0인 과거 레코드 업데이트
            past_update_query = text("""
                UPDATE organization_usage 
                SET 
                    current_users = :active_users,
                    updated_at = NOW()
                WHERE org_id = :org_id
                AND current_users = 0
                AND DATE(usage_date) < :today
            """)
            
            past_result = db.execute(past_update_query, {
                "active_users": active_users,
                "org_id": org_id,
                "today": today
            })
            
            if past_result.rowcount > 0:
                past_updated_count += past_result.rowcount
                print(f"  ✅ 과거 레코드 업데이트: {org_name} - {past_result.rowcount}개 레코드")
        
        # 트랜잭션 커밋
        db.commit()
        
        print(f"\n✅ 완료!")
        print(f"📊 오늘 레코드 업데이트: {updated_count}개")
        print(f"📊 오늘 레코드 삽입: {inserted_count}개")
        print(f"📊 과거 레코드 업데이트: {past_updated_count}개")
        
        # 4. 결과 확인
        print("\n🔍 수정 결과 확인:")
        
        verification_query = text("""
            SELECT 
                ou.org_id,
                o.name as org_name,
                DATE(ou.usage_date) as usage_date,
                ou.current_users,
                ou.emails_sent_today,
                ou.total_emails_sent,
                ou.updated_at
            FROM organization_usage ou
            LEFT JOIN organizations o ON ou.org_id = o.org_id
            WHERE DATE(ou.usage_date) = CURRENT_DATE
            ORDER BY ou.current_users DESC
        """)
        
        verification_result = db.execute(verification_query)
        
        total_recorded_users = 0
        for row in verification_result:
            total_recorded_users += row.current_users
            print(f"  - {row.org_name}: {row.current_users}명 (메일: 오늘 {row.emails_sent_today}개, 총 {row.total_emails_sent}개)")
        
        print(f"\n📊 총 기록된 사용자 수: {total_recorded_users}명")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
            db.close()

if __name__ == "__main__":
    fix_current_users()