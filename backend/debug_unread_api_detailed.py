#!/usr/bin/env python3
"""
읽지 않은 메일 API 상세 디버깅

SkyBoot Mail SaaS 시스템의 읽지 않은 메일 API를 상세히 디버깅합니다.
"""
import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

def login_user(user_id: str, password: str) -> str:
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중: {user_id}")
    
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"로그인 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {token[:50]}...")
        return token
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def test_unread_mail_api_detailed(token: str):
    """읽지 않은 메일 API 상세 테스트"""
    if not token:
        print("❌ 토큰이 없어 테스트를 건너뜁니다.")
        return
    
    print(f"\n📧 읽지 않은 메일 API 상세 테스트")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 기본 읽지 않은 메일 API 호출
    print(f"\n1️⃣ 기본 읽지 않은 메일 API 호출")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE}/mail/unread", headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 호출 성공!")
            print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 응답 구조 분석
            if isinstance(result, dict):
                success = result.get("success", False)
                message = result.get("message", "")
                data = result.get("data", {})
                
                print(f"\n📊 응답 분석:")
                print(f"   Success: {success}")
                print(f"   Message: {message}")
                print(f"   Data Type: {type(data)}")
                
                if isinstance(data, dict):
                    mails = data.get("mails", [])
                    total = data.get("total", 0)
                    page = data.get("page", 1)
                    limit = data.get("limit", 20)
                    pages = data.get("pages", 0)
                    
                    print(f"   Total: {total}")
                    print(f"   Mails Count: {len(mails)}")
                    print(f"   Page: {page}")
                    print(f"   Limit: {limit}")
                    print(f"   Pages: {pages}")
                    
                    if mails:
                        print(f"\n📋 메일 목록:")
                        for i, mail in enumerate(mails, 1):
                            print(f"     {i}. {mail.get('subject', 'No Subject')}")
                            print(f"        ID: {mail.get('id', 'N/A')}")
                            print(f"        Sender: {mail.get('sender_email', 'N/A')}")
                            print(f"        Created: {mail.get('created_at', 'N/A')}")
                            print(f"        Is Read: {mail.get('is_read', 'N/A')}")
                            print()
                    else:
                        print(f"   📭 메일 목록이 비어있습니다.")
                else:
                    print(f"   ⚠️ Data가 딕셔너리가 아닙니다: {data}")
            else:
                print(f"   ⚠️ 응답이 딕셔너리가 아닙니다: {type(result)}")
        else:
            print(f"❌ API 호출 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ API 요청 중 오류: {e}")
    
    # 2. 페이지네이션 파라미터와 함께 호출
    print(f"\n2️⃣ 페이지네이션 파라미터와 함께 호출")
    print("-" * 40)
    
    try:
        params = {"page": 1, "limit": 10}
        response = requests.get(f"{API_BASE}/mail/unread", headers=headers, params=params)
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 페이지네이션 API 호출 성공!")
            
            if isinstance(result, dict) and "data" in result:
                data = result["data"]
                total = data.get("total", 0)
                mails_count = len(data.get("mails", []))
                
                print(f"   Total: {total}")
                print(f"   Mails Count: {mails_count}")
            else:
                print(f"   응답 구조: {result}")
        else:
            print(f"❌ 페이지네이션 API 호출 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 페이지네이션 API 요청 중 오류: {e}")
    
    # 3. 받은편지함 API와 비교
    print(f"\n3️⃣ 받은편지함 API와 비교")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
        print(f"받은편지함 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 받은편지함 API 호출 성공!")
            
            # 받은편지함 응답 구조 분석
            if isinstance(result, dict):
                mails = result.get("mails", [])
                pagination = result.get("pagination", {})
                total = pagination.get("total", 0)
                
                print(f"   받은편지함 Total: {total}")
                print(f"   받은편지함 Mails Count: {len(mails)}")
                
                # 읽지 않은 메일 개수 계산
                unread_count = sum(1 for mail in mails if not mail.get("is_read", True))
                print(f"   받은편지함에서 읽지 않은 메일: {unread_count}개")
                
                if mails:
                    print(f"\n📋 받은편지함 메일 목록 (처음 3개):")
                    for i, mail in enumerate(mails[:3], 1):
                        print(f"     {i}. {mail.get('subject', 'No Subject')}")
                        print(f"        ID: {mail.get('mail_uuid', 'N/A')}")
                        print(f"        Is Read: {mail.get('is_read', 'N/A')}")
                        print()
            else:
                print(f"   받은편지함 응답 구조: {result}")
        else:
            print(f"❌ 받은편지함 API 호출 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 받은편지함 API 요청 중 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 읽지 않은 메일 API 상세 디버깅")
    print("=" * 60)
    print(f"시작 시간: {datetime.now()}")
    
    # 1. user01로 로그인
    token = login_user("user01", "test")
    
    # 2. 읽지 않은 메일 API 상세 테스트
    test_unread_mail_api_detailed(token)
    
    print(f"\n🏁 디버깅 완료")
    print("=" * 60)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()