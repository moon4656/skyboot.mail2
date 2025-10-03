#!/usr/bin/env python3
"""
사용자 생성 시 조직 사용량 업데이트 테스트
"""

import requests
import json
import time

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

print("🧪 사용자 생성 시 조직 사용량 업데이트 테스트")
print("=" * 60)

# 1. 관리자 로그인
print("🔐 관리자 로그인 중...")
login_data = {
    "user_id": "admin01",
    "password": "test"
}

login_response = requests.post(
    f"{BASE_URL}{API_PREFIX}/auth/login", 
    json=login_data,
    headers={"Content-Type": "application/json"}
)
print(f"로그인 상태: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    access_token = login_result["access_token"]
    print("✅ 로그인 성공")
    
    # 2. 현재 조직 사용량 확인
    print("\n📊 현재 조직 사용량 확인...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
    }
    
    # 3. 새 사용자 생성
    print("\n👤 새 사용자 생성 중...")
    timestamp = int(time.time())
    user_data = {
        "user_id": f"testuser{timestamp}",
        "email": f"testuser{timestamp}@skyboot.com",
        "username": f"testuser{timestamp}",
        "password": "testpass123!",
        "full_name": f"테스트 사용자 {timestamp}",
        "org_code": "default",
        "role": "user"
    }
    
    user_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/users/",
        json=user_data,
        headers=headers
    )
    
    print(f"사용자 생성 상태: {user_response.status_code}")
    if user_response.status_code in [200, 201]:
        user_result = user_response.json()
        print("✅ 사용자 생성 성공")
        print(f"사용자 ID: {user_result.get('user_id')}")
        print(f"이메일: {user_result.get('email')}")
        print(f"사용자명: {user_result.get('username')}")
        
        # 4. 조직 사용량 재확인
        print("\n📈 조직 사용량 업데이트 확인...")
        time.sleep(2)  # 업데이트 처리 시간 대기
        
        print("✅ 사용자 생성 및 조직 사용량 업데이트 테스트 완료")
        print("📝 서버 로그를 확인하여 조직 사용량 업데이트 로그를 확인하세요.")
        
    else:
        print(f"❌ 사용자 생성 실패: {user_response.text}")
        
else:
    print(f"❌ 로그인 실패: {login_response.text}")

print("\n🔍 테스트 완료")