#!/usr/bin/env python3
"""
API 응답 구조 디버그 스크립트
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USER_ID = "admin01"
TEST_PASSWORD = "test"

def get_auth_token():
    """인증 토큰 획득"""
    login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
    login_data = {
        "user_id": TEST_USER_ID,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 오류: {str(e)}")
        return None

def debug_api_response():
    """API 응답 구조 디버그"""
    print("🔍 API 응답 구조 디버그 시작")
    
    # 1. 인증 토큰 획득
    token = get_auth_token()
    if not token:
        print("❌ 인증 실패")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. 조직 설정 조회
    settings_url = f"{BASE_URL}{API_PREFIX}/organizations/current/settings"
    
    try:
        response = requests.get(settings_url, headers=headers)
        print(f"📡 응답 상태 코드: {response.status_code}")
        print(f"📡 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            raw_response = response.text
            print(f"📡 원시 응답 (처음 500자):")
            print(raw_response[:500])
            print("...")
            
            try:
                json_response = response.json()
                print(f"\n📊 JSON 응답 구조:")
                print(f"- 타입: {type(json_response)}")
                print(f"- 키들: {list(json_response.keys()) if isinstance(json_response, dict) else 'dict가 아님'}")
                
                if isinstance(json_response, dict):
                    for key, value in json_response.items():
                        print(f"  - {key}: {type(value)} (길이: {len(str(value))})")
                        if key == 'settings':
                            print(f"    settings 타입: {type(value)}")
                            if isinstance(value, dict):
                                print(f"    settings 키들: {list(value.keys())}")
                            elif isinstance(value, str):
                                print(f"    settings 문자열 내용 (처음 200자): {value[:200]}")
                
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {str(e)}")
                return False
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 오류: {str(e)}")
        return False

if __name__ == "__main__":
    debug_api_response()