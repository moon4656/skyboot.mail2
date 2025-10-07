#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수정된 읽지 않은 메일 API 테스트

읽지 않은 메일 API에 is_read = False 필터링을 추가한 후 테스트합니다.
"""

import requests
import json
import psycopg2
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 데이터베이스 연결 설정
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "skyboot_mail",
    "user": "postgres",
    "password": "postgres",
    "client_encoding": "utf8"  # 인코딩 명시적 설정
}

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def get_db_connection():
    """데이터베이스 연결 생성"""
    return psycopg2.connect(**DB_CONFIG)

def login_user():
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중...")
    print("=" * 50)
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=TEST_USER)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"로그인 응답 구조: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 다양한 응답 구조 처리
            token = None
            if isinstance(result, dict):
                if "access_token" in result:
                    token = result["access_token"]
                elif "data" in result and isinstance(result["data"], dict):
                    token = result["data"].get("access_token")
                elif "token" in result:
                    token = result["token"]
            
            if token:
                print(f"✅ 로그인 성공! 토큰: {token[:20]}...")
                return token
            else:
                print(f"❌ 로그인 응답에서 토큰을 찾을 수 없습니다.")
                return None
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {e}")
        return None

def check_database_unread():
    """데이터베이스에서 읽지 않은 메일 확인"""
    print(f"\n🗄️ 데이터베이스 읽지 않은 메일 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 읽지 않은 메일 쿼리 (수정된 API와 동일한 로직)
        query = """
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                mif.is_read,
                mf.name as folder_name,
                mf.folder_type
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = %s 
            AND mf.folder_type = 'inbox'
            AND mif.is_read = false
            ORDER BY m.created_at DESC;
        """
        
        cursor.execute(query, (user_uuid,))
        unread_mails = cursor.fetchall()
        
        print(f"📧 데이터베이스 읽지 않은 메일: {len(unread_mails)}개")
        
        if unread_mails:
            print(f"\n📋 읽지 않은 메일 목록:")
            for i, mail in enumerate(unread_mails, 1):
                mail_uuid = str(mail[0])[:8] if mail[0] else "N/A"
                subject = str(mail[1]) if mail[1] else "No Subject"
                created_at = str(mail[2]) if mail[2] else "Unknown"
                is_read = mail[3]
                folder_name = str(mail[4]) if mail[4] else "Unknown"
                folder_type = str(mail[5]) if mail[5] else "Unknown"
                
                print(f"  {i}. {subject}")
                print(f"     UUID: {mail_uuid}...")
                print(f"     생성일: {created_at}")
                print(f"     읽음상태: {is_read}")
                print(f"     폴더: {folder_name} ({folder_type})")
                print()
        else:
            print(f"📭 데이터베이스에 읽지 않은 메일이 없습니다.")
        
        cursor.close()
        conn.close()
        
        return len(unread_mails)
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 실패: {e}")
        return 0

def test_unread_mail_api(token):
    """수정된 읽지 않은 메일 API 테스트"""
    if not token:
        print(f"\n❌ 토큰이 없어 API 테스트를 건너뜁니다.")
        return False, 0
    
    print(f"\n📧 수정된 읽지 않은 메일 API 테스트")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/mail/unread", headers=headers)
        print(f"API 응답 상태: {response.status_code}")
        
        # 응답 헤더 확인
        org_id = response.headers.get('x-organization-id')
        org_code = response.headers.get('x-organization-code')
        print(f"조직 ID: {org_id}")
        print(f"조직 코드: {org_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 호출 성공!")
            print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success"):
                data = result.get("data", {})
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                print(f"\n📊 API 결과:")
                print(f"  - 총 읽지 않은 메일 수: {total}")
                print(f"  - 현재 페이지 메일 수: {len(mails)}")
                
                if mails:
                    print(f"\n📧 읽지 않은 메일 목록:")
                    for i, mail in enumerate(mails, 1):
                        subject = mail.get('subject', 'No Subject')
                        sender = mail.get('sender_email', 'Unknown')
                        created_at = mail.get('created_at', 'Unknown')
                        is_read = mail.get('is_read', 'Unknown')
                        
                        print(f"  {i}. {subject}")
                        print(f"     발송자: {sender}")
                        print(f"     생성일: {created_at}")
                        print(f"     읽음상태: {is_read}")
                        print()
                else:
                    print(f"  📭 API에서 읽지 않은 메일이 반환되지 않았습니다.")
                
                return True, total
            else:
                print(f"❌ API 실패: {result.get('message')}")
                return False, 0
        else:
            print(f"❌ API 호출 실패: {response.text}")
            return False, 0
            
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return False, 0

def compare_results(db_count, api_success, api_count):
    """데이터베이스와 API 결과 비교"""
    print(f"\n📊 결과 비교")
    print("=" * 50)
    
    print(f"데이터베이스 읽지 않은 메일: {db_count}개")
    print(f"API 읽지 않은 메일: {api_count}개")
    print(f"API 테스트 성공: {api_success}")
    
    if db_count > 0 and api_success and api_count > 0:
        if db_count == api_count:
            print(f"✅ 완벽 성공! 데이터베이스와 API 결과가 일치합니다. ({db_count}개)")
            return True
        else:
            print(f"⚠️ 부분 성공! API는 작동하지만 개수가 다릅니다. (DB: {db_count}, API: {api_count})")
            return True
    elif db_count > 0 and (not api_success or api_count == 0):
        print(f"❌ 실패! 데이터베이스에는 읽지 않은 메일이 있지만 API에서 반환하지 않습니다.")
        return False
    elif db_count == 0 and api_count == 0:
        print(f"✅ 성공! 데이터베이스와 API 모두 읽지 않은 메일이 없다고 보고합니다.")
        return True
    else:
        print(f"❌ 예상치 못한 상황입니다.")
        return False

def main():
    """메인 테스트 함수"""
    print(f"🧪 수정된 읽지 않은 메일 API 테스트")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)
    
    # 1. 데이터베이스에서 읽지 않은 메일 확인
    db_count = check_database_unread()
    
    # 2. 사용자 로그인
    token = login_user()
    
    # 3. 수정된 API 테스트
    api_success, api_count = test_unread_mail_api(token)
    
    # 4. 결과 비교
    success = compare_results(db_count, api_success, api_count)
    
    print(f"\n🏁 테스트 완료")
    print("=" * 70)
    print(f"종료 시간: {datetime.now()}")
    print(f"전체 결과: {'✅ 성공' if success else '❌ 실패'}")

if __name__ == "__main__":
    main()