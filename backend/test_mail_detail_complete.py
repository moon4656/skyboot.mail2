#!/usr/bin/env python3
"""
메일 상세 스키마 수정 완전 검증 테스트
- 테스트 메일 발송
- 메일 상세 조회
- 스키마 검증
"""

import requests
import json
import time

def test_mail_detail_schema():
    """메일 상세 스키마 수정을 완전히 검증합니다."""
    
    base_url = "http://localhost:8000"
    
    print("🧪 MailDetailResponse 스키마 완전 검증 테스트 시작\n")
    
    # 1. 로그인
    print("1️⃣ 사용자 로그인")
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        return False
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    print("✅ 로그인 성공")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. 테스트 메일 발송
    print("\n2️⃣ 테스트 메일 발송")
    mail_data = {
        "to_emails": "test@example.com",
        "subject": "스키마 테스트 메일",
        "content": "MailDetailResponse 스키마 검증을 위한 테스트 메일입니다.",
        "priority": "normal"
    }
    
    send_response = requests.post(
        f"{base_url}/api/v1/mail/send",
        headers=headers,
        data=mail_data  # Form 데이터로 전송
    )
    
    print(f"메일 발송 응답 상태: {send_response.status_code}")
    
    if send_response.status_code != 200:
        print(f"❌ 메일 발송 실패: {send_response.text}")
        return False
    
    send_result = send_response.json()
    print("✅ 테스트 메일 발송 성공")
    print(f"📧 메일 ID: {send_result.get('data', {}).get('mail_uuid', 'N/A')}")
    
    # 3. 잠시 대기 (메일# 메일 처리 대기
    print("\n⏳ 메일 처리 대기 중...")
    time.sleep(5)  # 대기 시간 증가
    
    # 4. 보낸 메일함 조회
    print("\n3️⃣ 보낸 메일함 조회")
    sent_response = requests.get(
        f"{base_url}/api/v1/mail/sent",
        headers=headers
    )
    
    print(f"보낸 메일함 조회 상태: {sent_response.status_code}")
    
    if sent_response.status_code != 200:
        print(f"❌ 보낸 메일함 조회 실패: {sent_response.text}")
        print("❌ 테스트 실패: 스키마 수정 확인 필요")
        return
    
    sent_data = sent_response.json()
    print(f"🔍 보낸 메일함 응답 구조: {list(sent_data.keys())}")
    
    # 응답 구조가 {"mails": [...], "pagination": {...}} 형태
    mails = sent_data.get("mails", [])
    print(f"🔍 mails 개수: {len(mails)}")
    
    if not mails:
        print("📭 보낸 메일함이 비어있습니다.")
        print("❌ 테스트 실패: 스키마 수정 확인 필요")
        return
    
    print(f"📧 보낸 메일 개수: {len(mails)}")
    
    # 첫 번째 메일의 UUID 가져오기
    first_mail = mails[0]
    mail_uuid = first_mail.get("mail_uuid")
    print(f"🔍 첫 번째 메일 UUID: {mail_uuid}")
    
    if not mail_uuid:
        print("❌ 메일 UUID를 찾을 수 없습니다.")
        print("❌ 테스트 실패: 스키마 수정 확인 필요")
        return
    
    print(f"✅ 메일 발견: {mail_uuid}")
    
    # 5. 메일 상세 조회 및 스키마 검증
    print("\n4️⃣ 메일 상세 조회 및 스키마 검증")
    detail_response = requests.get(
        f"{base_url}/api/v1/mail/sent/{mail_uuid}",
        headers=headers
    )
    
    print(f"메일 상세 조회 상태: {detail_response.status_code}")
    
    if detail_response.status_code != 200:
        print(f"❌ 메일 상세 조회 실패: {detail_response.text}")
        return False
    
    detail_result = detail_response.json()
    print("✅ 메일 상세 조회 성공")
    print(f"🔍 메일 상세 응답 구조: {json.dumps(detail_result, indent=2, ensure_ascii=False)}")
    
    # 6. 스키마 검증
    print("\n5️⃣ MailDetailResponse 스키마 검증")
    
    # 최상위 필드 검증
    required_top_fields = ["success", "message", "data"]
    missing_top_fields = []
    
    for field in required_top_fields:
        if field not in detail_result:
            missing_top_fields.append(field)
    
    if missing_top_fields:
        print(f"❌ 최상위 필드 누락: {missing_top_fields}")
        return False
    
    print("✅ 최상위 필드 검증 통과 (success, message, data)")
    
    # success 필드 타입 검증
    if not isinstance(detail_result["success"], bool):
        print(f"❌ success 필드 타입 오류: {type(detail_result['success'])}")
        return False
    
    print("✅ success 필드 타입 검증 통과 (bool)")
    
    # message 필드 타입 검증
    if not isinstance(detail_result["message"], str):
        print(f"❌ message 필드 타입 오류: {type(detail_result['message'])}")
        return False
    
    print("✅ message 필드 타입 검증 통과 (str)")
    
    # data 필드 내용 검증
    data = detail_result["data"]
    if not isinstance(data, dict):
        print(f"❌ data 필드 타입 오류: {type(data)}")
        return False
    
    print("✅ data 필드 타입 검증 통과 (dict)")
    
    # data 내부 필드 검증
    required_data_fields = [
        "mail_uuid", "subject", "content", "sender_email", 
        "to_emails", "cc_emails", "bcc_emails",
        "status", "priority", "attachments", "created_at", "sent_at"
    ]
    
    missing_data_fields = []
    for field in required_data_fields:
        if field not in data:
            missing_data_fields.append(field)
    
    if missing_data_fields:
        print(f"❌ data 내부 필드 누락: {missing_data_fields}")
        return False
    
    print("✅ data 내부 필드 검증 통과")
    
    # 7. 응답 데이터 출력
    print("\n6️⃣ 응답 데이터 확인")
    print(f"📄 응답 구조:")
    print(f"  - success: {detail_result['success']} ({type(detail_result['success']).__name__})")
    print(f"  - message: '{detail_result['message']}' ({type(detail_result['message']).__name__})")
    print(f"  - data: dict with {len(data)} fields")
    print(f"    - mail_uuid: {data.get('mail_uuid')}")
    print(f"    - subject: {data.get('subject')}")
    print(f"    - status: {data.get('status')}")
    print(f"    - sent_at: {data.get('sent_at')}")
    
    print("\n🎉 MailDetailResponse 스키마 수정 검증 완료!")
    print("✅ 모든 필드가 올바르게 구성되어 있습니다.")
    
    return True

if __name__ == "__main__":
    success = test_mail_detail_schema()
    if success:
        print("\n✅ 테스트 성공: 스키마 수정이 올바르게 적용되었습니다.")
    else:
        print("\n❌ 테스트 실패: 스키마 수정 확인 필요")