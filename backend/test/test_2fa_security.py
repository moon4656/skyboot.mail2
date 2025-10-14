"""
2FA (Two-Factor Authentication) 보안 기능 테스트

이 모듈은 2FA 관련 모든 기능을 테스트합니다:
- TOTP 시크릿 생성 및 검증
- 백업 코드 생성 및 사용
- QR 코드 생성
- 2FA 설정/해제
- 2FA 로그인 플로우
"""

import pytest
import pyotp
import qrcode
from io import BytesIO
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.service.two_factor_service import TwoFactorService
from app.service.auth_service import AuthService
from app.model.user_model import User
from app.model.organization_model import Organization
from app.schemas.auth_schema import (
    TwoFactorSetupRequest,
    TwoFactorVerifyRequest,
    TwoFactorLoginRequest,
    TwoFactorDisableRequest
)


class TestTwoFactorService:
    """2FA 서비스 테스트 클래스"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.two_factor_service = TwoFactorService()
        self.auth_service = Mock(spec=AuthService)
        
        # 테스트용 사용자 생성
        self.test_user = User(
            id=1,
            user_uuid="test-user-uuid",
            email="test@example.com",
            password_hash="hashed_password",
            organization_id=1,
            is_2fa_enabled=False,
            totp_secret=None,
            backup_codes=None
        )
        
        # 테스트용 조직 생성
        self.test_org = Organization(
            id=1,
            org_uuid="test-org-uuid",
            name="Test Organization",
            domain="test.com"
        )

    def test_generate_totp_secret(self):
        """TOTP 시크릿 생성 테스트"""
        secret = self.two_factor_service.generate_totp_secret()
        
        # 시크릿이 32자리 Base32 문자열인지 확인
        assert len(secret) == 32
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in secret)
        
        # pyotp로 검증 가능한지 확인
        totp = pyotp.TOTP(secret)
        assert totp.now() is not None

    def test_generate_backup_codes(self):
        """백업 코드 생성 테스트"""
        backup_codes = self.two_factor_service.generate_backup_codes()
        
        # 10개의 백업 코드가 생성되는지 확인
        assert len(backup_codes) == 10
        
        # 각 백업 코드가 8자리 숫자인지 확인
        for code in backup_codes:
            assert len(code) == 8
            assert code.isdigit()
        
        # 모든 백업 코드가 고유한지 확인
        assert len(set(backup_codes)) == 10

    def test_generate_qr_code(self):
        """QR 코드 생성 테스트"""
        secret = "JBSWY3DPEHPK3PXP"
        qr_code_data = self.two_factor_service.generate_qr_code(
            secret=secret,
            user_email="test@example.com",
            issuer_name="SkyBoot Mail"
        )
        
        # QR 코드 데이터가 base64 문자열인지 확인
        assert isinstance(qr_code_data, str)
        assert len(qr_code_data) > 0
        
        # base64 디코딩이 가능한지 확인
        import base64
        try:
            decoded_data = base64.b64decode(qr_code_data)
            assert len(decoded_data) > 0
        except Exception:
            pytest.fail("QR 코드 데이터가 올바른 base64 형식이 아닙니다")

    def test_verify_totp_code_valid(self):
        """유효한 TOTP 코드 검증 테스트"""
        secret = "JBSWY3DPEHPK3PXP"
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        # 현재 시간의 TOTP 코드 검증
        assert self.two_factor_service.verify_totp_code(secret, current_code) is True

    def test_verify_totp_code_invalid(self):
        """잘못된 TOTP 코드 검증 테스트"""
        secret = "JBSWY3DPEHPK3PXP"
        invalid_code = "000000"
        
        # 잘못된 TOTP 코드 검증
        assert self.two_factor_service.verify_totp_code(secret, invalid_code) is False

    def test_verify_totp_code_with_window(self):
        """시간 윈도우를 고려한 TOTP 코드 검증 테스트"""
        secret = "JBSWY3DPEHPK3PXP"
        totp = pyotp.TOTP(secret)
        
        # 이전 시간 슬롯의 코드 생성
        previous_time = datetime.now() - timedelta(seconds=30)
        previous_code = totp.at(previous_time)
        
        # 윈도우 내에서 이전 코드도 유효한지 확인
        assert self.two_factor_service.verify_totp_code(secret, previous_code) is True

    def test_verify_backup_code_valid(self):
        """유효한 백업 코드 검증 테스트"""
        backup_codes = ["12345678", "87654321", "11111111"]
        hashed_codes = [self.two_factor_service._hash_backup_code(code) for code in backup_codes]
        
        # 유효한 백업 코드 검증
        assert self.two_factor_service.verify_backup_code("12345678", hashed_codes) is True
        assert self.two_factor_service.verify_backup_code("87654321", hashed_codes) is True

    def test_verify_backup_code_invalid(self):
        """잘못된 백업 코드 검증 테스트"""
        backup_codes = ["12345678", "87654321", "11111111"]
        hashed_codes = [self.two_factor_service._hash_backup_code(code) for code in backup_codes]
        
        # 잘못된 백업 코드 검증
        assert self.two_factor_service.verify_backup_code("99999999", hashed_codes) is False
        assert self.two_factor_service.verify_backup_code("00000000", hashed_codes) is False

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    @patch('app.service.two_factor_service.TwoFactorService._update_user_2fa')
    def test_setup_2fa_success(self, mock_update_user, mock_get_user):
        """2FA 설정 성공 테스트"""
        mock_get_user.return_value = self.test_user
        mock_update_user.return_value = True
        
        result = self.two_factor_service.setup_2fa(
            user_id=1,
            organization_id=1
        )
        
        # 결과 검증
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10
        
        # 메서드 호출 검증
        mock_get_user.assert_called_once_with(1, 1)
        mock_update_user.assert_called_once()

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    def test_setup_2fa_user_not_found(self, mock_get_user):
        """2FA 설정 시 사용자 없음 테스트"""
        mock_get_user.return_value = None
        
        with pytest.raises(ValueError, match="사용자를 찾을 수 없습니다"):
            self.two_factor_service.setup_2fa(
                user_id=999,
                organization_id=1
            )

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    def test_setup_2fa_already_enabled(self, mock_get_user):
        """이미 2FA가 활성화된 사용자 테스트"""
        self.test_user.is_2fa_enabled = True
        mock_get_user.return_value = self.test_user
        
        with pytest.raises(ValueError, match="이미 2FA가 활성화되어 있습니다"):
            self.two_factor_service.setup_2fa(
                user_id=1,
                organization_id=1
            )

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    @patch('app.service.two_factor_service.TwoFactorService._update_user_2fa')
    def test_verify_and_enable_2fa_success(self, mock_update_user, mock_get_user):
        """2FA 검증 및 활성화 성공 테스트"""
        # 2FA 설정된 사용자 (아직 활성화되지 않음)
        self.test_user.totp_secret = "JBSWY3DPEHPK3PXP"
        self.test_user.backup_codes = ["12345678"]
        mock_get_user.return_value = self.test_user
        mock_update_user.return_value = True
        
        # 현재 시간의 TOTP 코드 생성
        totp = pyotp.TOTP(self.test_user.totp_secret)
        current_code = totp.now()
        
        result = self.two_factor_service.verify_and_enable_2fa(
            user_id=1,
            organization_id=1,
            totp_code=current_code
        )
        
        # 결과 검증
        assert result["success"] is True
        assert "2FA가 성공적으로 활성화되었습니다" in result["message"]
        
        # 메서드 호출 검증
        mock_update_user.assert_called_once()

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    def test_verify_and_enable_2fa_invalid_code(self, mock_get_user):
        """2FA 검증 시 잘못된 코드 테스트"""
        self.test_user.totp_secret = "JBSWY3DPEHPK3PXP"
        mock_get_user.return_value = self.test_user
        
        result = self.two_factor_service.verify_and_enable_2fa(
            user_id=1,
            organization_id=1,
            totp_code="000000"  # 잘못된 코드
        )
        
        # 결과 검증
        assert result["success"] is False
        assert "잘못된 인증 코드입니다" in result["message"]

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    @patch('app.service.two_factor_service.TwoFactorService._update_user_2fa')
    def test_disable_2fa_success(self, mock_update_user, mock_get_user):
        """2FA 비활성화 성공 테스트"""
        # 2FA 활성화된 사용자
        self.test_user.is_2fa_enabled = True
        self.test_user.totp_secret = "JBSWY3DPEHPK3PXP"
        mock_get_user.return_value = self.test_user
        mock_update_user.return_value = True
        
        # 현재 시간의 TOTP 코드 생성
        totp = pyotp.TOTP(self.test_user.totp_secret)
        current_code = totp.now()
        
        result = self.two_factor_service.disable_2fa(
            user_id=1,
            organization_id=1,
            totp_code=current_code
        )
        
        # 결과 검증
        assert result["success"] is True
        assert "2FA가 성공적으로 비활성화되었습니다" in result["message"]

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    def test_disable_2fa_not_enabled(self, mock_get_user):
        """2FA가 활성화되지 않은 사용자 비활성화 테스트"""
        mock_get_user.return_value = self.test_user
        
        with pytest.raises(ValueError, match="2FA가 활성화되어 있지 않습니다"):
            self.two_factor_service.disable_2fa(
                user_id=1,
                organization_id=1,
                totp_code="123456"
            )

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    @patch('app.service.two_factor_service.TwoFactorService._update_user_2fa')
    def test_authenticate_2fa_with_totp(self, mock_update_user, mock_get_user):
        """TOTP 코드로 2FA 인증 테스트"""
        # 2FA 활성화된 사용자
        self.test_user.is_2fa_enabled = True
        self.test_user.totp_secret = "JBSWY3DPEHPK3PXP"
        mock_get_user.return_value = self.test_user
        mock_update_user.return_value = True
        
        # 현재 시간의 TOTP 코드 생성
        totp = pyotp.TOTP(self.test_user.totp_secret)
        current_code = totp.now()
        
        result = self.two_factor_service.authenticate_2fa(
            user_id=1,
            organization_id=1,
            totp_code=current_code
        )
        
        # 결과 검증
        assert result["success"] is True
        assert result["method"] == "totp"

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    @patch('app.service.two_factor_service.TwoFactorService._update_user_2fa')
    def test_authenticate_2fa_with_backup_code(self, mock_update_user, mock_get_user):
        """백업 코드로 2FA 인증 테스트"""
        # 2FA 활성화된 사용자 (백업 코드 포함)
        self.test_user.is_2fa_enabled = True
        backup_codes = ["12345678", "87654321"]
        hashed_codes = [self.two_factor_service._hash_backup_code(code) for code in backup_codes]
        self.test_user.backup_codes = hashed_codes
        mock_get_user.return_value = self.test_user
        mock_update_user.return_value = True
        
        result = self.two_factor_service.authenticate_2fa(
            user_id=1,
            organization_id=1,
            backup_code="12345678"
        )
        
        # 결과 검증
        assert result["success"] is True
        assert result["method"] == "backup_code"
        
        # 사용된 백업 코드가 제거되었는지 확인
        mock_update_user.assert_called_once()

    @patch('app.service.two_factor_service.TwoFactorService._get_user_by_id')
    def test_authenticate_2fa_invalid_credentials(self, mock_get_user):
        """잘못된 2FA 인증 정보 테스트"""
        self.test_user.is_2fa_enabled = True
        self.test_user.totp_secret = "JBSWY3DPEHPK3PXP"
        mock_get_user.return_value = self.test_user
        
        result = self.two_factor_service.authenticate_2fa(
            user_id=1,
            organization_id=1,
            totp_code="000000"  # 잘못된 코드
        )
        
        # 결과 검증
        assert result["success"] is False
        assert "잘못된 인증 코드입니다" in result["message"]

    def test_hash_backup_code(self):
        """백업 코드 해시 테스트"""
        code = "12345678"
        hashed = self.two_factor_service._hash_backup_code(code)
        
        # 해시가 생성되었는지 확인
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != code  # 원본과 다른지 확인
        
        # 같은 코드는 같은 해시를 생성하는지 확인
        hashed2 = self.two_factor_service._hash_backup_code(code)
        assert hashed == hashed2

    def test_remove_used_backup_code(self):
        """사용된 백업 코드 제거 테스트"""
        backup_codes = ["12345678", "87654321", "11111111"]
        hashed_codes = [self.two_factor_service._hash_backup_code(code) for code in backup_codes]
        
        # 첫 번째 코드 제거
        used_code_hash = hashed_codes[0]
        remaining_codes = self.two_factor_service._remove_used_backup_code(
            hashed_codes, used_code_hash
        )
        
        # 제거 결과 검증
        assert len(remaining_codes) == 2
        assert used_code_hash not in remaining_codes
        assert hashed_codes[1] in remaining_codes
        assert hashed_codes[2] in remaining_codes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])