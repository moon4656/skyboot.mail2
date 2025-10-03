#!/usr/bin/env python3
"""
현재 사용자 수 문제를 조사하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime

def check_current_users():
    """현재 사용자 수 문제를 조사합니다."""
    print("👥 현재 사용자 수 문제 조사")
    print("=" * 80)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 1. 실제 사용자 수 확인 (조직별)
        print("📊 실제 사용자 수 확인 (users 테이블):")
        
        actual_users_query = text("""
            SELECT 
                u.org_id,
                o.name as org_name,
                COUNT(*) as actual_user_count,
                COUNT(CASE WHEN u.is_active = true THEN 1 END) as active_user_count,
                COUNT(CASE WHEN u.is_active = false THEN 1 END) as inactive_user_count
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.org_id
            GROUP BY u.org_id, o.name
            ORDER BY actual_user_count DESC
        """)
        
        actual_users_result = db.execute(actual_users_query)
        actual_users_data = {}
        
        for row in actual_users_result:
            org_id = row.org_id
            actual_users_data[org_id] = {
                'org_name': row.org_name,
                'total_users': row.actual_user_count,
                'active_users': row.active_user_count,
                'inactive_users': row.inactive_user_count
            }
            print(f"  - 조직 {org_id} ({row.org_name}): 총 {row.actual_user_count}명 (활성: {row.active_user_count}, 비활성: {row.inactive_user_count})")
        
        print(f"\n📈 총 실제 사용자 수: {sum(data['total_users'] for data in actual_users_data.values())}명")
        
        # 2. organization_usage 테이블의 current_users 확인
        print("\n📋 organization_usage 테이블의 current_users:")
        
        usage_users_query = text("""
            SELECT 
                org_id,
                usage_date,
                current_users,
                emails_sent_today,
                total_emails_sent,
                updated_at
            FROM organization_usage 
            ORDER BY org_id, usage_date DESC
        """)
        
        usage_users_result = db.execute(usage_users_query)
        usage_users_data = {}
        
        for row in usage_users_result:
            org_id = row.org_id
            if org_id not in usage_users_data:
                usage_users_data[org_id] = []
            
            usage_users_data[org_id].append({
                'usage_date': row.usage_date,
                'current_users': row.current_users,
                'emails_sent_today': row.emails_sent_today,
                'total_emails_sent': row.total_emails_sent,
                'updated_at': row.updated_at
            })
        
        for org_id, usage_list in usage_users_data.items():
            org_name = actual_users_data.get(org_id, {}).get('org_name', 'Unknown')
            print(f"\n  🏢 조직 {org_id} ({org_name}):")
            for usage in usage_list[:3]:  # 최근 3개만 표시
                print(f"    - {usage['usage_date'].strftime('%Y-%m-%d')}: current_users={usage['current_users']}, emails_sent={usage['emails_sent_today']}")
        
        # 3. 불일치 분석
        print("\n🔍 사용자 수 불일치 분석:")
        
        for org_id, actual_data in actual_users_data.items():
            if org_id in usage_users_data and usage_users_data[org_id]:
                latest_usage = usage_users_data[org_id][0]  # 가장 최근 기록
                recorded_users = latest_usage['current_users']
                actual_active_users = actual_data['active_users']
                
                if recorded_users != actual_active_users:
                    print(f"  ❌ 조직 {org_id} ({actual_data['org_name']}):")
                    print(f"    실제 활성 사용자: {actual_active_users}명")
                    print(f"    기록된 사용자: {recorded_users}명")
                    print(f"    차이: {actual_active_users - recorded_users}명")
                else:
                    print(f"  ✅ 조직 {org_id} ({actual_data['org_name']}): 일치 ({actual_active_users}명)")
            else:
                print(f"  ⚠️ 조직 {org_id} ({actual_data['org_name']}): organization_usage에 기록 없음")
        
        # 4. 사용자 상세 정보 확인
        print("\n👤 사용자 상세 정보:")
        
        user_details_query = text("""
            SELECT 
                u.user_uuid,
                u.email,
                u.org_id,
                u.is_active,
                u.role,
                u.created_at,
                u.last_login_at,
                o.name as org_name
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.org_id
            ORDER BY u.org_id, u.created_at DESC
        """)
        
        user_details_result = db.execute(user_details_query)
        
        current_org = None
        for row in user_details_result:
            if current_org != row.org_id:
                current_org = row.org_id
                print(f"\n  🏢 조직 {row.org_id} ({row.org_name}):")
            
            status = "🟢 활성" if row.is_active else "🔴 비활성"
            last_login = row.last_login_at.strftime('%Y-%m-%d %H:%M') if row.last_login_at else "로그인 기록 없음"
            print(f"    - {row.email} ({row.role}) {status} | 마지막 로그인: {last_login}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    check_current_users()