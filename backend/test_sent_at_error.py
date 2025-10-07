#!/usr/bin/env python3
"""
sent_at 필드 오류 재현 및 해결 테스트
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

print("📧 sent_at 필드 오류 재현 테스트")
print("=" * 60)

# 1. 로그인
print("🔐 관리자 로그인 중...")
login_data = {
    "user_id": "admin01",
    "password": "test"
}

try:
    login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login", 
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"로그인 상태: {login_response.status_code}")

    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result["access_token"]
        print("✅ 로그인 성공")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
        }
        
        # 2. 테스트 메일 발송
        print("\n📤 테스트 메일 발송 중...")
        mail_data = {
            "to": ["test@example.com"],
            "subject": "sent_at 필드 테스트 메일",
            "body_text": "이 메일은 sent_at 필드 오류를 테스트하기 위한 메일입니다.",
            "priority": "normal",
            "is_draft": False
        }
        
        send_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/send-json",
            json=mail_data,
            headers=headers
        )
        
        print(f"메일 발송 상태: {send_response.status_code}")
        
        if send_response.status_code == 200:
            send_result = send_response.json()
            print("✅ 메일 발송 성공!")
            print(f"메일 UUID: {send_result.get('mail_uuid')}")
            print(f"발송 시간: {send_result.get('sent_at')}")
            
            # 3. 발송함 조회 (sent_at 필드 확인)
            print("\n📤 발송함 조회 중...")
            sent_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/sent",
                headers=headers,
                params={"page": 1, "limit": 5}
            )
            
            print(f"발송함 조회 상태: {sent_response.status_code}")
            
            if sent_response.status_code == 200:
                sent_result = sent_response.json()
                print("✅ 발송함 조회 성공!")
                
                mails = sent_result.get('mails', [])
                if mails:
                    print(f"\n📧 발송 메일 목록 ({len(mails)}개):")
                    for i, mail in enumerate(mails, 1):
                        print(f"   {i}. 제목: {mail.get('subject', 'N/A')}")
                        print(f"      상태: {mail.get('status', 'N/A')}")
                        print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                        print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                        print(f"      전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
                        print()
                else:
                    print("📭 발송함이 비어있습니다.")
            else:
                print(f"❌ 발송함 조회 실패: {sent_response.status_code}")
                print(f"오류 내용: {sent_response.text}")
                
            # 4. 받은 메일함 조회 (sent_at 필드 확인)
            print("\n📥 받은 메일함 조회 중...")
            inbox_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/inbox",
                headers=headers,
                params={"page": 1, "limit": 5}
            )
            
            print(f"받은 메일함 조회 상태: {inbox_response.status_code}")
            
            if inbox_response.status_code == 200:
                inbox_result = inbox_response.json()
                print("✅ 받은 메일함 조회 성공!")
                
                mails = inbox_result.get('mails', [])
                if mails:
                    print(f"\n📧 받은 메일 목록 ({len(mails)}개):")
                    for i, mail in enumerate(mails, 1):
                        print(f"   {i}. 제목: {mail.get('subject', 'N/A')}")
                        print(f"      상태: {mail.get('status', 'N/A')}")
                        print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                        print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                        print(f"      전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
                        print()
                else:
                    print("📭 받은 메일함이 비어있습니다.")
            else:
                print(f"❌ 받은 메일함 조회 실패: {inbox_response.status_code}")
                print(f"오류 내용: {inbox_response.text}")
                
        else:
            print(f"❌ 메일 발송 실패: {send_response.status_code}")
            print(f"오류 내용: {send_response.text}")
            
    else:
        print(f"❌ 로그인 실패: {login_response.status_code}")
        print(f"오류 내용: {login_response.text}")

except Exception as e:
    print(f"❌ 예외 발생: {str(e)}")
    import traceback
    print(f"상세 오류: {traceback.format_exc()}")

print("\n🔍 테스트 완료!")