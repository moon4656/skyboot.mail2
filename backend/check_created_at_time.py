#!/usr/bin/env python3
"""
메일 테이블의 created_at 시간 확인 스크립트
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_mail_created_at():
    """메일 테이블의 created_at 시간을 확인합니다."""
    print("🕐 메일 created_at 시간 확인 중...")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # 최근 10개 메일의 created_at 시간 조회
            query = text("""
                SELECT 
                    mail_uuid,
                    subject,
                    sender_uuid,
                    created_at,
                    sent_at,
                    status,
                    EXTRACT(TIMEZONE FROM created_at) as timezone_offset
                FROM mails 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            result = db.execute(query)
            mails = result.fetchall()
            
            if not mails:
                print("❌ 메일 데이터가 없습니다.")
                return
            
            print(f"📧 최근 {len(mails)}개 메일의 created_at 시간:")
            print("-" * 60)
            
            current_time = datetime.now(timezone.utc)
            print(f"🕐 현재 시간 (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"🕐 현재 시간 (로컬): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            for i, mail in enumerate(mails, 1):
                print(f"\n{i}. 메일 UUID: {mail.mail_uuid}")
                print(f"   제목: {mail.subject}")
                print(f"   발송자 UUID: {mail.sender_uuid}")
                print(f"   상태: {mail.status}")
                print(f"   📅 created_at: {mail.created_at}")
                print(f"   📤 sent_at: {mail.sent_at}")
                
                if mail.timezone_offset is not None:
                    print(f"   🌍 타임존 오프셋: {mail.timezone_offset}초")
                
                # 시간 차이 계산
                if mail.created_at:
                    if mail.created_at.tzinfo is None:
                        # naive datetime인 경우 UTC로 가정
                        mail_time_utc = mail.created_at.replace(tzinfo=timezone.utc)
                    else:
                        mail_time_utc = mail.created_at.astimezone(timezone.utc)
                    
                    time_diff = current_time - mail_time_utc
                    print(f"   ⏱️  현재 시간과의 차이: {time_diff}")
                    
                    # 시간 형식 분석
                    print(f"   🔍 시간 형식 분석:")
                    print(f"      - 원본: {mail.created_at}")
                    print(f"      - 타입: {type(mail.created_at)}")
                    print(f"      - 타임존 정보: {mail.created_at.tzinfo}")
                    print(f"      - UTC 변환: {mail_time_utc}")
            
            # 타임존 설정 확인
            print("\n" + "=" * 60)
            print("🌍 데이터베이스 타임존 설정 확인:")
            
            timezone_query = text("SHOW timezone;")
            timezone_result = db.execute(timezone_query)
            db_timezone = timezone_result.fetchone()
            print(f"   데이터베이스 타임존: {db_timezone[0] if db_timezone else 'Unknown'}")
            
            # 현재 시간 비교
            now_query = text("SELECT NOW(), CURRENT_TIMESTAMP, timezone('UTC', NOW());")
            now_result = db.execute(now_query)
            now_times = now_result.fetchone()
            
            if now_times:
                print(f"   DB NOW(): {now_times[0]}")
                print(f"   DB CURRENT_TIMESTAMP: {now_times[1]}")
                print(f"   DB UTC NOW(): {now_times[2]}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_mail_created_at()