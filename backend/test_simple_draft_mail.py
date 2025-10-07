#!/usr/bin/env python3
"""
간단한 임시보관함 메일 생성 테스트
Terminal#1016-1020 오류 해결 확인
"""

import requests
import json

# API 기본 URL
BASE_URL = "http://localhost:8000"

def test_simple_draft_mail():
    """간단한 임시보관함 메일 생성 테스트"""
    print("🧪 간단한 임시보관함 메일 생성 테스트 시작")
    
    # 1. 로그인
    print("🔐 로그인 시도...")
    login_data = {
        "user_id": "testuser_folder",
        "password": "test123"
    }
    
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        return False
    
    login_result = login_response.json()
    access_token = login_result["access_token"]
    print("✅ 로그인 성공")
    
    # 2. 임시보관함 메일 생성
    print("📝 임시보관함 메일 생성 시도...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    mail_data = {
        "to_emails": "test@example.com",
        "subject": "테스트 임시보관함 메일",
        "content": "이것은 임시보관함 테스트 메일입니다.",
        "priority": "normal",
        "is_draft": "true"  # 임시보관함으로 설정
    }
    
    mail_response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=mail_data, headers=headers)
    print(f"메일 생성 응답 상태: {mail_response.status_code}")
    
    if mail_response.status_code == 200:
        mail_result = mail_response.json()
        print("✅ 임시보관함 메일 생성 성공")
        print(f"메일 ID: {mail_result.get('mail_uuid')}")
        
        # 3. 임시보관함 메일 상세 조회 테스트
        mail_uuid = mail_result.get('mail_uuid')
        if mail_uuid:
            print(f"📧 임시보관함 메일 상세 조회 시도 - ID: {mail_uuid}")
            detail_response = requests.get(f"{BASE_URL}/api/v1/mail/drafts/{mail_uuid}", headers=headers)
            print(f"상세 조회 응답 상태: {detail_response.status_code}")
            
            if detail_response.status_code == 200:
                print("✅ 임시보관함 메일 상세 조회 성공")
                detail_result = detail_response.json()
                print(f"메일 제목: {detail_result.get('subject')}")
                print(f"메일 상태: {detail_result.get('status')}")
                return True
            else:
                print(f"❌ 임시보관함 메일 상세 조회 실패: {detail_response.text}")
                return False
        else:
            print("❌ 메일 UUID를 받지 못했습니다.")
            return False
    else:
        print(f"❌ 임시보관함 메일 생성 실패: {mail_response.text}")
        return False

if __name__ == "__main__":
    success = test_simple_draft_mail()
    if success:
        print("🎉 모든 테스트 통과!")
    else:
        print("💥 테스트 실패!")