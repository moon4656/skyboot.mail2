#!/usr/bin/env python3
"""
엔드포인트 직접 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint_exists():
    """엔드포인트가 존재하는지 확인"""
    
    # 1. 인증 없이 검색 엔드포인트 테스트
    print("1. 메일 검색 엔드포인트 테스트 (인증 없음)")
    try:
        response = requests.post(f"{BASE_URL}/mail/search", json={"query": "test"})
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 2. 통계 엔드포인트 테스트
    print("\n2. 메일 통계 엔드포인트 테스트 (인증 없음)")
    try:
        response = requests.get(f"{BASE_URL}/mail/stats")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 3. 읽지 않은 메일 엔드포인트 테스트
    print("\n3. 읽지 않은 메일 엔드포인트 테스트 (인증 없음)")
    try:
        response = requests.get(f"{BASE_URL}/mail/unread")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 4. 로그인 후 토큰으로 테스트
    print("\n4. 로그인 후 인증된 요청 테스트")
    
    # 로그인
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"   로그인 성공, 토큰 획득")
            
            # 인증된 요청
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 검색 테스트
            response = requests.post(f"{BASE_URL}/mail/search", json={"query": "test"}, headers=headers)
            print(f"   검색 (인증됨) - 상태 코드: {response.status_code}")
            print(f"   응답: {response.text[:200]}...")
            
        else:
            print(f"   로그인 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   오류: {e}")

if __name__ == "__main__":
    test_endpoint_exists()