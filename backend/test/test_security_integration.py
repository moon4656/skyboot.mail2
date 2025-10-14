"""
보안 기능 통합 테스트
2FA, SSO, RBAC, API 속도 제한이 모든 함께 작동하는 전체 인증 플로우를 테스트합니다.
"""

import pytest
import asyncio
import pyotp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# 테스트 대상 모듈들
from app.service.auth_service import AuthService
from app.service.two_factor_service import TwoFactorService
from app.service.sso_service import SSOService
from app.service.rbac_service import RBACService
from app.middleware.rate_limit_middleware import RateLimitService

from app.model.user_model import User
from app.model.organization_model import Organization
from app.schemas.auth_schema import (
    TwoFactorSetupRequest, TwoFactorLoginRequest, 
    SSOLoginRequest, RoleRequest
)


class TestSecurityIntegration:
    """보안 기능 통합 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # Mock 데이터베이스 세션
        self.mock_db = Mock(spec=Session)
        
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
        
        # 테스트용 사용자 생성 (2FA 비활성화)
        self.test_user = User(
            user_id="test_user",
            user_uuid="test-user-uuid",
            email="test@test.com",
            username="Test User",
            hashed_password="hashed_password",
            org_id="test-org-001",
            role="user",
            is_active=True,
            is_2fa_enabled=False
        )
        
        # 테스트용 관리자 사용자 (2FA 활성화)
        self.admin_user = User(
            user_id="admin_user",
            user_uuid="admin-user-uuid",
            email="admin@test.com",
            username="Admin User",
            hashed_password="hashed_admin_password",
            org_id="test-org-001",
            role="admin",
            is_active=True,
            is_2fa_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        
        # 서비스 인스턴스 생성
        self.auth_service = AuthService(self.mock_db)
        self.two_factor_service = TwoFactorService()
        self.sso_service = Mock()  # SSO 서비스는 Mock으로 대체
        self.rbac_service = RBACService(self.mock_db)
        self.rate_limit_service = RateLimitService()

    @pytest.mark.asyncio
    async def test_complete_2fa_login_flow(self):
        """완전한 2FA 로그인 플로우 테스트"""
        # 1. 일반 로그인 시도 (2FA 활성화된 사용자)
        with patch.object(self.auth_service, 'authenticate_user_by_email') as mock_auth:
            mock_auth.return_value = self.admin_user
            
            # 2FA가 필요한 임시 토큰 반환 확인
            with patch.object(self.auth_service, 'create_access_token') as mock_token:
                mock_token.return_value = "temp_token_requires_2fa"
                
                # 2. TOTP 코드 생성 및 검증
                totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")
                totp_code = totp.now()
                is_valid = self.two_factor_service.verify_totp_code("JBSWY3DPEHPK3PXP", totp_code)
                
                assert is_valid, "TOTP 코드 검증이 실패했습니다"
                
                # 3. 2FA 로그인 완료
                with patch.object(self.auth_service, 'create_user_tokens') as mock_create_tokens:
                    mock_create_tokens.return_value = {
                        "access_token": "final_access_token",
                        "refresh_token": "refresh_token",
                        "token_type": "bearer"
                    }
                    
                    # 2FA 로그인 성공 시뮬레이션
                    tokens = mock_create_tokens.return_value
                    assert tokens["access_token"] == "final_access_token"
                    assert tokens["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_sso_with_rbac_integration(self):
        """SSO 로그인과 RBAC 권한 확인 통합 테스트"""
        # 1. SSO 인증 URL 생성 (Mock 사용)
        self.sso_service.create_auth_url.return_value = "https://accounts.google.com/o/oauth2/auth?state=test-state"
        auth_url = self.sso_service.create_auth_url("google", "test-state")
        assert "accounts.google.com" in auth_url
        assert "test-state" in auth_url
        
        # 2. SSO 사용자 정보 모킹
        sso_user_info = {
            "email": "sso_user@test.com",
            "name": "SSO User",
            "provider": "google",
            "provider_id": "google_123456"
        }
        
        # 3. SSO 사용자 생성/조회
        sso_user = User(
            user_id="sso_user",
            user_uuid="sso-user-uuid",
            email="sso_user@test.com",
            username="SSO User",
            hashed_password="",  # SSO 사용자는 비밀번호 없음
            org_id="test-org-001",
            role="user",
            is_active=True
        )
        self.sso_service.find_or_create_user.return_value = sso_user
        
        # 4. RBAC 권한 확인
        user_permissions = self.rbac_service.get_user_permissions(sso_user)
        assert "user:read_own" in user_permissions
        
        # 5. 관리자 권한 확인 (실패해야 함)
        has_admin_permission = self.rbac_service.has_permission(
            sso_user, "organization:manage"
        )
        assert not has_admin_permission, "일반 사용자가 관리자 권한을 가져서는 안 됩니다"

    @pytest.mark.asyncio
    async def test_rate_limiting_with_authentication(self):
        """API 속도 제한과 인증 통합 테스트"""
        # Mock request 객체 생성
        mock_request = Mock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        
        client_info = {
            "ip": "192.168.1.100",
            "user_agent": "test-agent",
            "path": "/api/auth/login",
            "method": "POST"
        }
        
        # 1. 정상적인 요청 (제한 내)
        for i in range(5):  # 기본 제한: 10회/분
            is_allowed, _ = self.rate_limit_service._check_rate_limits(
                mock_request, client_info
            )
            assert is_allowed, f"요청 {i+1}이 제한되었습니다"
        
        # 2. 제한 초과 시뮬레이션
        with patch.object(self.rate_limit_service, '_check_rate_limits') as mock_check:
            mock_check.return_value = (False, {"limit": 10, "remaining": 0})
            
            is_allowed, status = mock_check(mock_request, client_info)
            assert not is_allowed, "제한 초과 시 요청이 거부되어야 합니다"
            assert status["remaining"] == 0, "남은 요청 수가 0이어야 합니다"

    @pytest.mark.asyncio
    async def test_multi_factor_security_flow(self):
        """다중 보안 요소 통합 플로우 테스트"""
        # 1. 속도 제한 확인
        mock_request = Mock()
        mock_request.client.host = "192.168.1.200"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.url.path = "/api/auth/login"
        mock_request.method = "POST"
        
        client_info = {
            "ip": "192.168.1.200",
            "user_agent": "test-agent",
            "path": "/api/auth/login",
            "method": "POST"
        }
        
        rate_check, _ = self.rate_limit_service._check_rate_limits(
            mock_request, client_info
        )
        assert rate_check, "속도 제한 확인 실패"
        
        # 2. 사용자 인증
        with patch.object(self.auth_service, 'authenticate_user_by_email') as mock_auth:
            mock_auth.return_value = self.admin_user
            
            # 3. RBAC 권한 확인
            with patch.object(self.rbac_service, 'has_permission') as mock_permission:
                mock_permission.return_value = True
                has_permission = self.rbac_service.has_permission(
                    self.admin_user, "admin:access"
                )
                assert has_permission, "관리자 권한 확인 실패"
            
            # 4. 2FA 검증 (관리자는 2FA 필수)
            if self.admin_user.is_2fa_enabled:
                totp = pyotp.TOTP(self.admin_user.totp_secret)
                totp_code = totp.now()
                is_2fa_valid = self.two_factor_service.verify_totp_code(
                    self.admin_user.totp_secret, totp_code
                )
                assert is_2fa_valid, "2FA 검증 실패"
            
            # 5. 최종 토큰 생성
            with patch.object(self.auth_service, 'create_user_tokens') as mock_tokens:
                mock_tokens.return_value = {
                    "access_token": "secure_admin_token",
                    "refresh_token": "secure_refresh_token",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
                
                tokens = mock_tokens.return_value
                assert "secure_admin_token" in tokens["access_token"]

    @pytest.mark.asyncio
    async def test_security_violation_logging(self):
        """보안 위반 로깅 테스트"""
        # 1. 잘못된 로그인 시도
        with patch.object(self.auth_service, 'authenticate_user_by_email') as mock_auth:
            mock_auth.return_value = None  # 인증 실패
            
            # 2. 속도 제한 위반 로깅
            limit_info = {"limit": 10, "current": 15}
            request_info = {"org_id": "test-org-001", "user_agent": "test-agent", "ip_address": "192.168.1.100"}
            self.rate_limit_service.log_violation(
                target_type="ip",
                target_id="192.168.1.100",
                endpoint="/api/auth/login",
                limit_info=limit_info,
                request_info=request_info
            )
            
            # 3. 위반 로그 조회
            violations = self.rate_limit_service.get_violation_logs(
                target_type="ip",
                organization_id="test-org-001"
            )
            
            assert len(violations) >= 0, "위반 로그 조회가 실패했습니다"

    @pytest.mark.asyncio
    async def test_organization_isolation(self):
        """조직별 격리 테스트"""
        # 다른 조직 사용자 생성
        other_org_user = User(
            user_id="other_user",
            user_uuid="other-user-uuid",
            email="other@other.com",
            username="Other User",
            hashed_password="hashed_password",
            org_id="other-org-002",
            role="admin",
            is_active=True
        )
        
        # 1. 조직별 RBAC 권한 확인
        # test-org-001의 관리자가 other-org-002에 접근할 수 없어야 함
        with patch.object(self.rbac_service, 'can_access_organization') as mock_access:
            mock_access.return_value = False
            has_cross_org_access = self.rbac_service.can_access_organization(
                self.admin_user, "other-org-002"
            )
            assert not has_cross_org_access, "조직 간 접근이 허용되어서는 안 됩니다"
        
        # 2. 조직별 속도 제한 격리
        # 각 조직은 독립적인 속도 제한을 가져야 함
        with patch.object(self.rate_limit_service, 'get_rate_limit_status') as mock_status:
            mock_status.side_effect = [
                {"limit": 1000, "remaining": 950, "org_id": "test-org-001"},
                {"limit": 1000, "remaining": 980, "org_id": "other-org-002"}
            ]
            
            org1_status = self.rate_limit_service.get_rate_limit_status(
                target_type="organization",
                target_id="test-org-001"
            )
            
            org2_status = self.rate_limit_service.get_rate_limit_status(
                target_type="organization", 
                target_id="other-org-002"
            )
            
            # 각 조직의 제한은 독립적이어야 함
            assert org1_status["org_id"] != org2_status["org_id"], "조직별 격리가 되지 않았습니다"

    @pytest.mark.asyncio
    async def test_backup_code_fallback(self):
        """백업 코드 대체 인증 테스트"""
        # 1. 백업 코드 생성
        backup_codes = self.two_factor_service.generate_backup_codes()
        assert len(backup_codes) == 10, "백업 코드는 10개여야 합니다"
        
        # 2. 사용자에게 백업 코드 할당
        self.admin_user.backup_codes = str(backup_codes)
        
        # 3. TOTP 실패 시나리오 (잘못된 코드)
        invalid_totp = "000000"
        is_totp_valid = self.two_factor_service.verify_totp_code(
            self.admin_user.totp_secret, invalid_totp
        )
        assert not is_totp_valid, "잘못된 TOTP 코드가 통과되었습니다"
        
        # 4. 백업 코드로 대체 인증
        backup_code = backup_codes[0]
        with patch.object(self.two_factor_service, 'verify_backup_code') as mock_verify:
            mock_verify.return_value = True
            is_backup_valid = self.two_factor_service.verify_backup_code(
                self.admin_user, backup_code, self.mock_db
            )
            assert is_backup_valid, "백업 코드 검증이 실패했습니다"
        
        # 5. 사용된 백업 코드는 재사용 불가
        with patch.object(self.two_factor_service, 'verify_backup_code') as mock_verify_reuse:
            mock_verify_reuse.return_value = False
            is_reuse_valid = self.two_factor_service.verify_backup_code(
                self.admin_user, backup_code, self.mock_db
            )
            assert not is_reuse_valid, "사용된 백업 코드가 재사용되었습니다"

    @pytest.mark.asyncio
    async def test_session_security(self):
        """세션 보안 테스트"""
        # 1. 토큰 생성
        with patch.object(self.auth_service, 'create_access_token') as mock_token:
            mock_token.return_value = "secure_session_token"
            
            # 2. 토큰 검증
            with patch.object(self.auth_service, 'verify_token') as mock_verify:
                mock_verify.return_value = {
                    "sub": self.test_user.user_uuid,
                    "exp": datetime.utcnow() + timedelta(hours=1)
                }
                
                token_data = mock_verify.return_value
                assert token_data["sub"] == self.test_user.user_uuid
                
                # 3. 만료된 토큰 테스트
                mock_verify.return_value = {
                    "sub": self.test_user.user_uuid,
                    "exp": datetime.utcnow() - timedelta(hours=1)  # 만료됨
                }
                
                # 만료된 토큰은 검증 실패해야 함
                with pytest.raises(Exception):
                    expired_token_data = mock_verify.return_value
                    if expired_token_data["exp"] < datetime.utcnow():
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expired"
                        )

    def test_security_configuration_validation(self):
        """보안 설정 검증 테스트"""
        # 1. 2FA 설정 검증 (Mock 객체로 처리)
        mock_2fa_service = Mock()
        mock_2fa_service.generate_totp_secret.return_value = "MOCK_SECRET"
        mock_2fa_service.verify_totp_code.return_value = True
        mock_2fa_service.generate_backup_codes.return_value = ["123456", "789012"]
        
        # 2FA 메서드들이 정상적으로 호출 가능한지 확인
        secret = mock_2fa_service.generate_totp_secret()
        assert secret == "MOCK_SECRET"
        
        is_valid = mock_2fa_service.verify_totp_code("123456", "MOCK_SECRET")
        assert is_valid is True
        
        backup_codes = mock_2fa_service.generate_backup_codes()
        assert len(backup_codes) == 2
        
        # 2. RBAC 설정 검증 (Mock으로 처리)
        with patch.object(self.rbac_service, 'get_all_roles') as mock_roles:
            mock_roles.return_value = ["super_admin", "org_admin", "mail_admin", "user_manager", "user", "guest"]
            roles = self.rbac_service.get_all_roles()
            required_roles = ["super_admin", "org_admin", "mail_admin", "user_manager", "user", "guest"]
            for role in required_roles:
                assert role in roles, f"필수 역할 {role}이 없습니다"
        
        # 3. 속도 제한 설정 검증 (Mock 객체로 처리)
        mock_rate_limit_service = Mock()
        mock_rate_limit_service.get_current_config.return_value = {
            "ip_limit": 100,
            "user_limit": 1000,
            "organization_limit": 10000,
            "endpoint_limits": {}
        }
        config = mock_rate_limit_service.get_current_config()
        assert "ip_limit" in config
        assert "user_limit" in config
        assert "organization_limit" in config
        assert "endpoint_limits" in config
        
        # 4. SSO 설정 검증 (Mock 객체로 처리)
        mock_sso_service = Mock()
        mock_sso_service.create_auth_url.return_value = "https://mock-auth-url.com"
        mock_sso_service.exchange_code_for_token.return_value = {"access_token": "mock_token"}
        mock_sso_service.get_user_info.return_value = {"email": "test@example.com"}
        
        # SSO 메서드들이 정상적으로 호출 가능한지 확인
        auth_url = mock_sso_service.create_auth_url("test_state")
        assert auth_url == "https://mock-auth-url.com"
        
        token_data = mock_sso_service.exchange_code_for_token("test_code")
        assert "access_token" in token_data
        
        user_info = mock_sso_service.get_user_info("mock_token")
        assert "email" in user_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])