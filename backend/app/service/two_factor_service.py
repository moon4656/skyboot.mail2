"""
2FA (Two-Factor Authentication) 서비스

TOTP 기반 2단계 인증 기능을 제공합니다.
"""
import logging
import secrets
import json
import qrcode
import io
import base64
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import pyotp
from sqlalchemy.orm import Session

from ..model.user_model import User
from ..schemas.auth_schema import (
    TwoFactorSetupResponse, 
    TwoFactorVerifyRequest,
    SecurityEventLog
)
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)


class TwoFactorService:
    """2FA 인증 서비스 클래스"""
    
    def __init__(self):
        self.issuer_name = settings.APP_NAME or "SkyBoot Mail"
        self.backup_codes_count = 10
        logger.info("🔐 2FA 서비스 초기화 완료")
    
    def generate_secret(self) -> str:
        """
        TOTP 시크릿 키 생성
        
        Returns:
            32자리 Base32 인코딩된 시크릿 키
        """
        return pyotp.random_base32()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        백업 코드 생성
        
        Args:
            count: 생성할 백업 코드 수
            
        Returns:
            백업 코드 목록
        """
        backup_codes = []
        for _ in range(count):
            # 8자리 랜덤 코드 생성
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            backup_codes.append(code)
        
        logger.info(f"🔑 백업 코드 {count}개 생성 완료")
        return backup_codes
    
    def generate_qr_code(self, secret: str, user_email: str) -> str:
        """
        QR 코드 생성
        
        Args:
            secret: TOTP 시크릿 키
            user_email: 사용자 이메일
            
        Returns:
            Base64 인코딩된 QR 코드 이미지
        """
        try:
            # TOTP URI 생성
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=self.issuer_name
            )
            
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # 이미지 생성
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Base64 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info(f"📱 QR 코드 생성 완료 - 사용자: {user_email}")
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"❌ QR 코드 생성 실패: {str(e)}")
            raise Exception("QR 코드 생성에 실패했습니다")
    
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """
        TOTP 코드 검증
        
        Args:
            secret: TOTP 시크릿 키
            code: 6자리 인증 코드
            window: 시간 윈도우 (기본 1 = ±30초)
            
        Returns:
            검증 성공 여부
        """
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(code, valid_window=window)
            
            if is_valid:
                logger.info(f"✅ TOTP 코드 검증 성공")
            else:
                logger.warning(f"⚠️ TOTP 코드 검증 실패")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ TOTP 코드 검증 오류: {str(e)}")
            return False
    
    def verify_backup_code(self, user: User, code: str, db: Session) -> bool:
        """
        백업 코드 검증 및 사용 처리
        
        Args:
            user: 사용자 객체
            code: 백업 코드
            db: 데이터베이스 세션
            
        Returns:
            검증 성공 여부
        """
        try:
            if not user.backup_codes:
                return False
            
            backup_codes = json.loads(user.backup_codes)
            
            if code in backup_codes:
                # 사용된 백업 코드 제거
                backup_codes.remove(code)
                user.backup_codes = json.dumps(backup_codes)
                db.commit()
                
                logger.info(f"✅ 백업 코드 사용 완료 - 사용자: {user.email}")
                return True
            else:
                logger.warning(f"⚠️ 잘못된 백업 코드 - 사용자: {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 백업 코드 검증 오류: {str(e)}")
            return False
    
    def setup_2fa(self, user: User, password: str, db: Session) -> TwoFactorSetupResponse:
        """
        2FA 설정
        
        Args:
            user: 사용자 객체
            password: 현재 비밀번호
            db: 데이터베이스 세션
            
        Returns:
            2FA 설정 응답
        """
        try:
            # 비밀번호 확인은 auth_service에서 처리
            
            # 시크릿 키 생성
            secret = self.generate_secret()
            
            # 백업 코드 생성
            backup_codes = self.generate_backup_codes(self.backup_codes_count)
            
            # QR 코드 생성
            qr_code_url = self.generate_qr_code(secret, user.email)
            
            # 사용자 정보 업데이트 (아직 활성화하지 않음)
            user.totp_secret = secret
            user.backup_codes = json.dumps(backup_codes)
            db.commit()
            
            logger.info(f"🔐 2FA 설정 완료 - 사용자: {user.email}")
            
            return TwoFactorSetupResponse(
                secret=secret,
                qr_code_url=qr_code_url,
                backup_codes=backup_codes
            )
            
        except Exception as e:
            logger.error(f"❌ 2FA 설정 실패: {str(e)}")
            db.rollback()
            raise Exception("2FA 설정에 실패했습니다")
    
    def enable_2fa(self, user: User, code: str, db: Session) -> bool:
        """
        2FA 활성화 (설정 후 코드 검증)
        
        Args:
            user: 사용자 객체
            code: 6자리 인증 코드
            db: 데이터베이스 세션
            
        Returns:
            활성화 성공 여부
        """
        try:
            if not user.totp_secret:
                raise Exception("2FA가 설정되지 않았습니다")
            
            # TOTP 코드 검증
            if self.verify_totp_code(user.totp_secret, code):
                user.is_2fa_enabled = True
                user.last_2fa_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"✅ 2FA 활성화 완료 - 사용자: {user.email}")
                return True
            else:
                logger.warning(f"⚠️ 2FA 활성화 실패 - 잘못된 코드: {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 2FA 활성화 오류: {str(e)}")
            db.rollback()
            return False
    
    def disable_2fa(self, user: User, password: str, code: str, db: Session) -> bool:
        """
        2FA 비활성화
        
        Args:
            user: 사용자 객체
            password: 현재 비밀번호
            code: 6자리 인증 코드
            db: 데이터베이스 세션
            
        Returns:
            비활성화 성공 여부
        """
        try:
            if not user.is_2fa_enabled:
                raise Exception("2FA가 활성화되지 않았습니다")
            
            # 비밀번호 확인은 auth_service에서 처리
            
            # TOTP 코드 검증
            if self.verify_totp_code(user.totp_secret, code):
                user.is_2fa_enabled = False
                user.totp_secret = None
                user.backup_codes = None
                user.last_2fa_at = None
                db.commit()
                
                logger.info(f"🔓 2FA 비활성화 완료 - 사용자: {user.email}")
                return True
            else:
                logger.warning(f"⚠️ 2FA 비활성화 실패 - 잘못된 코드: {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 2FA 비활성화 오류: {str(e)}")
            db.rollback()
            return False
    
    def authenticate_2fa(self, user: User, code: str = None, backup_code: str = None, db: Session = None) -> bool:
        """
        2FA 인증 (로그인 시 사용)
        
        Args:
            user: 사용자 객체
            code: 6자리 TOTP 코드
            backup_code: 백업 코드
            db: 데이터베이스 세션
            
        Returns:
            인증 성공 여부
        """
        try:
            if not user.is_2fa_enabled:
                return True  # 2FA가 비활성화된 경우 통과
            
            # TOTP 코드 검증
            if code and self.verify_totp_code(user.totp_secret, code):
                user.last_2fa_at = datetime.utcnow()
                if db:
                    db.commit()
                logger.info(f"✅ 2FA 인증 성공 (TOTP) - 사용자: {user.email}")
                return True
            
            # 백업 코드 검증
            if backup_code and db and self.verify_backup_code(user, backup_code, db):
                user.last_2fa_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ 2FA 인증 성공 (백업코드) - 사용자: {user.email}")
                return True
            
            logger.warning(f"⚠️ 2FA 인증 실패 - 사용자: {user.email}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 2FA 인증 오류: {str(e)}")
            return False
    
    def get_backup_codes_count(self, user: User) -> int:
        """
        남은 백업 코드 수 조회
        
        Args:
            user: 사용자 객체
            
        Returns:
            남은 백업 코드 수
        """
        try:
            if not user.backup_codes:
                return 0
            
            backup_codes = json.loads(user.backup_codes)
            return len(backup_codes)
            
        except Exception as e:
            logger.error(f"❌ 백업 코드 수 조회 오류: {str(e)}")
            return 0
    
    def regenerate_backup_codes(self, user: User, password: str, db: Session) -> List[str]:
        """
        백업 코드 재생성
        
        Args:
            user: 사용자 객체
            password: 현재 비밀번호
            db: 데이터베이스 세션
            
        Returns:
            새로운 백업 코드 목록
        """
        try:
            if not user.is_2fa_enabled:
                raise Exception("2FA가 활성화되지 않았습니다")
            
            # 비밀번호 확인은 auth_service에서 처리
            
            # 새 백업 코드 생성
            backup_codes = self.generate_backup_codes(self.backup_codes_count)
            user.backup_codes = json.dumps(backup_codes)
            db.commit()
            
            logger.info(f"🔑 백업 코드 재생성 완료 - 사용자: {user.email}")
            return backup_codes
            
        except Exception as e:
            logger.error(f"❌ 백업 코드 재생성 실패: {str(e)}")
            db.rollback()
            raise Exception("백업 코드 재생성에 실패했습니다")


# 전역 2FA 서비스 인스턴스
two_factor_service = TwoFactorService()