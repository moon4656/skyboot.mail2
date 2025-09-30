#!/usr/bin/env python3
"""
SkyBoot Mail SaaS - Auth Router 종합 테스트

모든 인증 엔드포인트와 보안 기능을 체계적으로 검증합니다.
"""
import sys
import os
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi.testclient import TestClient
    from fastapi import status
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    from main import app
    from app.database.user import get_db
    from app.model.user_model import User, RefreshToken, LoginLog
    from app.model.organization_model import Organization
    from app.service.auth_service import AuthService
    from app.config import settings
    
except ImportError as e:
    print(f"❌ 모듈 임포트 오류: {e}")
    sys.exit(1)

class AuthRouterComprehensiveTest:
    """Auth Router 종합 테스트 클래스"""
    
    def __init__(self):
        """테스트 초기화"""
        self.client = TestClient(app)
        self.test_results = []
        self.admin_credentials = {
            "email": "admin@skyboot.com",
            "password": "Admin123!@#"
        }
        self.test_user_data = {
            "email": f"test_{uuid.uuid4().hex[:8]}@skyboot.com",
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "TestPass123!@#"
        }
        self.access_token = None
        self.refresh_token = None
        
        print("🚀 Auth Router 종합 테스트 시작")
        print("=" * 80)
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """테스트 결과 기록"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        time_info = f" ({response_time:.3f}s)" if response_time > 0 else ""
        print(f"{status_icon} {test_name}{time_info}")
        if details:
            print(f"   📝 {details}")
    
    def test_01_admin_login(self):
        """CP-1.2: 관리자 로그인 테스트"""
        print("\n📋 Phase 1: 기본 기능 테스트")
        print("-" * 40)
        
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json=self.admin_credentials
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                
                # 토큰 구조 검증
                if self.access_token and self.refresh_token:
                    self.log_test_result(
                        "CP-1.2: Admin 로그인",
                        True,
                        f"토큰 발급 성공, 만료시간: {data.get('expires_in')}초",
                        response_time
                    )
                else:
                    self.log_test_result(
                        "CP-1.2: Admin 로그인",
                        False,
                        "토큰이 응답에 포함되지 않음",
                        response_time
                    )
            else:
                self.log_test_result(
                    "CP-1.2: Admin 로그인",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-1.2: Admin 로그인",
                False,
                f"예외 발생: {str(e)}"
            )
    
    def test_02_user_info(self):
        """CP-1.4: 사용자 정보 조회 테스트"""
        if not self.access_token:
            self.log_test_result(
                "CP-1.4: 사용자 정보 조회",
                False,
                "액세스 토큰이 없음"
            )
            return
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.client.get("/api/v1/auth/me", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["user_id", "email", "username", "org_id", "role"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.log_test_result(
                        "CP-1.4: 사용자 정보 조회",
                        True,
                        f"사용자: {data.get('email')}, 역할: {data.get('role')}",
                        response_time
                    )
                else:
                    self.log_test_result(
                        "CP-1.4: 사용자 정보 조회",
                        False,
                        f"누락된 필드: {missing_fields}",
                        response_time
                    )
            else:
                self.log_test_result(
                    "CP-1.4: 사용자 정보 조회",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-1.4: 사용자 정보 조회",
                False,
                f"예외 발생: {str(e)}"
            )
    
    def test_03_user_registration(self):
        """CP-1.1: 회원가입 테스트"""
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/v1/auth/register",
                json=self.test_user_data
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                expected_fields = ["user_id", "email", "username", "org_id"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.log_test_result(
                        "CP-1.1: 회원가입",
                        True,
                        f"사용자 생성: {data.get('email')}",
                        response_time
                    )
                else:
                    self.log_test_result(
                        "CP-1.1: 회원가입",
                        False,
                        f"누락된 필드: {missing_fields}",
                        response_time
                    )
            else:
                self.log_test_result(
                    "CP-1.1: 회원가입",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-1.1: 회원가입",
                False,
                f"예외 발생: {str(e)}"
            )
    
    def test_04_token_refresh(self):
        """CP-1.3: 토큰 재발급 테스트"""
        if not self.refresh_token:
            self.log_test_result(
                "CP-1.3: 토큰 재발급",
                False,
                "리프레시 토큰이 없음"
            )
            return
        
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                new_refresh_token = data.get("refresh_token")
                
                if new_access_token and new_access_token != self.access_token:
                    self.log_test_result(
                        "CP-1.3: 토큰 재발급",
                        True,
                        f"새 액세스 토큰 발급 성공",
                        response_time
                    )
                    # 새 토큰으로 업데이트
                    self.access_token = new_access_token
                    # 새 refresh token이 있으면 업데이트
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                        print(f"🔄 새 refresh token으로 업데이트: {new_refresh_token[:20]}...")
                else:
                    self.log_test_result(
                        "CP-1.3: 토큰 재발급",
                        False,
                        "새 토큰이 발급되지 않음",
                        response_time
                    )
            else:
                self.log_test_result(
                    "CP-1.3: 토큰 재발급",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-1.3: 토큰 재발급",
                False,
                f"예외 발생: {str(e)}"
            )
    
    def test_05_error_handling(self):
        """Phase 2: 에러 처리 테스트"""
        print("\n📋 Phase 2: 에러 처리 테스트")
        print("-" * 40)
        
        # CP-2.1: 중복 이메일 회원가입
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/v1/auth/register",
                json=self.test_user_data  # 이미 등록된 사용자 데이터
            )
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test_result(
                    "CP-2.1: 중복 이메일 회원가입 차단",
                    True,
                    "중복 이메일 등록이 적절히 차단됨",
                    response_time
                )
            else:
                self.log_test_result(
                    "CP-2.1: 중복 이메일 회원가입 차단",
                    False,
                    f"예상과 다른 응답: HTTP {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-2.1: 중복 이메일 회원가입 차단",
                False,
                f"예외 발생: {str(e)}"
            )
        
        # CP-2.2: 잘못된 비밀번호 로그인
        start_time = time.time()
        try:
            wrong_credentials = {
                "email": self.admin_credentials["email"],
                "password": "WrongPassword123"
            }
            response = self.client.post("/api/v1/auth/login", json=wrong_credentials)
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test_result(
                    "CP-2.2: 잘못된 비밀번호 로그인 차단",
                    True,
                    "잘못된 비밀번호 로그인이 적절히 차단됨",
                    response_time
                )
            else:
                self.log_test_result(
                    "CP-2.2: 잘못된 비밀번호 로그인 차단",
                    False,
                    f"예상과 다른 응답: HTTP {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-2.2: 잘못된 비밀번호 로그인 차단",
                False,
                f"예외 발생: {str(e)}"
            )
        
        # CP-2.5: 잘못된 토큰으로 사용자 정보 조회
        start_time = time.time()
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = self.client.get("/api/v1/auth/me", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test_result(
                    "CP-2.5: 잘못된 토큰 접근 차단",
                    True,
                    "잘못된 토큰 접근이 적절히 차단됨",
                    response_time
                )
            else:
                self.log_test_result(
                    "CP-2.5: 잘못된 토큰 접근 차단",
                    False,
                    f"예상과 다른 응답: HTTP {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_test_result(
                "CP-2.5: 잘못된 토큰 접근 차단",
                False,
                f"예외 발생: {str(e)}"
            )
    
    def test_06_security_validation(self):
        """Phase 3: 보안 검증 테스트"""
        print("\n📋 Phase 3: 보안 검증 테스트")
        print("-" * 40)
        
        # CP-3.1: JWT 토큰 구조 검증
        if self.access_token:
            try:
                import jwt
                # 토큰 디코딩 (서명 검증 없이)
                decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                
                required_claims = ["sub", "exp", "type", "org_id"]
                missing_claims = [claim for claim in required_claims if claim not in decoded]
                
                if not missing_claims and decoded.get("type") == "access":
                    self.log_test_result(
                        "CP-3.1: JWT 토큰 구조 검증",
                        True,
                        f"토큰 구조 올바름, 만료시간: {datetime.fromtimestamp(decoded['exp'])}"
                    )
                else:
                    self.log_test_result(
                        "CP-3.1: JWT 토큰 구조 검증",
                        False,
                        f"누락된 클레임: {missing_claims} 또는 잘못된 타입"
                    )
            except Exception as e:
                self.log_test_result(
                    "CP-3.1: JWT 토큰 구조 검증",
                    False,
                    f"토큰 디코딩 실패: {str(e)}"
                )
        else:
            self.log_test_result(
                "CP-3.1: JWT 토큰 구조 검증",
                False,
                "액세스 토큰이 없음"
            )
        
        # CP-3.2: 비밀번호 해싱 검증
        try:
            test_password = "TestPassword123"
            hashed = AuthService.get_password_hash(test_password)
            is_valid = AuthService.verify_password(test_password, hashed)
            is_invalid = AuthService.verify_password("WrongPassword", hashed)
            
            if is_valid and not is_invalid and hashed != test_password:
                self.log_test_result(
                    "CP-3.2: 비밀번호 해싱 검증",
                    True,
                    "bcrypt 해싱이 올바르게 동작함"
                )
            else:
                self.log_test_result(
                    "CP-3.2: 비밀번호 해싱 검증",
                    False,
                    "해싱 또는 검증 로직에 문제가 있음"
                )
        except Exception as e:
            self.log_test_result(
                "CP-3.2: 비밀번호 해싱 검증",
                False,
                f"해싱 테스트 실패: {str(e)}"
            )
    
    def test_07_performance(self):
        """Phase 5: 성능 테스트"""
        print("\n📋 Phase 5: 성능 테스트")
        print("-" * 40)
        
        # CP-5.1: 동시 로그인 요청 처리
        import concurrent.futures
        import threading
        
        def single_login_request():
            try:
                start_time = time.time()
                response = self.client.post("/api/v1/auth/login", json=self.admin_credentials)
                response_time = time.time() - start_time
                return response.status_code == 200, response_time
            except Exception:
                return False, 0
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(single_login_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful_requests = sum(1 for success, _ in results if success)
            avg_response_time = sum(time for _, time in results) / len(results)
            
            if successful_requests >= 4 and avg_response_time < 2.0:
                self.log_test_result(
                    "CP-5.1: 동시 로그인 요청 처리",
                    True,
                    f"성공률: {successful_requests}/5, 평균 응답시간: {avg_response_time:.3f}s"
                )
            else:
                self.log_test_result(
                    "CP-5.1: 동시 로그인 요청 처리",
                    False,
                    f"성능 기준 미달 - 성공률: {successful_requests}/5, 평균 응답시간: {avg_response_time:.3f}s"
                )
        except Exception as e:
            self.log_test_result(
                "CP-5.1: 동시 로그인 요청 처리",
                False,
                f"동시 요청 테스트 실패: {str(e)}"
            )
    
    def test_08_database_integration(self):
        """Phase 6: 데이터베이스 통합 테스트"""
        print("\n📋 Phase 6: 데이터베이스 통합 테스트")
        print("-" * 40)
        
        try:
            # 데이터베이스 연결
            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            
            # CP-6.2: 로그인 로그 기록 확인
            recent_logs = db.query(LoginLog).filter(
                LoginLog.email == self.admin_credentials["email"]
            ).order_by(LoginLog.created_at.desc()).limit(5).all()
            
            if recent_logs:
                success_logs = [log for log in recent_logs if log.login_status == "success"]
                self.log_test_result(
                    "CP-6.2: 로그인 로그 기록 확인",
                    True,
                    f"최근 로그 {len(recent_logs)}개, 성공 로그 {len(success_logs)}개"
                )
            else:
                self.log_test_result(
                    "CP-6.2: 로그인 로그 기록 확인",
                    False,
                    "로그인 로그가 기록되지 않음"
                )
            
            # CP-6.3: 리프레시 토큰 저장 확인
            if self.refresh_token:
                stored_token = db.query(RefreshToken).filter(
                    RefreshToken.token == self.refresh_token
                ).first()
                
                if stored_token and not stored_token.is_revoked:
                    self.log_test_result(
                        "CP-6.3: 리프레시 토큰 저장 확인",
                        True,
                        f"토큰이 데이터베이스에 올바르게 저장됨"
                    )
                else:
                    # 토큰이 있지만 찾을 수 없는 경우 디버깅 정보 추가
                    debug_info = []
                    debug_info.append(f"검색한 토큰: {self.refresh_token[:20]}...")
                    debug_info.append(f"stored_token 결과: {stored_token}")
                    
                    if stored_token:
                        debug_info.append(f"토큰 무효화 상태: {stored_token.is_revoked}")
                        debug_info.append(f"토큰 만료 시간: {stored_token.expires_at}")
                    
                    # 최근 토큰들과 비교
                    recent_tokens = db.query(RefreshToken).order_by(RefreshToken.created_at.desc()).limit(3).all()
                    debug_info.append(f"최근 토큰 수: {len(recent_tokens)}")
                    
                    for i, token in enumerate(recent_tokens):
                        debug_info.append(f"토큰 {i+1}: {token.token[:20]}... (무효화: {token.is_revoked})")
                    
                    self.log_test_result(
                        "CP-6.3: 리프레시 토큰 저장 확인",
                        False,
                        f"토큰이 데이터베이스에 저장되지 않았거나 무효화됨 - 디버깅: {'; '.join(debug_info)}"
                    )
            else:
                # 상세한 디버깅 정보 추가
                debug_info = []
                debug_info.append(f"self.refresh_token 값: {self.refresh_token}")
                debug_info.append(f"self.access_token 존재: {bool(self.access_token)}")
                
                # 최근 토큰들 확인
                recent_tokens = db.query(RefreshToken).order_by(RefreshToken.created_at.desc()).limit(3).all()
                debug_info.append(f"최근 생성된 토큰 수: {len(recent_tokens)}")
                
                for i, token in enumerate(recent_tokens):
                    debug_info.append(f"토큰 {i+1}: {token.token[:20]}... (생성: {token.created_at}, 무효화: {token.is_revoked})")
                
                self.log_test_result(
                    "CP-6.3: 리프레시 토큰 저장 확인",
                    False,
                    f"리프레시 토큰이 없음 - 디버깅 정보: {'; '.join(debug_info)}"
                )
            
            db.close()
            
        except Exception as e:
            self.log_test_result(
                "CP-6.x: 데이터베이스 통합 테스트",
                False,
                f"데이터베이스 연결 또는 쿼리 실패: {str(e)}"
            )
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        test_methods = [
            self.test_01_admin_login,
            self.test_02_user_info,
            self.test_03_user_registration,
            self.test_04_token_refresh,
            self.test_05_error_handling,
            self.test_06_security_validation,
            self.test_07_performance,
            self.test_08_database_integration
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ 테스트 실행 중 예외 발생: {test_method.__name__} - {str(e)}")
        
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📊 Auth Router 종합 테스트 결과 요약")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ 성공: {successful_tests}개")
        print(f"❌ 실패: {failed_tests}개")
        print(f"📈 성공률: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        # 평균 응답 시간 계산
        response_times = [r["response_time"] for r in self.test_results if r["response_time"] > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"\n⏱️ 평균 응답 시간: {avg_response_time:.3f}초")
        
        # 결과를 JSON 파일로 저장
        with open("auth_router_test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0
                },
                "detailed_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 결과가 'auth_router_test_results.json'에 저장되었습니다.")

def main():
    """메인 함수"""
    tester = AuthRouterComprehensiveTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()