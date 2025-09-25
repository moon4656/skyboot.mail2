#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메일 읽지 않음 처리 엔드포인트 테스트 스크립트

이 스크립트는 다음 기능들을 테스트합니다:
1. 사용자 생성 및 로그인
2. 테스트용 메일 발송
3. 보낸 메일함에서 메일 조회
4. 메일 읽음 처리 (읽음 상태로 만들기)
5. 메일 읽지 않음 처리 테스트
6. 이미 읽지 않음 상태인 메일 다시 읽지 않음 처리
7. 존재하지 않는 메일 읽지 않음 처리 테스트
"""

import requests
import json
import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123",
    "display_name": "testuser"
}

def send_test_mail(headers, recipient_email="test@example.com"):
    """테스트용 메일 발송"""
    subject = "테스트 메일 - 읽지 않음 처리 테스트"
    content = "이것은 읽지 않음 처리 테스트를 위한 메일입니다."
    
    mail_data = {
        "to_emails": recipient_email,
        "subject": subject,
        "content": content,
        "priority": "normal"
    }
    
    response = requests.post(f"{BASE_URL}/mail/send", data=mail_data, headers=headers)
    print(f"메일 발송 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"메일 발송 성공: {json.dumps(data, indent=2, ensure_ascii=False)}")
        mail_uuid = data.get("mail_uuid")
        print(f"✅ 테스트용 메일 발송 성공! Mail UUID: {mail_uuid}")
        return mail_uuid
    else:
        print(f"❌ 메일 발송 실패: {response.text}")
        return None

def test_unread_endpoint():
    """메일 읽지 않음 처리 엔드포인트 테스트"""
    print("=== 메일 읽지 않음 처리 엔드포인트 테스트 시작 ===")
    print(f"테스트 시간: {datetime.datetime.now()}")
    
    # 1. 테스트용 사용자 생성
    print("\n1. 테스트용 사용자 생성...")
    register_data = {
        "email": TEST_USER["email"],
        "username": "testuser",
        "password": TEST_USER["password"]
    }
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"사용자 생성 테스트 - 상태 코드: {register_response.status_code}")
    
    if register_response.status_code == 400:
        print("사용자가 이미 존재합니다.")
    elif register_response.status_code == 201:
        print("✅ 새 사용자 생성 성공")
    else:
        print(f"❌ 사용자 생성 실패: {register_response.text}")
        return
    
    # 2. 로그인
    print("\n2. 로그인...")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"로그인 테스트 - 상태 코드: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ 로그인 성공")
    else:
        print(f"❌ 로그인 실패: {login_response.text}")
        return
    
    # 3. 테스트용 메일 발송
    print("\n3. 테스트용 메일 발송...")
    mail_uuid = send_test_mail(headers)
    if not mail_uuid:
        print("❌ 테스트용 메일 발송 실패로 테스트를 중단합니다.")
        return
    
    # 잠시 대기 (메일 처리 시간)
    import time
    time.sleep(2)
    
    # 4. 보낸 메일함 조회 (자신에게 보낸 메일 확인)
    print("\n4. 보낸 메일함 조회...")
    
    response = requests.get(f"{BASE_URL}/mail/sent", headers=headers)
    print(f"보낸 메일함 조회 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 메일이 있는지 확인
        mails = data.get("mails", [])
        if not mails:
            print("⚠️ 테스트할 메일이 없습니다.")
            return
        
        # 첫 번째 메일 ID 가져오기
        test_mail_id = mails[0].get("mail_uuid")
        print(f"테스트할 메일 ID: {test_mail_id}")
        
        # 5. 먼저 메일을 읽음 상태로 만들기
        print("\n5. 메일을 읽음 상태로 만들기...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/read", headers=headers)
        print(f"메일 읽음 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("success"):
                print("✅ 메일 읽음 처리 성공!")
            else:
                print(f"❌ 메일 읽음 처리 실패: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 메일 읽음 처리 실패: {response.text}")
        
        # 6. 메일 읽지 않음 처리 테스트
        print("\n6. 메일 읽지 않음 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/unread", headers=headers)
        print(f"메일 읽지 않음 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 응답 검증
            if data.get("success"):
                print("✅ 메일 읽지 않음 처리 성공!")
            else:
                print(f"❌ 메일 읽지 않음 처리 실패: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 메일 읽지 않음 처리 실패: {response.text}")
        
        # 7. 같은 메일 다시 읽지 않음 처리 (이미 읽지 않음 상태인 메일)
        print("\n7. 이미 읽지 않음 상태인 메일 다시 읽지 않음 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/unread", headers=headers)
        print(f"이미 읽지 않음 상태인 메일 읽지 않음 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("success"):
                print("✅ 이미 읽지 않음 상태인 메일 처리 성공!")
            else:
                print(f"⚠️ 이미 읽지 않음 상태인 메일 처리: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 이미 읽지 않음 상태인 메일 처리 실패: {response.text}")
    else:
        print(f"❌ 보낸 메일함 조회 실패: {response.text}")
        return
    
    # 8. 존재하지 않는 메일 읽지 않음 처리 테스트
    print("\n8. 존재하지 않는 메일 읽지 않음 처리 테스트...")
    
    nonexistent_mail_id = "nonexistent-mail-id-12345"
    response = requests.post(f"{BASE_URL}/mail/{nonexistent_mail_id}/unread", headers=headers)
    print(f"존재하지 않는 메일 읽지 않음 처리 - 상태 코드: {response.status_code}")
    
    if response.status_code == 404:
        data = response.json()
        print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("✅ 존재하지 않는 메일 처리 성공 (404 반환)")
    elif response.status_code == 200:
        data = response.json()
        print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        if not data.get("success"):
            print("✅ 존재하지 않는 메일 처리 성공 (실패 응답)")
        else:
            print("⚠️ 존재하지 않는 메일인데 성공 응답이 반환됨")
    else:
        print(f"❌ 예상하지 못한 응답: {response.text}")
    
    print("\n=== 테스트 완료 ===")

def main():
    """메인 함수"""
    test_unread_endpoint()

if __name__ == "__main__":
    test_unread_endpoint()