#!/usr/bin/env python3
"""
Restore 엔드포인트 직접 테스트 스크립트
"""

import requests
import json
import tempfile
import zipfile
import os

def test_restore_endpoint():
    """Restore 엔드포인트를 직접 테스트합니다."""
    
    base_url = "http://localhost:8001"
    
    print("🔍 Restore 엔드포인트 테스트 시작...")
    
    # 1. 로그인
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
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
    
    # 2. 테스트용 백업 파일 생성
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_path = temp_file.name
            
        with zipfile.ZipFile(temp_path, 'w') as zip_file:
            # 테스트용 메일 데이터 생성 (실제 백업 형식에 맞춤)
            mails_data = [
                {
                    "mail_uuid": "test-mail-001",
                    "subject": "테스트 메일 1",
                    "content": "테스트 메일 내용 1",
                    "status": "sent",
                    "priority": "normal",
                    "created_at": "2024-01-01T10:00:00",
                    "sent_at": "2024-01-01T10:00:00",
                    "recipients": [
                        {
                            "email": "test@example.com",
                            "type": "to"
                        }
                    ]
                },
                {
                    "mail_uuid": "test-mail-002", 
                    "subject": "테스트 메일 2",
                    "content": "테스트 메일 내용 2",
                    "status": "sent",
                    "priority": "high",
                    "created_at": "2024-01-01T11:00:00",
                    "sent_at": "2024-01-01T11:00:00",
                    "recipients": [
                        {
                            "email": "test2@example.com",
                            "type": "to"
                        },
                        {
                            "email": "cc@example.com",
                            "type": "cc"
                        }
                    ]
                }
            ]
            zip_file.writestr("mails.json", json.dumps(mails_data, ensure_ascii=False, indent=2))
        
        print(f"✅ 테스트 백업 파일 생성: {temp_path}")
        
    except Exception as e:
        print(f"❌ 백업 파일 생성 실패: {e}")
        return
    
    # 3. Restore API 호출
    try:
        with open(temp_path, 'rb') as f:
            files = {'backup_file': ('test_backup.zip', f, 'application/zip')}
            data = {'organization_id': '1'}
            
            print("📤 Restore API 호출 중...")
            response = requests.post(
                f"{base_url}/api/v1/mail/restore",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📊 응답 헤더: {dict(response.headers)}")
            print(f"📊 응답 내용: {response.text}")
            
            if response.status_code == 200:
                print("✅ Restore API 성공!")
            else:
                print(f"❌ Restore API 실패: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Restore API 호출 중 오류: {e}")
    
    finally:
        # 임시 파일 정리
        try:
            os.unlink(temp_path)
            print("🧹 임시 파일 정리 완료")
        except:
            pass

if __name__ == "__main__":
    test_restore_endpoint()