#!/usr/bin/env python3
"""
restore_mails 함수 파일 처리 오류 수정 테스트 스크립트
"""

import requests
import json
import os
import tempfile
import zipfile
from datetime import datetime

# API 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"

def create_test_backup_file():
    """테스트용 백업 파일 생성 (다양한 인코딩 테스트 포함)"""
    print("📦 테스트용 백업 파일 생성 중...")
    
    # 테스트 메일 데이터 (한글 포함)
    test_mail_data = [
        {
            "id": 999999,
            "mail_uuid": f"test_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "subject": "복원 테스트 메일 - UTF-8 인코딩 테스트",
            "content": "이 메일은 복원 기능 테스트를 위한 메일입니다. 한글 인코딩 테스트: 안녕하세요! 🚀",
            "status": "sent",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "sent_at": datetime.now().isoformat(),
            "read_at": None,
            "recipients": [
                {
                    "email": "test@example.com",
                    "type": "to"
                }
            ]
        },
        {
            "id": 999998,
            "mail_uuid": f"test_restore_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "subject": "두 번째 테스트 메일",
            "content": "특수문자 테스트: ♥♦♣♠ 이모지 테스트: 😀😃😄😁",
            "status": "draft",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
            "sent_at": None,
            "read_at": None,
            "recipients": [
                {
                    "email": "test2@example.com",
                    "type": "to"
                }
            ]
        }
    ]
    
    # 임시 백업 파일 생성 (UTF-8 인코딩 명시)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            # mails.json 파일 생성 (UTF-8 인코딩 명시)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_json:
                json.dump(test_mail_data, temp_json, indent=2, ensure_ascii=False, default=str)
                temp_json.flush()
                temp_json.close()
                zipf.write(temp_json.name, "mails.json")
                os.unlink(temp_json.name)  # 임시 JSON 파일 정리
        
        backup_file_path = temp_zip.name
    
    print(f"✅ 테스트 백업 파일 생성 완료: {backup_file_path}")
    return backup_file_path

def test_restore_function():
    """restore_mails 함수 테스트"""
    print("🔧 restore_mails 함수 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 로그인
        print("\n🔐 로그인 중...")
        login_data = {
            "user_id": "user01",
            "password": "test"
        }
        
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code != 200:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
        
        login_result = response.json()
        token = login_result["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 로그인 성공")
        
        # 2. 테스트 백업 파일 생성
        backup_file_path = create_test_backup_file()
        
        # 3. 메일 복원 테스트
        print(f"\n📦 메일 복원 테스트...")
        restore_url = f"{BASE_URL}/api/v1/mail/restore"
        
        # 파일 업로드 준비
        with open(backup_file_path, 'rb') as backup_file:
            files = {
                'backup_file': ('test_backup.zip', backup_file, 'application/zip')
            }
            data = {
                'overwrite_existing': 'false'
            }
            
            response = requests.post(restore_url, files=files, data=data, headers=headers)
        
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 복원된 메일 수 확인
            if result.get("success"):
                print("✅ 메일 복원 성공!")
                restored_count = result.get("data", {}).get("restored_count", 0)
                skipped_count = result.get("data", {}).get("skipped_count", 0)
                print(f"📊 복원 결과: 복원 {restored_count}개, 건너뜀 {skipped_count}개")
            else:
                print(f"❌ 복원 실패: {result.get('message', '알 수 없는 오류')}")
                print(f"📋 오류 상세: {result}")
            
            return True
        else:
            print(f"❌ 메일 복원 실패: {response.status_code}")
            try:
                error_data = response.json()
                print(f"오류 상세: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"오류 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 테스트 백업 파일 정리
        if 'backup_file_path' in locals() and os.path.exists(backup_file_path):
            try:
                os.unlink(backup_file_path)
                print(f"🗑️ 테스트 백업 파일 정리 완료: {backup_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ 테스트 백업 파일 정리 실패: {str(cleanup_error)}")

def test_multiple_restores():
    """여러 번 복원 테스트 (파일 잠금 문제 확인)"""
    print("\n🔄 연속 복원 테스트 (파일 잠금 문제 확인)")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"\n📦 복원 테스트 {i+1}/{total_tests}")
        if test_restore_function():
            success_count += 1
            print(f"✅ 테스트 {i+1} 성공")
        else:
            print(f"❌ 테스트 {i+1} 실패")
    
    print(f"\n📊 연속 테스트 결과: {success_count}/{total_tests} 성공")
    
    if success_count == total_tests:
        print("🎉 모든 연속 복원 테스트가 성공했습니다! 파일 잠금 문제가 해결되었습니다.")
        return True
    else:
        print("❌ 일부 테스트가 실패했습니다. 추가 확인이 필요합니다.")
        return False

def main():
    print("🔧 restore_mails 파일 처리 오류 수정 테스트")
    print("=" * 60)
    
    # 단일 복원 테스트
    single_test_result = test_restore_function()
    
    # 연속 복원 테스트
    multiple_test_result = test_multiple_restores()
    
    print("\n" + "=" * 60)
    print("📋 최종 테스트 결과")
    print(f"단일 복원 테스트: {'✅ 성공' if single_test_result else '❌ 실패'}")
    print(f"연속 복원 테스트: {'✅ 성공' if multiple_test_result else '❌ 실패'}")
    
    if single_test_result and multiple_test_result:
        print("🎉 모든 테스트가 성공했습니다! 파일 처리 오류가 완전히 해결되었습니다.")
    else:
        print("❌ 일부 테스트가 실패했습니다. 추가 디버깅이 필요합니다.")

if __name__ == "__main__":
    main()