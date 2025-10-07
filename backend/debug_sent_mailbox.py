#!/usr/bin/env python3
"""
보낸 메일함 API 디버깅 스크립트
"""

import requests
import json
import time
import random

def debug_sent_mailbox():
    """보낸 메일함 API를 디버깅합니다."""
    base_url = "http://localhost:8001/api/v1"
    
    # 고유한 사용자 생성
    timestamp = int(time.time())
    user_email = f"debug_user_{timestamp}@example.com"
    
    print("1. 새로운 사용자 생성")
    register_data = {
        "user_id": user_email,
        "username": f"debug_user_{timestamp}",
        "email": user_email,
        "password": "test123",
        "org_code": "test"
    }
    
    register_response = requests.post(f"{base_url}/auth/register", json=register_data)
    print(f"   - 회원가입 응답 상태: {register_response.status_code}")
    
    if register_response.status_code != 201:
        print(f"   ❌ 회원가입 실패: {register_response.text}")
        return
    
    print("   ✅ 회원가입 성공")
    
    print("2. 사용자 로그인")
    login_data = {
        "user_id": user_email,
        "password": "test123"
    }
    
    login_response = requests.post(f"{base_url}/auth/login", json=login_data)
    print(f"   - 로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("   ❌ 로그인 실패")
        print(f"   - 오류 내용: {login_response.json()}")
        return
    
    print("   ✅ 로그인 성공")
    
    # 토큰 추출
    login_result = login_response.json()
    print(f"   - 로그인 응답 전체: {login_result}")
    
    access_token = login_result.get("data", {}).get("access_token")
    if not access_token:
        # 다른 구조 시도
        access_token = login_result.get("access_token")
    
    if not access_token:
        print("   ❌ 토큰 추출 실패")
        return
    
    print(f"   - 토큰: {access_token[:50]}...")
    
    # 헤더 설정
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("\n3. 현재 사용자 정보 확인")
    user_info_response = requests.get(f"{base_url}/auth/me", headers=headers)
    print(f"   - 사용자 정보 응답 상태: {user_info_response.status_code}")
    
    if user_info_response.status_code == 200:
        user_info = user_info_response.json()
        print(f"   - 사용자 정보 전체: {user_info}")
        
        # 다양한 구조 시도
        user_uuid = user_info.get('data', {}).get('user_uuid') or user_info.get('user_uuid', 'N/A')
        user_email_info = user_info.get('data', {}).get('email') or user_info.get('email', 'N/A')
        org_id = user_info.get('data', {}).get('org_id') or user_info.get('org_id', 'N/A')
        
        print(f"   - 사용자 UUID: {user_uuid}")
        print(f"   - 이메일: {user_email_info}")
        print(f"   - 조직 ID: {org_id}")
    else:
        print(f"   ❌ 사용자 정보 조회 실패: {user_info_response.text}")
        return
    
    print("\n4. 메일 발송 (테스트용)")
    mail_data = {
        "to": ["recipient@example.com"],
        "subject": f"디버그 테스트 메일 - {timestamp}",
        "content": "보낸 메일함 디버깅을 위한 테스트 메일입니다.",
        "priority": "normal"
    }
    
    send_response = requests.post(f"{base_url}/mail/send-json", json=mail_data, headers=headers)
    print(f"   - 메일 발송 응답 상태: {send_response.status_code}")
    
    if send_response.status_code == 200:
        send_result = send_response.json()
        mail_uuid = send_result.get("data", {}).get("mail_uuid", "N/A")
        print(f"   ✅ 메일 발송 성공")
        print(f"   - 메일 UUID: {mail_uuid}")
    else:
        print(f"   ❌ 메일 발송 실패: {send_response.text}")
        return
    
    print("\n5. 잠시 대기 (메일 처리 시간)")
    time.sleep(3)
    
    print("\n6. 보낸 메일함 조회")
    sent_response = requests.get(f"{base_url}/mail/sent", headers=headers)
    print(f"   - 보낸 메일함 응답 상태: {sent_response.status_code}")
    
    if sent_response.status_code == 200:
        sent_result = sent_response.json()
        print(f"   - 보낸 메일함 응답: {sent_result}")
        
        # MailListWithPaginationResponse 스키마에 맞게 응답 파싱
        sent_mails = sent_result.get("mails", [])
        pagination = sent_result.get("pagination", {})
        
        print(f"   - 조회된 메일 수: {len(sent_mails)}")
        print(f"   - 페이지네이션 정보: {pagination}")
        
        if sent_mails:
            print("   - 최근 보낸 메일 목록:")
            for i, mail in enumerate(sent_mails[:3]):  # 최근 3개만 표시
                print(f"     {i+1}. 제목: {mail.get('subject', 'N/A')}")
                print(f"        UUID: {mail.get('mail_uuid', 'N/A')}")
                print(f"        발송일: {mail.get('sent_at', 'N/A')}")
                print(f"        수신자: {mail.get('recipients', [])}")
                sender = mail.get('sender', {})
                print(f"        발송자: {sender.get('email', 'N/A') if sender else 'N/A'}")
            print("   ✅ 보낸 메일함 조회 성공!")
        else:
            print("   ❌ 보낸 메일이 없습니다 - 이것이 문제입니다!")
            
        # 방금 발송한 메일이 목록에 있는지 확인
        found_mail = False
        for mail in sent_mails:
            if mail.get('mail_uuid') == mail_uuid:
                found_mail = True
                print(f"   ✅ 방금 발송한 메일을 보낸 메일함에서 찾았습니다!")
                break
        
        if not found_mail and mail_uuid != "N/A":
            print(f"   ❌ 방금 발송한 메일({mail_uuid})이 보낸 메일함에 없습니다!")
            
    else:
        print(f"   ❌ 보낸 메일함 조회 실패: {sent_response.text}")
        
    print("\n7. 개별 메일 조회 (방금 발송한 메일)")
    if mail_uuid != "N/A":
        detail_response = requests.get(f"{base_url}/mail/{mail_uuid}", headers=headers)
        print(f"   - 개별 메일 조회 응답 상태: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            detail_result = detail_response.json()
            mail_detail = detail_result.get("data", {})
            print(f"   - 메일 제목: {mail_detail.get('subject', 'N/A')}")
            print(f"   - 메일 상태: {mail_detail.get('status', 'N/A')}")
            print(f"   - 발송자 UUID: {mail_detail.get('sender_uuid', 'N/A')}")
            print(f"   - 현재 사용자 UUID: {user_uuid}")
            print(f"   - UUID 일치 여부: {mail_detail.get('sender_uuid') == user_uuid}")
        else:
            print(f"   ❌ 개별 메일 조회 실패: {detail_response.text}")

if __name__ == "__main__":
    debug_sent_mailbox()