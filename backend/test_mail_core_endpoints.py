#!/usr/bin/env python3
"""
mail_core_router.py 엔드포인트 테스트 스크립트
각 엔드포인트를 단계별로 테스트하고 결과를 기록합니다.
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MailCoreEndpointTester:
    """mail_core_router.py 엔드포인트 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.test_results = {}
        self.session = requests.Session()
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """테스트 결과 로깅"""
        self.test_results[test_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        status = "✅ 성공" if success else "❌ 실패"
        logger.info(f"{status} - {test_name}: {details.get('message', '')}")
        
    def authenticate(self, email: str = "admin@skyboot.com", password: str = "admin123") -> bool:
        """로그인하여 인증 토큰 획득"""
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                self.log_test_result("로그인", True, {
                    "message": "인증 토큰 획득 성공",
                    "token_type": token_data.get("token_type"),
                    "expires_in": token_data.get("expires_in")
                })
                return True
            else:
                self.log_test_result("로그인", False, {
                    "message": f"로그인 실패: {response.status_code}",
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_test_result("로그인", False, {
                "message": f"로그인 오류: {str(e)}"
            })
            return False
    
    def test_send_mail(self) -> bool:
        """메일 발송 엔드포인트 테스트"""
        try:
            # Form 데이터로 메일 발송 테스트
            mail_data = {
                "to_emails": "test@example.com",
                "subject": "테스트 메일",
                "content": "이것은 테스트 메일입니다.",
                "priority": "NORMAL"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/mail/send",
                data=mail_data
            )
            
            success = response.status_code in [200, 201]
            self.log_test_result("메일 발송", success, {
                "message": f"응답 코드: {response.status_code}",
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("메일 발송", False, {
                "message": f"메일 발송 오류: {str(e)}"
            })
            return False
    
    def test_inbox(self) -> bool:
        """받은 메일함 엔드포인트 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/mail/inbox")
            
            success = response.status_code == 200
            self.log_test_result("받은 메일함 조회", success, {
                "message": f"응답 코드: {response.status_code}",
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("받은 메일함 조회", False, {
                "message": f"받은 메일함 조회 오류: {str(e)}"
            })
            return False
    
    def test_sent(self) -> bool:
        """보낸 메일함 엔드포인트 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/mail/sent")
            
            success = response.status_code == 200
            self.log_test_result("보낸 메일함 조회", success, {
                "message": f"응답 코드: {response.status_code}",
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("보낸 메일함 조회", False, {
                "message": f"보낸 메일함 조회 오류: {str(e)}"
            })
            return False
    
    def test_drafts(self) -> bool:
        """임시보관함 엔드포인트 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/mail/drafts")
            
            success = response.status_code == 200
            self.log_test_result("임시보관함 조회", success, {
                "message": f"응답 코드: {response.status_code}",
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("임시보관함 조회", False, {
                "message": f"임시보관함 조회 오류: {str(e)}"
            })
            return False
    
    def test_trash(self) -> bool:
        """휴지통 엔드포인트 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/mail/trash")
            
            success = response.status_code == 200
            self.log_test_result("휴지통 조회", success, {
                "message": f"응답 코드: {response.status_code}",
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("휴지통 조회", False, {
                "message": f"휴지통 조회 오류: {str(e)}"
            })
            return False
    
    def test_mail_detail(self, mail_id: str, folder: str = "inbox") -> bool:
        """메일 상세 조회 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/api/mail/{folder}/{mail_id}")
            
            success = response.status_code == 200
            self.log_test_result(f"{folder} 메일 상세 조회", success, {
                "message": f"응답 코드: {response.status_code}",
                "mail_id": mail_id,
                "response": response.text[:500] if response.text else "No response body"
            })
            
            return success
            
        except Exception as e:
            self.log_test_result(f"{folder} 메일 상세 조회", False, {
                "message": f"메일 상세 조회 오류: {str(e)}",
                "mail_id": mail_id
            })
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("=" * 60)
        print("🧪 mail_core_router.py 엔드포인트 테스트 시작")
        print("=" * 60)
        
        # 1. 인증 테스트
        if not self.authenticate():
            print("❌ 인증 실패로 테스트 중단")
            return self.test_results
        
        # 2. 기본 엔드포인트 테스트
        test_methods = [
            ("메일 발송", self.test_send_mail),
            ("받은 메일함", self.test_inbox),
            ("보낸 메일함", self.test_sent),
            ("임시보관함", self.test_drafts),
            ("휴지통", self.test_trash)
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n🔍 {test_name} 테스트 중...")
            test_method()
        
        # 3. 결과 요약
        self.print_test_summary()
        
        return self.test_results
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {successful_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%")
        
        print("\n📋 상세 결과:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['details'].get('message', '')}")
        
        print("=" * 60)

def main():
    """메인 함수"""
    tester = MailCoreEndpointTester()
    results = tester.run_all_tests()
    
    # 결과를 JSON 파일로 저장
    with open("mail_core_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과가 'mail_core_test_results.json'에 저장되었습니다.")

if __name__ == "__main__":
    main()