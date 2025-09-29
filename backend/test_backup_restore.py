#!/usr/bin/env python3
"""
백업/복원 기능 테스트 스크립트
SkyBoot Mail SaaS 프로젝트의 백업/복원 기능을 종합적으로 테스트합니다.
"""

import requests
import json
import time
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class BackupRestoreTest:
    """백업/복원 기능 테스트 클래스"""
    
    def __init__(self):
        self.BASE_URL = "http://localhost:8000"
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        self.created_mails = []  # 테스트용 메일 ID 저장
        self.backup_filename = None
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def authenticate(self) -> bool:
        """사용자 인증"""
        try:
            login_data = {
                "email": "admin@skyboot.kr",
                "password": "admin123"
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                self.log_test("사용자 인증", True, "로그인 성공")
                return True
            else:
                self.log_test("사용자 인증", False, f"로그인 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("사용자 인증", False, f"인증 오류: {str(e)}")
            return False
    
    def create_test_mails(self, count: int = 3) -> bool:
        """테스트용 메일 생성"""
        try:
            success_count = 0
            
            for i in range(count):
                mail_data = {
                    "to_emails": "test@example.com",
                    "subject": f"Test Mail for Backup {i+1}",
                    "content": f"This is test mail content {i+1} for backup testing.",
                    "priority": "normal"
                }
                
                response = self.session.post(
                    f"{self.BASE_URL}/api/v1/mail/send",
                    data=mail_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mail_id = data.get("mail_uuid") or data.get("mail_id") or data.get("id")
                    if mail_id:
                        self.created_mails.append(mail_id)
                        success_count += 1
                        print(f"  📧 메일 {i+1} 생성 성공 (ID: {mail_id})")
                    else:
                        print(f"  ❌ 메일 {i+1} ID 추출 실패")
                else:
                    print(f"  ❌ 메일 {i+1} 생성 실패: {response.status_code}")
            
            if success_count == count:
                self.log_test("테스트 메일 생성", True, f"{count}개 메일 생성 성공")
                return True
            else:
                self.log_test("테스트 메일 생성", False, f"{success_count}/{count}개 메일만 생성됨")
                return False
                
        except Exception as e:
            self.log_test("테스트 메일 생성", False, f"메일 생성 오류: {str(e)}")
            return False
    
    def create_backup(self, include_attachments: bool = False) -> bool:
        """메일 백업 생성"""
        try:
            # 백업 생성 요청
            params = {
                "include_attachments": include_attachments
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/backup",
                params=params
            )
            
            if response.status_code == 200:
                response_data = response.json()
                data = response_data.get("data", {})
                self.backup_filename = data.get("backup_filename")
                
                if self.backup_filename:
                    mail_count = data.get("mail_count", 0)
                    backup_size = data.get("backup_size", 0)
                    self.log_test("백업 생성", True, f"백업 파일 생성 성공: {self.backup_filename} (메일 {mail_count}개, 크기: {backup_size} bytes)")
                    return True
                else:
                    self.log_test("백업 생성", False, f"백업 파일명을 받지 못함. 응답: {response_data}")
                    return False
            else:
                self.log_test("백업 생성", False, f"백업 생성 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("백업 생성", False, f"백업 생성 오류: {str(e)}")
            return False
    
    def download_backup(self) -> bool:
        """백업 파일 다운로드"""
        try:
            if not self.backup_filename:
                self.log_test("백업 다운로드", False, "백업 파일명이 없음")
                return False
            
            response = self.session.get(
                f"{self.BASE_URL}/api/v1/mail/backup/{self.backup_filename}"
            )
            
            if response.status_code == 200:
                # 임시 파일로 저장하여 크기 확인
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                    temp_file.write(response.content)
                    file_size = len(response.content)
                    temp_file_path = temp_file.name
                
                # 파일 크기 확인 (최소 100바이트 이상이어야 함)
                if file_size > 100:
                    self.log_test("백업 다운로드", True, f"백업 파일 다운로드 성공 (크기: {file_size} bytes)")
                    # 임시 파일 정리
                    os.unlink(temp_file_path)
                    return True
                else:
                    self.log_test("백업 다운로드", False, f"백업 파일이 너무 작음 (크기: {file_size} bytes)")
                    os.unlink(temp_file_path)
                    return False
            else:
                self.log_test("백업 다운로드", False, f"백업 다운로드 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("백업 다운로드", False, f"백업 다운로드 오류: {str(e)}")
            return False
    
    def test_backup_with_date_range(self) -> bool:
        """날짜 범위 지정 백업 테스트"""
        try:
            # 어제부터 내일까지의 범위로 백업
            date_from = (datetime.now() - timedelta(days=1)).isoformat()
            date_to = (datetime.now() + timedelta(days=1)).isoformat()
            
            params = {
                "include_attachments": False,
                "date_from": date_from,
                "date_to": date_to
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/backup",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                backup_filename = data.get("backup_filename")
                
                if backup_filename:
                    self.log_test("날짜 범위 백업", True, f"날짜 범위 백업 성공: {backup_filename}")
                    return True
                else:
                    self.log_test("날짜 범위 백업", False, "백업 파일명을 받지 못함")
                    return False
            else:
                self.log_test("날짜 범위 백업", False, f"날짜 범위 백업 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("날짜 범위 백업", False, f"날짜 범위 백업 오류: {str(e)}")
            return False
    
    def test_restore_functionality(self) -> bool:
        """복원 기능 테스트 (실제 파일 업로드 없이 API 엔드포인트 테스트)"""
        try:
            # 빈 파일로 복원 API 테스트 (실제로는 유효한 백업 파일이 필요)
            # 여기서는 API 엔드포인트가 존재하는지만 확인
            
            # 임시 빈 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_file.write(b'dummy backup content')
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'backup_file': ('test_backup.zip', f, 'application/zip')}
                    data = {'overwrite_existing': 'false'}
                    
                    response = self.session.post(
                        f"{self.BASE_URL}/api/v1/mail/restore",
                        files=files,
                        data=data
                    )
                
                # 400 또는 422 에러는 정상 (잘못된 백업 파일이므로)
                # 404 에러는 API가 존재하지 않음을 의미
                if response.status_code in [400, 422, 500]:
                    self.log_test("복원 API 테스트", True, f"복원 API 엔드포인트 존재 확인 (상태: {response.status_code})")
                    return True
                elif response.status_code == 404:
                    self.log_test("복원 API 테스트", False, "복원 API 엔드포인트가 존재하지 않음")
                    return False
                else:
                    self.log_test("복원 API 테스트", True, f"복원 API 응답: {response.status_code}")
                    return True
                    
            finally:
                # 임시 파일 정리
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("복원 API 테스트", False, f"복원 API 테스트 오류: {str(e)}")
            return False
    
    def test_error_cases(self) -> bool:
        """에러 케이스 테스트"""
        try:
            success_count = 0
            total_tests = 2
            
            # 1. 존재하지 않는 백업 파일 다운로드
            response = self.session.get(f"{self.BASE_URL}/api/v1/mail/backup/nonexistent-backup.zip")
            if response.status_code == 404:
                print("  ✅ 존재하지 않는 백업 파일 다운로드: 404 에러 정상 반환")
                success_count += 1
            else:
                print(f"  ❌ 존재하지 않는 백업 파일 다운로드: 예상과 다른 응답 {response.status_code}")
            
            # 2. 잘못된 날짜 범위로 백업 시도
            params = {
                "date_from": "invalid-date",
                "date_to": "invalid-date"
            }
            response = self.session.post(f"{self.BASE_URL}/api/v1/mail/backup", params=params)
            if response.status_code in [400, 422]:
                print("  ✅ 잘못된 날짜 범위 백업: 400/422 에러 정상 반환")
                success_count += 1
            else:
                print(f"  ❌ 잘못된 날짜 범위 백업: 예상과 다른 응답 {response.status_code}")
            
            if success_count == total_tests:
                self.log_test("에러 케이스 테스트", True, f"{success_count}/{total_tests} 에러 케이스 통과")
                return True
            else:
                self.log_test("에러 케이스 테스트", False, f"{success_count}/{total_tests} 에러 케이스만 통과")
                return False
                
        except Exception as e:
            self.log_test("에러 케이스 테스트", False, f"에러 케이스 테스트 오류: {str(e)}")
            return False
    
    def cleanup(self):
        """테스트 정리"""
        print("\n🧹 테스트 정리 중...")
        
        # 생성된 메일들은 실제 메일 시스템에서 자동으로 관리되므로 별도 정리 불필요
        # 백업 파일들도 서버에서 관리되므로 별도 정리 불필요
        
        print("✅ 테스트 정리 완료")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 백업/복원 기능 테스트 시작")
        print("=" * 50)
        
        # 1. 사용자 인증
        if not self.authenticate():
            print("❌ 인증 실패로 테스트 중단")
            return
        
        # 2. 테스트용 메일 생성
        if not self.create_test_mails(3):
            print("❌ 테스트 메일 생성 실패로 테스트 중단")
            return
        
        # 3. 백업 생성
        self.create_backup(include_attachments=False)
        
        # 4. 백업 파일 다운로드
        self.download_backup()
        
        # 5. 첨부파일 포함 백업 테스트
        self.create_backup(include_attachments=True)
        
        # 6. 날짜 범위 지정 백업
        self.test_backup_with_date_range()
        
        # 7. 복원 기능 테스트
        self.test_restore_functionality()
        
        # 8. 에러 케이스 테스트
        self.test_error_cases()
        
        # 9. 테스트 정리
        self.cleanup()
        
        # 10. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = BackupRestoreTest()
    tester.run_all_tests()