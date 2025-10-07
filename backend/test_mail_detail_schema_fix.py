#!/usr/bin/env python3
"""
MailDetailResponse 스키마 수정 검증 테스트
"""

import requests
import json
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_mail_detail_schema_fix():
    """메일 상세 조회 스키마 수정 검증"""
    print("🧪 MailDetailResponse 스키마 수정 검증 테스트 시작")
    
    # 1. 로그인
    print("\n1️⃣ 사용자 로그인")
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        return False
    
    login_result = login_response.json()
    access_token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ 로그인 성공")
    
    # 2. 받은 메일함 조회하여 메일 UUID 가져오기
    print("\n2️⃣ 받은 메일함 조회")
    inbox_response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
    print(f"받은 메일함 조회 상태: {inbox_response.status_code}")
    
    if inbox_response.status_code != 200:
        print(f"❌ 받은 메일함 조회 실패: {inbox_response.text}")
        return False
    
    inbox_data = inbox_response.json()
    if not inbox_data.get("mails"):
        print("📭 받은 메일함이 비어있습니다. 테스트용 메일을 먼저 발송해주세요.")
        return False
    
    # 첫 번째 메일의 UUID 가져오기
    first_mail = inbox_data["mails"][0]
    mail_uuid = first_mail["mail_uuid"]
    print(f"✅ 테스트할 메일 UUID: {mail_uuid}")
    
    # 3. 메일 상세 조회 테스트
    print("\n3️⃣ 메일 상세 조회 테스트")
    detail_response = requests.get(f"{API_BASE}/mail/inbox/{mail_uuid}", headers=headers)
    print(f"메일 상세 조회 상태: {detail_response.status_code}")
    
    if detail_response.status_code != 200:
        print(f"❌ 메일 상세 조회 실패: {detail_response.text}")
        return False
    
    detail_data = detail_response.json()
    print("✅ 메일 상세 조회 성공")
    
    # 4. 응답 스키마 검증
    print("\n4️⃣ 응답 스키마 검증")
    
    # 필수 필드 확인
    required_fields = ["success", "message", "data"]
    for field in required_fields:
        if field not in detail_data:
            print(f"❌ 필수 필드 누락: {field}")
            return False
        print(f"✅ 필수 필드 확인: {field}")
    
    # success 필드 확인
    if not isinstance(detail_data["success"], bool):
        print(f"❌ success 필드 타입 오류: {type(detail_data['success'])}")
        return False
    print(f"✅ success 필드: {detail_data['success']}")
    
    # message 필드 확인
    if not isinstance(detail_data["message"], str):
        print(f"❌ message 필드 타입 오류: {type(detail_data['message'])}")
        return False
    print(f"✅ message 필드: {detail_data['message']}")
    
    # data 필드 확인
    if not isinstance(detail_data["data"], dict):
        print(f"❌ data 필드 타입 오류: {type(detail_data['data'])}")
        return False
    print("✅ data 필드: dict 타입 확인")
    
    # data 내부 필드 확인
    data = detail_data["data"]
    expected_data_fields = [
        "mail_uuid", "subject", "content", "sender_email",
        "to_emails", "cc_emails", "bcc_emails", "status",
        "priority", "attachments", "created_at", "sent_at", "read_at"
    ]
    
    for field in expected_data_fields:
        if field not in data:
            print(f"❌ data 내부 필드 누락: {field}")
            return False
        print(f"✅ data 내부 필드 확인: {field}")
    
    # 5. 전체 응답 구조 출력
    print("\n5️⃣ 전체 응답 구조")
    print(json.dumps(detail_data, indent=2, ensure_ascii=False, default=str))
    
    print("\n🎉 모든 테스트 통과! MailDetailResponse 스키마 수정이 성공적으로 적용되었습니다.")
    return True

if __name__ == "__main__":
    try:
        success = test_mail_detail_schema_fix()
        if success:
            print("\n✅ 테스트 완료: 스키마 수정 성공")
        else:
            print("\n❌ 테스트 실패: 스키마 수정 확인 필요")
    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()