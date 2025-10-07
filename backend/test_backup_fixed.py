#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수정된 백업 기능 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

def test_backup_api():
    """수정된 백업 API를 테스트합니다."""
    print("=" * 60)
    print("수정된 백업 기능 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # 1. 로그인
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        print("🔐 로그인 중...")
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 로그인 성공")
        
    except Exception as e:
        print(f"❌ 로그인 중 오류: {e}")
        return
    
    # 2. 백업 API 호출
    try:
        print("💾 백업 API 호출 중...")
        backup_url = f"{base_url}/api/v1/mail/backup"
        params = {
            "include_attachments": False
        }
        
        response = requests.post(backup_url, headers=headers, params=params, timeout=30)
        
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                backup_filename = data.get("backup_filename")
                backup_count = data.get("mail_count", 0)
                backup_size = data.get("backup_size", 0)
                
                print(f"✅ 백업 성공!")
                print(f"   - 백업 파일명: {backup_filename}")
                print(f"   - 백업된 메일 수: {backup_count}개")
                print(f"   - 백업 파일 크기: {backup_size} bytes")
                
                if backup_filename:
                    return backup_filename
            else:
                print(f"❌ 백업 실패: {result.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 백업 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 백업 API 호출 중 오류: {e}")
    
    return None

def check_backup_file_content(backup_filename):
    """백업 파일 내용을 확인합니다."""
    if not backup_filename:
        print("❌ 백업 파일명이 없습니다.")
        return
        
    print("\n" + "=" * 60)
    print("백업 파일 내용 확인")
    print("=" * 60)
    
    import zipfile
    import os
    
    backup_path = f"c:\\Users\\moon4\\skyboot.mail2\\backend\\backups\\{backup_filename}"
    
    if os.path.exists(backup_path):
        print(f"✅ 백업 파일 존재: {backup_path}")
        print(f"   파일 크기: {os.path.getsize(backup_path)} bytes")
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                print(f"   ZIP 파일 내용: {zipf.namelist()}")
                
                if 'mails.json' in zipf.namelist():
                    json_content = zipf.read('mails.json').decode('utf-8')
                    print(f"   mails.json 내용 길이: {len(json_content)} characters")
                    
                    # JSON 파싱
                    try:
                        mail_data = json.loads(json_content)
                        print(f"   파싱된 데이터 타입: {type(mail_data)}")
                        
                        if isinstance(mail_data, list):
                            print(f"   ✅ 메일 개수: {len(mail_data)}개")
                            if len(mail_data) > 0:
                                print("   첫 번째 메일 샘플:")
                                first_mail = mail_data[0]
                                print(f"      - 제목: {first_mail.get('subject', 'N/A')}")
                                print(f"      - 발송자: {first_mail.get('sender_email', 'N/A')}")
                                print(f"      - 수신자: {first_mail.get('recipients', [])}")
                                print(f"      - 발송 시간: {first_mail.get('sent_at', 'N/A')}")
                        else:
                            print(f"   ❌ 예상하지 못한 데이터 구조: {type(mail_data)}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON 파싱 오류: {e}")
                else:
                    print("   ❌ mails.json 파일이 ZIP에 없습니다")
                    
        except Exception as e:
            print(f"   ❌ ZIP 파일 읽기 오류: {e}")
    else:
        print(f"❌ 백업 파일이 존재하지 않습니다: {backup_path}")

if __name__ == "__main__":
    backup_filename = test_backup_api()
    if backup_filename:
        time.sleep(1)  # 파일 생성 완료 대기
        check_backup_file_content(backup_filename)