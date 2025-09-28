#!/usr/bin/env python3
"""
스키마 수정 후 받은 메일함 API 테스트
"""

import requests
import json
import os
from dotenv import load_dotenv

def test_inbox_api():
    """받은 메일함 API 테스트"""
    # 환경 변수 로드
    load_dotenv()
    
    # API 기본 URL
    base_url = "http://localhost:8000"
    
    print("📧 받은 메일함 API 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 로그인하여 토큰 획득
        print("\n1. 로그인 테스트:")
        login_data = {
            "email": "mailtest@skyboot.com",
            "password": "testpassword123"
        }
        
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  - 로그인 상태 코드: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"  - 로그인 실패: {login_response.text}")
            return
        
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        
        if not access_token:
            print(f"  - 토큰 없음: {login_result}")
            return
        
        print(f"  - 로그인 성공, 토큰 획득")
        
        # 2. 받은 메일함 조회 테스트
        print("\n=== 받은 메일함 조회 테스트 ===")
        inbox_response = requests.get(
            f"{base_url}/api/v1/mail/inbox",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"받은 메일함 응답 상태: {inbox_response.status_code}")
        if inbox_response.status_code == 200:
            inbox_data = inbox_response.json()
            print(f"✅ 받은 메일함 조회 성공 - 메일 수: {len(inbox_data.get('mails', []))}")
            print(f"메일 목록: {inbox_data}")
        else:
            print(f"❌ 받은 메일함 조회 실패: {inbox_response.text}")

        # 3. 메일 통계 조회 테스트
        print("\n=== 메일 통계 조회 테스트 ===")
        stats_response = requests.get(
            f"{base_url}/api/v1/mail/stats",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"메일 통계 응답 상태: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"✅ 메일 통계 조회 성공: {stats_data}")
        else:
            print(f"❌ 메일 통계 조회 실패: {stats_response.text}")

        # 4. 휴지통 조회 테스트
        print("\n=== 휴지통 조회 테스트 ===")
        trash_response = requests.get(
            f"{base_url}/api/v1/mail/trash",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"휴지통 응답 상태: {trash_response.status_code}")
        if trash_response.status_code == 200:
            trash_data = trash_response.json()
            print(f"✅ 휴지통 조회 성공 - 메일 수: {len(trash_data.get('mails', []))}")
        else:
            print(f"❌ 휴지통 조회 실패: {trash_response.text}")

        # 5. 메일 폴더 목록 조회 테스트
        print("\n=== 메일 폴더 목록 조회 테스트 ===")
        folders_response = requests.get(
            f"{base_url}/api/v1/mail/folders",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"폴더 목록 응답 상태: {folders_response.status_code}")
        if folders_response.status_code == 200:
            folders_data = folders_response.json()
            print(f"✅ 폴더 목록 조회 성공 - 폴더 수: {len(folders_data.get('folders', []))}")
            print(f"폴더 목록: {folders_data}")
        else:
            print(f"❌ 폴더 목록 조회 실패: {folders_response.text}")
        
        print("\n✅ 받은 메일함 API 테스트 완료")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    test_inbox_api()