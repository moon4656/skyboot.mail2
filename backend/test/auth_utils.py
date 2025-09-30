#!/usr/bin/env python3
"""
테스트용 인증 유틸리티
관리자 토큰 생성 로직을 개선하여 모든 테스트에서 일관되게 사용할 수 있도록 합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Optional, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.model.user_model import User
from app.database.user import get_db
from app.service.auth_service import AuthService, create_access_token
import logging

logger = logging.getLogger(__name__)

class TestAuthUtils:
    """테스트용 인증 유틸리티 클래스"""
    
    # 실제 데이터베이스의 관리자 계정 정보
    ADMIN_CREDENTIALS = {
        "email": "admin@skyboot.com",
        "password": "Admin123!@#"  # 실제 관리자 비밀번호
    }
    
    # 테스트용 사용자 계정 정보 (존재하지 않을 수 있음)
    USER_CREDENTIALS = {
        "email": "user@skyboot.com",
        "password": "user123"
    }
    
    # 토큰 캐시 (클래스 변수로 토큰을 저장)
    _cached_admin_token = None
    _cached_user_token = None
    
    @classmethod
    def get_admin_token(cls, client: TestClient) -> Optional[str]:
        """
        관리자 액세스 토큰을 생성합니다. (캐싱 지원)
        
        Args:
            client: FastAPI TestClient 인스턴스
            
        Returns:
            관리자 액세스 토큰 또는 None (실패 시)
        """
        # 캐시된 토큰이 있으면 반환
        if cls._cached_admin_token:
            logger.info("🔄 캐시된 관리자 토큰 사용")
            return cls._cached_admin_token
            
        try:
            # 관리자 로그인 시도
            response = client.post(
                "/api/v1/auth/login",
                json=cls.ADMIN_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    # 토큰을 캐시에 저장
                    cls._cached_admin_token = access_token
                    logger.info("✅ 관리자 토큰 생성 및 캐시 저장 성공")
                    return access_token
                else:
                    logger.error("❌ 응답에 액세스 토큰이 없습니다")
            else:
                logger.error(f"❌ 관리자 로그인 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ 관리자 토큰 생성 중 오류: {str(e)}")
            
        return None
    
    @classmethod
    def get_user_token(cls, client: TestClient) -> Optional[str]:
        """
        일반 사용자 액세스 토큰을 생성합니다. (캐싱 지원)
        
        Args:
            client: FastAPI TestClient 인스턴스
            
        Returns:
            사용자 액세스 토큰 또는 None (실패 시)
        """
        # 캐시된 토큰이 있으면 반환
        if cls._cached_user_token:
            logger.info("🔄 캐시된 사용자 토큰 사용")
            return cls._cached_user_token
            
        try:
            # 사용자 로그인 시도
            response = client.post(
                "/api/v1/auth/login",
                json=cls.USER_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    # 토큰을 캐시에 저장
                    cls._cached_user_token = access_token
                    logger.info("✅ 사용자 토큰 생성 및 캐시 저장 성공")
                    return access_token
                else:
                    logger.error("❌ 응답에 액세스 토큰이 없습니다")
            else:
                logger.warning(f"⚠️ 사용자 로그인 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ 사용자 토큰 생성 중 오류: {str(e)}")
            
        return None
    
    @classmethod
    def clear_token_cache(cls):
        """
        토큰 캐시를 초기화합니다.
        """
        cls._cached_admin_token = None
        cls._cached_user_token = None
        logger.info("🗑️ 토큰 캐시 초기화 완료")
    
    @classmethod
    def get_auth_headers(cls, client: TestClient, is_admin: bool = True) -> Dict[str, str]:
        """
        인증 헤더를 생성합니다.
        
        Args:
            client: FastAPI TestClient 인스턴스
            is_admin: 관리자 토큰 여부 (기본값: True)
            
        Returns:
            Authorization 헤더가 포함된 딕셔너리
        """
        if is_admin:
            token = cls.get_admin_token(client)
        else:
            token = cls.get_user_token(client)
            
        if token:
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        else:
            logger.warning("⚠️ 토큰 생성 실패, 빈 헤더 반환")
            return {"Content-Type": "application/json"}
    
    @classmethod
    def create_test_token_direct(cls, user_data: Dict[str, Any]) -> str:
        """
        사용자 데이터로부터 직접 테스트 토큰을 생성합니다.
        데이터베이스 연결 없이 토큰을 생성할 때 사용합니다.
        
        Args:
            user_data: 사용자 정보 딕셔너리
            
        Returns:
            JWT 액세스 토큰
        """
        try:
            token_data = {
                "sub": user_data.get("user_uuid"),
                "email": user_data.get("email"),
                "username": user_data.get("username", "testuser"),
                "role": user_data.get("role", "user"),
                "org_id": user_data.get("org_id"),
                "org_code": user_data.get("org_code", "test"),
                "is_admin": user_data.get("role") in ["admin", "system_admin"]
            }
            
            access_token = create_access_token(data=token_data)
            logger.info(f"✅ 직접 토큰 생성 성공 - 사용자: {user_data.get('email')}")
            return access_token
            
        except Exception as e:
            logger.error(f"❌ 직접 토큰 생성 실패: {str(e)}")
            raise
    
    @classmethod
    def verify_admin_account(cls) -> bool:
        """
        관리자 계정이 존재하고 접근 가능한지 확인합니다.
        
        Returns:
            관리자 계정 접근 가능 여부
        """
        try:
            db: Session = next(get_db())
            
            # 관리자 계정 조회
            admin_user = db.query(User).filter(
                User.email == cls.ADMIN_CREDENTIALS["email"]
            ).first()
            
            if not admin_user:
                logger.error("❌ 관리자 계정을 찾을 수 없습니다")
                return False
            
            if not admin_user.is_active:
                logger.error("❌ 관리자 계정이 비활성화되어 있습니다")
                return False
            
            # 비밀번호 검증
            is_valid = AuthService.verify_password(
                cls.ADMIN_CREDENTIALS["password"], 
                admin_user.hashed_password
            )
            
            if not is_valid:
                logger.error("❌ 관리자 계정 비밀번호가 일치하지 않습니다")
                return False
            
            logger.info("✅ 관리자 계정 검증 성공")
            return True
            
        except Exception as e:
            logger.error(f"❌ 관리자 계정 검증 중 오류: {str(e)}")
            return False
        finally:
            db.close()

def get_test_admin_token(client: TestClient) -> Optional[str]:
    """
    편의 함수: 관리자 토큰 생성
    
    Args:
        client: FastAPI TestClient 인스턴스
        
    Returns:
        관리자 액세스 토큰 또는 None
    """
    return TestAuthUtils.get_admin_token(client)

def get_test_user_token(client: TestClient) -> Optional[str]:
    """
    편의 함수: 사용자 토큰 생성
    
    Args:
        client: FastAPI TestClient 인스턴스
        
    Returns:
        사용자 액세스 토큰 또는 None
    """
    return TestAuthUtils.get_user_token(client)

def get_test_auth_headers(client: TestClient, is_admin: bool = True) -> Dict[str, str]:
    """
    편의 함수: 인증 헤더 생성
    
    Args:
        client: FastAPI TestClient 인스턴스
        is_admin: 관리자 토큰 여부
        
    Returns:
        Authorization 헤더가 포함된 딕셔너리
    """
    return TestAuthUtils.get_auth_headers(client, is_admin)