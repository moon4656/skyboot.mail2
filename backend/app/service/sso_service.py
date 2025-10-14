"""
SSO (Single Sign-On) 인증 서비스

다중 조직 지원을 위한 SSO 인증 기능을 제공합니다.
SAML, OAuth2, OpenID Connect 등의 프로토콜을 지원합니다.
"""
import logging
import uuid
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, parse_qs
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..model import User, Organization
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)


class SSOService:
    """
    SSO 인증 서비스 클래스
    다중 조직 지원을 위한 SSO 인증 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        """
        SSOService 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self.oauth_providers = {
            "google": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile"
            },
            "microsoft": {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "user_info_url": "https://graph.microsoft.com/v1.0/me",
                "scope": "openid email profile"
            }
        }
    
    def generate_sso_state(self, org_id: str, provider: str) -> str:
        """
        SSO 인증을 위한 state 파라미터를 생성합니다.
        
        Args:
            org_id: 조직 ID
            provider: SSO 제공자 (google, microsoft 등)
            
        Returns:
            생성된 state 문자열
        """
        try:
            state_data = {
                "org_id": org_id,
                "provider": provider,
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": secrets.token_urlsafe(32)
            }
            
            state_json = json.dumps(state_data)
            state_encoded = base64.urlsafe_b64encode(state_json.encode()).decode()
            
            logger.info(f"🔐 SSO state 생성 - 조직: {org_id}, 제공자: {provider}")
            return state_encoded
            
        except Exception as e:
            logger.error(f"❌ SSO state 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO state 생성에 실패했습니다."
            )
    
    def verify_sso_state(self, state: str) -> Dict[str, Any]:
        """
        SSO state 파라미터를 검증합니다.
        
        Args:
            state: 검증할 state 문자열
            
        Returns:
            검증된 state 데이터
        """
        try:
            state_json = base64.urlsafe_b64decode(state.encode()).decode()
            state_data = json.loads(state_json)
            
            # 타임스탬프 검증 (5분 이내)
            timestamp = datetime.fromisoformat(state_data["timestamp"])
            if datetime.utcnow() - timestamp > timedelta(minutes=5):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSO state가 만료되었습니다."
                )
            
            logger.info(f"✅ SSO state 검증 성공 - 조직: {state_data['org_id']}")
            return state_data
            
        except json.JSONDecodeError:
            logger.error("❌ SSO state 형식이 잘못되었습니다.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 SSO state 형식입니다."
            )
        except Exception as e:
            logger.error(f"❌ SSO state 검증 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSO state 검증에 실패했습니다."
            )
    
    def get_sso_auth_url(self, provider: str, org_id: str, redirect_uri: str) -> str:
        """
        SSO 인증 URL을 생성합니다.
        
        Args:
            provider: SSO 제공자
            org_id: 조직 ID
            redirect_uri: 리다이렉트 URI
            
        Returns:
            SSO 인증 URL
        """
        try:
            if provider not in self.oauth_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"지원하지 않는 SSO 제공자입니다: {provider}"
                )
            
            provider_config = self.oauth_providers[provider]
            state = self.generate_sso_state(org_id, provider)
            
            auth_params = {
                "client_id": provider_config["client_id"],
                "response_type": "code",
                "scope": provider_config["scope"],
                "redirect_uri": redirect_uri,
                "state": state
            }
            
            auth_url = f"{provider_config['auth_url']}?{urlencode(auth_params)}"
            
            logger.info(f"🔗 SSO 인증 URL 생성 - 제공자: {provider}, 조직: {org_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"❌ SSO 인증 URL 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 인증 URL 생성에 실패했습니다."
            )
    
    def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        인증 코드를 액세스 토큰으로 교환합니다.
        
        Args:
            provider: SSO 제공자
            code: 인증 코드
            redirect_uri: 리다이렉트 URI
            
        Returns:
            액세스 토큰 정보
        """
        try:
            if provider not in self.oauth_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"지원하지 않는 SSO 제공자입니다: {provider}"
                )
            
            provider_config = self.oauth_providers[provider]
            
            token_data = {
                "client_id": provider_config["client_id"],
                "client_secret": provider_config["client_secret"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            response = requests.post(
                provider_config["token_url"],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ 토큰 교환 실패 - 상태코드: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSO 토큰 교환에 실패했습니다."
                )
            
            token_info = response.json()
            logger.info(f"✅ SSO 토큰 교환 성공 - 제공자: {provider}")
            return token_info
            
        except requests.RequestException as e:
            logger.error(f"❌ SSO 토큰 교환 네트워크 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 서비스와의 통신에 실패했습니다."
            )
        except Exception as e:
            logger.error(f"❌ SSO 토큰 교환 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 토큰 교환에 실패했습니다."
            )
    
    def get_user_info_from_provider(self, provider: str, access_token: str) -> Dict[str, Any]:
        """
        SSO 제공자로부터 사용자 정보를 가져옵니다.
        
        Args:
            provider: SSO 제공자
            access_token: 액세스 토큰
            
        Returns:
            사용자 정보
        """
        try:
            if provider not in self.oauth_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"지원하지 않는 SSO 제공자입니다: {provider}"
                )
            
            provider_config = self.oauth_providers[provider]
            
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                provider_config["user_info_url"],
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ 사용자 정보 조회 실패 - 상태코드: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSO 사용자 정보 조회에 실패했습니다."
                )
            
            user_info = response.json()
            logger.info(f"✅ SSO 사용자 정보 조회 성공 - 제공자: {provider}")
            return user_info
            
        except requests.RequestException as e:
            logger.error(f"❌ SSO 사용자 정보 조회 네트워크 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 서비스와의 통신에 실패했습니다."
            )
        except Exception as e:
            logger.error(f"❌ SSO 사용자 정보 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 사용자 정보 조회에 실패했습니다."
            )
    
    def find_or_create_sso_user(self, user_info: Dict[str, Any], org_id: str, provider: str) -> User:
        """
        SSO 사용자 정보를 기반으로 사용자를 찾거나 생성합니다.
        
        Args:
            user_info: SSO 제공자로부터 받은 사용자 정보
            org_id: 조직 ID
            provider: SSO 제공자
            
        Returns:
            사용자 객체
        """
        try:
            # 이메일 추출 (제공자별로 다를 수 있음)
            email = user_info.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSO 제공자로부터 이메일 정보를 받을 수 없습니다."
                )
            
            # 기존 사용자 조회
            user = self.db.query(User).filter(
                User.email == email,
                User.org_id == org_id
            ).first()
            
            if user:
                # 기존 사용자 업데이트
                user.last_login_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"✅ 기존 SSO 사용자 로그인 - 이메일: {email}, 조직: {org_id}")
                return user
            
            # 새 사용자 생성
            new_user = User(
                user_uuid=str(uuid.uuid4()),
                org_id=org_id,
                email=email,
                username=user_info.get("name", email.split("@")[0]),
                hashed_password="",  # SSO 사용자는 비밀번호 없음
                role="user",
                is_active=True,
                is_email_verified=True,  # SSO 사용자는 이메일 인증됨
                created_at=datetime.utcnow(),
                last_login_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"✅ 새 SSO 사용자 생성 - 이메일: {email}, 조직: {org_id}")
            return new_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ SSO 사용자 생성/조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 사용자 처리에 실패했습니다."
            )
    
    def authenticate_sso_user(self, provider: str, code: str, state: str, redirect_uri: str) -> User:
        """
        SSO 인증을 통해 사용자를 인증합니다.
        
        Args:
            provider: SSO 제공자
            code: 인증 코드
            state: state 파라미터
            redirect_uri: 리다이렉트 URI
            
        Returns:
            인증된 사용자 객체
        """
        try:
            # State 검증
            state_data = self.verify_sso_state(state)
            org_id = state_data["org_id"]
            
            # 조직 활성화 상태 확인
            organization = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="조직을 찾을 수 없거나 비활성화되었습니다."
                )
            
            # 토큰 교환
            token_info = self.exchange_code_for_token(provider, code, redirect_uri)
            access_token = token_info.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSO 액세스 토큰을 받을 수 없습니다."
                )
            
            # 사용자 정보 조회
            user_info = self.get_user_info_from_provider(provider, access_token)
            
            # 사용자 찾기 또는 생성
            user = self.find_or_create_sso_user(user_info, org_id, provider)
            
            logger.info(f"✅ SSO 인증 완료 - 제공자: {provider}, 사용자: {user.email}, 조직: {org_id}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ SSO 인증 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO 인증에 실패했습니다."
            )