#!/usr/bin/env python3
"""
받은 메일함 API 테스트 및 오류 디버깅
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

print("📬 받은 메일함 API 테스트 (오류 디버깅)")
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
        
        # 2. 받은 메일함 조회
        print("\n📬 받은 메일함 조회 중...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
        }
        
        inbox_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/inbox",
            headers=headers,
            params={"page": 1, "limit": 10}
        )
        
        print(f"받은 메일함 조회 상태: {inbox_response.status_code}")
        
        if inbox_response.status_code == 200:
            inbox_result = inbox_response.json()
            print("✅ 받은 메일함 조회 성공!")
            print(f"📊 총 메일 수: {inbox_result.get('total', 0)}")
            print(f"📄 현재 페이지: {inbox_result.get('page', 1)}")
            print(f"📝 페이지당 메일 수: {inbox_result.get('limit', 10)}")
            
            mails = inbox_result.get('mails', [])
            if mails:
                print(f"\n📧 메일 목록 ({len(mails)}개):")
                for i, mail in enumerate(mails[:3], 1):  # 최대 3개만 표시
                    print(f"   {i}. 제목: {mail.get('subject', 'N/A')}")
                    print(f"      발송자: {mail.get('sender_email', 'N/A')}")
                    print(f"      수신 시간: {mail.get('received_at', 'N/A')}")
                    print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                    print(f"      읽음 상태: {'읽음' if mail.get('is_read') else '읽지 않음'}")
                    print(f"      메일 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
                    print()
            else:
                print("📭 받은 메일함이 비어있습니다.")
                
        else:
            print(f"❌ 받은 메일함 조회 실패: {inbox_response.status_code}")
            print(f"오류 내용: {inbox_response.text}")
            
        # 3. 메일 폴더 목록 조회 (추가 확인)
        print("\n📁 메일 폴더 목록 조회 중...")
        folders_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/folders",
            headers=headers
        )
        
        print(f"폴더 목록 조회 상태: {folders_response.status_code}")
        
        if folders_response.status_code == 200:
            folders_result = folders_response.json()
            print("✅ 폴더 목록 조회 성공!")
            
            folders = folders_result.get('folders', [])
            if folders:
                print(f"\n📂 폴더 목록 ({len(folders)}개):")
                for folder in folders:
                    print(f"   - {folder.get('name', 'N/A')} ({folder.get('folder_type', 'N/A')})")
                    print(f"     메일 수: {folder.get('mail_count', 0)}")
                    print(f"     시스템 폴더: {'예' if folder.get('is_system') else '아니오'}")
                    print()
            else:
                print("📁 폴더가 없습니다.")
        else:
            print(f"❌ 폴더 목록 조회 실패: {folders_response.status_code}")
            print(f"오류 내용: {folders_response.text}")
            
    else:
        print(f"❌ 로그인 실패: {login_response.status_code}")
        print(f"오류 내용: {login_response.text}")

except Exception as e:
    print(f"❌ 예외 발생: {str(e)}")
    import traceback
    print(f"상세 오류: {traceback.format_exc()}")

print("\n🔍 테스트 완료!")