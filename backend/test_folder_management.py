#!/usr/bin/env python3
"""
폴더 관리 기능 테스트 스크립트
- 폴더 생성, 조회, 수정, 삭제
- 메일 이동 기능
- 에러 케이스 처리
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "simpletest@example.com"
TEST_PASSWORD = "TestPassword123!"

class FolderManagementTest:
    def __init__(self):
        self.access_token = None
        self.test_results = []
        self.created_folders = []
        self.created_mails = []
        
    def get_headers(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        if not self.access_token:
            raise ValueError("Access token이 없습니다. 먼저 로그인하세요.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def log_test_result(self, test_name: str, success: bool, message: str):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def authenticate(self) -> bool:
        """사용자 인증"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                self.log_test_result("사용자 인증", True, "로그인 성공")
                return True
            else:
                self.log_test_result("사용자 인증", False, f"로그인 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("사용자 인증", False, f"인증 중 예외: {str(e)}")
            return False
    
    def create_folder(self, name: str, description: str = None) -> Optional[str]:
        """폴더 생성"""
        try:
            folder_data = {
                "name": name,
                "description": description or f"{name} 설명"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/mail/folders",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                # folder_uuid 우선, 없으면 id 사용
                folder_id = result.get("folder_uuid") or result.get("id")
                if folder_id:
                    self.created_folders.append(folder_id)
                    id_type = "UUID" if result.get("folder_uuid") else "ID"
                    self.log_test_result("폴더 생성", True, f"폴더 '{name}' 생성 성공 ({id_type}: {folder_id})")
                    return folder_id
                else:
                    self.log_test_result("폴더 생성", False, f"폴더 '{name}' 생성 응답에 ID가 없음")
                    return None
            else:
                self.log_test_result("폴더 생성", False, f"폴더 '{name}' 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_test_result("폴더 생성", False, f"폴더 '{name}' 생성 중 예외: {str(e)}")
            return None
    
    def list_folders(self) -> bool:
        """폴더 목록 조회"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/mail/folders",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                folders = response.json()
                folder_count = len(folders) if isinstance(folders, list) else 0
                self.log_test_result("폴더 목록 조회", True, f"폴더 {folder_count}개 조회 성공")
                return True
            else:
                self.log_test_result("폴더 목록 조회", False, f"폴더 목록 조회 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("폴더 목록 조회", False, f"폴더 목록 조회 중 예외: {str(e)}")
            return False
    
    def update_folder(self, folder_id: str, new_name: str) -> bool:
        """폴더 수정"""
        try:
            update_data = {
                "name": new_name,
                "description": f"{new_name} 수정된 설명"
            }
            
            response = requests.put(
                f"{BASE_URL}/api/v1/mail/folders/{folder_id}",
                json=update_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_test_result("폴더 수정", True, f"폴더 {folder_id} 수정 성공")
                return True
            else:
                self.log_test_result("폴더 수정", False, f"폴더 {folder_id} 수정 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result("폴더 수정", False, f"폴더 {folder_id} 수정 중 예외: {str(e)}")
            return False
    
    def create_test_mail(self, subject: str, content: str) -> Optional[str]:
        """테스트용 메일 생성"""
        try:
            # 폼 데이터로 전송
            mail_data = {
                "to_emails": TEST_EMAIL,
                "subject": subject,
                "content": content
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/mail/send",
                data=mail_data,  # JSON 대신 data 사용
                headers={"Authorization": f"Bearer {self.access_token}"}  # Content-Type 제거
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                # mail_uuid 우선, 없으면 mail_id나 id 사용
                mail_id = result.get("mail_uuid") or result.get("mail_id") or result.get("id")
                if mail_id:
                    self.created_mails.append(mail_id)
                    id_type = "UUID" if result.get("mail_uuid") else "ID"
                    self.log_test_result("테스트 메일 생성", True, f"메일 '{subject}' 생성 성공 ({id_type}: {mail_id})")
                    return mail_id
                else:
                    self.log_test_result("테스트 메일 생성", False, f"메일 '{subject}' 생성 응답에 ID가 없음")
                    return None
            else:
                self.log_test_result("테스트 메일 생성", False, f"메일 '{subject}' 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_test_result("테스트 메일 생성", False, f"메일 '{subject}' 생성 중 예외: {str(e)}")
            return None
    
    def move_mail_to_folder(self, mail_id: str, folder_id: str) -> bool:
        """메일을 폴더로 이동"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/mail/folders/{folder_id}/mails/{mail_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_test_result("메일 이동", True, f"메일 {mail_id}를 폴더 {folder_id}로 이동 성공")
                return True
            else:
                self.log_test_result("메일 이동", False, f"메일 이동 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result("메일 이동", False, f"메일 이동 중 예외: {str(e)}")
            return False
    
    def delete_folder(self, folder_id: str) -> bool:
        """폴더 삭제"""
        try:
            response = requests.delete(
                f"{BASE_URL}/api/v1/mail/folders/{folder_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_test_result("폴더 삭제", True, f"폴더 {folder_id} 삭제 성공")
                return True
            else:
                self.log_test_result("폴더 삭제", False, f"폴더 {folder_id} 삭제 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result("폴더 삭제", False, f"폴더 {folder_id} 삭제 중 예외: {str(e)}")
            return False
    
    def test_error_cases(self) -> bool:
        """에러 케이스 테스트"""
        success_count = 0
        
        # 존재하지 않는 폴더 수정 시도
        try:
            response = requests.put(
                f"{BASE_URL}/api/v1/mail/folders/nonexistent-folder-id",
                json={"name": "Should Fail"},
                headers=self.get_headers()
            )
            
            if response.status_code == 404:
                self.log_test_result("에러 케이스 - 존재하지 않는 폴더 수정", True, "404 에러 정상 반환")
                success_count += 1
            else:
                self.log_test_result("에러 케이스 - 존재하지 않는 폴더 수정", False, f"예상과 다른 응답: {response.status_code}")
        except Exception as e:
            self.log_test_result("에러 케이스 - 존재하지 않는 폴더 수정", False, f"예외 발생: {str(e)}")
        
        # 존재하지 않는 폴더 삭제 시도
        try:
            response = requests.delete(
                f"{BASE_URL}/api/v1/mail/folders/nonexistent-folder-id",
                headers=self.get_headers()
            )
            
            if response.status_code == 404:
                self.log_test_result("에러 케이스 - 존재하지 않는 폴더 삭제", True, "404 에러 정상 반환")
                success_count += 1
            else:
                self.log_test_result("에러 케이스 - 존재하지 않는 폴더 삭제", False, f"예상과 다른 응답: {response.status_code}")
        except Exception as e:
            self.log_test_result("에러 케이스 - 존재하지 않는 폴더 삭제", False, f"예외 발생: {str(e)}")
        
        return success_count == 2
    
    def cleanup(self):
        """테스트 후 정리"""
        print("\n🧹 테스트 정리 중...")
        
        # 생성된 폴더 삭제
        for folder_id in self.created_folders:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/v1/mail/folders/{folder_id}",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    print(f"✅ 폴더 {folder_id} 정리 완료")
                else:
                    print(f"⚠️ 폴더 {folder_id} 정리 실패: {response.status_code}")
            except Exception as e:
                print(f"❌ 폴더 {folder_id} 정리 중 예외: {str(e)}")
    
    def run_tests(self):
        """전체 테스트 실행"""
        print("🚀 폴더 관리 기능 테스트 시작")
        print("=" * 50)
        
        # 1. 사용자 인증
        if not self.authenticate():
            print("❌ 인증 실패로 테스트를 중단합니다.")
            return
        
        # 2. 폴더 생성 테스트
        timestamp = str(int(time.time()))
        folder1_id = self.create_folder(f"Test Folder 1 {timestamp}")
        folder2_id = self.create_folder(f"Test Folder 2 {timestamp}")
        
        if not folder1_id or not folder2_id:
            print("❌ 폴더 생성 실패로 테스트를 중단합니다.")
            return
        
        # 3. 폴더 목록 조회
        self.list_folders()
        
        # 4. 폴더 수정
        self.update_folder(folder1_id, f"Updated Folder 1 {timestamp}")
        
        # 5. 테스트 메일 생성
        mail_id = self.create_test_mail("Test Mail for Folder", "This is a test mail for folder management")
        
        # 6. 메일 이동 (메일이 생성된 경우에만)
        if mail_id:
            self.move_mail_to_folder(mail_id, folder1_id)
        
        # 7. 폴더 삭제
        self.delete_folder(folder2_id)
        
        # 8. 에러 케이스 테스트
        self.test_error_cases()
        
        # 9. 정리
        self.cleanup()
        
        # 10. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

if __name__ == "__main__":
    test = FolderManagementTest()
    test.run_tests()