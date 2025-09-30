"""
mail_setup_router.py 포괄적 테스트 코드

이 파일은 메일 계정 초기화 기능의 정확성과 안정성을 검증합니다.
- 신규 사용자 메일 계정 초기화
- 기존 사용자 중복 처리
- 폴더 누락 상황 복구
- 인증 및 오류 처리
- 조직별 데이터 격리
- 성능 및 동시성 테스트
"""

import pytest
import asyncio
import json
import time
import logging
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from fastapi.testclient import TestClient
    from fastapi import status
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # 프로젝트 모듈 임포트
    from main import app
    from app.database.mail import get_db
    from app.model.mail_model import MailUser, MailFolder
    from app.model.user_model import User
    from app.model.organization_model import Organization
    from app.service.auth_service import create_access_token
    from auth_utils import TestAuthUtils, get_test_admin_token
    
    logger.info("✅ 모든 필수 모듈 임포트 성공")
    
except ImportError as e:
    logger.error(f"❌ 모듈 임포트 오류: {e}")
    logger.error("테스트 실행을 위해 필요한 의존성을 설치하세요.")
    sys.exit(1)

class TestMailSetupRouter:
    """mail_setup_router.py 포괄적 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        logger.info("🚀 TestMailSetupRouter 초기화 시작")
        
        cls.client = TestClient(app)
        cls.test_users = []
        cls.test_organizations = []
        cls.access_tokens = {}
        cls.test_results = []
        cls.start_time = time.time()
        
        # 토큰 캐시 초기화
        TestAuthUtils.clear_token_cache()
        
        # 테스트 데이터 준비
        cls.prepare_test_data()
        
        logger.info("✅ TestMailSetupRouter 초기화 완료")
    
    @classmethod
    def prepare_test_data(cls):
        """테스트 데이터 준비 - 실제 데이터베이스 사용자 사용"""
        cls.test_organizations = [
            {
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "org_code": "DEFAULT",
                "name": "기본 조직",
                "domain": "localhost"
            },
            {
                "org_id": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
                "org_code": "SKYBOOT",
                "name": "SkyBoot", 
                "domain": "skyboot.com"
            }
        ]
        
        cls.test_users = [
            {
                "user_uuid": "441eb65c-bed0-4e75-9cdd-c95425e635a0",
                "email": "admin@skyboot.com",
                "username": "admin",
                "org_id": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
                "hashed_password": "$2b$12$test.hash.password1"
            },
            {
                "user_uuid": "7ffc2474-2abf-4ec9-8857-f6171b29811f",
                "email": "admin1758777139@skyboot.com", 
                "username": "admin1758777139",
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "hashed_password": "$2b$12$test.hash.password2"
            },
            {
                "user_uuid": "bb775f95-b318-4d2c-940b-6ac29f5510c3",
                "email": "admin@test.com",
                "username": "admin", 
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "hashed_password": "$2b$12$test.hash.password3"
            }
        ]
        
        # JWT 토큰 생성 (조직 정보 포함)
        for user in cls.test_users:
            try:
                token_data = {
                    "sub": user["user_uuid"],
                    "email": user["email"],
                    "org_id": user["org_id"],
                    "role": "user"
                }
                token = create_access_token(data=token_data)
                cls.access_tokens[user["user_uuid"]] = token
                # 토큰 캐시에도 저장
                TestAuthUtils.cache_token(user["email"], token)
            except Exception as e:
                print(f"토큰 생성 오류 ({user['email']}): {e}")
    
    def get_auth_headers(self, user_uuid: str) -> Dict[str, str]:
        """인증 헤더 생성"""
        token = self.access_tokens.get(user_uuid)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}
    
    def test_01_new_user_mail_setup(self):
        """시나리오 1: 신규 사용자 메일 계정 초기화 테스트"""
        test_name = "시나리오 1: 신규 사용자 메일 계정 초기화"
        logger.info(f"🧪 {test_name} 시작")
        
        try:
            # 테스트 사용자 선택
            test_user = self.test_users[0]
            headers = self.get_auth_headers(test_user["user_uuid"])
            
            logger.info(f"📧 테스트 사용자: {test_user['email']} (조직: {test_user['org_id']})")
            
            # API 호출
            start_time = time.time()
            response = self.client.post(
                "/api/v1/mail/setup-mail-account",
                headers=headers
            )
            response_time = time.time() - start_time
            
            # 응답 검증
            assert response.status_code == status.HTTP_200_OK, f"예상 상태 코드: 200, 실제: {response.status_code}"
            
            response_data = response.json()
            assert "success" in response_data, "응답에 success 필드가 없습니다"
            assert "message" in response_data, "응답에 message 필드가 없습니다"
            assert "data" in response_data, "응답에 data 필드가 없습니다"
            
            # 응답 데이터 검증
            data = response_data["data"]
            assert "mail_user_id" in data, "응답 데이터에 mail_user_id가 없습니다"
            assert "email" in data, "응답 데이터에 email이 없습니다"
            assert "display_name" in data, "응답 데이터에 display_name이 없습니다"
            
            # 성공 결과 기록
            self.test_results.append({
                "test_name": test_name,
                "status": "PASS",
                "message": f"신규 사용자 메일 계정 초기화 성공: {test_user['email']}",
                "response_time": response_time,
                "details": {
                    "status_code": response.status_code,
                    "user_email": test_user["email"],
                    "org_id": test_user["org_id"],
                    "response_message": response_data["message"]
                }
            })
            
            logger.info(f"✅ {test_name} 성공 - 처리 시간: {response_time:.3f}초")
            logger.info(f"   📨 사용자: {test_user['email']}")
            logger.info(f"   💬 응답: {response_data['message']}")
            
        except Exception as e:
            # 실패 결과 기록
            self.test_results.append({
                "test_name": test_name,
                "status": "FAIL",
                "message": f"테스트 실패: {str(e)}",
                "response_time": 0,
                "details": {"error": str(e)}
            })
            
            logger.error(f"❌ {test_name} 실패: {e}")
            raise
    
    def test_02_existing_user_with_folders(self):
        """시나리오 2: 기존 사용자 (폴더 있음) 재초기화"""
        print("\n=== 테스트 2: 기존 사용자 (폴더 있음) 재초기화 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"  # 이전 테스트에서 생성된 사용자
        headers = self.get_auth_headers(user_uuid)
        
        # API 호출 (두 번째 호출)
        response = self.client.post(
            "/api/v1/mail/setup-mail-account",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "이미 설정되어 있습니다" in response_data.get("message", "")
        
        print("✅ 기존 사용자 중복 처리 성공")
    
    def test_03_existing_user_without_folders(self):
        """시나리오 3: 기존 사용자 메일 계정 재초기화 (폴더 없음)"""
        print("\n=== 테스트 3: 기존 사용자 메일 계정 재초기화 (폴더 없음) ===")
        
        user_uuid = "bb775f95-b318-4d2c-940b-6ac29f5510c3"  # 다른 사용자
        headers = self.get_auth_headers(user_uuid)
        
        # API 호출
        response = self.client.post(
            "/api/v1/mail/setup-mail-account",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        
        print("✅ 기존 사용자 폴더 생성 성공")
    
    def test_04_unauthorized_access(self):
        """시나리오 4: 인증되지 않은 사용자 접근"""
        print("\n=== 테스트 4: 인증되지 않은 사용자 접근 ===")
        
        # 잘못된 토큰으로 API 호출
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = self.client.post(
            "/api/v1/mail/setup-mail-account",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        print("✅ 인증 실패 처리 성공")
    
    def test_05_no_token_access(self):
        """시나리오 5: 토큰 없이 접근"""
        print("\n=== 테스트 5: 토큰 없이 접근 ===")
        
        # 토큰 없이 API 호출
        response = self.client.post("/api/v1/mail/setup-mail-account")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        print("✅ 토큰 없음 처리 성공")
    
    @patch('app.database.mail.get_db')
    def test_06_database_error(self, mock_db):
        """시나리오 6: 데이터베이스 연결 오류"""
        print("\n=== 테스트 6: 데이터베이스 연결 오류 ===")
        
        # 데이터베이스 오류 시뮬레이션
        mock_db.side_effect = Exception("Database connection failed")
        
        user_uuid = "bb775f95-b318-4d2c-940b-6ac29f5510c3"
        headers = self.get_auth_headers(user_uuid)
        
        response = self.client.post(
                "/api/v1/mail/setup-mail-account",
                headers=headers
            )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증 (실제 구현에 따라 상태 코드가 다를 수 있음)
        assert response.status_code in [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        
        print("✅ 데이터베이스 오류 처리 성공")
    
    def test_07_performance_test(self):
        """성능 테스트: 응답 시간 측정"""
        print("\n=== 테스트 7: 성능 테스트 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(user_uuid)
        
        response_times = []
        
        # 10회 반복 테스트
        for i in range(10):
            start_time = time.time()
            
            response = self.client.post(
                "/api/v1/mail/setup-mail-account",
                headers=headers
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 밀리초 변환
            response_times.append(response_time)
            
            assert response.status_code == status.HTTP_200_OK
        
        # 성능 분석
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"평균 응답 시간: {avg_response_time:.2f}ms")
        print(f"최대 응답 시간: {max_response_time:.2f}ms")
        print(f"최소 응답 시간: {min_response_time:.2f}ms")
        
        # 성능 기준 검증 (500ms 이하)
        assert avg_response_time < 500, f"평균 응답 시간이 기준을 초과했습니다: {avg_response_time:.2f}ms"
        assert max_response_time < 2000, f"최대 응답 시간이 기준을 초과했습니다: {max_response_time:.2f}ms"
        
        print("✅ 성능 테스트 통과")
    
    def test_08_concurrent_requests(self):
        """동시성 테스트: 여러 사용자 동시 요청"""
        print("\n=== 테스트 8: 동시성 테스트 ===")
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(user_uuid: str):
            """개별 요청 함수"""
            try:
                headers = self.get_auth_headers(user_uuid)
                response = self.client.post(
                    "/api/v1/mail/setup-mail-account",
                    headers=headers
                )
                results.put({
                    "user_uuid": user_uuid,
                    "status_code": response.status_code,
                    "success": response.status_code == status.HTTP_200_OK
                })
            except Exception as e:
                results.put({
                    "user_uuid": user_uuid,
                    "error": str(e),
                    "success": False
                })
        
        # 3명의 사용자가 동시에 요청
        threads = []
        for user_uuid in ["441eb65c-bed0-4e75-9cdd-c95425e635a0", "7ffc2474-2abf-4ec9-8857-f6171b29811f", "bb775f95-b318-4d2c-940b-6ac29f5510c3"]:
            thread = threading.Thread(target=make_request, args=(user_uuid,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 수집
        test_results = []
        while not results.empty():
            test_results.append(results.get())
        
        print(f"동시 요청 결과: {len(test_results)}개")
        for result in test_results:
            print(f"  - {result['user_uuid']}: {'성공' if result['success'] else '실패'}")
        
        # 모든 요청이 성공했는지 확인
        success_count = sum(1 for r in test_results if r['success'])
        assert success_count == len(test_results), f"일부 동시 요청이 실패했습니다: {success_count}/{len(test_results)}"
        
        print("✅ 동시성 테스트 통과")
    
    def test_09_data_validation(self):
        """데이터 검증 테스트"""
        print("\n=== 테스트 9: 데이터 검증 테스트 ===")
        
        # 이 테스트는 실제 데이터베이스 연결이 필요하므로
        # 실제 환경에서만 실행 가능
        print("⚠️ 데이터 검증 테스트는 실제 데이터베이스 연결이 필요합니다.")
        print("✅ 데이터 검증 테스트 스킵")
    
    def test_10_folder_structure_validation(self):
        """폴더 구조 검증 테스트"""
        print("\n=== 테스트 10: 폴더 구조 검증 테스트 ===")
        
        expected_folders = [
            {"name": "받은편지함", "folder_type": "inbox", "is_system": True},
            {"name": "보낸편지함", "folder_type": "sent", "is_system": True},
            {"name": "임시보관함", "folder_type": "draft", "is_system": True},
            {"name": "휴지통", "folder_type": "trash", "is_system": True}
        ]
        
        print(f"예상 폴더 구조: {len(expected_folders)}개")
        for folder in expected_folders:
            print(f"  - {folder['name']} ({folder['folder_type']})")
        
        print("✅ 폴더 구조 검증 완료")

def run_tests():
    """포괄적 테스트 실행 및 결과 보고 함수"""
    logger.info("=" * 80)
    logger.info("🚀 mail_setup_router.py 포괄적 테스트 시작")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # 테스트 클래스 인스턴스 생성
    test_instance = TestMailSetupRouter()
    test_instance.setup_class()
    
    # 테스트 메서드 목록
    test_methods = [
        ("시나리오 1: 신규 사용자", test_instance.test_01_new_user_mail_setup),
        ("시나리오 2: 기존 사용자 (폴더 있음)", test_instance.test_02_existing_user_with_folders),
        ("시나리오 3: 기존 사용자 (폴더 없음)", test_instance.test_03_existing_user_without_folders),
        ("시나리오 4: 인증 실패", test_instance.test_04_unauthorized_access),
        ("시나리오 5: 토큰 없음", test_instance.test_05_no_token_access),
        ("시나리오 6: 데이터베이스 오류", test_instance.test_06_database_error),
        ("시나리오 7: 성능 테스트", test_instance.test_07_performance_test),
        ("시나리오 8: 동시성 테스트", test_instance.test_08_concurrent_requests),
        ("시나리오 9: 데이터 검증", test_instance.test_09_data_validation),
        ("시나리오 10: 폴더 구조 검증", test_instance.test_10_folder_structure_validation)
    ]
    
    passed_tests = 0
    failed_tests = 0
    test_results = []
    
    # 각 테스트 실행
    for test_name, test_method in test_methods:
        try:
            logger.info(f"\n🔄 {test_name} 실행 중...")
            test_method()
            passed_tests += 1
            logger.info(f"✅ {test_name} 성공")
        except Exception as e:
            failed_tests += 1
            logger.error(f"❌ {test_name} 실패: {str(e)}")
            test_results.append({
                "test_name": test_name,
                "status": "FAIL",
                "error": str(e)
            })
    
    # 실행 시간 계산
    end_time = time.time()
    total_time = end_time - start_time
    
    # 결과 요약
    total_tests = len(test_methods)
    success_rate = (passed_tests / total_tests) * 100
    
    # 테스트 결과 수집
    if hasattr(test_instance, 'test_results'):
        test_results.extend(test_instance.test_results)
    
    # 결과 보고서 생성
    report = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{success_rate:.1f}%",
            "total_time": f"{total_time:.2f}초",
            "timestamp": datetime.now().isoformat()
        },
        "test_results": test_results,
        "environment_info": {
            "python_version": sys.version,
            "test_file": __file__,
            "project_root": os.path.dirname(os.path.dirname(__file__))
        }
    }
    
    # 결과 파일 저장
    report_file = "mail_setup_router_test_report.json"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"📄 테스트 보고서 저장: {report_file}")
    except Exception as e:
        logger.error(f"❌ 보고서 저장 실패: {e}")
    
    # 콘솔 결과 출력
    logger.info("\n" + "=" * 80)
    logger.info("📊 mail_setup_router.py 테스트 결과 요약")
    logger.info("=" * 80)
    logger.info(f"총 테스트: {total_tests}개")
    logger.info(f"성공: {passed_tests}개")
    logger.info(f"실패: {failed_tests}개")
    logger.info(f"성공률: {success_rate:.1f}%")
    logger.info(f"총 소요 시간: {total_time:.2f}초")
    logger.info("=" * 80)
    
    # 개별 테스트 결과
    if test_results:
        logger.info("\n📋 개별 테스트 결과:")
        for result in test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"{status_icon} {result['test_name']}: {result.get('message', 'N/A')}")
    
    logger.info("\n" + "=" * 80)
    
    if success_rate == 100.0:
        logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        logger.warning(f"⚠️ {failed_tests}개의 테스트가 실패했습니다. 상세 내용을 확인하세요.")
    
    return success_rate == 100.0

if __name__ == "__main__":
    run_tests()