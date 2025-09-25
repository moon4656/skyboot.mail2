#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mail Advanced Router 엔드포인트 테스트 스크립트

이 스크립트는 mail_advanced_router.py의 모든 엔드포인트를 테스트합니다:
- 폴더 관리 (생성, 조회, 수정, 삭제, 메일 이동)
- 백업 및 복원 (백업 생성, 다운로드, 복원)
- 메일 분석 (사용 통계)
"""

import requests
import json
import time
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

# 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}"

# 테스트 결과 저장용 딕셔너리
test_results = {}

# 전역 변수
access_token = None
test_folder_id = None
test_mail_id = None
backup_filename = None

def print_separator(title: str):
    """구분선과 제목을 출력합니다."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_test_result(test_name: str, success: bool, message: str = "", data: Any = None):
    """테스트 결과를 출력하고 저장합니다."""
    status = "✅ 성공" if success else "❌ 실패"
    print(f"{status} {test_name}")
    if message:
        print(f"   📝 {message}")
    if data and isinstance(data, dict) and data.get('data'):
        print(f"   📊 응답 데이터: {json.dumps(data['data'], ensure_ascii=False, indent=2)[:200]}...")
    
    test_results[test_name] = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

def login_and_get_token() -> bool:
    """로그인하여 인증 토큰을 획득합니다."""
    global access_token
    
    print_separator("🔐 사용자 인증")
    
    # 로그인 요청
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print_test_result("로그인 및 토큰 획득", True, f"토큰 획득 성공")
                return True
            else:
                print_test_result("로그인 및 토큰 획득", False, "응답에서 토큰을 찾을 수 없음")
                return False
        else:
            print_test_result("로그인 및 토큰 획득", False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("로그인 및 토큰 획득", False, f"요청 오류: {str(e)}")
        return False

def get_auth_headers() -> Dict[str, str]:
    """인증 헤더를 반환합니다."""
    if not access_token:
        raise Exception("인증 토큰이 없습니다. 먼저 로그인하세요.")
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

def get_test_mail_id() -> Optional[str]:
    """테스트용 메일 ID를 획득합니다."""
    global test_mail_id
    
    try:
        # 받은 메일함에서 메일 조회
        response = requests.get(
            f"{API_BASE}/mail/inbox?limit=1",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('mails') and len(data['mails']) > 0:
                test_mail_id = data['mails'][0].get('mail_uuid') or data['mails'][0].get('id')
                print(f"   📧 테스트용 메일 ID 획득: {test_mail_id}")
                return test_mail_id
        
        # 보낸 메일함에서 메일 조회
        response = requests.get(
            f"{API_BASE}/mail/sent?limit=1",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('mails') and len(data['mails']) > 0:
                test_mail_id = data['mails'][0].get('mail_uuid') or data['mails'][0].get('id')
                print(f"   📧 테스트용 메일 ID 획득: {test_mail_id}")
                return test_mail_id
        
        print("   ⚠️ 테스트용 메일을 찾을 수 없습니다.")
        return None
        
    except Exception as e:
        print(f"   ❌ 메일 ID 획득 오류: {str(e)}")
        return None

# =============================================================================
# 폴더 관리 엔드포인트 테스트
# =============================================================================

def test_get_folders():
    """폴더 목록 조회 테스트"""
    try:
        response = requests.get(
            f"{API_BASE}/mail/folders",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("폴더 목록 조회", True, "폴더 목록 조회 성공", data)
        else:
            print_test_result("폴더 목록 조회", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("폴더 목록 조회", False, f"요청 오류: {str(e)}")

def test_create_folder():
    """폴더 생성 테스트"""
    global test_folder_id
    
    folder_data = {
        "name": f"테스트폴더_{int(time.time())}",
        "description": "자동 테스트로 생성된 폴더입니다."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/mail/folders",
            headers=get_auth_headers(),
            json=folder_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('id'):
                test_folder_id = data['id']
                print_test_result("폴더 생성", True, f"폴더 생성 성공 (ID: {test_folder_id})", data)
            else:
                print_test_result("폴더 생성", False, "응답에서 폴더 ID를 찾을 수 없음")
        else:
            print_test_result("폴더 생성", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("폴더 생성", False, f"요청 오류: {str(e)}")

def test_update_folder():
    """폴더 수정 테스트"""
    if not test_folder_id:
        print_test_result("폴더 수정", False, "테스트용 폴더 ID가 없습니다.")
        return
    
    update_data = {
        "name": f"수정된폴더_{int(time.time())}",
        "description": "수정된 폴더 설명입니다."
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/mail/folders/{test_folder_id}",
            headers=get_auth_headers(),
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("폴더 수정", True, "폴더 수정 성공", data)
        else:
            print_test_result("폴더 수정", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("폴더 수정", False, f"요청 오류: {str(e)}")

def test_move_mail_to_folder():
    """메일을 폴더로 이동 테스트"""
    if not test_folder_id:
        print_test_result("메일 폴더 이동", False, "테스트용 폴더 ID가 없습니다.")
        return
    
    if not test_mail_id:
        print_test_result("메일 폴더 이동", False, "테스트용 메일 ID가 없습니다.")
        return
    
    try:
        response = requests.post(
            f"{API_BASE}/mail/folders/{test_folder_id}/mails/{test_mail_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("메일 폴더 이동", True, "메일 폴더 이동 성공", data)
        else:
            print_test_result("메일 폴더 이동", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("메일 폴더 이동", False, f"요청 오류: {str(e)}")

def test_delete_folder():
    """폴더 삭제 테스트"""
    if not test_folder_id:
        print_test_result("폴더 삭제", False, "테스트용 폴더 ID가 없습니다.")
        return
    
    try:
        response = requests.delete(
            f"{API_BASE}/mail/folders/{test_folder_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("폴더 삭제", True, "폴더 삭제 성공", data)
        else:
            print_test_result("폴더 삭제", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("폴더 삭제", False, f"요청 오류: {str(e)}")

# =============================================================================
# 백업 및 복원 엔드포인트 테스트
# =============================================================================

def test_backup_mails():
    """메일 백업 테스트"""
    global backup_filename
    
    try:
        response = requests.post(
            f"{API_BASE}/mail/backup",
            headers=get_auth_headers(),
            params={"include_attachments": False}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('backup_filename'):
                backup_filename = data['data']['backup_filename']
                print_test_result("메일 백업", True, f"백업 생성 성공 (파일: {backup_filename})", data)
            else:
                print_test_result("메일 백업", False, "응답에서 백업 파일명을 찾을 수 없음")
        else:
            print_test_result("메일 백업", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("메일 백업", False, f"요청 오류: {str(e)}")

def test_download_backup():
    """백업 파일 다운로드 테스트"""
    if not backup_filename:
        print_test_result("백업 파일 다운로드", False, "백업 파일명이 없습니다.")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/mail/backup/{backup_filename}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            # 파일 크기 확인
            content_length = len(response.content)
            print_test_result("백업 파일 다운로드", True, f"백업 파일 다운로드 성공 (크기: {content_length} bytes)")
        else:
            print_test_result("백업 파일 다운로드", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print_test_result("백업 파일 다운로드", False, f"요청 오류: {str(e)}")

def test_restore_mails():
    """메일 복원 테스트"""
    if not backup_filename:
        print_test_result("메일 복원", False, "백업 파일명이 없습니다.")
        return
    
    try:
        # 임시 백업 파일 생성 (실제 백업 파일 대신 더미 파일 사용)
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(b'PK\x03\x04')  # ZIP 파일 시그니처
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'backup_file': ('test_backup.zip', f, 'application/zip')}
                data = {'overwrite_existing': 'false'}
                
                # Content-Type을 multipart/form-data로 설정하기 위해 headers에서 제거
                headers = {"Authorization": f"Bearer {access_token}"}
                
                response = requests.post(
                    f"{API_BASE}/mail/restore",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_test_result("메일 복원", True, "메일 복원 테스트 성공", data)
                else:
                    print_test_result("메일 복원", False, f"HTTP {response.status_code}: {response.text}")
        
        finally:
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
    except Exception as e:
        print_test_result("메일 복원", False, f"요청 오류: {str(e)}")

# =============================================================================
# 분석 엔드포인트 테스트
# =============================================================================

def test_mail_analytics():
    """메일 분석 테스트"""
    periods = ["week", "month", "year"]
    
    for period in periods:
        try:
            response = requests.get(
                f"{API_BASE}/mail/analytics?period={period}",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print_test_result(f"메일 분석 ({period})", True, f"{period} 기간 분석 성공", data)
            else:
                print_test_result(f"메일 분석 ({period})", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print_test_result(f"메일 분석 ({period})", False, f"요청 오류: {str(e)}")

# =============================================================================
# 메인 테스트 실행 함수
# =============================================================================

def run_all_tests():
    """모든 테스트를 실행합니다."""
    print_separator("🚀 Mail Advanced Router 엔드포인트 테스트 시작")
    
    # 1. 인증
    if not login_and_get_token():
        print("\n❌ 인증 실패로 테스트를 중단합니다.")
        return
    
    # 테스트용 메일 ID 획득
    get_test_mail_id()
    
    # 2. 폴더 관리 테스트
    print_separator("📁 폴더 관리 엔드포인트 테스트")
    test_get_folders()
    test_create_folder()
    test_update_folder()
    test_move_mail_to_folder()
    test_delete_folder()
    
    # 3. 백업 및 복원 테스트
    print_separator("💾 백업 및 복원 엔드포인트 테스트")
    test_backup_mails()
    test_download_backup()
    test_restore_mails()
    
    # 4. 분석 테스트
    print_separator("📊 메일 분석 엔드포인트 테스트")
    test_mail_analytics()
    
    # 5. 테스트 결과 요약
    print_separator("📋 테스트 결과 요약")
    
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results.values() if result['success'])
    failed_tests = total_tests - successful_tests
    
    print(f"📊 총 테스트 수: {total_tests}")
    print(f"✅ 성공: {successful_tests}")
    print(f"❌ 실패: {failed_tests}")
    print(f"📈 성공률: {(successful_tests/total_tests*100):.1f}%")
    
    # 실패한 테스트 목록
    if failed_tests > 0:
        print("\n❌ 실패한 테스트:")
        for test_name, result in test_results.items():
            if not result['success']:
                print(f"   • {test_name}: {result['message']}")
    
    # 테스트 결과를 JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"mail_advanced_test_results_{timestamp}.json"
    
    with open(result_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(successful_tests/total_tests*100):.1f}%",
                "timestamp": datetime.now().isoformat()
            },
            "test_results": test_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과가 {result_filename}에 저장되었습니다.")

if __name__ == "__main__":
    run_all_tests()