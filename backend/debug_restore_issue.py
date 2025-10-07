#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
복원 문제 디버깅 스크립트
"""

import requests
import json
import zipfile
import os

def debug_restore_issue():
    """복원 문제를 디버깅합니다."""
    print("=" * 60)
    print("복원 문제 디버깅")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    backup_filename = "mail_backup_user01@example.com_20251006_220355.zip"
    backup_path = f"c:\\Users\\moon4\\skyboot.mail2\\backend\\backups\\{backup_filename}"
    
    # 1. 백업 파일 내용 상세 분석
    print("📦 백업 파일 상세 분석")
    print("-" * 40)
    
    if os.path.exists(backup_path):
        print(f"✅ 백업 파일 존재: {backup_filename}")
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
                                print("\n   📧 첫 번째 메일 상세 정보:")
                                first_mail = mail_data[0]
                                for key, value in first_mail.items():
                                    if key == 'content' and len(str(value)) > 100:
                                        print(f"      - {key}: {str(value)[:100]}...")
                                    else:
                                        print(f"      - {key}: {value}")
                                
                                print("\n   📧 두 번째 메일 상세 정보:")
                                if len(mail_data) > 1:
                                    second_mail = mail_data[1]
                                    for key, value in second_mail.items():
                                        if key == 'content' and len(str(value)) > 100:
                                            print(f"      - {key}: {str(value)[:100]}...")
                                        else:
                                            print(f"      - {key}: {value}")
                                else:
                                    print("      두 번째 메일이 없습니다.")
                            else:
                                print("   ❌ 메일 데이터가 비어있습니다!")
                        else:
                            print(f"   ❌ 예상하지 못한 데이터 구조: {type(mail_data)}")
                            print(f"   데이터 내용: {mail_data}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON 파싱 오류: {e}")
                        print(f"   JSON 내용 미리보기: {json_content[:500]}")
                else:
                    print("   ❌ mails.json 파일이 ZIP에 없습니다")
                    
        except Exception as e:
            print(f"   ❌ ZIP 파일 읽기 오류: {e}")
    else:
        print(f"❌ 백업 파일이 존재하지 않습니다: {backup_path}")
        return
    
    # 2. 로그인 및 복원 API 호출 (상세 로깅)
    print("\n" + "=" * 60)
    print("복원 API 호출 테스트")
    print("=" * 60)
    
    # 로그인
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
    
    # 복원 API 호출
    try:
        print("\n📥 복원 API 호출 중...")
        restore_url = f"{base_url}/api/v1/mail/restore"
        
        # 파일 업로드
        with open(backup_path, 'rb') as f:
            files = {'backup_file': (backup_filename, f, 'application/zip')}
            data = {
                'overwrite_existing': 'false'
            }
            
            response = requests.post(restore_url, headers=headers, files=files, data=data, timeout=60)
        
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 헤더: {dict(response.headers)}")
        print(f"📊 응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API 호출 성공!")
            print(f"   응답 구조: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 복원 API 호출 중 오류: {e}")

if __name__ == "__main__":
    debug_restore_issue()