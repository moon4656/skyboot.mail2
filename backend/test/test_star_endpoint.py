#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메일 중요 표시 엔드포인트 테스트 스크립트

이 스크립트는 다음 기능들을 테스트합니다:
1. 사용자 생성 및 로그인
2. 테스트용 메일 발송
3. 보낸 메일함 조회
4. 메일 중요 표시 처리
5. 이미 중요 표시된 메일 다시 중요 표시 처리
6. 존재하지 않는 메일 중요 표시 처리
"""

import requests
import json
import time
import uuid

# 서버 설정
BASE_URL = "http://localhost:8000"

def send_test_mail(headers):
    """
    테스트용 메일을 발송합니다.
    
    Args:
        headers: 인증 헤더
        
    Returns:
        bool: 발송 성공 여부
    """
    mail_data = {
        "to_emails": "test@example.com",
        "subject": f"중요 표시 테스트 메일 - {uuid.uuid4()}",
        "content": "이 메일은 중요 표시 기능을 테스트하기 위한 메일입니다."
    }
    
    response = requests.post(f"{BASE_URL}/mail/send", data=mail_data, headers=headers)
    print(f"메일 발송 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"메일 발송 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("success", False)
    else:
        print(f"메일 발송 실패: {response.text}")
        return False

def create_test_user():
    """기존 MailUser가 연결된 사용자를 사용합니다."""
    print("1. 기존 MailUser 연결된 사용자 사용...")
    
    # sync_mail_users.py 실행 결과에서 확인된 연결된 사용자
    user_data = {
        "email": "test@skyboot.com",
        "username": "skybootuser",
        "password": "test123456"  # test_existing_user.py에서 사용한 비밀번호
    }
    
    print("✅ 기존 연결된 사용자 정보 준비 완료!")
    return user_data

def test_star_endpoint():
    """
    메일 중요 표시 엔드포인트를 테스트합니다.
    """
    print("=== 메일 중요 표시 엔드포인트 테스트 시작 ===\n")
    
    # 1. 기존 연결된 사용자 사용
    register_data = create_test_user()
    
    if not register_data:
        print("❌ 테스트 사용자 준비 실패")
        return
    
    # 2. 로그인
    print("\n2. 로그인...")
    
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"로그인 - 상태 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.text}")
        return
    
    data = response.json()
    access_token = data.get("access_token")
    
    if not access_token:
        print("❌ 액세스 토큰을 받지 못했습니다.")
        return
    
    print("✅ 로그인 성공!")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 3. 테스트용 메일 발송
    print("\n3. 테스트용 메일 발송...")
    
    if not send_test_mail(headers):
        print("❌ 테스트용 메일 발송 실패")
        return
    
    print("✅ 테스트용 메일 발송 성공!")
    
    # 잠시 대기 (메일 처리 시간)
    print("\n메일 처리를 위해 3초 대기...")
    time.sleep(3)
    
    # 4. 보낸 메일함 조회
    print("\n4. 보낸 메일함 조회...")
    
    response = requests.get(f"{BASE_URL}/mail/sent", headers=headers)
    print(f"보낸 메일함 조회 - 상태 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 보낸 메일함 조회 실패: {response.text}")
        return
    
    data = response.json()
    print(f"보낸 메일함 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 메일 목록에서 테스트할 메일 찾기
    mails = data.get("mails", [])
    
    if not mails:
        print("⚠️ 테스트할 메일이 없습니다.")
        return
    
    # 첫 번째 메일을 테스트 대상으로 선택
    test_mail_id = mails[0].get("mail_uuid")
    
    if not test_mail_id:
        print("❌ 메일 ID를 찾을 수 없습니다.")
        return
    
    print(f"✅ 테스트할 메일 ID: {test_mail_id}")
    
    # 5. 메일 중요 표시 처리 테스트
    if test_mail_id:
        print("\n5. 메일 중요 표시 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/star", headers=headers)
        print(f"메일 중요 표시 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 응답 검증
            if data.get("success"):
                print("✅ 메일 중요 표시 처리 성공!")
            else:
                print(f"❌ 메일 중요 표시 처리 실패: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 메일 중요 표시 처리 실패: {response.text}")
        
        # 6. 같은 메일 다시 중요 표시 처리 (이미 중요 표시된 메일)
        print("\n6. 이미 중요 표시된 메일 다시 중요 표시 처리 테스트...")
        
        response = requests.post(f"{BASE_URL}/mail/{test_mail_id}/star", headers=headers)
        print(f"이미 중요 표시된 메일 중요 표시 처리 - 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 응답 검증 (이미 중요 표시된 메일도 성공으로 처리될 수 있음)
            if data.get("success"):
                print("✅ 이미 중요 표시된 메일 처리 성공!")
            else:
                print(f"⚠️ 이미 중요 표시된 메일 처리: {data.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 이미 중요 표시된 메일 처리 실패: {response.text}")
    
    # 7. 존재하지 않는 메일 중요 표시 처리 테스트
    print("\n7. 존재하지 않는 메일 중요 표시 처리 테스트...")
    
    nonexistent_mail_id = "nonexistent-mail-id-12345"
    response = requests.post(f"{BASE_URL}/mail/{nonexistent_mail_id}/star", headers=headers)
    print(f"존재하지 않는 메일 중요 표시 처리 - 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 존재하지 않는 메일은 실패 응답이 와야 함
        if not data.get("success"):
            print("✅ 존재하지 않는 메일 처리 성공 (실패 응답)")
        else:
            print("❌ 존재하지 않는 메일이 성공 응답을 반환했습니다.")
    else:
        print(f"존재하지 않는 메일 처리 응답: {response.text}")
        print("✅ 존재하지 않는 메일 처리 성공 (에러 응답)")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_star_endpoint()