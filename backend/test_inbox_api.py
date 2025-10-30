#!/usr/bin/env python3
"""
받은편지함 API 기능 테스트 스크립트

이 스크립트는 user01의 받은편지함 API가 정상적으로 작동하는지 확인합니다.
"""

import requests
import json
from datetime import datetime

# API 설정
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
INBOX_URL = f"{BASE_URL}/api/v1/mail/inbox"

def test_inbox_api():
    """받은편지함 API 테스트"""
    print("📧 받은편지함 API 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. user01 로그인
        print("🔐 1. user01 로그인 시도")
        login_data = {
            "user_id": "user01",
            "password": "test"
        }
        
        login_response = requests.post(LOGIN_URL, json=login_data)
        print(f"로그인 응답 상태: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.text}")
            return
        
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        
        if not access_token:
            print("❌ 액세스 토큰을 받지 못했습니다.")
            return
        
        print("✅ 로그인 성공")
        
        # 2. 받은편지함 조회 (기본)
        print("\n📥 2. 받은편지함 조회 (기본)")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        inbox_response = requests.get(INBOX_URL, headers=headers)
        print(f"받은편지함 응답 상태: {inbox_response.status_code}")
        
        if inbox_response.status_code == 200:
            inbox_data = inbox_response.json()
            print(f"✅ 받은편지함 조회 성공")
            print(f"📊 총 메일 수: {inbox_data.get('total', 0)}")
            print(f"📄 현재 페이지: {inbox_data.get('page', 1)}")
            print(f"📋 페이지당 메일 수: {inbox_data.get('limit', 20)}")
            
            mails = inbox_data.get('mails', [])
            print(f"📧 조회된 메일 수: {len(mails)}")
            
            if mails:
                print("\n📋 메일 목록:")
                for i, mail in enumerate(mails[:5], 1):  # 최대 5개만 표시
                    print(f"   {i}. {mail.get('subject', 'No Subject')}")
                    print(f"      발송자: {mail.get('sender_email', 'Unknown')}")
                    print(f"      발송 시간: {mail.get('sent_at', 'Unknown')}")
                    print(f"      상태: {mail.get('status', 'Unknown')}")
                    print()
            else:
                print("📭 받은편지함이 비어있습니다.")
        else:
            print(f"❌ 받은편지함 조회 실패: {inbox_response.text}")
        
        # 3. 페이지네이션 테스트
        print("\n📄 3. 페이지네이션 테스트")
        pagination_params = {"page": 1, "limit": 5}
        pagination_response = requests.get(INBOX_URL, headers=headers, params=pagination_params)
        
        if pagination_response.status_code == 200:
            pagination_data = pagination_response.json()
            print(f"✅ 페이지네이션 테스트 성공")
            print(f"📊 요청한 limit: 5, 실제 조회된 메일 수: {len(pagination_data.get('mails', []))}")
        else:
            print(f"❌ 페이지네이션 테스트 실패: {pagination_response.text}")
        
        # 4. 검색 기능 테스트 (있다면)
        print("\n🔍 4. 검색 기능 테스트")
        search_params = {"search": "Test"}
        search_response = requests.get(INBOX_URL, headers=headers, params=search_params)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"✅ 검색 기능 테스트 성공")
            print(f"📊 'Test' 검색 결과: {len(search_data.get('mails', []))}개")
        else:
            print(f"⚠️ 검색 기능 테스트: {search_response.status_code} - {search_response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 받은편지함 API 테스트 완료")

if __name__ == "__main__":
    test_inbox_api()