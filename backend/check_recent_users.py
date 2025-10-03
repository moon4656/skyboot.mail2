#!/usr/bin/env python3
"""
최근 생성된 사용자 및 조직 사용량 확인
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime, timedelta

def check_recent_users():
    """최근 생성된 사용자 및 조직 사용량 확인"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 최근 생성된 사용자 및 조직 사용량 확인")
        print("=" * 60)
        
        # 최근 1시간 내 생성된 사용자 조회
        recent_time = datetime.now() - timedelta(hours=1)
        
        query = text("""
            SELECT 
                user_id,
                username,
                email,
                role,
                is_active,
                org_id,
                created_at
            FROM users 
            WHERE created_at >= :recent_time
            ORDER BY created_at DESC
        """)
        
        result = db.execute(query, {"recent_time": recent_time})
        recent_users = result.fetchall()
        
        if recent_users:
            print(f"📊 최근 1시간 내 생성된 사용자: {len(recent_users)}명")
            print()
            
            for user in recent_users:
                print(f"👤 사용자 ID: {user.user_id}")
                print(f"   사용자명: {user.username}")
                print(f"   이메일: {user.email}")
                print(f"   역할: {user.role}")
                print(f"   활성 상태: {user.is_active}")
                print(f"   조직 ID: {user.org_id}")
                print(f"   생성일: {user.created_at}")
                print()
        else:
            print("❌ 최근 1시간 내 생성된 사용자가 없습니다.")
        
        # 조직 사용량 확인 (오늘 날짜)
        print("\n📈 오늘의 조직 사용량:")
        print("-" * 40)
        
        usage_query = text("""
            SELECT 
                org_id,
                current_users,
                emails_sent_today,
                total_emails_sent,
                usage_date,
                updated_at
            FROM organization_usage 
            WHERE DATE(usage_date) = CURRENT_DATE
            ORDER BY updated_at DESC
        """)
        
        usage_result = db.execute(usage_query)
        usage_records = usage_result.fetchall()
        
        if usage_records:
            for record in usage_records:
                print(f"🏢 조직 ID: {record.org_id}")
                print(f"   현재 사용자 수: {record.current_users}명")
                print(f"   오늘 발송 메일: {record.emails_sent_today}건")
                print(f"   총 발송 메일: {record.total_emails_sent}건")
                print(f"   사용량 날짜: {record.usage_date}")
                print(f"   마지막 업데이트: {record.updated_at}")
                print()
        else:
            print("❌ 오늘의 조직 사용량 기록이 없습니다.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_users()