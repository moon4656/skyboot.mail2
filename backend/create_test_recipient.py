#!/usr/bin/env python3
"""
테스트 수신자 사용자 생성 스크립트
"""

import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
import bcrypt
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_recipient():
    """테스트 수신자 사용자 생성"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # 기본 조직 찾기 (test.example.com 도메인)
            org = session.query(Organization).filter(Organization.domain == "test.example.com").first()
            if not org:
                print("❌ test.example.com 조직을 찾을 수 없습니다.")
                return None
            
            print(f"✅ 조직 확인: {org.name} (ID: {org.org_id})")
            
            # 기존 사용자 확인
            email = "recipient@test.example.com"
            existing_user = session.query(User).filter(User.email == email).first()
            
            if existing_user:
                # 기존 사용자 비밀번호 업데이트
                print(f"📝 기존 사용자 발견: {email}")
                existing_user.hashed_password = bcrypt.hashpw("recipient123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                session.commit()
                print(f"✅ 비밀번호 업데이트 완료")
                return existing_user.user_id
            else:
                # 새 사용자 생성
                print(f"👤 새 사용자 생성: {email}")
                
                # 비밀번호 해시화
                password = "recipient123"
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                new_user = User(
                    user_id=f"recipient_{int(time.time())}",
                    user_uuid=str(uuid.uuid4()),
                    org_id=org.org_id,
                    email=email,
                    username="recipient",
                    hashed_password=hashed_password,
                    role="user",
                    is_active=True,
                    is_email_verified=True
                )
                
                session.add(new_user)
                session.commit()
                print(f"✅ 새 사용자 생성 완료: {new_user.user_id}")
                return new_user.user_id
                
    except Exception as e:
        print(f"❌ 사용자 생성 오류: {e}")
        return None

def test_login(user_info):
    """생성된 사용자로 로그인 테스트"""
    if not user_info:
        return False
    
    print(f"\n=== 로그인 테스트: {user_info['user_id']} ===")
    
    import requests
    
    BASE_URL = "http://localhost:8001"
    
    login_data = {
        "user_id": user_info["user_id"],
        "password": user_info["password"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers=headers,
        json=login_data
    )
    
    print(f"로그인 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {token[:50]}...")
        return True
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return False

def main():
    """메인 함수"""
    user_info = create_test_recipient()
    
    if user_info:
        success = test_login(user_info)
        if success:
            print(f"\n🎉 테스트 수신자 준비 완료!")
            print(f"   사용자 ID: {user_info['user_id']}")
            print(f"   이메일: {user_info['email']}")
            print(f"   패스워드: {user_info['password']}")
        else:
            print("\n❌ 로그인 테스트 실패")
    else:
        print("\n❌ 사용자 생성 실패")

if __name__ == "__main__":
    main()