#!/usr/bin/env python3
"""
로그인 API 응답 확인 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_login_response():
    """로그인 API 응답을 테스트합니다."""
    
    print("🔍 로그인 API 응답 테스트 시작")
    print("=" * 50)
    
    # API 엔드포인트
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/auth/login"
    
    # 로그인 데이터
    login_data = {
        "email": "admin@skyboot.com",
        "password": "Admin123!@#"
    }
    
    try:
        print(f"📤 로그인 요청 전송: {login_url}")
        print(f"📋 요청 데이터: {json.dumps(login_data, indent=2)}")
        
        # 로그인 요청
        response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 응답 상태 코드: {response.status_code}")
        print(f"📋 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\n✅ 로그인 성공!")
            print(f"📋 응답 데이터:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 토큰 확인
            access_token = response_data.get("access_token")
            refresh_token = response_data.get("refresh_token")
            
            print(f"\n🔑 토큰 정보:")
            print(f"   - 액세스 토큰 존재: {'✅' if access_token else '❌'}")
            print(f"   - 리프레시 토큰 존재: {'✅' if refresh_token else '❌'}")
            
            if access_token:
                print(f"   - 액세스 토큰 길이: {len(access_token)}")
                print(f"   - 액세스 토큰 시작: {access_token[:50]}...")
                
            if refresh_token:
                print(f"   - 리프레시 토큰 길이: {len(refresh_token)}")
                print(f"   - 리프레시 토큰 시작: {refresh_token[:50]}...")
            
        else:
            print(f"\n❌ 로그인 실패!")
            print(f"📋 오류 응답:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 로그인 API 응답 테스트 완료")

if __name__ == "__main__":
    test_login_response()