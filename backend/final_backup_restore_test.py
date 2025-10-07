#!/usr/bin/env python3
"""
최종 백업 및 복원 기능 검증 스크립트
"""

import requests
import json
import os
from datetime import datetime

# API 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
BACKUP_URL = f"{BASE_URL}/api/v1/mail/backup"
RESTORE_URL = f"{BASE_URL}/api/v1/mail/restore"
INBOX_URL = f"{BASE_URL}/api/v1/mail/inbox"
SENT_URL = f"{BASE_URL}/api/v1/mail/sent"

# 사용자 정보
USER_ID = "user01"
PASSWORD = "test"

def login():
    """사용자 로그인"""
    print("🔐 로그인 중...")
    
    login_data = {
        "user_id": USER_ID,
        "password": PASSWORD
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ 로그인 성공")
        return token
    else:
        print(f"❌ 로그인 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def get_mail_count(token):
    """현재 메일 개수 확인"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 받은 메일함 확인
    inbox_response = requests.get(INBOX_URL, headers=headers)
    inbox_count = 0
    if inbox_response.status_code == 200:
        inbox_count = inbox_response.json().get("total", 0)
    
    # 보낸 메일함 확인
    sent_response = requests.get(SENT_URL, headers=headers)
    sent_count = 0
    if sent_response.status_code == 200:
        sent_count = sent_response.json().get("total", 0)
    
    return inbox_count, sent_count

def create_backup(token):
    """새로운 백업 파일 생성"""
    print("📦 새로운 백업 파일 생성 중...")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "include_attachments": False
    }
    
    response = requests.post(BACKUP_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        result = response.json()
        backup_filename = result["data"]["backup_filename"]
        print(f"✅ 백업 생성 성공: {backup_filename}")
        return backup_filename
    else:
        print(f"❌ 백업 생성 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def restore_backup(token, backup_filename, overwrite=True):
    """백업 파일 복원"""
    print(f"📥 백업 파일 복원 중: {backup_filename}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    backup_path = os.path.join("backups", backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_path}")
        return False
    
    with open(backup_path, "rb") as f:
        files = {"backup_file": (backup_filename, f, "application/zip")}
        data = {"overwrite_existing": str(overwrite).lower()}
        
        response = requests.post(RESTORE_URL, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 복원 성공!")
        print(f"   복원된 메일: {result['data']['restored_count']}개")
        print(f"   건너뛴 메일: {result['data']['skipped_count']}개")
        return True
    else:
        print(f"❌ 복원 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("최종 백업 및 복원 기능 검증")
    print("=" * 60)
    
    # 1. 로그인
    token = login()
    if not token:
        return
    
    # 2. 현재 메일 개수 확인
    print("\n📊 현재 메일 개수 확인")
    inbox_count, sent_count = get_mail_count(token)
    print(f"   받은 메일함: {inbox_count}개")
    print(f"   보낸 메일함: {sent_count}개")
    
    # 3. 새로운 백업 파일 생성
    print("\n📦 새로운 백업 파일 생성")
    backup_filename = create_backup(token)
    if not backup_filename:
        return
    
    # 4. 백업 파일 복원 (덮어쓰기 모드)
    print("\n📥 백업 파일 복원 (덮어쓰기 모드)")
    restore_success = restore_backup(token, backup_filename, overwrite=True)
    if not restore_success:
        return
    
    # 5. 복원 후 메일 개수 확인
    print("\n📊 복원 후 메일 개수 확인")
    new_inbox_count, new_sent_count = get_mail_count(token)
    print(f"   받은 메일함: {new_inbox_count}개")
    print(f"   보낸 메일함: {new_sent_count}개")
    
    # 6. 백업 파일 복원 (건너뛰기 모드)
    print("\n📥 백업 파일 복원 (건너뛰기 모드)")
    restore_success = restore_backup(token, backup_filename, overwrite=False)
    if not restore_success:
        return
    
    # 7. 최종 메일 개수 확인
    print("\n📊 최종 메일 개수 확인")
    final_inbox_count, final_sent_count = get_mail_count(token)
    print(f"   받은 메일함: {final_inbox_count}개")
    print(f"   보낸 메일함: {final_sent_count}개")
    
    print("\n" + "=" * 60)
    print("✅ 최종 백업 및 복원 기능 검증 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()