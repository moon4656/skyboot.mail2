#!/usr/bin/env python3
"""
수신자 사용자 활성화 스크립트

recipient@test.example.com 사용자를 활성화합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def activate_recipient():
    """수신자 사용자 활성화"""
    try:
        # 설정 사용
        
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("📧 recipient@test.example.com 사용자 활성화 중...")
        
        # MailUser 테이블에서 사용자 활성화
        result = db.execute(text("""
            UPDATE mail_users 
            SET is_active = true 
            WHERE email = 'recipient@test.example.com'
        """))
        
        # User 테이블에서도 활성화 (있다면)
        user_result = db.execute(text("""
            UPDATE users 
            SET is_active = true 
            WHERE email = 'recipient@test.example.com'
        """))
        
        db.commit()
        
        if result.rowcount > 0:
            print("✅ recipient@test.example.com 메일 사용자 활성화 완료")
        else:
            print("⚠️ recipient@test.example.com 메일 사용자를 찾을 수 없음")
            
        if user_result.rowcount > 0:
            print("✅ recipient@test.example.com 일반 사용자 활성화 완료")
        else:
            print("⚠️ recipient@test.example.com 일반 사용자를 찾을 수 없음")
        
        # 활성화 확인
        check_result = db.execute(text("""
            SELECT email, is_active, org_id 
            FROM mail_users 
            WHERE email = 'recipient@test.example.com'
        """)).fetchone()
        
        if check_result:
            print(f"📧 확인 결과:")
            print(f"   - 이메일: {check_result[0]}")
            print(f"   - 활성 상태: {check_result[1]}")
            print(f"   - 조직 ID: {check_result[2]}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 사용자 활성화 중 오류: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    success = activate_recipient()
    if success:
        print("\n✅ 수신자 활성화 완료")
    else:
        print("\n❌ 수신자 활성화 실패")
        sys.exit(1)