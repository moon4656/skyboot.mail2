#!/usr/bin/env python3
"""
메일 읽음 처리 엔드포인트 테스트 스크립트
"""

import requests
import json
from datetime import datetime

# 서버 설정
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"

def create_test_user(email: str, username: str, password: str):
    """테스트용 사용자 생성"""
    register_data = {
        "email": email,
        "username": username,
        "password": password
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data, headers=headers)
    print(f"사용자 생성 테스트 - 상태 코드: {response.status_code}")
    
    if response.status_code == 201:
        print("사용자 생성 성공!")
        return True
    elif response.status_code == 400:
        print("사용자가 이미 존재합니다.")
        return True  # 이미 존재하는 경우도 성공으로 처리
    else:
        print(f"사용자 생성 실패: {response.text}")
        return False

def login_user(email: str, password: str):
    """사용자 로그인"""
    login_data = {
        "email": email,
        "password": password
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(LOGIN_URL, json=login_data, headers=headers)
    print(f"로그인 테스트 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        return result.get("access_token")
    else:
        print(f"로그인 실패: {response.text}")
        return None





def send_test_mail(token: str) -> str:
    """테스트용 메일 발송"""
    headers = {"Authorization": f"Bearer {token}"}
    
    mail_data = {
        "to_emails": "test@example.com",  # 자기 자신에게 발송
        "subject": "테스트 메일 - 읽음 처리 테스트",
        "content": "이것은 읽음 처리 테스트를 위한 메일입니다.",
        "priority": "normal"
    }
    
    response = requests.post(f"{BASE_URL}/mail/send", headers=headers, data=mail_data)
    print(f"메일 발송 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"메일 발송 성공: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("mail_uuid")
    else:
        print(f"❌ 메일 발송 실패: {response.text}")
        return None

def test_read_endpoint():
    """메일 읽음 처리 엔드포인트 테스트 함수"""
    print("=== 메일 읽음 처리 엔드포인트 테스트 시작 ===")
    print(f"테스트 시간: {datetime.now()}")
    
    # 1. 테스트용 사용자 생성
    print("\n1. 테스트용 사용자 생성...")
    if not create_test_user("test@example.com", "testuser", "testpassword123"):
        print("❌ 사용자 생성 실패로 테스트를 중단합니다.")
        return
    
    # 2. 로그인
    print("\n2. 로그인...")
    token = login_user("test@example.com", "testpassword123")
    if not token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    print("✅ 로그인 성공")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. 테스트용 메일 발송
    print("\n3. 테스트용 메일 발송...")
    mail_uuid = send_test_mail(token)
    if not mail_uuid:
        print("❌ 테스트용 메일 발송 실패로 테스트를 중단합니다.")
        return
    
    print(f"✅ 테스트용 메일 발송 성공! Mail UUID: {mail_uuid}")
    
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
        
        # 5. 메일 읽음 처리 테스트
        print("\n5. 메일 읽음 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/read", headers=headers)
        print(f"메일 읽음 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 응답 검증
            if data.get("success"):
                print("✅ 메일 읽음 처리 성공!")
            else:
                print(f"❌ 메일 읽음 처리 실패: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 메일 읽음 처리 실패: {response.text}")
        
        # 6. 같은 메일 다시 읽음 처리 (이미 읽은 메일)
        print("\n6. 이미 읽은 메일 다시 읽음 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/read", headers=headers)
        print(f"이미 읽은 메일 읽음 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("success"):
                print("✅ 이미 읽은 메일 처리 성공!")
            else:
                print(f"⚠️ 이미 읽은 메일 처리: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 이미 읽은 메일 처리 실패: {response.text}")
    else:
        print(f"❌ 보낸 메일함 조회 실패: {response.text}")
        return
    
    # 7. 존재하지 않는 메일 읽음 처리 테스트
    print("\n7. 존재하지 않는 메일 읽음 처리 테스트...")
    
    nonexistent_mail_id = "nonexistent-mail-id-12345"
    response = requests.post(f"{BASE_URL}/mail/{nonexistent_mail_id}/read", headers=headers)
    print(f"존재하지 않는 메일 읽음 처리 - 상태 코드: {response.status_code}")
    
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
    test_read_endpoint()

if __name__ == "__main__":
    test_read_endpoint()