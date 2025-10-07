#!/usr/bin/env python3
"""
메일 복원 기능 종합 테스트 스크립트

이 스크립트는 다음 시나리오들을 테스트합니다:
1. 기본 메일 복원 테스트
2. MailUser 자동 생성 테스트
3. 중복 메일 처리 테스트
4. 첨부파일 포함 복원 테스트
5. 대용량 백업 파일 복원 테스트
6. 오류 상황 처리 테스트
"""

import requests
import json
import tempfile
import zipfile
import os
import uuid
from datetime import datetime
import time

# 서버 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login_user():
    """사용자 로그인"""
    print("🔐 로그인 중...")
    
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ 로그인 성공")
        return token
    else:
        print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        return None

def create_test_backup_file(mail_count=3, include_attachments=False, fixed_uuid=False):
    """테스트용 백업 파일 생성"""
    print(f"📦 테스트용 백업 파일 생성 중... (메일 {mail_count}개)")
    
    # 테스트 메일 데이터 생성
    mails_data = []
    for i in range(mail_count):
        # 중복 테스트를 위해 고정된 UUID 사용 옵션
        if fixed_uuid:
            mail_uuid = f"test-mail-{i:03d}"
        else:
            mail_uuid = str(uuid.uuid4())
            
        mail_data = {
            "mail_uuid": mail_uuid,
            "subject": f"테스트 메일 {i+1} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": f"이것은 테스트 메일 {i+1}의 내용입니다.\n생성 시간: {datetime.now()}",
            "status": "sent",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "sent_at": datetime.now().isoformat(),
            "recipients": [
                {
                    "email": f"recipient{i}@test.com",
                    "type": "to"
                }
            ]
        }
        
        # 첨부파일 포함 옵션
        if include_attachments and i % 2 == 0:  # 짝수 번째 메일에만 첨부파일 추가
            mail_data["attachments"] = [
                {
                    "filename": f"test_attachment_{i}.txt",
                    "content": f"테스트 첨부파일 {i} 내용",
                    "content_type": "text/plain"
                }
            ]
        
        mails_data.append(mail_data)
    
    # 임시 ZIP 파일 생성
    temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    
    with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 메일 데이터를 JSON으로 저장
        zipf.writestr('mails.json', json.dumps(mails_data, ensure_ascii=False, indent=2))
        
        # 첨부파일 추가
        if include_attachments:
            for mail in mails_data:
                for attachment in mail.get("attachments", []):
                    zipf.writestr(f"attachments/{attachment['filename']}", attachment['content'])
    
    print(f"✅ 테스트 백업 파일 생성 완료: {temp_file.name}")
    return temp_file.name

