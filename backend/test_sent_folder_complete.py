#!/usr/bin/env python3
"""메일 발송 및 보낸 메일함 조회 완전 테스트"""

import requests
import json
import time

def test_complete_mail_flow():
    """메일 발송부터 보낸 메일함 조회까지 완전한 플로우 테스트"""
    base_url = "http://localhost:8001/api/v1"
    
    # 1. 새로운 사용자 생성
    print("1. 새로운 사용자 생성")
    timestamp = int(time.time())
    register_data = {
        "user_id": f"sender_{timestamp}",
        "username": f"발송자_{timestamp}",
        "email": f"sender_{timestamp}@example.com",
        "password": "test123",
        "org_code": "example",
        "full_name": "메일 발송자"
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
    access_token = login_result["access_token"]
    print(f"   ✅ 로그인 성공")
    
    # 3. 보낸 메일함 조회 (발송 전)
    print("3. 보낸 메일함 조회 (발송 전)")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{base_url}/mail/sent", headers=headers)
    print(f"   - 보낸 메일함 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        sent_mails_before = response.json()
        mail_count_before = len(sent_mails_before.get('data', {}).get('mails', []))
        print(f"   ✅ 보낸 메일함 조회 성공")
        print(f"   - 발송 전 보낸 메일 수: {mail_count_before}")
    else:
        print(f"   ❌ 보낸 메일함 조회 실패")
        print(f"   - 오류 내용: {response.json()}")
        return
    
    # 4. 메일 발송
    print("4. 메일 발송")
    mail_data = {
        "to": ["testrecipient@example.com"],
        "subject": f"테스트 메일 {timestamp}",
        "body_text": f"이것은 {timestamp} 시점에 발송된 테스트 메일입니다.",
        "priority": "normal",
        "is_draft": False
    }
    
    response = requests.post(f"{base_url}/mail/send-json", json=mail_data, headers=headers)
    print(f"   - 메일 발송 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ 메일 발송 성공")
        response_data = response.json()
        print(f"   - 응답 데이터: {response_data}")
        mail_uuid = response_data.get("mail_uuid", "N/A")
        print(f"   - 메일 UUID: {mail_uuid}")
    else:
        print("   ❌ 메일 발송 실패")
        print(f"   - 오류 내용: {response.json()}")
        return
    
    # 5. 잠시 대기 (메일 처리 시간)
    print("5. 메일 처리 대기 (5초)")
    time.sleep(5)
    
    # 6. 보낸 메일함 조회 (발송 후)
    print("6. 보낸 메일함 조회 (발송 후)")
    response = requests.get(f"{base_url}/mail/sent", headers=headers)
    print(f"   - 보낸 메일함 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        sent_mails_after = response.json()
        mail_count_after = len(sent_mails_after.get('data', {}).get('mails', []))
        print(f"   ✅ 보낸 메일함 조회 성공")
        print(f"   - 발송 후 보낸 메일 수: {mail_count_after}")
        
        if mail_count_after > mail_count_before:
            print(f"   ✅ 보낸 메일이 보낸 메일함에 정상적으로 추가됨")
            
            # 최신 메일 정보 출력
            if sent_mails_after.get('data', {}).get('mails'):
                latest_mail = sent_mails_after['data']['mails'][0]
                print(f"   - 최신 보낸 메일:")
                print(f"     * 제목: {latest_mail.get('subject', 'N/A')}")
                print(f"     * 수신자: {latest_mail.get('recipients', [])}")
                print(f"     * 발송시간: {latest_mail.get('sent_at', 'N/A')}")
                print(f"     * 상태: {latest_mail.get('status', 'N/A')}")
        else:
            print(f"   ❌ 보낸 메일이 보낸 메일함에 추가되지 않음")
    else:
        print(f"   ❌ 보낸 메일함 조회 실패")
        print(f"   - 오류 내용: {response.json()}")
    
    # 7. 개별 메일 상세 조회 (메일 UUID가 있는 경우)
    if mail_uuid and mail_uuid != "N/A":
        print("7. 개별 메일 상세 조회")
        response = requests.get(f"{base_url}/mail/sent/{mail_uuid}", headers=headers)
        print(f"   - 메일 상세 조회 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 메일 상세 조회 성공")
            mail_detail = response.json()
            print(f"   - 메일 제목: {mail_detail.get('subject', 'N/A')}")
            print(f"   - 발송 시간: {mail_detail.get('sent_at', 'N/A')}")
        else:
            print("   ❌ 메일 상세 조회 실패")
            print(f"   - 오류 내용: {response.json()}")
    else:
        print("7. 개별 메일 상세 조회 건너뜀 (메일 UUID 없음)")
    
    print("\n🎯 테스트 완료!")
    print(f"📊 결과 요약:")
    print(f"   - 메일 발송: {'성공' if 'mail_uuid' in locals() and mail_uuid != 'N/A' else '실패'}")
    print(f"   - 보낸 메일함 반영: {'성공' if 'mail_count_after' in locals() and mail_count_after > 0 else '실패'}")
    print(f"   - 메일 UUID: {mail_uuid if 'mail_uuid' in locals() else 'N/A'}")

if __name__ == "__main__":
    test_complete_mail_flow()