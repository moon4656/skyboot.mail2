#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mail Router API 테스트 스크립트

이 스크립트는 mail_router.py의 모든 엔드포인트를 체계적으로 테스트합니다.
각 테스트는 인증이 필요하며, 성공/실패 결과를 상세히 기록합니다.
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import time

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}"
MAIL_API = f"{API_BASE}/mail"

# 테스트 사용자 정보
TEST_USER = {
    "email": "test@skyboot.com",
    "password": "test123456"
}

TEST_USER_2 = {
    "email": "test2@skyboot.com", 
    "password": "test123456"
}

class MailAPITester:
    """메일 API 테스트 클래스"""
    
    def __init__(self):
        self.access_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """테스트 결과를 기록합니다"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        self.total_tests += 1
        
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}: 성공")
            if details:
                print(f"   📝 {details}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: 실패")
            print(f"   📝 {details}")
            
    def register_test_user(self) -> bool:
        """테스트 사용자를 등록합니다"""
        try:
            register_data = {
                "email": TEST_USER["email"],
                "username": "testuser",
                "password": TEST_USER["password"]
            }
            
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=register_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                self.log_result("사용자 등록", True, "테스트 사용자 등록 성공")
                return True
            elif response.status_code == 400 and ("already registered" in response.text or "already taken" in response.text):
                self.log_result("사용자 등록", True, "사용자가 이미 존재함 (정상)")
                return True
            else:
                self.log_result("사용자 등록", False, f"등록 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("사용자 등록", False, f"등록 중 오류 발생: {str(e)}")
            return False
    
    def authenticate(self) -> bool:
        """사용자 인증을 수행합니다"""
        try:
            # 로그인 시도
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.log_result("사용자 인증", True, f"토큰 획득 성공")
                return True
            else:
                self.log_result("사용자 인증", False, f"로그인 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("사용자 인증", False, f"인증 중 오류 발생: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """인증 헤더를 반환합니다"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_mail_send(self) -> bool:
        """메일 발송 API 테스트"""
        try:
            mail_data = {
                "recipients": [TEST_USER_2["email"]],
                "subject": "테스트 메일",
                "content": "이것은 API 테스트용 메일입니다.",
                "content_type": "text/plain"
            }
            
            response = requests.post(
                f"{MAIL_API}/send",
                json=mail_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "POST /send - 메일 발송", 
                    True, 
                    f"메일 발송 성공, 메일 ID: {result.get('data', {}).get('mail_id', 'N/A')}",
                    result
                )
                return True
            else:
                self.log_result(
                    "POST /send - 메일 발송", 
                    False, 
                    f"응답 코드: {response.status_code}, 내용: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("POST /send - 메일 발송", False, f"오류 발생: {str(e)}")
            return False
    
    def test_inbox_list(self) -> bool:
        """받은 메일함 조회 API 테스트"""
        try:
            response = requests.get(
                f"{MAIL_API}/inbox?page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                mail_count = len(result.get('data', {}).get('mails', []))
                self.log_result(
                    "GET /inbox - 받은 메일함 조회", 
                    True, 
                    f"메일 {mail_count}개 조회 성공",
                    result
                )
                return True
            else:
                self.log_result(
                    "GET /inbox - 받은 메일함 조회", 
                    False, 
                    f"응답 코드: {response.status_code}, 내용: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /inbox - 받은 메일함 조회", False, f"오류 발생: {str(e)}")
            return False
    
    def test_sent_list(self) -> bool:
        """보낸 메일함 조회 API 테스트"""
        try:
            response = requests.get(
                f"{MAIL_API}/sent?page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                mail_count = len(result.get('data', {}).get('mails', []))
                self.log_result(
                    "GET /sent - 보낸 메일함 조회", 
                    True, 
                    f"메일 {mail_count}개 조회 성공",
                    result
                )
                return True
            else:
                self.log_result(
                    "GET /sent - 보낸 메일함 조회", 
                    False, 
                    f"응답 코드: {response.status_code}, 내용: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /sent - 보낸 메일함 조회", False, f"오류 발생: {str(e)}")
            return False
    
    def test_drafts_list(self) -> bool:
        """임시보관함 조회 API 테스트"""
        try:
            response = requests.get(
                f"{MAIL_API}/drafts?page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                mail_count = len(result.get('data', {}).get('mails', []))
                self.log_result(
                    "GET /drafts - 임시보관함 조회", 
                    True, 
                    f"메일 {mail_count}개 조회 성공",
                    result
                )
                return True
            else:
                self.log_result(
                    "GET /drafts - 임시보관함 조회", 
                    False, 
                    f"응답 코드: {response.status_code}, 내용: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /drafts - 임시보관함 조회", False, f"오류 발생: {str(e)}")
            return False
    
    def test_trash_list(self) -> bool:
        """휴지통 조회 API 테스트"""
        try:
            response = requests.get(
                f"{MAIL_API}/trash?page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                mail_count = len(result.get('data', {}).get('mails', []))
                self.log_result(
                    "GET /trash - 휴지통 조회", 
                    True, 
                    f"메일 {mail_count}개 조회 성공",
                    result
                )
                return True
            else:
                self.log_result(
                    "GET /trash - 휴지통 조회", 
                    False, 
                    f"응답 코드: {response.status_code}, 내용: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /trash - 휴지통 조회", False, f"오류 발생: {str(e)}")
            return False
    
    def run_tests(self):
        """모든 테스트를 실행합니다"""
        print("\n🚀 Mail Router API 테스트 시작")
        print("=" * 50)
        
        # 테스트 사용자 등록
        if not self.register_test_user():
            print("❌ 사용자 등록 실패로 테스트를 중단합니다.")
            return
        
        # 사용자 인증
        if not self.authenticate():
            print("❌ 인증 실패로 테스트를 중단합니다.")
            return
        
        print("\n📧 기본 메일 기능 테스트")
        print("-" * 30)
        
        # 기본 API 테스트
        self.test_mail_send()
        time.sleep(1)  # API 호출 간격
        
        self.test_inbox_list()
        time.sleep(1)
        
        self.test_sent_list()
        time.sleep(1)
        
        self.test_drafts_list()
        time.sleep(1)
        
        self.test_trash_list()
        
    def print_summary(self):
        """테스트 결과 요약을 출력합니다"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        print(f"총 테스트 수: {self.total_tests}")
        print(f"성공: {self.passed_tests}")
        print(f"실패: {self.failed_tests}")
        print(f"성공률: {(self.passed_tests/self.total_tests*100):.1f}%" if self.total_tests > 0 else "성공률: 0%")
        
        if self.failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
    
    def save_results(self, filename: str = "test_results.json"):
        """테스트 결과를 파일로 저장합니다"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": {
                        "total_tests": self.total_tests,
                        "passed_tests": self.passed_tests,
                        "failed_tests": self.failed_tests,
                        "success_rate": (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0
                    },
                    "results": self.test_results
                }, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"\n❌ 결과 저장 실패: {str(e)}")


def main():
    """메인 함수"""
    print("Mail Router API 테스트 도구")
    print("개발자: SkyBoot Mail Team")
    print(f"테스트 대상: {MAIL_API}")
    print("\n")
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 서버 응답 이상: {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print(f"   URL: {BASE_URL}")
        return
    
    # 테스트 실행
    tester = MailAPITester()
    tester.run_tests()
    
    # 결과 출력 및 저장
    tester.print_summary()
    tester.save_results()


if __name__ == "__main__":
    main()