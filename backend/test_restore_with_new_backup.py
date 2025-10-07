#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로 생성된 백업 파일로 복원 테스트 스크립트
"""

import requests
import os
import time

def test_restore_with_new_backup():
    """새로 생성된 백업 파일로 복원을 테스트합니다."""
    print("=" * 60)
    print("새 백업 파일로 복원 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    backup_filename = "mail_backup_user01@example.com_20251006_220355.zip"
    backup_path = f"c:\\Users\\moon4\\skyboot.mail2\\backend\\backups\\{backup_filename}"
    
    # 백업 파일 존재 확인
    if not os.path.exists(backup_path):
        print(f"❌ 백업 파일이 존재하지 않습니다: {backup_path}")
        return
    
    print(f"✅ 백업 파일 확인: {backup_filename}")
    print(f"   파일 크기: {os.path.getsize(backup_path)} bytes")
    
    # 1. 로그인
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        print("\n🔐 로그인 중...")
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
    
    # 2. 복원 API 호출
    try:
        print("\n📥 복원 API 호출 중...")
        restore_url = f"{base_url}/api/v1/mail/restore"
        
        # 파일 업로드
        with open(backup_path, 'rb') as f:
            files = {'backup_file': (backup_filename, f, 'application/zip')}
            data = {
                'skip_duplicates': 'true',
                'create_mail_user': 'true'
            }
            
            response = requests.post(restore_url, headers=headers, files=files, data=data, timeout=60)
        
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📊 응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                restored_count = data.get("restored_count", 0)
                skipped_count = data.get("skipped_count", 0)
                total_count = data.get("total_count", 0)
                processing_time = data.get("processing_time", 0)
                
                print(f"\n✅ 복원 성공!")
                print(f"   - 총 메일 수: {total_count}개")
                print(f"   - 복원된 메일: {restored_count}개")
                print(f"   - 건너뛴 메일: {skipped_count}개")
                print(f"   - 처리 시간: {processing_time:.2f}초")
                
                if restored_count > 0:
                    print(f"   🎉 {restored_count}개의 메일이 성공적으로 복원되었습니다!")
                elif skipped_count > 0:
                    print(f"   ℹ️ 모든 메일이 이미 존재하여 건너뛰었습니다.")
                else:
                    print(f"   ⚠️ 복원된 메일이 없습니다.")
                    
            else:
                print(f"❌ 복원 실패: {result.get('message', '알 수 없는 오류')}")
        else:
            print(f"❌ 복원 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 복원 API 호출 중 오류: {e}")

if __name__ == "__main__":
    test_restore_with_new_backup()