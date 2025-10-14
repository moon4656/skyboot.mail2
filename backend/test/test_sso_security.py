"""
SSO (Single Sign-On) 보안 기능 테스트

이 모듈은 SSO 관련 모든 기능을 테스트합니다:
- OAuth 인증 URL 생성
- 인증 코드 교환
- 사용자 정보 조회
- SSO 사용자 생성/매칭
- Google/Microsoft 프로바이더 지원
"""

import pytest
import jwt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.service.sso_service import SSOService
from app.model.user_model import User
from app.model.organization_model import Organization
from app.schemas.auth_schema import SSOLoginRequest


class TestSSOService:
    """SSO 서비스 테스트 클래스"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.sso_service = SSOService()
        
        # 테스트용 조직 생성
        self.test_org = Organization(
            id=1,
            org_uuid="test-org-uuid",
            name="Test Organization",
            domain="test.com"
        )
        
        # 테스트용 사용자 생성
        self.test_user = User(
            id=1,
            user_uuid="test-user-uuid",
            email="test@test.com",
            password_hash="hashed_password",
            organization_id=1,
            is_active=True
        )

    def test_generate_state_parameter(self):
        """SSO 상태 파라미터 생성 테스트"""
        organization_id = 1
        redirect_url = "https://example.com/callback"
        
        state = self.sso_service.generate_state_parameter(organization_id, redirect_url)
        
        # 상태 파라미터가 생성되었는지 확인
        assert state is not None
        assert len(state) > 0
        
        # JWT 토큰 형태인지 확인
        try:
            decoded = jwt.decode(state, options={"verify_signature": False})
            assert "org_id" in decoded
            assert "redirect_url" in decoded
            assert "exp" in decoded
            assert decoded["org_id"] == organization_id
            assert decoded["redirect_url"] == redirect_url
        except jwt.InvalidTokenError:
            pytest.fail("상태 파라미터가 올바른 JWT 형식이 아닙니다")

    def test_verify_state_parameter_valid(self):
        """유효한 SSO 상태 파라미터 검증 테스트"""
        organization_id = 1
        redirect_url = "https://example.com/callback"
        
        # 상태 파라미터 생성
        state = self.sso_service.generate_state_parameter(organization_id, redirect_url)
        
        # 상태 파라미터 검증
        result = self.sso_service.verify_state_parameter(state)
        
        assert result is not None
        assert result["org_id"] == organization_id
        assert result["redirect_url"] == redirect_url

    def test_verify_state_parameter_expired(self):
        """만료된 SSO 상태 파라미터 검증 테스트"""
        # 만료된 토큰 생성 (과거 시간으로 설정)
        expired_payload = {
            "org_id": 1,
            "redirect_url": "https://example.com/callback",
            "exp": datetime.utcnow() - timedelta(hours=1)  # 1시간 전 만료
        }
        expired_state = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        
        # 만료된 상태 파라미터 검증
        result = self.sso_service.verify_state_parameter(expired_state)
        
        assert result is None

    def test_verify_state_parameter_invalid(self):
        """잘못된 SSO 상태 파라미터 검증 테스트"""
        invalid_state = "invalid_jwt_token"
        
        result = self.sso_service.verify_state_parameter(invalid_state)
        
        assert result is None

    def test_create_auth_url_google(self):
        """Google OAuth 인증 URL 생성 테스트"""
        provider = "google"
        organization_id = 1
        redirect_url = "https://example.com/callback"
        
        auth_url = self.sso_service.create_auth_url(provider, organization_id, redirect_url)
        
        # URL이 생성되었는지 확인
        assert auth_url is not None
        assert "https://accounts.google.com/o/oauth2/auth" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=" in auth_url
        assert "state=" in auth_url
        assert "response_type=code" in auth_url

    def test_create_auth_url_microsoft(self):
        """Microsoft OAuth 인증 URL 생성 테스트"""
        provider = "microsoft"
        organization_id = 1
        redirect_url = "https://example.com/callback"
        
        auth_url = self.sso_service.create_auth_url(provider, organization_id, redirect_url)
        
        # URL이 생성되었는지 확인
        assert auth_url is not None
        assert "https://login.microsoftonline.com" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=" in auth_url
        assert "state=" in auth_url
        assert "response_type=code" in auth_url

    def test_create_auth_url_unsupported_provider(self):
        """지원하지 않는 프로바이더 테스트"""
        provider = "unsupported"
        organization_id = 1
        redirect_url = "https://example.com/callback"
        
        with pytest.raises(ValueError, match="지원하지 않는 SSO 프로바이더입니다"):
            self.sso_service.create_auth_url(provider, organization_id, redirect_url)

    @patch('requests.post')
    def test_exchange_code_for_token_google_success(self, mock_post):
        """Google OAuth 코드 교환 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token"
        }
        mock_post.return_value = mock_response
        
        provider = "google"
        code = "test_auth_code"
        redirect_uri = "https://example.com/callback"
        
        result = self.sso_service.exchange_code_for_token(provider, code, redirect_uri)
        
        # 결과 검증
        assert result is not None
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "Bearer"
        
        # API 호출 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://oauth2.googleapis.com/token" in call_args[1]["url"]

    @patch('requests.post')
    def test_exchange_code_for_token_microsoft_success(self, mock_post):
        """Microsoft OAuth 코드 교환 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token"
        }
        mock_post.return_value = mock_response
        
        provider = "microsoft"
        code = "test_auth_code"
        redirect_uri = "https://example.com/callback"
        
        result = self.sso_service.exchange_code_for_token(provider, code, redirect_uri)
        
        # 결과 검증
        assert result is not None
        assert result["access_token"] == "test_access_token"
        
        # API 호출 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://login.microsoftonline.com" in call_args[1]["url"]

    @patch('requests.post')
    def test_exchange_code_for_token_failure(self, mock_post):
        """OAuth 코드 교환 실패 테스트"""
        # Mock 응답 설정 (에러)
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }
        mock_post.return_value = mock_response
        
        provider = "google"
        code = "invalid_code"
        redirect_uri = "https://example.com/callback"
        
        result = self.sso_service.exchange_code_for_token(provider, code, redirect_uri)
        
        # 결과 검증 (실패 시 None 반환)
        assert result is None

    @patch('requests.get')
    def test_get_user_info_google_success(self, mock_get):
        """Google 사용자 정보 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "google_user_id",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "verified_email": True
        }
        mock_get.return_value = mock_response
        
        provider = "google"
        access_token = "test_access_token"
        
        result = self.sso_service.get_user_info(provider, access_token)
        
        # 결과 검증
        assert result is not None
        assert result["id"] == "google_user_id"
        assert result["email"] == "test@gmail.com"
        assert result["name"] == "Test User"
        
        # API 호출 검증
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://www.googleapis.com/oauth2/v2/userinfo" in call_args[1]["url"]

    @patch('requests.get')
    def test_get_user_info_microsoft_success(self, mock_get):
        """Microsoft 사용자 정보 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "microsoft_user_id",
            "mail": "test@outlook.com",
            "displayName": "Test User",
            "userPrincipalName": "test@outlook.com"
        }
        mock_get.return_value = mock_response
        
        provider = "microsoft"
        access_token = "test_access_token"
        
        result = self.sso_service.get_user_info(provider, access_token)
        
        # 결과 검증
        assert result is not None
        assert result["id"] == "microsoft_user_id"
        assert result["email"] == "test@outlook.com"
        assert result["name"] == "Test User"
        
        # API 호출 검증
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://graph.microsoft.com/v1.0/me" in call_args[1]["url"]

    @patch('requests.get')
    def test_get_user_info_failure(self, mock_get):
        """사용자 정보 조회 실패 테스트"""
        # Mock 응답 설정 (에러)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_token"
        }
        mock_get.return_value = mock_response
        
        provider = "google"
        access_token = "invalid_token"
        
        result = self.sso_service.get_user_info(provider, access_token)
        
        # 결과 검증 (실패 시 None 반환)
        assert result is None

    @patch('app.service.sso_service.SSOService._get_user_by_email')
    @patch('app.service.sso_service.SSOService._create_sso_user')
    def test_find_or_create_user_existing(self, mock_create_user, mock_get_user):
        """기존 사용자 찾기 테스트"""
        # 기존 사용자 반환 설정
        mock_get_user.return_value = self.test_user
        
        sso_user_info = {
            "id": "sso_user_id",
            "email": "test@test.com",
            "name": "Test User"
        }
        provider = "google"
        organization_id = 1
        
        result = self.sso_service.find_or_create_user(sso_user_info, provider, organization_id)
        
        # 결과 검증
        assert result == self.test_user
        
        # 기존 사용자를 찾았으므로 새 사용자 생성하지 않음
        mock_get_user.assert_called_once_with("test@test.com", organization_id)
        mock_create_user.assert_not_called()

    @patch('app.service.sso_service.SSOService._get_user_by_email')
    @patch('app.service.sso_service.SSOService._create_sso_user')
    def test_find_or_create_user_new(self, mock_create_user, mock_get_user):
        """새 사용자 생성 테스트"""
        # 기존 사용자 없음
        mock_get_user.return_value = None
        # 새 사용자 생성 반환
        mock_create_user.return_value = self.test_user
        
        sso_user_info = {
            "id": "sso_user_id",
            "email": "newuser@test.com",
            "name": "New User"
        }
        provider = "google"
        organization_id = 1
        
        result = self.sso_service.find_or_create_user(sso_user_info, provider, organization_id)
        
        # 결과 검증
        assert result == self.test_user
        
        # 새 사용자 생성 호출 확인
        mock_get_user.assert_called_once_with("newuser@test.com", organization_id)
        mock_create_user.assert_called_once_with(sso_user_info, provider, organization_id)

    @patch('app.service.sso_service.SSOService._get_organization_by_id')
    def test_find_or_create_user_invalid_organization(self, mock_get_org):
        """잘못된 조직 ID 테스트"""
        # 조직 없음
        mock_get_org.return_value = None
        
        sso_user_info = {
            "id": "sso_user_id",
            "email": "test@test.com",
            "name": "Test User"
        }
        provider = "google"
        organization_id = 999  # 존재하지 않는 조직
        
        with pytest.raises(ValueError, match="유효하지 않은 조직입니다"):
            self.sso_service.find_or_create_user(sso_user_info, provider, organization_id)

    def test_validate_sso_user_info_valid(self):
        """유효한 SSO 사용자 정보 검증 테스트"""
        valid_user_info = {
            "id": "sso_user_id",
            "email": "test@test.com",
            "name": "Test User"
        }
        
        # 예외가 발생하지 않아야 함
        try:
            self.sso_service._validate_sso_user_info(valid_user_info)
        except ValueError:
            pytest.fail("유효한 사용자 정보에서 예외가 발생했습니다")

    def test_validate_sso_user_info_missing_id(self):
        """SSO 사용자 ID 누락 테스트"""
        invalid_user_info = {
            "email": "test@test.com",
            "name": "Test User"
        }
        
        with pytest.raises(ValueError, match="SSO 사용자 ID가 필요합니다"):
            self.sso_service._validate_sso_user_info(invalid_user_info)

    def test_validate_sso_user_info_missing_email(self):
        """SSO 사용자 이메일 누락 테스트"""
        invalid_user_info = {
            "id": "sso_user_id",
            "name": "Test User"
        }
        
        with pytest.raises(ValueError, match="SSO 사용자 이메일이 필요합니다"):
            self.sso_service._validate_sso_user_info(invalid_user_info)

    def test_validate_sso_user_info_invalid_email(self):
        """잘못된 SSO 사용자 이메일 형식 테스트"""
        invalid_user_info = {
            "id": "sso_user_id",
            "email": "invalid_email",
            "name": "Test User"
        }
        
        with pytest.raises(ValueError, match="유효하지 않은 이메일 형식입니다"):
            self.sso_service._validate_sso_user_info(invalid_user_info)

    def test_normalize_user_info_google(self):
        """Google 사용자 정보 정규화 테스트"""
        google_user_info = {
            "id": "google_user_id",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "verified_email": True
        }
        
        normalized = self.sso_service._normalize_user_info(google_user_info, "google")
        
        assert normalized["id"] == "google_user_id"
        assert normalized["email"] == "test@gmail.com"
        assert normalized["name"] == "Test User"
        assert normalized["avatar_url"] == "https://example.com/avatar.jpg"

    def test_normalize_user_info_microsoft(self):
        """Microsoft 사용자 정보 정규화 테스트"""
        microsoft_user_info = {
            "id": "microsoft_user_id",
            "mail": "test@outlook.com",
            "displayName": "Test User",
            "userPrincipalName": "test@outlook.com"
        }
        
        normalized = self.sso_service._normalize_user_info(microsoft_user_info, "microsoft")
        
        assert normalized["id"] == "microsoft_user_id"
        assert normalized["email"] == "test@outlook.com"
        assert normalized["name"] == "Test User"

    def test_normalize_user_info_unsupported_provider(self):
        """지원하지 않는 프로바이더 정규화 테스트"""
        user_info = {"id": "test", "email": "test@test.com"}
        
        with pytest.raises(ValueError, match="지원하지 않는 SSO 프로바이더입니다"):
            self.sso_service._normalize_user_info(user_info, "unsupported")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])