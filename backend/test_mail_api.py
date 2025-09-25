#!/usr/bin/env python3
"""
받은편지함과 임시보관함 API 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_mail_apis():
    """메일 API들을 테스트합니다."""
    
    # 1. 로그인하여 토큰 획득
    print("1. 로그인 테스트...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"토큰 획득 성공: {access_token[:20]}...")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. 받은편지함 API 테스트
            print("\n2. 받은편지함 API 테스트...")
            inbox_response = requests.get(f"{BASE_URL}/mail/inbox", headers=headers)
            print(f"받은편지함 응답 상태: {inbox_response.status_code}")
            print(f"받은편지함 응답 내용: {inbox_response.text}")
            
            # 3. 임시보관함 API 테스트
            print("\n3. 임시보관함 API 테스트...")
            drafts_response = requests.get(f"{BASE_URL}/mail/drafts", headers=headers)
            print(f"임시보관함 응답 상태: {drafts_response.status_code}")
            print(f"임시보관함 응답 내용: {drafts_response.text}")
            
            # 4. 보낸편지함 API 테스트
            print("\n4. 보낸편지함 API 테스트...")
            sent_response = requests.get(f"{BASE_URL}/mail/sent", headers=headers)
            print(f"보낸편지함 응답 상태: {sent_response.status_code}")
            print(f"보낸편지함 응답 내용: {sent_response.text}")
            
        else:
            print(f"로그인 실패: {response.text}")
            
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_mail_apis()