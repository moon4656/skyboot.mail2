#!/usr/bin/env python3
"""
서버 연결 상태 확인 테스트 스크립트
"""

import requests
import json

def test_server_connection():
    """서버 연결 상태를 확인합니다."""
    
    base_url = "http://localhost:8001"
    
    print("🔍 서버 연결 상태 확인 중...")
    
    # 1. 기본 루트 엔드포인트 테스트
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ 루트 엔드포인트: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"❌ 루트 엔드포인트 실패: {e}")
    
    # 2. 헬스체크 엔드포인트 테스트
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ 헬스체크: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"❌ 헬스체크 실패: {e}")
    
    # 3. API 문서 엔드포인트 테스트
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ API 문서: {response.status_code}")
    except Exception as e:
        print(f"❌ API 문서 실패: {e}")
    
    # 4. 로그인 엔드포인트 테스트 (POST 요청)
    try:
        login_data = {
            "user_id": "user01",
            "password": "test"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=5)
        print(f"✅ 로그인 엔드포인트: {response.status_code}")
        if response.status_code == 200:
            print("   로그인 성공!")
        else:
            print(f"   로그인 실패: {response.text}")
    except Exception as e:
        print(f"❌ 로그인 엔드포인트 실패: {e}")

if __name__ == "__main__":
    test_server_connection()