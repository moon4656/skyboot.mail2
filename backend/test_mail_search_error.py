#!/usr/bin/env python3
"""
메일 검색 API에서 sent_at 필드 오류를 재현하는 테스트 스크립트
"""

import requests
import json

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
            print(f"로그인 응답: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
            
            # 응답 구조에 따라 토큰 추출
            if "data" in login_result:
                token = login_result["data"]["access_token"]
            elif "access_token" in login_result:
                token = login_result["access_token"]
            else:
                print(f"❌ 토큰을 찾을 수 없습니다: {login_result}")
                return
                
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 로그인 성공!")
        else:
            print(f"❌ 로그인 실패: {login_response.text}")
            return
        
        # 2. 메일 검색 API 호출 (다양한 파라미터로 테스트)
        print("\n🔍 메일 검색 API 테스트 중...")
        
        # 기본 검색
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
            print(f"📊 검색 결과: {len(search_result.get('data', {}).get('mails', []))}개 메일")
            
            # 각 메일의 sent_at 필드 확인
            mails = search_result.get('data', {}).get('mails', [])
            for i, mail in enumerate(mails, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                print(f"      전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 메일 검색 실패: {search_response.text}")
        
        # 3. 폴더별 검색 테스트
        print("\n📁 폴더별 검색 테스트...")
        folder_types = ["inbox", "sent", "draft", "trash"]
        
        for folder_type in folder_types:
            print(f"\n🔍 {folder_type.upper()} 폴더 검색 중...")
            folder_data = {
                "page": 1,
                "limit": 5,
                "folder_type": folder_type
            }
            
            folder_response = requests.post(
                f"{BASE_URL}{API_PREFIX}/mail/search",
                json=folder_data,
                headers=headers
            )
            
            print(f"{folder_type.upper()} 검색 상태: {folder_response.status_code}")
            if folder_response.status_code == 200:
                folder_result = folder_response.json()
                mails = folder_result.get('data', {}).get('mails', [])
                print(f"✅ {folder_type.upper()} 검색 성공! ({len(mails)}개 메일)")
                
                # sent_at 필드 확인
                for mail in mails:
                    sent_at = mail.get('sent_at')
                    if sent_at is None:
                        print(f"⚠️ sent_at 필드가 None인 메일 발견: {mail.get('subject', 'N/A')}")
                        print(f"   전체 데이터: {json.dumps(mail, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ {folder_type.upper()} 검색 실패: {folder_response.text}")
        
        print("\n🔍 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()