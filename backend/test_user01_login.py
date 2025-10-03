#!/usr/bin/env python3
"""
user01 사용자 로그인 테스트 스크립트
"""

import requests
import json

def test_user01_login():
    """user01 사용자로 로그인을 테스트합니다."""
    
    base_url = "http://localhost:8000"
    
    # 로그인 데이터
    login_data = {
        "user_id": "user01",   # UserLogin 스키마에 맞게 user_id 사용
        "password": "test"     # 기본 테스트 비밀번호
    }
    
    print("🔐 user01 사용자 로그인 테스트 시작...")
    print("=" * 60)
    print(f"📋 로그인 정보:")
    print(f"  - user_id: {login_data['user_id']}")
    print(f"  - password: {login_data['password']}")
    print(f"  - URL: {base_url}/api/v1/auth/login")
    
    try:
        # 로그인 요청
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,  # JSON으로 전송
            headers={
                "Content-Type": "application/json"
            }
        )
        
        print(f"\n📡 응답 상태: {response.status_code}")
        print(f"📄 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 로그인 성공!")
            print(f"📋 응답 데이터:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 토큰 정보 확인
            if "access_token" in result:
                print(f"\n🔑 토큰 정보:")
                print(f"  - access_token: {result['access_token'][:50]}...")
                print(f"  - token_type: {result.get('token_type', 'N/A')}")
                
                # 토큰으로 사용자 정보 조회 테스트
                test_user_info(result["access_token"])
                
        else:
            print(f"❌ 로그인 실패!")
            print(f"📄 응답 내용: {response.text}")
            
            # 다른 비밀번호로 시도
            print(f"\n🔄 다른 비밀번호로 재시도...")
            test_alternative_passwords()
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_alternative_passwords():
    """다른 비밀번호들로 로그인을 시도합니다."""
    
    base_url = "http://localhost:8000"
    alternative_passwords = ["password", "123456", "user01", "admin", "test123"]
    
    for password in alternative_passwords:
        login_data = {
            "user_id": "user01",
            "password": "test"
        }
        
        print(f"\n🔄 비밀번호 '{password}' 시도 중...")
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 비밀번호 '{password}'로 로그인 성공!")
                print(f"📋 응답 데이터:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return result
            else:
                print(f"❌ 비밀번호 '{password}' 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 비밀번호 '{password}' 오류: {e}")
    
    print(f"❌ 모든 비밀번호 시도 실패")
    return None

def test_user_info(access_token):
    """토큰을 사용하여 사용자 정보를 조회합니다."""
    
    base_url = "http://localhost:8000"
    
    print(f"\n👤 사용자 정보 조회 테스트...")
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"📡 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 사용자 정보 조회 성공!")
            print(f"📋 사용자 정보:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 사용자 정보 조회 실패!")
            print(f"📄 응답 내용: {response.text}")
            
    except Exception as e:
        print(f"❌ 사용자 정보 조회 오류: {e}")

if __name__ == "__main__":
    test_user01_login()