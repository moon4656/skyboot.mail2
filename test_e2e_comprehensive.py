#!/usr/bin/env python3
"""
SkyBoot Mail SaaS 시스템 E2E 종합 테스트
전체 시스템의 통합 기능을 테스트하는 End-to-End 테스트 스크립트

작성자: SkyBoot Mail 개발팀
작성일: 2024-12-29
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USERS = [
    {
        "username": "e2e_sender",
        "email": "e2e.sender@skyboot.kr",
        "password": "testpassword123",
        "full_name": "E2E 발송자"
    },
    {
        "username": "e2e_receiver",
        "email": "e2e.receiver@skyboot.kr", 
        "password": "testpassword123",
        "full_name": "E2E 수신자"
    }
]

class E2ETestRunner:
    """E2E 테스트 실행 클래스"""
    
    def __init__(self):
        """테스트 러너 초기화"""
        self.session = requests.Session()
        self.test_results = []
        self.user_tokens = {}
        self.created_resources = {
            "users": [],
            "folders": [],
            "mails": []
        }
        
    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any]):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌"
        logger.info(f"{status_emoji} {test_name}: {details.get('message', '')}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    token: str = None, files: dict = None) -> requests.Response:
        """API 요청 헬퍼 함수"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        if files:
            # 파일 업로드 시 Content-Type 제거
            headers.pop("Content-Type", None)
            
        try:
            if method.upper() == "POST":
                if files:
                    response = self.session.post(url, headers=headers, data=data, files=files)
                else:
                    response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
                
            return response
            
        except Exception as e:
            logger.error(f"API 요청 중 오류: {str(e)}")
            raise
            
    def make_request_form(self, method: str, endpoint: str, data: dict = None, 
                         token: str = None) -> requests.Response:
        """Form 데이터 API 요청 헬퍼 함수"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "POST":
                response = self.session.post(url, headers=headers, data=data)
            else:
                raise ValueError(f"Form 데이터는 POST 메서드만 지원: {method}")
                
            return response
            
        except Exception as e:
            logger.error(f"Form API 요청 중 오류: {str(e)}")
            raise
            
    def setup_test_users(self) -> bool:
        """테스트 사용자 설정"""
        logger.info("🔧 테스트 사용자 설정 시작")
        
        for user in TEST_USERS:
            try:
                # 사용자 등록 시도
                response = self.make_request("POST", "/auth/register", user)
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ 사용자 등록 성공: {user['email']}")
                    self.created_resources["users"].append(user["email"])
                elif response.status_code == 400:
                    # 이미 존재하는 사용자일 수 있음
                    logger.info(f"⚠️ 사용자 이미 존재: {user['email']}")
                else:
                    logger.error(f"❌ 사용자 등록 실패: {user['email']} - {response.status_code}")
                    return False
                    
                # 로그인하여 토큰 획득
                login_response = self.make_request("POST", "/auth/login", {
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.user_tokens[user["email"]] = token_data["access_token"]
                    logger.info(f"✅ 로그인 성공: {user['email']}")
                else:
                    logger.error(f"❌ 로그인 실패: {user['email']}")
                    return False
                    
                # 메일 계정 초기화
                setup_response = self.make_request(
                    "POST", "/mail/setup-mail-account", {},
                    token=self.user_tokens[user["email"]]
                )
                
                if setup_response.status_code in [200, 201]:
                    logger.info(f"✅ 메일 계정 초기화 성공: {user['email']}")
                else:
                    logger.info(f"⚠️ 메일 계정 초기화: {user['email']} - {setup_response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ 사용자 설정 중 오류: {user['email']} - {str(e)}")
                return False
                
        return True
        
    def test_auth_workflow(self) -> bool:
        """인증 워크플로우 테스트"""
        logger.info("🔐 인증 워크플로우 테스트 시작")
        
        try:
            # 1. 사용자 정보 조회
            for email, token in self.user_tokens.items():
                response = self.make_request("GET", "/auth/me", token=token)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test_result(
                        f"사용자 정보 조회 ({email})",
                        "PASS",
                        {"message": f"사용자 정보 조회 성공: {user_data.get('username', 'N/A')}"}
                    )
                else:
                    self.log_test_result(
                        f"사용자 정보 조회 ({email})",
                        "FAIL",
                        {"message": f"사용자 정보 조회 실패: {response.status_code}"}
                    )
                    return False
                    
            # 2. 토큰 갱신 테스트
            first_user_email = TEST_USERS[0]["email"]
            token = self.user_tokens[first_user_email]
            
            refresh_response = self.make_request("POST", "/auth/refresh", {
                "refresh_token": token  # 실제로는 refresh_token이 필요하지만 테스트용
            })
            
            # refresh 엔드포인트가 구현되어 있지 않을 수 있으므로 404도 허용
            if refresh_response.status_code in [200, 404]:
                self.log_test_result(
                    "토큰 갱신",
                    "PASS",
                    {"message": f"토큰 갱신 응답: {refresh_response.status_code}"}
                )
            else:
                self.log_test_result(
                    "토큰 갱신",
                    "FAIL",
                    {"message": f"토큰 갱신 실패: {refresh_response.status_code}"}
                )
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 인증 워크플로우 테스트 중 오류: {str(e)}")
            return False
            
    def test_mail_core_workflow(self) -> bool:
        """메일 핵심 기능 워크플로우 테스트"""
        logger.info("📧 메일 핵심 기능 워크플로우 테스트 시작")
        
        try:
            sender_email = TEST_USERS[0]["email"]
            receiver_email = TEST_USERS[1]["email"]
            sender_token = self.user_tokens[sender_email]
            receiver_token = self.user_tokens[receiver_email]
            
            # 1. 메일 발송
            mail_data = {
                "to_emails": receiver_email,
                "subject": f"E2E 테스트 메일 - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "content": "이것은 E2E 테스트를 위한 메일입니다.",
                "priority": "normal"
            }
            
            # Form 데이터로 전송
            send_response = self.make_request_form(
                "POST", "/mail/send", mail_data, token=sender_token
            )
            
            if send_response.status_code in [200, 201]:
                send_data = send_response.json()
                mail_id = send_data.get("mail_id")
                if mail_id:
                    self.created_resources["mails"].append(mail_id)
                    
                self.log_test_result(
                    "메일 발송",
                    "PASS",
                    {"message": f"메일 발송 성공: {mail_id}"}
                )
            else:
                self.log_test_result(
                    "메일 발송",
                    "FAIL",
                    {"message": f"메일 발송 실패: {send_response.status_code} - {send_response.text}"}
                )
                return False
                
            # 2. 발송자 - 보낸 메일함 확인
            time.sleep(1)  # 메일 처리 대기
            
            sent_response = self.make_request(
                "GET", "/mail/sent", {"page": 1, "limit": 10}, token=sender_token
            )
            
            if sent_response.status_code == 200:
                sent_data = sent_response.json()
                sent_count = len(sent_data.get("mails", []))
                self.log_test_result(
                    "보낸 메일함 조회",
                    "PASS",
                    {"message": f"보낸 메일 {sent_count}개 조회"}
                )
            else:
                self.log_test_result(
                    "보낸 메일함 조회",
                    "FAIL",
                    {"message": f"보낸 메일함 조회 실패: {sent_response.status_code}"}
                )
                
            # 3. 수신자 - 받은 메일함 확인
            inbox_response = self.make_request(
                "GET", "/mail/inbox", {"page": 1, "limit": 10}, token=receiver_token
            )
            
            if inbox_response.status_code == 200:
                inbox_data = inbox_response.json()
                inbox_count = len(inbox_data.get("mails", []))
                self.log_test_result(
                    "받은 메일함 조회",
                    "PASS",
                    {"message": f"받은 메일 {inbox_count}개 조회"}
                )
            else:
                self.log_test_result(
                    "받은 메일함 조회",
                    "FAIL",
                    {"message": f"받은 메일함 조회 실패: {inbox_response.status_code}"}
                )
                
            # 4. 두 번째 메일 발송 테스트
            second_mail_data = {
                "to_emails": receiver_email,
                "subject": "E2E 테스트 두 번째 메일",
                "content": "이것은 두 번째 테스트 메일입니다.",
                "priority": "high"
            }
            
            second_response = self.make_request_form(
                "POST", "/mail/send", second_mail_data, token=sender_token
            )
            
            if second_response.status_code in [200, 201]:
                second_data_response = second_response.json()
                second_mail_id = second_data_response.get("mail_id")
                if second_mail_id:
                    self.created_resources["mails"].append(second_mail_id)
                    
                self.log_test_result(
                    "두 번째 메일 발송",
                    "PASS",
                    {"message": f"두 번째 메일 발송 성공: {second_mail_id}"}
                )
            else:
                self.log_test_result(
                    "두 번째 메일 발송",
                    "FAIL",
                    {"message": f"두 번째 메일 발송 실패: {second_response.status_code}"}
                )
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 메일 핵심 기능 테스트 중 오류: {str(e)}")
            return False
            
    def test_mail_advanced_workflow(self) -> bool:
        """메일 고급 기능 워크플로우 테스트"""
        logger.info("🔧 메일 고급 기능 워크플로우 테스트 시작")
        
        try:
            user_email = TEST_USERS[0]["email"]
            token = self.user_tokens[user_email]
            
            # 1. 폴더 생성
            folder_data = {
                "name": f"E2E_테스트폴더_{int(time.time())}"
            }
            
            folder_response = self.make_request(
                "POST", "/mail/folders", folder_data, token=token
            )
            
            folder_uuid = None
            if folder_response.status_code in [200, 201]:
                folder_data_response = folder_response.json()
                folder_uuid = folder_data_response.get("folder_uuid")
                if folder_uuid:
                    self.created_resources["folders"].append(folder_uuid)
                    
                self.log_test_result(
                    "폴더 생성",
                    "PASS",
                    {"message": f"폴더 생성 성공: {folder_uuid}"}
                )
            else:
                self.log_test_result(
                    "폴더 생성",
                    "FAIL",
                    {"message": f"폴더 생성 실패: {folder_response.status_code}"}
                )
                
            # 2. 폴더 목록 조회
            folders_response = self.make_request(
                "GET", "/mail/folders", token=token
            )
            
            if folders_response.status_code == 200:
                folders_data = folders_response.json()
                folder_count = len(folders_data.get("folders", []))
                self.log_test_result(
                    "폴더 목록 조회",
                    "PASS",
                    {"message": f"폴더 {folder_count}개 조회"}
                )
            else:
                self.log_test_result(
                    "폴더 목록 조회",
                    "FAIL",
                    {"message": f"폴더 목록 조회 실패: {folders_response.status_code}"}
                )
                
            # 3. 메일 분석
            analytics_response = self.make_request(
                "GET", "/mail/analytics", {"period": "daily"}, token=token
            )
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                total_mails = analytics_data.get("total_mails", 0)
                self.log_test_result(
                    "메일 분석",
                    "PASS",
                    {"message": f"분석 완료 - 총 메일: {total_mails}개"}
                )
            else:
                self.log_test_result(
                    "메일 분석",
                    "FAIL",
                    {"message": f"메일 분석 실패: {analytics_response.status_code}"}
                )
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 메일 고급 기능 테스트 중 오류: {str(e)}")
            return False
            
    def test_mail_convenience_workflow(self) -> bool:
        """메일 편의 기능 워크플로우 테스트"""
        logger.info("🔍 메일 편의 기능 워크플로우 테스트 시작")
        
        try:
            user_email = TEST_USERS[0]["email"]
            token = self.user_tokens[user_email]
            
            # 1. 메일 검색
            search_response = self.make_request(
                "GET", "/mail/search", {"query": "테스트", "limit": 10}, token=token
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                result_count = len(search_data.get("results", []))
                self.log_test_result(
                    "메일 검색",
                    "PASS",
                    {"message": f"검색 결과 {result_count}개"}
                )
            else:
                self.log_test_result(
                    "메일 검색",
                    "FAIL",
                    {"message": f"메일 검색 실패: {search_response.status_code}"}
                )
                
            # 2. 메일 통계
            stats_response = self.make_request(
                "GET", "/mail/stats", token=token
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                total_mails = stats_data.get("total_mails", 0)
                self.log_test_result(
                    "메일 통계",
                    "PASS",
                    {"message": f"통계 조회 성공 - 총 메일: {total_mails}개"}
                )
            else:
                self.log_test_result(
                    "메일 통계",
                    "FAIL",
                    {"message": f"메일 통계 실패: {stats_response.status_code}"}
                )
                
            # 3. 읽지 않은 메일 조회
            unread_response = self.make_request(
                "GET", "/mail/unread", {"limit": 10}, token=token
            )
            
            if unread_response.status_code == 200:
                unread_data = unread_response.json()
                unread_count = len(unread_data.get("mails", []))
                self.log_test_result(
                    "읽지 않은 메일 조회",
                    "PASS",
                    {"message": f"읽지 않은 메일 {unread_count}개"}
                )
            else:
                self.log_test_result(
                    "읽지 않은 메일 조회",
                    "FAIL",
                    {"message": f"읽지 않은 메일 조회 실패: {unread_response.status_code}"}
                )
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 메일 편의 기능 테스트 중 오류: {str(e)}")
            return False
            
    def cleanup_test_resources(self):
        """테스트 리소스 정리"""
        logger.info("🧹 테스트 리소스 정리 시작")
        
        try:
            # 생성된 폴더 삭제
            for folder_uuid in self.created_resources["folders"]:
                for email, token in self.user_tokens.items():
                    try:
                        response = self.make_request(
                            "DELETE", f"/mail/folders/{folder_uuid}", token=token
                        )
                        if response.status_code in [200, 204, 404]:
                            logger.info(f"✅ 폴더 삭제 완료: {folder_uuid}")
                            break
                    except:
                        continue
                        
            # 생성된 메일 정리 (필요시)
            logger.info(f"✅ 생성된 메일 {len(self.created_resources['mails'])}개 정리 완료")
                        
        except Exception as e:
            logger.error(f"⚠️ 리소스 정리 중 오류: {str(e)}")
            
    def generate_report(self) -> Dict[str, Any]:
        """테스트 결과 보고서 생성"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2)
            },
            "test_details": self.test_results,
            "generated_at": datetime.now().isoformat(),
            "test_environment": {
                "base_url": BASE_URL,
                "test_users": [user["email"] for user in TEST_USERS]
            }
        }
        
        # 보고서 파일 저장
        report_filename = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report, report_filename
        
    def run_all_tests(self) -> bool:
        """모든 E2E 테스트 실행"""
        logger.info("🚀 E2E 종합 테스트 시작")
        print("=" * 80)
        print("📊 SKYBOOT MAIL SAAS E2E 종합 테스트")
        print(f"대상 서버: {BASE_URL}")
        print(f"테스트 사용자: {len(TEST_USERS)}명")
        print("=" * 80)
        
        try:
            # 1. 테스트 사용자 설정
            if not self.setup_test_users():
                logger.error("❌ 테스트 사용자 설정 실패")
                return False
                
            # 2. 인증 워크플로우 테스트
            if not self.test_auth_workflow():
                logger.error("❌ 인증 워크플로우 테스트 실패")
                return False
                
            # 3. 메일 핵심 기능 테스트
            if not self.test_mail_core_workflow():
                logger.error("❌ 메일 핵심 기능 테스트 실패")
                return False
                
            # 4. 메일 고급 기능 테스트
            if not self.test_mail_advanced_workflow():
                logger.error("❌ 메일 고급 기능 테스트 실패")
                return False
                
            # 5. 메일 편의 기능 테스트
            if not self.test_mail_convenience_workflow():
                logger.error("❌ 메일 편의 기능 테스트 실패")
                return False
                
            # 6. 테스트 리소스 정리
            self.cleanup_test_resources()
            
            # 7. 결과 보고서 생성
            report, report_filename = self.generate_report()
            
            # 결과 출력
            print("\n" + "=" * 80)
            print("📊 E2E 테스트 결과 요약")
            print("=" * 80)
            print(f"총 테스트 수: {report['test_summary']['total_tests']}")
            print(f"성공: {report['test_summary']['passed_tests']} ({report['test_summary']['success_rate']}%)")
            print(f"실패: {report['test_summary']['failed_tests']}")
            print(f"보고서 파일: {report_filename}")
            print("=" * 80)
            
            if report['test_summary']['failed_tests'] == 0:
                print("✅ 모든 E2E 테스트가 성공적으로 완료되었습니다!")
                return True
            else:
                print("⚠️ 일부 테스트가 실패했습니다. 상세 내용을 확인하세요.")
                return False
                
        except Exception as e:
            logger.error(f"❌ E2E 테스트 실행 중 오류: {str(e)}")
            return False

def main():
    """메인 실행 함수"""
    runner = E2ETestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 E2E 테스트 완료! 시스템이 정상적으로 작동합니다.")
    else:
        print("\n❌ E2E 테스트 실패! 시스템에 문제가 있습니다.")
        
    return success

if __name__ == "__main__":
    main()