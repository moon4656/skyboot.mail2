#!/usr/bin/env python3
"""
메일 테스트용 사용자 등록 스크립트
"""

import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def register_test_user():
    """테스트용 사용자 등록"""
    print("=" * 60)
    print("🔧 메일 테스트용 사용자 등록")
    print("=" * 60)
    
    # 사용자 등록 데이터
    register_data = {
        "username": "mailtest",
        "email": "mailtest@example.com",
        "password": "password123",
        "full_name": "Mail Test User",
        "org_name": "SkyBoot Mail Test Org"
    }
    
    try:
        print("📝 사용자 등록 중...")
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 사용자 등록 성공!")
            print(f"   이메일: {register_data['email']}")
            print(f"   이름: {register_data['full_name']}")
            print(f"   조직: {register_data['org_name']}")
            print(f"   사용자 UUID: {result.get('user_uuid')}")
            print(f"   조직 ID: {result.get('org_id')}")
            
            # 등록 후 바로 로그인 테스트
            print("\n🔑 로그인 테스트...")
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            
            login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                print("✅ 로그인 성공!")
                print(f"   토큰 타입: {token_data.get('token_type')}")
                print(f"   만료 시간: {token_data.get('expires_in')}초")
                return True
            else:
                print(f"❌ 로그인 실패: {login_response.text}")
                return False
                
        else:
            print(f"❌ 사용자 등록 실패 (상태코드: {response.status_code})")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"📅 시작 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")
    success = register_test_user()
    
    if success:
        print("\n🎉 테스트용 사용자 등록 및 로그인이 성공적으로 완료되었습니다!")
        print("이제 mail_core_router.py 테스트를 진행할 수 있습니다.")
    else:
        print("\n⚠️ 테스트용 사용자 등록에 실패했습니다.")
    
    print(f"📅 종료 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")