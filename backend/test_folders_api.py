#!/usr/bin/env python3
"""
메일 폴더 API 테스트 스크립트
스웨거에서 INBOX가 없는 문제를 확인하기 위한 테스트
"""
import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

print("📁 메일 폴더 API 테스트")
print("=" * 50)

# 1. 로그인
print("🔐 관리자 로그인 중...")
login_data = {
    "user_id": "admin01",
    "password": "test"
}

login_response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_data)
print(f"로그인 상태: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    access_token = login_result["access_token"]
    print("✅ 로그인 성공")
    
    # 2. 메일 폴더 목록 조회
    print("\n📁 메일 폴더 목록 조회 중...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
    }
    
    folders_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/folders",
        headers=headers
    )
    
    print(f"폴더 목록 조회 상태: {folders_response.status_code}")
    
    if folders_response.status_code == 200:
        folders_result = folders_response.json()
        print("✅ 폴더 목록 조회 성공!")
        print(f"응답 데이터: {json.dumps(folders_result, indent=2, ensure_ascii=False)}")
        
        folders = folders_result.get("folders", [])
        if folders:
            print(f"\n📂 폴더 목록 ({len(folders)}개):")
            for folder in folders:
                print(f"   - 이름: {folder.get('name', 'N/A')}")
                print(f"     타입: {folder.get('folder_type', 'N/A')}")
                print(f"     UUID: {folder.get('folder_uuid', 'N/A')}")
                print(f"     메일 수: {folder.get('mail_count', 0)}")
                print()
                
            # INBOX 폴더 확인
            inbox_folders = [f for f in folders if f.get("name") == "INBOX" or f.get("folder_type") == "INBOX"]
            if inbox_folders:
                print("✅ INBOX 폴더 발견!")
                for inbox in inbox_folders:
                    print(f"   INBOX 정보: {json.dumps(inbox, indent=2, ensure_ascii=False)}")
            else:
                print("❌ INBOX 폴더를 찾을 수 없습니다!")
                print("   현재 폴더 이름들:", [f.get('name') for f in folders])
                print("   현재 폴더 타입들:", [f.get('folder_type') for f in folders])
        else:
            print("📁 폴더가 없습니다.")
    else:
        print(f"❌ 폴더 목록 조회 실패: {folders_response.text}")
        
else:
    print(f"❌ 로그인 실패: {login_response.text}")

print("\n🔍 테스트 완료!")