#!/usr/bin/env python3
"""
메일 삭제 기능 테스트 스크립트
Terminal#1007-1020 오류 수정 검증용
"""

import requests
import json
import time
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login_user():
    """사용자 로그인"""
    print("🔐 사용자 로그인 중...")
    
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"✅ 로그인 성공: {TEST_USER['user_id']}")
        return access_token
    else:
        print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        return None

def create_test_mail(access_token):
    """테스트용 메일 생성"""
    print("📧 테스트 메일 생성 중...")
    
    mail_data = {
        "to": ["test@example.com"],
        "subject": f"삭제 테스트 메일 - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "body_text": "이 메일은 삭제 테스트용입니다.",
        "is_draft": False
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/mail/send-json",
        json=mail_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        mail_uuid = result.get("mail_uuid")
        print(f"✅ 테스트 메일 생성 성공: {mail_uuid}")
        return mail_uuid
    else:
        print(f"❌ 테스트 메일 생성 실패: {response.status_code} - {response.text}")
        return None

def delete_mail_soft(access_token, mail_uuid):
    """메일 소프트 삭제 (휴지통으로 이동)"""
    print(f"🗑️ 메일 소프트 삭제 중: {mail_uuid}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.delete(
        f"{BASE_URL}/api/v1/mail/{mail_uuid}?permanent=false",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ 메일 소프트 삭제 성공: {mail_uuid}")
        return True
    else:
        print(f"❌ 메일 소프트 삭제 실패: {response.status_code} - {response.text}")
        return False

def delete_mail_permanent(access_token, mail_uuid):
    """메일 영구 삭제"""
    print(f"🗑️ 메일 영구 삭제 중: {mail_uuid}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.delete(
        f"{BASE_URL}/api/v1/mail/{mail_uuid}?permanent=true",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ 메일 영구 삭제 성공: {mail_uuid}")
        return True
    else:
        print(f"❌ 메일 영구 삭제 실패: {response.status_code} - {response.text}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 메일 삭제 기능 테스트 시작")
    print("=" * 50)
    
    # 1. 로그인
    access_token = login_user()
    if not access_token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 2. 테스트 메일 생성
    mail_uuid = create_test_mail(access_token)
    if not mail_uuid:
        print("❌ 테스트 메일 생성 실패로 테스트 중단")
        return
    
    # 3. 소프트 삭제 테스트
    print("\n📋 소프트 삭제 테스트")
    print("-" * 30)
    if delete_mail_soft(access_token, mail_uuid):
        print("✅ 소프트 삭제 테스트 통과")
    else:
        print("❌ 소프트 삭제 테스트 실패")
        return
    
    # 4. 영구 삭제 테스트 (Terminal#1007-1020 오류 수정 검증)
    print("\n📋 영구 삭제 테스트 (오류 수정 검증)")
    print("-" * 30)
    if delete_mail_permanent(access_token, mail_uuid):
        print("✅ 영구 삭제 테스트 통과 - mail_in_folders NULL 제약조건 오류 해결됨!")
    else:
        print("❌ 영구 삭제 테스트 실패 - 오류가 여전히 존재함")
        return
    
    print("\n🎉 모든 테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()