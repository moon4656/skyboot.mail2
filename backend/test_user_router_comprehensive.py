#!/usr/bin/env python3
"""
User Router 포괄적 테스트 스크립트
각 엔드포인트별 체크리스트를 기반으로 한 체계적인 테스트
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserRouterComprehensiveTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.api_prefix = "/api/v1/users"
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        self.created_users = []  # 테스트 중 생성된 사용자 추적
        
        # 테스트 데이터
        self.test_admin = {
            "email": "test_admin@example.com",
            "password": "admin123!@#"
        }
        self.test_user = {
            "email": "test_user@example.com", 
            "password": "user123!@#"
        }
        
    def log_test_result(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """테스트 결과를 로깅하고 저장"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def setup_tokens(self):
        """관리자 및 일반 사용자 토큰 설정"""
        logger.info("🔑 토큰 설정 시작...")
        
        # 관리자 토큰 획득 시도
        try:
            admin_login_data = {
                "username": self.test_admin["email"],
                "password": self.test_admin["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=admin_login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
                logger.info("✅ 관리자 토큰 획득 성공")
            else:
                logger.warning(f"⚠️ 관리자 로그인 실패: {response.status_code}")
                self.admin_token = "fake_admin_token"  # 테스트용 가짜 토큰
                
        except Exception as e:
            logger.warning(f"⚠️ 관리자 토큰 설정 오류: {e}")
            self.admin_token = "fake_admin_token"
        
        # 일반 사용자 토큰 획득 시도
        try:
            user_login_data = {
                "username": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=user_login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                self.user_token = response.json()["access_token"]
                logger.info("✅ 일반 사용자 토큰 획득 성공")
            else:
                logger.warning(f"⚠️ 일반 사용자 로그인 실패: {response.status_code}")
                self.user_token = "fake_user_token"  # 테스트용 가짜 토큰
                
        except Exception as e:
            logger.warning(f"⚠️ 일반 사용자 토큰 설정 오류: {e}")
            self.user_token = "fake_user_token"
    
    def get_headers(self, token: str = None) -> Dict[str, str]:
        """인증 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    # 1. POST / - 사용자 생성 테스트
    def test_create_user(self):
        """사용자 생성 엔드포인트 테스트"""
        logger.info("🧪 사용자 생성 테스트 시작...")
        
        # 1-1. 관리자 토큰으로 정상 사용자 생성 (200)
        test_user_data = {
            "email": f"new_user_{int(time.time())}@example.com",
            "name": "테스트 사용자",
            "password": "newuser123!@#",
            "is_admin": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/",
                json=test_user_data,
                headers=self.get_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_user = response.json()
                self.created_users.append(created_user.get("id"))
                self.log_test_result(
                    "사용자 생성 - 관리자 권한",
                    True,
                    f"사용자 생성 성공: {test_user_data['email']}",
                    created_user
                )
            else:
                self.log_test_result(
                    "사용자 생성 - 관리자 권한",
                    False,
                    f"예상 상태코드 200, 실제: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("사용자 생성 - 관리자 권한", False, f"요청 오류: {e}")
        
        # 1-2. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/",
                json=test_user_data,
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 생성 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 생성 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 1-3. 토큰 없이 접근 시 인증 오류 (401)
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/",
                json=test_user_data
            )
            
            success = response.status_code == 401
            self.log_test_result(
                "사용자 생성 - 인증 없음",
                success,
                f"예상 상태코드 401, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 생성 - 인증 없음", False, f"요청 오류: {e}")
        
        # 1-4. 필수 필드 누락 시 검증 오류 (422)
        invalid_data = {"name": "테스트"}  # email, password 누락
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/",
                json=invalid_data,
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code == 422
            self.log_test_result(
                "사용자 생성 - 필수 필드 누락",
                success,
                f"예상 상태코드 422, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 생성 - 필수 필드 누락", False, f"요청 오류: {e}")
    
    # 2. GET / - 사용자 목록 조회 테스트
    def test_get_users(self):
        """사용자 목록 조회 엔드포인트 테스트"""
        logger.info("🧪 사용자 목록 조회 테스트 시작...")
        
        # 2-1. 관리자 토큰으로 사용자 목록 조회 (200)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/",
                headers=self.get_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users_data = response.json()
                self.log_test_result(
                    "사용자 목록 조회 - 관리자 권한",
                    True,
                    f"사용자 목록 조회 성공, 총 {len(users_data.get('items', []))}명",
                    {"total_count": len(users_data.get('items', []))}
                )
            else:
                self.log_test_result(
                    "사용자 목록 조회 - 관리자 권한",
                    False,
                    f"예상 상태코드 200, 실제: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("사용자 목록 조회 - 관리자 권한", False, f"요청 오류: {e}")
        
        # 2-2. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 목록 조회 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 목록 조회 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 2-3. 페이지네이션 파라미터 테스트
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/?page=1&limit=5",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code == 200
            self.log_test_result(
                "사용자 목록 조회 - 페이지네이션",
                success,
                f"페이지네이션 테스트, 상태코드: {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test_result("사용자 목록 조회 - 페이지네이션", False, f"요청 오류: {e}")
    
    # 3. GET /me - 현재 사용자 정보 조회 테스트
    def test_get_current_user(self):
        """현재 사용자 정보 조회 엔드포인트 테스트"""
        logger.info("🧪 현재 사용자 정보 조회 테스트 시작...")
        
        # 3-1. 유효한 토큰으로 본인 정보 조회 (200)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/me",
                headers=self.get_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_test_result(
                    "현재 사용자 조회 - 유효한 토큰",
                    True,
                    f"사용자 정보 조회 성공: {user_data.get('email', 'N/A')}",
                    {"email": user_data.get("email")}
                )
            else:
                self.log_test_result(
                    "현재 사용자 조회 - 유효한 토큰",
                    False,
                    f"예상 상태코드 200, 실제: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("현재 사용자 조회 - 유효한 토큰", False, f"요청 오류: {e}")
        
        # 3-2. 토큰 없이 접근 시 인증 오류 (401)
        try:
            response = requests.get(f"{self.base_url}{self.api_prefix}/me")
            
            success = response.status_code == 401
            self.log_test_result(
                "현재 사용자 조회 - 인증 없음",
                success,
                f"예상 상태코드 401, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("현재 사용자 조회 - 인증 없음", False, f"요청 오류: {e}")
        
        # 3-3. 잘못된 토큰으로 접근 시 오류 (401)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/me",
                headers=self.get_headers("invalid_token")
            )
            
            success = response.status_code == 401
            self.log_test_result(
                "현재 사용자 조회 - 잘못된 토큰",
                success,
                f"예상 상태코드 401, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("현재 사용자 조회 - 잘못된 토큰", False, f"요청 오류: {e}")
    
    # 4. GET /{user_id} - 특정 사용자 조회 테스트
    def test_get_user_by_id(self):
        """특정 사용자 조회 엔드포인트 테스트"""
        logger.info("🧪 특정 사용자 조회 테스트 시작...")
        
        test_user_id = 1  # 테스트용 사용자 ID
        
        # 4-1. 관리자가 다른 사용자 조회 (200)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code in [200, 404]  # 사용자가 존재하지 않을 수도 있음
            self.log_test_result(
                "특정 사용자 조회 - 관리자 권한",
                success,
                f"상태코드: {response.status_code}",
                response.json() if response.status_code == 200 else response.text
            )
        except Exception as e:
            self.log_test_result("특정 사용자 조회 - 관리자 권한", False, f"요청 오류: {e}")
        
        # 4-2. 일반 사용자가 다른 사용자 조회 시 권한 오류 (403)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code in [403, 404]  # 권한 오류 또는 사용자 없음
            self.log_test_result(
                "특정 사용자 조회 - 일반 사용자 권한 거부",
                success,
                f"상태코드: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("특정 사용자 조회 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 4-3. 존재하지 않는 사용자 ID 조회 (404)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/99999",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code == 404
            self.log_test_result(
                "특정 사용자 조회 - 존재하지 않는 ID",
                success,
                f"예상 상태코드 404, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("특정 사용자 조회 - 존재하지 않는 ID", False, f"요청 오류: {e}")
    
    # 5. PUT /{user_id} - 사용자 정보 수정 테스트
    def test_update_user(self):
        """사용자 정보 수정 엔드포인트 테스트"""
        logger.info("🧪 사용자 정보 수정 테스트 시작...")
        
        test_user_id = 1
        update_data = {
            "name": "수정된 이름",
            "email": f"updated_{int(time.time())}@example.com"
        }
        
        # 5-1. 관리자가 다른 사용자 정보 수정
        try:
            response = requests.put(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                json=update_data,
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code in [200, 404]
            self.log_test_result(
                "사용자 정보 수정 - 관리자 권한",
                success,
                f"상태코드: {response.status_code}",
                response.json() if response.status_code == 200 else response.text
            )
        except Exception as e:
            self.log_test_result("사용자 정보 수정 - 관리자 권한", False, f"요청 오류: {e}")
        
        # 5-2. 일반 사용자가 다른 사용자 수정 시 권한 오류
        try:
            response = requests.put(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                json=update_data,
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code in [403, 404]
            self.log_test_result(
                "사용자 정보 수정 - 일반 사용자 권한 거부",
                success,
                f"상태코드: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 정보 수정 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
    
    # 6. DELETE /{user_id} - 사용자 삭제 테스트
    def test_delete_user(self):
        """사용자 삭제 엔드포인트 테스트"""
        logger.info("🧪 사용자 삭제 테스트 시작...")
        
        # 삭제할 테스트 사용자가 있다면 사용, 없으면 존재하지 않는 ID 사용
        test_user_id = self.created_users[0] if self.created_users else 99999
        
        # 6-1. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.delete(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 삭제 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 삭제 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 6-2. 관리자가 사용자 삭제
        try:
            response = requests.delete(
                f"{self.base_url}{self.api_prefix}/{test_user_id}",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code in [200, 404, 400]  # 성공, 없음, 또는 본인 삭제 시도
            self.log_test_result(
                "사용자 삭제 - 관리자 권한",
                success,
                f"상태코드: {response.status_code}",
                response.json() if response.status_code == 200 else response.text
            )
        except Exception as e:
            self.log_test_result("사용자 삭제 - 관리자 권한", False, f"요청 오류: {e}")
    
    # 7. POST /{user_id}/change-password - 비밀번호 변경 테스트
    def test_change_password(self):
        """비밀번호 변경 엔드포인트 테스트"""
        logger.info("🧪 비밀번호 변경 테스트 시작...")
        
        test_user_id = 1
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123!@#"
        }
        
        # 7-1. 일반 사용자가 다른 사용자 비밀번호 변경 시 권한 오류
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/change-password",
                json=password_data,
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code in [403, 404]
            self.log_test_result(
                "비밀번호 변경 - 일반 사용자 권한 거부",
                success,
                f"상태코드: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("비밀번호 변경 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 7-2. 필수 필드 누락 시 오류
        invalid_data = {"current_password": "test"}  # new_password 누락
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/change-password",
                json=invalid_data,
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code == 400
            self.log_test_result(
                "비밀번호 변경 - 필수 필드 누락",
                success,
                f"예상 상태코드 400, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("비밀번호 변경 - 필수 필드 누락", False, f"요청 오류: {e}")
    
    # 8. GET /stats/overview - 사용자 통계 조회 테스트
    def test_user_stats(self):
        """사용자 통계 조회 엔드포인트 테스트"""
        logger.info("🧪 사용자 통계 조회 테스트 시작...")
        
        # 8-1. 관리자 토큰으로 통계 조회 (200)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/stats/overview",
                headers=self.get_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                stats_data = response.json()
                self.log_test_result(
                    "사용자 통계 조회 - 관리자 권한",
                    True,
                    "통계 조회 성공",
                    stats_data
                )
            else:
                self.log_test_result(
                    "사용자 통계 조회 - 관리자 권한",
                    False,
                    f"예상 상태코드 200, 실제: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("사용자 통계 조회 - 관리자 권한", False, f"요청 오류: {e}")
        
        # 8-2. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.get(
                f"{self.base_url}{self.api_prefix}/stats/overview",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 통계 조회 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 통계 조회 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
    
    # 9. POST /{user_id}/activate - 사용자 활성화 테스트
    def test_activate_user(self):
        """사용자 활성화 엔드포인트 테스트"""
        logger.info("🧪 사용자 활성화 테스트 시작...")
        
        test_user_id = 1
        
        # 9-1. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/activate",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 활성화 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 활성화 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 9-2. 관리자가 사용자 활성화
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/activate",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code in [200, 404]
            self.log_test_result(
                "사용자 활성화 - 관리자 권한",
                success,
                f"상태코드: {response.status_code}",
                response.json() if response.status_code == 200 else response.text
            )
        except Exception as e:
            self.log_test_result("사용자 활성화 - 관리자 권한", False, f"요청 오류: {e}")
    
    # 10. POST /{user_id}/deactivate - 사용자 비활성화 테스트
    def test_deactivate_user(self):
        """사용자 비활성화 엔드포인트 테스트"""
        logger.info("🧪 사용자 비활성화 테스트 시작...")
        
        test_user_id = 1
        
        # 10-1. 일반 사용자 토큰으로 접근 시 권한 오류 (403)
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/deactivate",
                headers=self.get_headers(self.user_token)
            )
            
            success = response.status_code == 403
            self.log_test_result(
                "사용자 비활성화 - 일반 사용자 권한 거부",
                success,
                f"예상 상태코드 403, 실제: {response.status_code}",
                response.text if not success else None
            )
        except Exception as e:
            self.log_test_result("사용자 비활성화 - 일반 사용자 권한 거부", False, f"요청 오류: {e}")
        
        # 10-2. 관리자가 사용자 비활성화
        try:
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/{test_user_id}/deactivate",
                headers=self.get_headers(self.admin_token)
            )
            
            success = response.status_code in [200, 404, 400]  # 성공, 없음, 또는 본인 비활성화 시도
            self.log_test_result(
                "사용자 비활성화 - 관리자 권한",
                success,
                f"상태코드: {response.status_code}",
                response.json() if response.status_code == 200 else response.text
            )
        except Exception as e:
            self.log_test_result("사용자 비활성화 - 관리자 권한", False, f"요청 오류: {e}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("🚀 User Router 포괄적 테스트 시작...")
        
        # 토큰 설정
        self.setup_tokens()
        
        # 모든 테스트 실행
        test_methods = [
            self.test_create_user,
            self.test_get_users,
            self.test_get_current_user,
            self.test_get_user_by_id,
            self.test_update_user,
            self.test_delete_user,
            self.test_change_password,
            self.test_user_stats,
            self.test_activate_user,
            self.test_deactivate_user
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # 테스트 간 간격
            except Exception as e:
                logger.error(f"❌ 테스트 실행 오류 {test_method.__name__}: {e}")
        
        # 결과 요약
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 80)
        logger.info("📊 테스트 결과 요약")
        logger.info("=" * 80)
        logger.info(f"총 테스트: {total_tests}")
        logger.info(f"✅ 성공: {passed_tests}")
        logger.info(f"❌ 실패: {failed_tests}")
        logger.info(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        logger.info("=" * 80)
        
        if failed_tests > 0:
            logger.info("❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test_name']}: {result['details']}")
    
    def save_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_router_test_results_{timestamp}.json"
        
        summary = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": f"{(sum(1 for r in self.test_results if r['success'])/len(self.test_results)*100):.1f}%"
            },
            "test_results": self.test_results,
            "test_timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"❌ 결과 저장 오류: {e}")

def main():
    """메인 실행 함수"""
    print("🧪 User Router 포괄적 테스트 스크립트")
    print("=" * 60)
    
    # 서버 연결 확인
    try:
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            print("✅ 서버 연결 확인됨")
        else:
            print(f"⚠️ 서버 응답 이상: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("서버가 실행 중인지 확인해주세요.")
        return
    
    # 테스트 실행
    tester = UserRouterComprehensiveTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()