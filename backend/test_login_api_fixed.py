#!/usr/bin/env python3
"""수정된 로그인 API 테스트 스크립트"""

import requests
import json

def test_login_api():
    """user_id 기반 로그인 API를 테스트합니다."""
    
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/auth/login"
    
    # 테스트 데이터 (user_id 기반)
    test_credentials = {
        "user_id": "moonsoo",  # email 대신 user_id 사용
        "password": "safe70!!"
    }
    
    print("🧪 로그인 API 테스트 시작...")
    print(f"URL: {login_url}")
    print(f"요청 데이터: {json.dumps(test_credentials, indent=2, ensure_ascii=False)}")
    
    try:
        # 로그인 요청
        response = requests.post(
            login_url,
            json=test_credentials,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 응답 상태 코드: {response.status_code}")
        print(f"📊 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 로그인 성공!")
            print(f"📄 응답 데이터:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 토큰 확인
            if "access_token" in result:
                print(f"🔑 액세스 토큰: {result['access_token'][:50]}...")
            if "refresh_token" in result:
                print(f"🔄 리프레시 토큰: {result['refresh_token'][:50]}...")
                
        else:
            print("❌ 로그인 실패!")
            try:
                error_data = response.json()
                print(f"📄 오류 응답:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"📄 오류 텍스트: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_login_api()