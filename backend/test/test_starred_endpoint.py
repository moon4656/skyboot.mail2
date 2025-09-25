#!/usr/bin/env python3
"""
중요 표시된 메일 조회 엔드포인트 테스트 스크립트
"""

import requests
import json

# 서버 URL
BASE_URL = "http://localhost:8000"

def test_starred_endpoint():
    """중요 표시된 메일 조회 엔드포인트 테스트"""
    
    # 1. 로그인
    print("1. 로그인 테스트...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"로그인 응답 상태 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"로그인 실패: {response.text}")
        return
    
    login_result = response.json()
    access_token = login_result["access_token"]
    print("로그인 성공!")
    
    # 2. 중요 표시된 메일 조회 테스트
    print("\n2. 중요 표시된 메일 조회 테스트...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/mail/starred", headers=headers)
    print(f"중요 표시된 메일 조회 응답 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("중요 표시된 메일 조회 성공!")
        print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"중요 표시된 메일 조회 실패: {response.text}")
    
    # 3. 페이지네이션 테스트
    print("\n3. 페이지네이션 테스트...")
    response = requests.get(f"{BASE_URL}/mail/starred?page=1&limit=5", headers=headers)
    print(f"페이지네이션 응답 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("페이지네이션 테스트 성공!")
        print(f"페이지 정보: 페이지 {result['data']['page']}, 총 {result['data']['total']}개")
    else:
        print(f"페이지네이션 테스트 실패: {response.text}")

if __name__ == "__main__":
    test_starred_endpoint()