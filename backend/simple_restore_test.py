#!/usr/bin/env python3
"""
간단한 복원 API 테스트 스크립트
"""

import requests
import json
import os

# API 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
RESTORE_URL = f"{BASE_URL}/api/v1/mail/restore"

# 백업 파일 경로
BACKUP_FILE = "backups/mail_backup_user01@example.com_20251006_220355.zip"

def main():
    print("=" * 60)
    print("간단한 복원 API 테스트")
    print("=" * 60)
    
    # 백업 파일 확인
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ 백업 파일이 없습니다: {BACKUP_FILE}")
        return
    
    print(f"✅ 백업 파일 확인: {BACKUP_FILE}")
    print(f"📊 파일 크기: {os.path.getsize(BACKUP_FILE)} bytes")
    
    # 로그인
    print("\n🔐 로그인 중...")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    login_response = requests.post(LOGIN_URL, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.status_code}")
        print(f"응답: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 로그인 성공")
    
    # 복원 API 호출 (매우 간단한 형태)
    print("\n📥 복원 API 호출 중...")
    
    with open(BACKUP_FILE, 'rb') as f:
        files = {'backup_file': f}
        data = {
            'overwrite_existing': 'true'  # 기존 메일 덮어쓰기 활성화
        }
        
        response = requests.post(RESTORE_URL, files=files, data=data, headers=headers)
    
    print(f"📊 응답 상태: {response.status_code}")
    print(f"📊 응답 내용: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ API 호출 성공!")
        print(f"   복원된 메일: {result['data']['restored_count']}개")
        print(f"   건너뛴 메일: {result['data']['skipped_count']}개")
    else:
        print(f"\n❌ API 호출 실패!")

if __name__ == "__main__":
    main()