#!/usr/bin/env python3
"""
휴지통 메일 조회 API 테스트 - user01 계정
메일 상태 필터 확인 및 실행 내역 검증
"""

import requests
import json
from datetime import datetime

# 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_trash_api():
    """휴지통 API 테스트"""
    print("🗑️ 휴지통 메일 조회 API 테스트 시작")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. user01 로그인
    print("\n🔐 user01 로그인 중...")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json=login_data
    )
    
    print(f"로그인 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        return
    
    login_result = login_response.json()
    access_token = login_result.get("access_token")
    
    if not access_token:
        print("❌ 액세스 토큰을 받을 수 없습니다.")
        return
    
    print("✅ 로그인 성공!")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 휴지통 메일 조회 (기본)
    print("\n🗑️ 휴지통 메일 조회 (기본) 중...")
    trash_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=10",
        headers=headers
    )
    
    print(f"휴지통 조회 상태: {trash_response.status_code}")
    
    if trash_response.status_code == 200:
        trash_result = trash_response.json()
        print("✅ 휴지통 조회 성공!")
        print(f"📊 총 메일 수: {trash_result.get('pagination', {}).get('total', 0)}")
        print(f"📄 현재 페이지: {trash_result.get('pagination', {}).get('page', 1)}")
        print(f"📝 페이지당 메일 수: {trash_result.get('pagination', {}).get('limit', 10)}")
        
        mails = trash_result.get('mails', [])
        if mails:
            print(f"\n📧 휴지통 메일 목록 ({len(mails)}개):")
            for i, mail in enumerate(mails[:3], 1):  # 최대 3개만 표시
                print(f"   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      발송자: {mail.get('sender_email', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                print()
        else:
            print("📭 휴지통이 비어있습니다.")
    else:
        print(f"❌ 휴지통 조회 실패: {trash_response.status_code}")
        print(f"오류 내용: {trash_response.text}")
    
    # 3. 휴지통 메일 조회 (상태 필터 적용)
    print("\n🔍 휴지통 메일 조회 (상태 필터 적용) 중...")
    
    # 가능한 메일 상태들
    mail_statuses = ["draft", "sent", "failed", "deleted", "trash"]
    
    for status in mail_statuses:
        print(f"\n📋 상태 필터: {status}")
        filtered_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&status={status}",
            headers=headers
        )
        
        print(f"   상태: {filtered_response.status_code}")
        
        if filtered_response.status_code == 200:
            filtered_result = filtered_response.json()
            total = filtered_result.get('pagination', {}).get('total', 0)
            mails = filtered_result.get('mails', [])
            print(f"   📊 {status} 상태 메일 수: {total}")
            
            if mails:
                print(f"   📧 첫 번째 메일:")
                first_mail = mails[0]
                print(f"      제목: {first_mail.get('subject', 'N/A')}")
                print(f"      상태: {first_mail.get('status', 'N/A')}")
                print(f"      발송자: {first_mail.get('sender_email', 'N/A')}")
        else:
            print(f"   ❌ 필터링 실패: {filtered_response.text}")
    
    # 4. 휴지통 메일 조회 (검색 키워드 적용)
    print("\n🔍 휴지통 메일 조회 (검색 키워드 적용) 중...")
    search_keywords = ["test", "메일", "안녕"]
    
    for keyword in search_keywords:
        print(f"\n🔎 검색 키워드: '{keyword}'")
        search_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&search={keyword}",
            headers=headers
        )
        
        print(f"   상태: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            total = search_result.get('pagination', {}).get('total', 0)
            print(f"   📊 '{keyword}' 검색 결과: {total}개")
        else:
            print(f"   ❌ 검색 실패: {search_response.text}")
    
    # 5. 휴지통 메일 상세 조회 (첫 번째 메일이 있는 경우)
    if trash_response.status_code == 200:
        trash_result = trash_response.json()
        mails = trash_result.get('mails', [])
        
        if mails:
            first_mail_uuid = mails[0].get('mail_uuid')
            if first_mail_uuid:
                print(f"\n📄 휴지통 메일 상세 조회 중... (UUID: {first_mail_uuid})")
                detail_response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/mail/trash/{first_mail_uuid}",
                    headers=headers
                )
                
                print(f"상세 조회 상태: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    detail_result = detail_response.json()
                    print("✅ 휴지통 메일 상세 조회 성공!")
                    
                    data = detail_result.get('data', {})
                    print(f"📧 메일 정보:")
                    print(f"   제목: {data.get('subject', 'N/A')}")
                    print(f"   발송자: {data.get('sender_email', 'N/A')}")
                    print(f"   수신자: {', '.join(data.get('to_emails', []))}")
                    print(f"   상태: {data.get('status', 'N/A')}")
                    print(f"   우선순위: {data.get('priority', 'N/A')}")
                    print(f"   첨부파일 수: {len(data.get('attachments', []))}")
                    print(f"   생성 시간: {data.get('created_at', 'N/A')}")
                else:
                    print(f"❌ 상세 조회 실패: {detail_response.text}")
    
    print("\n" + "=" * 60)
    print("🏁 휴지통 API 테스트 완료!")
    print(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_trash_api()