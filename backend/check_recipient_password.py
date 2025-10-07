#!/usr/bin/env python3
"""
recipient@test.example.com 사용자의 비밀번호 확인 및 설정 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from passlib.context import CryptContext
import requests

# 패스워드 해싱 컨텍스트 (AuthService와 동일)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_and_set_password():
    """수신자 비밀번호 확인 및 설정"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("📧 recipient@test.example.com 사용자 비밀번호 확인 중...")
        
        # 사용자 정보 조회
        user_result = db.execute(text("""
            SELECT user_id, email, hashed_password 
            FROM users 
            WHERE email = 'recipient@test.example.com'
        """)).fetchone()
        
        if user_result:
            print(f"✅ 사용자 발견:")
            print(f"   - user_id: {user_result[0]}")
            print(f"   - email: {user_result[1]}")
            print(f"   - hashed_password 존재: {'Yes' if user_result[2] else 'No'}")
            
            # 새 비밀번호 설정
            new_password = "recipient123"
            password_hash = pwd_context.hash(new_password)
            
            # 비밀번호 업데이트
            db.execute(text("""
                UPDATE users 
                SET hashed_password = :password_hash 
                WHERE email = 'recipient@test.example.com'
            """), {"password_hash": password_hash})
            
            db.commit()
            print(f"✅ 비밀번호 업데이트 완료: {new_password}")
            
            # 로그인 테스트
            print("\n🔐 로그인 테스트 중...")
            print(f"   - user_id로 로그인 시도: {user_result[0]}")
            login_data = {
                "user_id": user_result[0],  # user_id 사용
                "password": new_password
            }
            
            response = requests.post(
                "http://localhost:8001/api/v1/auth/login",
                headers={"Content-Type": "application/json"},
                json=login_data
            )
            
            print(f"   - 응답 상태 코드: {response.status_code}")
            print(f"   - 응답 내용: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("access_token"):
                    print("✅ 로그인 테스트 성공!")
                    print(f"   - 토큰: {result.get('access_token', 'N/A')[:50]}...")
                else:
                    print(f"❌ 로그인 실패: {result}")
            else:
                print(f"❌ 로그인 요청 실패: {response.status_code}")
        else:
            print("❌ recipient@test.example.com 사용자를 찾을 수 없음")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 비밀번호 확인 중 오류: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    success = check_and_set_password()
    if success:
        print("\n✅ 비밀번호 확인 및 설정 완료")
    else:
        print("\n❌ 비밀번호 확인 및 설정 실패")
        sys.exit(1)