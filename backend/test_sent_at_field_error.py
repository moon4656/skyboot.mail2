#!/usr/bin/env python3
"""
메일 발송 후 검색에서 sent_at 필드 오류를 재현하는 테스트 스크립트
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def main():
    try:
        # 1. 로그인
        print("🔐 로그인 중...")
        login_data = {
            "user_id": "admin01",
            "password": "test"
        }
        
        login_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=login_data
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 로그인 성공!")
        else:
            print(f"❌ 로그인 실패: {login_response.text}")
            return
        
        # 2. 테스트 메일 발송
        print("\n📤 테스트 메일 발송 중...")
        mail_data = {
            "to": ["test@example.com"],
            "subject": "sent_at 필드 오류 테스트 메일",
            "body_text": "이 메일은 sent_at 필드 오류를 재현하기 위한 테스트 메일입니다.",
            "priority": "normal"
        }
        
        send_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/send-json",
            json=mail_data,
            headers=headers
        )
        
        if send_response.status_code == 200:
            send_result = send_response.json()
            print("✅ 메일 발송 성공!")
            print(f"📧 발송된 메일 ID: {send_result.get('mail_uuid', 'N/A')}")
        else:
            print(f"❌ 메일 발송 실패: {send_response.text}")
            return
        
        # 잠시 대기
        time.sleep(1)
        
        # 3. 메일 검색 (기본 검색)
        print("\n🔍 기본 메일 검색 중...")
        search_data = {
            "page": 1,
            "limit": 10
        }
        
        search_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/search",
            json=search_data,
            headers=headers
        )
        
        print(f"메일 검색 상태: {search_response.status_code}")
        if search_response.status_code == 200:
            search_result = search_response.json()
            print("✅ 메일 검색 성공!")
            
            mails = search_result.get('data', {}).get('mails', [])
            print(f"📊 검색 결과: {len(mails)}개 메일")
            
            for i, mail in enumerate(mails, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                
                # sent_at 필드가 None인지 확인
                if mail.get('sent_at') is None:
                    print(f"⚠️ sent_at 필드가 None인 메일 발견!")
                    print(f"   전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 메일 검색 실패: {search_response.text}")
        
        # 4. SENT 폴더 검색
        print("\n📁 SENT 폴더 검색 중...")
        sent_search_data = {
            "page": 1,
            "limit": 10,
            "folder_type": "sent"
        }
        
        sent_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/search",
            json=sent_search_data,
            headers=headers
        )
        
        print(f"SENT 폴더 검색 상태: {sent_response.status_code}")
        if sent_response.status_code == 200:
            sent_result = sent_response.json()
            print("✅ SENT 폴더 검색 성공!")
            
            sent_mails = sent_result.get('data', {}).get('mails', [])
            print(f"📊 SENT 폴더 결과: {len(sent_mails)}개 메일")
            
            for i, mail in enumerate(sent_mails, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                
                # sent_at 필드가 None인지 확인
                if mail.get('sent_at') is None:
                    print(f"⚠️ sent_at 필드가 None인 메일 발견!")
                    print(f"   전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ SENT 폴더 검색 실패: {sent_response.text}")
        
        # 5. 발송 메일함 조회 (기존 API)
        print("\n📤 발송 메일함 조회 중...")
        sent_box_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/sent",
            headers=headers
        )
        
        print(f"발송 메일함 조회 상태: {sent_box_response.status_code}")
        if sent_box_response.status_code == 200:
            sent_box_result = sent_box_response.json()
            print("✅ 발송 메일함 조회 성공!")
            
            sent_box_mails = sent_box_result.get('data', {}).get('mails', [])
            print(f"📊 발송 메일함 결과: {len(sent_box_mails)}개 메일")
            
            for i, mail in enumerate(sent_box_mails, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                
                # sent_at 필드가 None인지 확인
                if mail.get('sent_at') is None:
                    print(f"⚠️ sent_at 필드가 None인 메일 발견!")
                    print(f"   전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 발송 메일함 조회 실패: {sent_box_response.text}")
        
        print("\n🔍 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()