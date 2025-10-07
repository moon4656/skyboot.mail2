#!/usr/bin/env python3
"""
임시보관함 메일 생성 및 상세 조회 테스트
Terminal#1016-1020 오류 해결 확인
"""
import requests
import json
import sys
from datetime import datetime

# FastAPI 서버 URL
BASE_URL = "http://localhost:8000"

def login_user(user_id: str, password: str):
    """사용자 로그인"""
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"🔐 로그인 시도 - 사용자: {user_id}, 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if "access_token" in result:
            print(f"✅ 로그인 성공 - 사용자: {user_id}")
            return result["access_token"]
        else:
            print(f"❌ 로그인 실패 - 토큰 없음: {result}")
            return None
    else:
        print(f"❌ 로그인 실패 - 상태: {response.status_code}, 응답: {response.text}")
        return None

def create_draft_mail(token: str):
    """임시보관함 메일 생성"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 임시보관함 메일 생성 (is_draft=true)
    mail_data = {
        "to_emails": "test@example.com",
        "subject": "테스트 임시보관함 메일",
        "content": "이것은 임시보관함 테스트 메일입니다.",
        "priority": "normal",
        "is_draft": "true"  # 임시보관함으로 저장
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=mail_data, headers=headers)
    print(f"📧 임시보관함 메일 생성 시도 - 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 임시보관함 메일 생성 성공")
        print(f"📋 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result.get("mail_uuid")
    else:
        print(f"❌ 임시보관함 메일 생성 실패 - 상태: {response.status_code}")
        print(f"📋 응답: {response.text}")
        return None

def get_draft_mails(token: str):
    """임시보관함 메일 목록 조회"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/mail/drafts", headers=headers)
    print(f"📋 임시보관함 목록 조회 - 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 임시보관함 목록 조회 성공 - 메일 수: {len(result.get('mails', []))}")
        return result.get('mails', [])
    else:
        print(f"❌ 임시보관함 목록 조회 실패 - 상태: {response.status_code}")
        print(f"📋 응답: {response.text}")
        return []

def get_draft_mail_detail(token: str, mail_uuid: str):
    """임시보관함 메일 상세 조회 (수정된 API 테스트)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/mail/drafts/{mail_uuid}", headers=headers)
    print(f"📧 임시보관함 메일 상세 조회 - UUID: {mail_uuid}, 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 임시보관함 메일 상세 조회 성공!")
        print(f"📋 메일 정보:")
        print(f"   - 제목: {result.get('subject')}")
        print(f"   - 발송자: {result.get('sender', {}).get('email')}")
        print(f"   - 생성시간: {result.get('created_at')}")
        print(f"   - 임시보관함 여부: {result.get('is_draft')}")
        return True
    else:
        print(f"❌ 임시보관함 메일 상세 조회 실패!")
        print(f"   - 상태 코드: {response.status_code}")
        print(f"   - 응답: {response.text}")
        
        # 500 에러인 경우 Terminal#1016-1020과 같은 오류
        if response.status_code == 500:
            print(f"🚨 500 Internal Server Error 발생 - Terminal#1016-1020과 동일한 오류!")
        elif response.status_code == 403:
            print(f"🚨 403 Access Denied 발생 - 조직 분리 로직 문제!")
        
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 임시보관함 메일 생성 및 상세 조회 테스트 시작")
    print("📋 Terminal#1016-1020 오류 해결 확인")
    
    # 1. 사용자 로그인
    token = login_user("testuser_folder", "test123")
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return False
    
    # 2. 임시보관함 메일 생성
    mail_uuid = create_draft_mail(token)
    if not mail_uuid:
        print("❌ 임시보관함 메일 생성 실패")
        
        # 기존 임시보관함 메일 확인
        print("\n🔍 기존 임시보관함 메일 확인...")
        draft_mails = get_draft_mails(token)
        if draft_mails:
            mail_uuid = draft_mails[0].get("mail_uuid")
            print(f"✅ 기존 임시보관함 메일 사용 - UUID: {mail_uuid}")
        else:
            print("❌ 사용 가능한 임시보관함 메일이 없습니다.")
            return False
    
    # 3. 임시보관함 메일 상세 조회 (수정된 API 테스트)
    print(f"\n📧 임시보관함 메일 상세 조회 테스트 - UUID: {mail_uuid}")
    success = get_draft_mail_detail(token, mail_uuid)
    
    if success:
        print("\n✅ 테스트 성공! Terminal#1016-1020 오류가 해결되었습니다.")
        return True
    else:
        print("\n❌ 테스트 실패! Terminal#1016-1020 오류가 여전히 발생합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)