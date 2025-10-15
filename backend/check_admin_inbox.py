#!/usr/bin/env python3
"""
Admin 받은 메일함 확인 스크립트

admin 계정으로 로그인하여 받은 메일함을 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
INBOX_URL = f"{BASE_URL}/mail/inbox"

def login_user(user_id: str, password: str) -> dict:
    """
    사용자 로그인을 수행하고 JWT 토큰을 반환합니다.
    
    Args:
        user_id: 사용자 ID
        password: 패스워드
        
    Returns:
        로그인 응답 데이터 (토큰 포함)
    """
    print(f"🔐 로그인 시도 - 사용자: {user_id}")
    
    login_data = {
        "user_id": "admin",
        "password": "test"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 로그인 성공 - 사용자: {user_id}")
            return result
        else:
            print(f"❌ 로그인 실패 - 사용자: {user_id}")
            print(f"   상태 코드: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류 - 사용자: {user_id}, 오류: {str(e)}")
        return None

def get_inbox(access_token: str, page: int = 1, limit: int = 10) -> dict:
    """
    받은 메일함을 조회합니다.
    
    Args:
        access_token: JWT 액세스 토큰
        page: 페이지 번호
        limit: 페이지당 메일 수
        
    Returns:
        받은 메일함 응답 데이터
    """
    print(f"📥 받은 메일함 조회 - 페이지: {page}, 제한: {limit}")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "page": page,
        "limit": limit
    }
    
    try:
        response = requests.get(INBOX_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 받은 메일함 조회 성공")
            print(f"   응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"❌ 받은 메일함 조회 실패")
            print(f"   상태 코드: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 받은 메일함 조회 오류: {str(e)}")
        return None

def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("📧 Admin 받은 메일함 확인")
    print("=" * 60)
    print(f"⏰ 확인 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. admin 계정으로 로그인
    print("1️⃣ Admin 로그인")
    print("-" * 30)
    
    login_result = login_user("admin", "test")
    if not login_result:
        print("❌ 로그인 실패로 확인을 중단합니다.")
        return
    
    access_token = login_result.get("access_token")
    if not access_token:
        print("❌ 액세스 토큰을 찾을 수 없습니다.")
        return
    
    print()
    
    # 2. 받은 메일함 조회
    print("2️⃣ 받은 메일함 조회")
    print("-" * 30)
    
    inbox_result = get_inbox(access_token)
    if not inbox_result:
        print("❌ 받은 메일함 조회 실패로 확인을 중단합니다.")
        return
    
    # 3. 메일 목록 출력
    print("3️⃣ 메일 목록")
    print("-" * 30)
    
    if inbox_result:
        mails = inbox_result.get("mails", [])
        pagination = inbox_result.get("pagination", {})
        total_count = pagination.get("total", 0)
        
        print(f"📊 총 {total_count}개의 메일이 있습니다.")
        print()
        
        if mails:
            for i, mail in enumerate(mails, 1):
                print(f"{i}. 메일 정보:")
                print(f"   - 메일 UUID: {mail.get('mail_uuid', 'N/A')}")
                print(f"   - 제목: {mail.get('subject', 'N/A')}")
                print(f"   - 발송자: {mail.get('sender', {}).get('email', 'N/A')}")
                print(f"   - 상태: {mail.get('status', 'N/A')}")
                print(f"   - 우선순위: {mail.get('priority', 'N/A')}")
                print(f"   - 읽음 상태: {'읽음' if mail.get('is_read') else '읽지 않음'}")
                print(f"   - 첨부파일: {mail.get('attachment_count', 0)}개")
                print(f"   - 발송일: {mail.get('sent_at', 'N/A')}")
                print()
        else:
            print("📭 받은 메일함이 비어있습니다.")
    else:
        print(f"❌ 받은 메일함 조회 실패")
    
    print()
    
    # 4. 결과 요약
    print("4️⃣ 확인 결과 요약")
    print("-" * 30)
    print("✅ Admin 받은 메일함 확인이 완료되었습니다!")
    print()
    print("📊 확인 결과:")
    print(f"   ✅ 로그인: 성공 (admin)")
    print(f"   ✅ 받은 메일함 조회: 성공")
    if inbox_result:
        pagination = inbox_result.get("pagination", {})
        total_count = pagination.get("total", 0)
        print(f"   📧 메일 수: {total_count}개")
    print()
    print(f"⏰ 확인 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()