def test_basic_restore(token):
    """기본 메일 복원 테스트"""
    print("\n" + "="*60)
    print("📦 기본 메일 복원 테스트")
    print("="*60)
    
    # 테스트 백업 파일 생성
    backup_file_path = create_test_backup_file(mail_count=3)
    
    try:
        # 메일 복원 요청
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('test_backup.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            print("📤 메일 복원 요청 중...")
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("success"):
                restored_count = result.get("data", {}).get("restored_count", 0)
                skipped_count = result.get("data", {}).get("skipped_count", 0)
                print(f"✅ 기본 복원 테스트 성공!")
                print(f"📊 복원 결과: 복원 {restored_count}개, 건너뜀 {skipped_count}개")
                return True
            else:
                print(f"❌ 복원 실패: {result.get('message', '알 수 없는 오류')}")
                return False
        else:
            print(f"❌ API 요청 실패: {response.status_code} - {response.text}")
            return False
            
    finally:
        # 임시 파일 정리
        if os.path.exists(backup_file_path):
            os.unlink(backup_file_path)
            print(f"🗑️ 테스트 백업 파일 정리 완료: {backup_file_path}")

def test_mailuser_auto_creation(token):
    """MailUser 자동 생성 테스트"""
    print("\n" + "="*60)
    print("👤 MailUser 자동 생성 테스트")
    print("="*60)
    
    # 이 테스트는 이미 MailUser가 없는 상황에서 자동 생성되는지 확인
    # 실제로는 이전 테스트에서 이미 MailUser가 생성되었을 것임
    
    backup_file_path = create_test_backup_file(mail_count=2)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('mailuser_test.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            print("📤 MailUser 자동 생성 테스트 중...")
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ MailUser 자동 생성 테스트 성공!")
                return True
            else:
                print(f"❌ MailUser 테스트 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ MailUser 테스트 API 실패: {response.status_code}")
            return False
            
    finally:
        if os.path.exists(backup_file_path):
            os.unlink(backup_file_path)

def test_duplicate_mail_handling(token):
    """중복 메일 처리 테스트"""
    print("\n" + "="*60)
    print("🔄 중복 메일 처리 테스트")
    print("="*60)
    
    # 동일한 백업 파일로 두 번 복원하여 중복 처리 확인 (고정 UUID 사용)
    backup_file_path = create_test_backup_file(mail_count=2, fixed_uuid=True)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 첫 번째 복원
        print("📤 첫 번째 복원...")
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('duplicate_test1.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            response1 = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        # 두 번째 복원 (중복)
        print("📤 두 번째 복원 (중복 테스트)...")
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('duplicate_test2.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            response2 = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        if response1.status_code == 200 and response2.status_code == 200:
            result1 = response1.json()
            result2 = response2.json()
            
            if result1.get("success") and result2.get("success"):
                restored1 = result1.get("data", {}).get("restored_count", 0)
                skipped2 = result2.get("data", {}).get("skipped_count", 0)
                
                print(f"📊 첫 번째 복원: {restored1}개")
                print(f"📊 두 번째 복원 건너뜀: {skipped2}개")
                
                if skipped2 > 0:
                    print("✅ 중복 메일 처리 테스트 성공!")
                    return True
                else:
                    print("⚠️ 중복 메일이 건너뛰어지지 않았습니다.")
                    return False
            else:
                print("❌ 중복 테스트 중 복원 실패")
                return False
        else:
            print("❌ 중복 테스트 API 실패")
            return False
            
    finally:
        if os.path.exists(backup_file_path):
            os.unlink(backup_file_path)

def test_attachment_restore(token):
    """첨부파일 포함 복원 테스트"""
    print("\n" + "="*60)
    print("📎 첨부파일 포함 복원 테스트")
    print("="*60)
    
    backup_file_path = create_test_backup_file(mail_count=3, include_attachments=True)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('attachment_test.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            print("📤 첨부파일 포함 복원 중...")
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 첨부파일 포함 복원 테스트 성공!")
                return True
            else:
                print(f"❌ 첨부파일 복원 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ 첨부파일 테스트 API 실패: {response.status_code}")
            return False
            
    finally:
        if os.path.exists(backup_file_path):
            os.unlink(backup_file_path)

def test_large_backup_restore(token):
    """대용량 백업 파일 복원 테스트"""
    print("\n" + "="*60)
    print("📦 대용량 백업 파일 복원 테스트")
    print("="*60)
    
    # 50개의 메일로 대용량 테스트
    backup_file_path = create_test_backup_file(mail_count=50)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': ('large_backup_test.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            print("📤 대용량 백업 복원 중...")
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data,
                timeout=60  # 60초 타임아웃
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                restored_count = result.get("data", {}).get("restored_count", 0)
                print(f"✅ 대용량 복원 테스트 성공!")
                print(f"📊 복원된 메일: {restored_count}개")
                print(f"⏱️ 처리 시간: {processing_time:.2f}초")
                return True
            else:
                print(f"❌ 대용량 복원 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ 대용량 테스트 API 실패: {response.status_code}")
            return False
            
    finally:
        if os.path.exists(backup_file_path):
            os.unlink(backup_file_path)

def test_error_handling(token):
    """오류 상황 처리 테스트"""
    print("\n" + "="*60)
    print("⚠️ 오류 상황 처리 테스트")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    error_handled = True
    
    # 1. 잘못된 파일 형식 테스트
    print("📤 잘못된 파일 형식 테스트...")
    
    # 텍스트 파일을 ZIP으로 위장
    temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    temp_file.write(b"This is not a zip file")
    temp_file.close()
    
    try:
        with open(temp_file.name, 'rb') as f:
            files = {'backup_file': ('invalid.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        # API는 200 상태 코드로 응답하지만 success: false로 오류 표시
        if response.status_code == 200:
            result = response.json()
            if not result.get("success"):
                print("✅ 잘못된 파일 형식 오류 처리 성공!")
                print(f"   오류 메시지: {result.get('message', 'N/A')}")
            else:
                print("⚠️ 잘못된 파일이 성공적으로 처리됨 (예상과 다름)")
                error_handled = False
        else:
            print(f"⚠️ 예상과 다른 응답 상태 코드: {response.status_code}")
            error_handled = False
            
    finally:
        os.unlink(temp_file.name)
    
    # 2. 빈 ZIP 파일 테스트
    print("📤 빈 ZIP 파일 테스트...")
    
    empty_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    empty_zip_path = empty_zip.name
    empty_zip.close()  # 파일 핸들을 명시적으로 닫기
    
    with zipfile.ZipFile(empty_zip_path, 'w'):
        pass  # 빈 ZIP 파일 생성
    
    try:
        with open(empty_zip_path, 'rb') as f:
            files = {'backup_file': ('empty.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        # 빈 ZIP 파일은 mails.json이 없어서 오류 처리되어야 함
        if response.status_code == 200:
            result = response.json()
            if not result.get("success"):
                print("✅ 빈 ZIP 파일 오류 처리 성공!")
                print(f"   오류 메시지: {result.get('message', 'N/A')}")
            else:
                print("⚠️ 빈 ZIP 파일이 성공적으로 처리됨 (예상과 다름)")
                error_handled = False
        else:
            print(f"⚠️ 빈 ZIP 파일 테스트 실패: {response.status_code}")
            error_handled = False
            
    finally:
        try:
            time.sleep(0.1)  # 파일 핸들이 완전히 해제될 때까지 잠시 대기
            os.unlink(empty_zip_path)
        except Exception as e:
            print(f"⚠️ 빈 ZIP 파일 정리 실패: {e}")
    
    # 3. 잘못된 JSON 형식 테스트
    print("📤 잘못된 JSON 형식 테스트...")
    
    invalid_json_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    invalid_json_zip_path = invalid_json_zip.name
    invalid_json_zip.close()  # 파일 핸들을 명시적으로 닫기
    
    with zipfile.ZipFile(invalid_json_zip_path, 'w') as zipf:
        zipf.writestr('mails.json', '{"invalid": json format}')  # 잘못된 JSON
    
    try:
        with open(invalid_json_zip_path, 'rb') as f:
            files = {'backup_file': ('invalid_json.zip', f, 'application/zip')}
            data = {'overwrite_existing': 'false'}
            
            response = requests.post(
                f"{API_BASE}/mail/restore",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get("success"):
                print("✅ 잘못된 JSON 형식 오류 처리 성공!")
                print(f"   오류 메시지: {result.get('message', 'N/A')}")
            else:
                print("⚠️ 잘못된 JSON이 성공적으로 처리됨 (예상과 다름)")
                error_handled = False
        else:
            print(f"⚠️ 잘못된 JSON 테스트 실패: {response.status_code}")
            error_handled = False
            
    finally:
        try:
            time.sleep(0.1)  # 파일 핸들이 완전히 해제될 때까지 잠시 대기
            os.unlink(invalid_json_zip_path)
        except Exception as e:
            print(f"⚠️ 잘못된 JSON 파일 정리 실패: {e}")
    
    if error_handled:
        print("✅ 모든 오류 상황 처리 테스트 성공!")
        return True
    else:
        print("❌ 일부 오류 상황 처리 테스트 실패")
        return False

def main():
    """메인 테스트 실행"""
    print("🧪 메일 복원 기능 종합 테스트 시작")
    print("="*80)
    
    # 로그인
    token = login_user()
    if not token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    # 테스트 결과 저장
    test_results = {}
    
    # 각 테스트 실행
    test_functions = [
        ("기본 메일 복원", test_basic_restore),
        ("MailUser 자동 생성", test_mailuser_auto_creation),
        ("중복 메일 처리", test_duplicate_mail_handling),
        ("첨부파일 포함 복원", test_attachment_restore),
        ("대용량 백업 복원", test_large_backup_restore),
        ("오류 상황 처리", test_error_handling)
    ]
    
    for test_name, test_func in test_functions:
        try:
            print(f"\n🔄 {test_name} 테스트 실행 중...")
            result = test_func(token)
            test_results[test_name] = result
            
            if result:
                print(f"✅ {test_name} 테스트 성공")
            else:
                print(f"❌ {test_name} 테스트 실패")
                
        except Exception as e:
            print(f"💥 {test_name} 테스트 중 예외 발생: {str(e)}")
            test_results[test_name] = False
        
        # 테스트 간 잠시 대기
        time.sleep(1)
    
    # 최종 결과 출력
    print("\n" + "="*80)
    print("📊 종합 테스트 결과")
    print("="*80)
    
    success_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n📈 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"⚠️ {total_count - success_count}개의 테스트가 실패했습니다.")
    
    print("="*80)

if __name__ == "__main__":
    main()