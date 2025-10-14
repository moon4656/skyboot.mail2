"""
API Rate Limiting 보안 기능 테스트

이 모듈은 API 속도 제한 관련 모든 기능을 테스트합니다:
- IP 기반 속도 제한
- 사용자 기반 속도 제한
- 조직 기반 속도 제한
- 엔드포인트별 속도 제한
- 속도 제한 위반 로깅
- 속도 제한 설정 관리
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.middleware.rate_limit_middleware import RateLimitService
from app.model.user_model import User
from app.model.organization_model import Organization


class TestRateLimitService:
    """속도 제한 서비스 테스트 클래스"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        # Mock Redis 클라이언트 생성
        self.mock_redis = Mock()
        self.rate_limit_service = RateLimitService()
        self.rate_limit_service.redis_client = self.mock_redis
        
        # 테스트용 조직 생성
        self.test_org = Organization(
            org_id="test-org-001",
            org_code="test",
            name="Test Organization",
            subdomain="test",
            admin_email="admin@test.com",
            domain="test.com",
            is_active=True
        )
        
        # 테스트용 사용자 생성
        self.test_user = User(
            user_id="test_user",
            user_uuid="test-user-uuid",
            email="test@test.com",
            username="Test User",
            hashed_password="hashed_password",
            org_id="test-org-001",
            role="admin",
            is_active=True
        )
        
        self.admin_user = User(
            id=2,
            user_uuid="admin-user-uuid",
            email="admin@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role="admin",
            is_active=True
        )

    def test_default_rate_limits_configuration(self):
        """기본 속도 제한 설정 테스트"""
        # 기본 설정이 올바르게 로드되는지 확인
        assert self.rate_limit_service.rate_limits["ip"]["requests"] == 1000
        assert self.rate_limit_service.rate_limits["ip"]["window"] == 3600
        
        assert self.rate_limit_service.rate_limits["user"]["requests"] == 500
        assert self.rate_limit_service.rate_limits["user"]["window"] == 3600
        
        assert self.rate_limit_service.rate_limits["organization"]["requests"] == 5000
        assert self.rate_limit_service.rate_limits["organization"]["window"] == 3600

    def test_extract_client_info_with_user(self):
        """사용자 정보가 있는 클라이언트 정보 추출 테스트"""
        # Mock 요청 객체 생성
        mock_request = Mock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "TestAgent/1.0"}
        mock_request.state.current_user = self.test_user
        mock_request.state.current_organization = self.test_org
        
        client_info = self.rate_limit_service._extract_client_info(mock_request)
        
        assert client_info["ip"] == "192.168.1.100"
        assert client_info["user_agent"] == "TestAgent/1.0"
        assert client_info["user_id"] == 1
        assert client_info["organization_id"] == 1

    def test_extract_client_info_without_user(self):
        """사용자 정보가 없는 클라이언트 정보 추출 테스트"""
        # Mock 요청 객체 생성 (인증되지 않은 사용자)
        mock_request = Mock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "TestAgent/1.0"}
        mock_request.state.current_user = None
        mock_request.state.current_organization = None
        
        client_info = self.rate_limit_service._extract_client_info(mock_request)
        
        assert client_info["ip"] == "192.168.1.100"
        assert client_info["user_agent"] == "TestAgent/1.0"
        assert client_info["user_id"] is None
        assert client_info["organization_id"] is None

    def test_check_rate_limits_within_limit(self):
        """속도 제한 내 요청 테스트"""
        # Redis에서 현재 카운트가 제한보다 낮게 설정
        self.mock_redis.get.return_value = b"50"  # 현재 50개 요청
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/test"
        
        is_allowed, limits_info = self.rate_limit_service._check_rate_limits(
            client_info, endpoint
        )
        
        assert is_allowed is True
        assert limits_info is not None
        assert "ip" in limits_info
        assert "user" in limits_info
        assert "organization" in limits_info

    def test_check_rate_limits_ip_exceeded(self):
        """IP 속도 제한 초과 테스트"""
        # Redis에서 IP 카운트가 제한을 초과하도록 설정
        def mock_get(key):
            if "ip:192.168.1.100" in key:
                return b"1001"  # IP 제한 초과
            return b"50"
        
        self.mock_redis.get.side_effect = mock_get
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/test"
        
        is_allowed, limits_info = self.rate_limit_service._check_rate_limits(
            client_info, endpoint
        )
        
        assert is_allowed is False
        assert limits_info["ip"]["exceeded"] is True

    def test_check_rate_limits_user_exceeded(self):
        """사용자 속도 제한 초과 테스트"""
        # Redis에서 사용자 카운트가 제한을 초과하도록 설정
        def mock_get(key):
            if "user:1" in key:
                return b"501"  # 사용자 제한 초과
            return b"50"
        
        self.mock_redis.get.side_effect = mock_get
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/test"
        
        is_allowed, limits_info = self.rate_limit_service._check_rate_limits(
            client_info, endpoint
        )
        
        assert is_allowed is False
        assert limits_info["user"]["exceeded"] is True

    def test_check_rate_limits_organization_exceeded(self):
        """조직 속도 제한 초과 테스트"""
        # Redis에서 조직 카운트가 제한을 초과하도록 설정
        def mock_get(key):
            if "org:1" in key:
                return b"5001"  # 조직 제한 초과
            return b"50"
        
        self.mock_redis.get.side_effect = mock_get
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/test"
        
        is_allowed, limits_info = self.rate_limit_service._check_rate_limits(
            client_info, endpoint
        )
        
        assert is_allowed is False
        assert limits_info["organization"]["exceeded"] is True

    def test_check_rate_limits_endpoint_specific(self):
        """엔드포인트별 속도 제한 테스트"""
        # 특정 엔드포인트에 대한 제한 설정
        self.rate_limit_service.rate_limits["endpoints"] = {
            "/api/mail/send": {"requests": 10, "window": 60}
        }
        
        # Redis에서 엔드포인트 카운트가 제한을 초과하도록 설정
        def mock_get(key):
            if "endpoint:/api/mail/send" in key:
                return b"11"  # 엔드포인트 제한 초과
            return b"50"
        
        self.mock_redis.get.side_effect = mock_get
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/mail/send"
        
        is_allowed, limits_info = self.rate_limit_service._check_rate_limits(
            client_info, endpoint
        )
        
        assert is_allowed is False
        assert limits_info["endpoint"]["exceeded"] is True

    def test_increment_counters(self):
        """카운터 증가 테스트"""
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        endpoint = "/api/test"
        
        self.rate_limit_service._increment_counters(client_info, endpoint)
        
        # Redis incr 메서드가 호출되었는지 확인
        assert self.mock_redis.incr.call_count >= 3  # IP, 사용자, 조직 카운터
        assert self.mock_redis.expire.call_count >= 3  # 만료 시간 설정

    def test_get_rate_limit_status(self):
        """속도 제한 상태 조회 테스트"""
        # Redis에서 현재 카운트 반환 설정
        def mock_get(key):
            if "ip:" in key:
                return b"100"
            elif "user:" in key:
                return b"50"
            elif "org:" in key:
                return b"200"
            return b"0"
        
        self.mock_redis.get.side_effect = mock_get
        
        status = self.rate_limit_service.get_rate_limit_status(
            ip="192.168.1.100",
            user_id=1,
            organization_id=1,
            endpoint="/api/test"
        )
        
        assert status["ip"]["current"] == 100
        assert status["ip"]["limit"] == 1000
        assert status["user"]["current"] == 50
        assert status["user"]["limit"] == 500
        assert status["organization"]["current"] == 200
        assert status["organization"]["limit"] == 5000

    def test_reset_rate_limit_ip(self):
        """IP 속도 제한 리셋 테스트"""
        result = self.rate_limit_service.reset_rate_limit(
            target_type="ip",
            target_value="192.168.1.100"
        )
        
        assert result["success"] is True
        assert "IP 192.168.1.100의 속도 제한이 리셋되었습니다" in result["message"]
        
        # Redis delete 메서드가 호출되었는지 확인
        self.mock_redis.delete.assert_called()

    def test_reset_rate_limit_user(self):
        """사용자 속도 제한 리셋 테스트"""
        result = self.rate_limit_service.reset_rate_limit(
            target_type="user",
            target_value="1"
        )
        
        assert result["success"] is True
        assert "사용자 1의 속도 제한이 리셋되었습니다" in result["message"]

    def test_reset_rate_limit_organization(self):
        """조직 속도 제한 리셋 테스트"""
        result = self.rate_limit_service.reset_rate_limit(
            target_type="organization",
            target_value="1"
        )
        
        assert result["success"] is True
        assert "조직 1의 속도 제한이 리셋되었습니다" in result["message"]

    def test_reset_rate_limit_invalid_type(self):
        """잘못된 타입으로 속도 제한 리셋 테스트"""
        with pytest.raises(ValueError, match="지원하지 않는 대상 타입입니다"):
            self.rate_limit_service.reset_rate_limit(
                target_type="invalid",
                target_value="test"
            )

    @patch('app.middleware.rate_limit_middleware.RateLimitService._get_violation_logs_from_db')
    def test_get_violation_logs(self, mock_get_logs):
        """속도 제한 위반 로그 조회 테스트"""
        # Mock 위반 로그 데이터
        mock_logs = [
            {
                "id": 1,
                "ip": "192.168.1.100",
                "user_id": 1,
                "organization_id": 1,
                "endpoint": "/api/test",
                "violation_type": "ip",
                "timestamp": datetime.now(),
                "user_agent": "TestAgent/1.0"
            }
        ]
        mock_get_logs.return_value = mock_logs
        
        logs = self.rate_limit_service.get_violation_logs(
            limit=10,
            offset=0
        )
        
        assert len(logs) == 1
        assert logs[0]["ip"] == "192.168.1.100"
        assert logs[0]["violation_type"] == "ip"

    @patch('app.middleware.rate_limit_middleware.RateLimitService._save_violation_to_db')
    def test_log_violation(self, mock_save_violation):
        """속도 제한 위반 로깅 테스트"""
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1,
            "user_agent": "TestAgent/1.0"
        }
        endpoint = "/api/test"
        violation_type = "ip"
        
        self.rate_limit_service.log_violation(client_info, endpoint, violation_type)
        
        # 데이터베이스 저장 메서드가 호출되었는지 확인
        mock_save_violation.assert_called_once()
        call_args = mock_save_violation.call_args[0][0]
        assert call_args["ip"] == "192.168.1.100"
        assert call_args["endpoint"] == "/api/test"
        assert call_args["violation_type"] == "ip"

    def test_is_excluded_path_static_files(self):
        """정적 파일 경로 제외 테스트"""
        assert self.rate_limit_service._is_excluded_path("/static/css/style.css") is True
        assert self.rate_limit_service._is_excluded_path("/static/js/app.js") is True
        assert self.rate_limit_service._is_excluded_path("/favicon.ico") is True

    def test_is_excluded_path_health_check(self):
        """헬스 체크 경로 제외 테스트"""
        assert self.rate_limit_service._is_excluded_path("/health") is True
        assert self.rate_limit_service._is_excluded_path("/ping") is True
        assert self.rate_limit_service._is_excluded_path("/status") is True

    def test_is_excluded_path_api_endpoints(self):
        """API 엔드포인트 포함 테스트"""
        assert self.rate_limit_service._is_excluded_path("/api/auth/login") is False
        assert self.rate_limit_service._is_excluded_path("/api/mail/send") is False
        assert self.rate_limit_service._is_excluded_path("/api/users") is False

    def test_create_rate_limit_response(self):
        """속도 제한 응답 생성 테스트"""
        limits_info = {
            "ip": {"exceeded": True, "current": 1001, "limit": 1000, "window": 3600},
            "user": {"exceeded": False, "current": 50, "limit": 500, "window": 3600},
            "organization": {"exceeded": False, "current": 200, "limit": 5000, "window": 3600}
        }
        
        response = self.rate_limit_service._create_rate_limit_response(limits_info)
        
        assert response.status_code == 429
        assert "application/json" in response.headers["content-type"]

    def test_add_rate_limit_headers(self):
        """속도 제한 헤더 추가 테스트"""
        # Mock 응답 객체
        mock_response = Mock()
        mock_response.headers = {}
        
        limits_info = {
            "ip": {"current": 100, "limit": 1000, "window": 3600, "exceeded": False},
            "user": {"current": 50, "limit": 500, "window": 3600, "exceeded": False}
        }
        
        self.rate_limit_service._add_rate_limit_headers(mock_response, limits_info)
        
        # 헤더가 추가되었는지 확인
        assert "X-RateLimit-Limit-IP" in mock_response.headers
        assert "X-RateLimit-Remaining-IP" in mock_response.headers
        assert "X-RateLimit-Limit-User" in mock_response.headers
        assert "X-RateLimit-Remaining-User" in mock_response.headers

    def test_update_rate_limit_config(self):
        """속도 제한 설정 업데이트 테스트"""
        new_config = {
            "ip": {"requests": 2000, "window": 3600},
            "user": {"requests": 1000, "window": 3600}
        }
        
        # 설정 업데이트
        self.rate_limit_service.rate_limits.update(new_config)
        
        assert self.rate_limit_service.rate_limits["ip"]["requests"] == 2000
        assert self.rate_limit_service.rate_limits["user"]["requests"] == 1000

    def test_get_current_config(self):
        """현재 속도 제한 설정 조회 테스트"""
        config = self.rate_limit_service.rate_limits
        
        assert "ip" in config
        assert "user" in config
        assert "organization" in config
        assert config["ip"]["requests"] == 1000
        assert config["user"]["requests"] == 500

    @patch('time.time')
    def test_sliding_window_rate_limiting(self, mock_time):
        """슬라이딩 윈도우 속도 제한 테스트"""
        # 현재 시간 설정
        current_time = 1640995200  # 2022-01-01 00:00:00
        mock_time.return_value = current_time
        
        # Redis에서 시간별 카운트 반환 설정
        def mock_get(key):
            if "sliding:" in key:
                return b"100"
            return b"50"
        
        self.mock_redis.get.side_effect = mock_get
        
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        
        # 슬라이딩 윈도우 체크 (구현되어 있다면)
        is_allowed, _ = self.rate_limit_service._check_rate_limits(
            client_info, "/api/test"
        )
        
        # 기본적으로는 허용되어야 함
        assert is_allowed is True

    def test_burst_protection(self):
        """버스트 보호 테스트"""
        client_info = {
            "ip": "192.168.1.100",
            "user_id": 1,
            "organization_id": 1
        }
        
        # 짧은 시간 내 많은 요청 시뮬레이션
        for i in range(10):
            # Redis에서 증가하는 카운트 시뮬레이션
            self.mock_redis.get.return_value = str(i + 1).encode()
            
            is_allowed, _ = self.rate_limit_service._check_rate_limits(
                client_info, "/api/test"
            )
            
            # 처음 몇 개 요청은 허용되어야 함
            if i < 5:
                assert is_allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])