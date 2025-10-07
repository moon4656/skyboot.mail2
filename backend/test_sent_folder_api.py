#!/usr/bin/env python3
"""보낸 메일함 조회 API 테스트"""

import requests
import json
import time

def test_sent_folder_api():
    """보낸 메일함 조회 API 테스트"""
    base_url = "http://localhost:8001/api/v1"
    
    # 1. 새로운 사용자 생성
    print("1. 새로운 사용자 생성")
    timestamp = int(time.time())
    register_data = {
        "user_id": f"testuser_{timestamp}",
        "username": f"테스트사용자_{timestamp}",
        "email": f"testuser_{timestamp}@example.com",
        "password": "test123",
        "org_code": "example",
        "full_name": "테스트 사용자"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    print(f"   - 회원가입 응답 상태: {response.status_code}")
    
    if response.status_code != 201:
        print(f"   ❌ 회원가입 실패")
        print(f"   - 오류 내용: {response.json()}")
        return
    
    print(f"   ✅ 회원가입 성공")
    user_data = response.json()
    print(f"   - 생성된 사용자 ID: {user_data['user_id']}")
    user_id = register_data["user_id"]
    password = register_data["password"]
    
    # 2. 로그인
    print("2. 로그인")
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    print(f"   - 로그인 응답 상태: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 로그인 실패")
        print(f"   - 오류 내용: {response.json()}")
        return
    
    login_result = response.json()
    print(f"   - 로그인 응답: {login_result}")
    
    # 응답 구조에 따라 토큰 추출
    if "data" in login_result:
        access_token = login_result["data"]["access_token"]
    else:
        access_token = login_result["access_token"]
    
    print(f"   ✅ 로그인 성공")
    
    # 3. 보낸 메일함 조회
    print("3. 보낸 메일함 조회")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{base_url}/mail/sent", headers=headers)
    print(f"   - 보낸 메일함 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        sent_mails = response.json()
        print(f"   ✅ 보낸 메일함 조회 성공")
        print(f"   - 보낸 메일 수: {len(sent_mails.get('data', {}).get('mails', []))}")
        
        if sent_mails.get('data', {}).get('mails'):
            print("   - 보낸 메일 목록:")
            for mail in sent_mails['data']['mails'][:3]:  # 최대 3개만 표시
                print(f"     * 제목: {mail.get('subject', 'N/A')}")
                print(f"       수신자: {mail.get('recipients', [])}")
                print(f"       발송시간: {mail.get('sent_at', 'N/A')}")
    else:
        print(f"   ❌ 보낸 메일함 조회 실패")
        print(f"   - 오류 내용: {response.json()}")
    
    # 4. 모든 메일 폴더 목록 조회
    print("4. 모든 메일 폴더 목록 조회")
    response = requests.get(f"{base_url}/mail/folders", headers=headers)
    print(f"   - 폴더 목록 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        folders = response.json()
        print(f"   ✅ 폴더 목록 조회 성공")
        print(f"   - 폴더 목록:")
        for folder in folders.get('data', []):
            print(f"     * {folder.get('name', 'N/A')} ({folder.get('folder_type', 'N/A')})")
    else:
        print(f"   ❌ 폴더 목록 조회 실패")
        print(f"   - 오류 내용: {response.json()}")

if __name__ == "__main__":
    test_sent_folder_api()