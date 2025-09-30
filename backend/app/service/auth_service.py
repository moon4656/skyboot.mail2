"""
인증 및 권한 관리 - 조직별 데이터 격리 지원

SaaS 다중 조직 지원을 위한 사용자 인증, JWT 토큰 관리, 비밀번호 해싱 등의 기능을 제공합니다.
"""
import logging
import uuid
import json
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from ..model import User, RefreshToken, Organization
from ..schemas.user_schema import UserCreate, UserLogin, Token
from ..config import settings
from ..database.user import get_db
from ..middleware.tenant_middleware import get_current_org_id

# 로거 설정
logger = logging.getLogger(__name__)

# 패스워드 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# HTTP Bearer 스키마
security = HTTPBearer()


class AuthService:
    """
    인증 서비스 클래스 - 조직별 데이터 격리
    SaaS 다중 조직 지원을 위한 사용자 인증, 토큰 관리, 비밀번호 해싱 등의 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        """
        AuthService 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """액세스 토큰 생성"""
        import uuid
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire, 
            "type": "access",
            "jti": str(uuid.uuid4())  # JWT ID로 고유성 보장
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """리프레시 토큰 생성"""
        import uuid
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire, 
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID로 고유성 보장
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    

    
    @staticmethod
    def get_user_by_token(db: Session, org_id: str, user_uuid: str):
        """
        토큰으로 사용자 조회 - 조직별 격리
        
        Args:
            db: 데이터베이스 세션
            org_id: 조직 ID
            user_uuid: 사용자 UUID
        
        Returns:
            사용자 또는 None
        """
        try:
            user = db.query(User).filter(
                User.org_id == org_id,
                User.user_uuid == user_uuid,
                User.is_active == True
            ).first()
            
            return user
            
        except Exception as e:
            logger.error(f"❌ 토큰으로 사용자 조회 오류: {str(e)}")
            return None
    
    @staticmethod
    def create_user_tokens(user: User) -> Dict[str, str]:
        """사용자 토큰 생성"""
        # 액세스 토큰 데이터
        access_token_data = {
            "sub": user.user_uuid,
            "org_id": user.org_id,
            "email": user.email,
            "role": user.role
        }
        
        # 리프레시 토큰 데이터
        refresh_token_data = {
            "sub": user.user_uuid,
            "org_id": user.org_id
        }
        
        # 토큰 생성
        access_token = AuthService.create_access_token(access_token_data)
        refresh_token = AuthService.create_refresh_token(refresh_token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def save_refresh_token(db: Session, user_uuid: str, refresh_token: str):
        """리프레시 토큰 저장"""
        try:
            # 기존 리프레시 토큰 삭제
            db.query(RefreshToken).filter(
                RefreshToken.user_uuid == user_uuid
            ).delete()
            
            # 새 리프레시 토큰 저장
            new_refresh_token = RefreshToken(
                user_uuid=user_uuid,
                token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            db.add(new_refresh_token)
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ 리프레시 토큰 저장 오류: {str(e)}")
            db.rollback()
    
    @staticmethod
    def get_mail_user_by_id(db: Session, org_id: str, user_id: str):
        """
        조직별 사용자 ID로 메일 사용자를 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            org_id: 조직 ID
            user_id: 사용자 ID
        
        Returns:
            User 객체 또는 None (찾지 못한 경우)
        """
        try:
            return db.query(User).filter(
                User.org_id == org_id,
                User.user_id == user_id,
                User.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"❌ 사용자 ID로 조회 오류: {str(e)}")
            return None
    
    @staticmethod
    def get_mail_user_by_email(db: Session, org_id: str, email: str):
        """
        조직별 이메일 주소로 메일 사용자를 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            org_id: 조직 ID
            email: 이메일 주소
        
        Returns:
            User 객체 또는 None (찾지 못한 경우)
        """
        try:
            return db.query(User).filter(
                User.org_id == org_id,
                User.email == email,
                User.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"❌ 이메일로 사용자 조회 오류: {str(e)}")
            return None

    def create_tokens(self, user: User) -> Dict[str, Any]:
        """
        액세스 토큰과 리프레시 토큰을 생성합니다.
        
        Args:
            user: 사용자 객체
            
        Returns:
            토큰 정보 딕셔너리
        """
        try:
            logger.info(f"🎫 토큰 생성 - 사용자 UUID: {user.user_uuid}, 조직 ID: {user.org_id}")
            
            # 최신 사용자 정보 다시 조회 (역할 업데이트 반영)
            fresh_user = self.db.query(User).filter(User.user_uuid == user.user_uuid).first()
            if fresh_user:
                user = fresh_user
                logger.info(f"🔄 최신 사용자 정보 조회 완료 - 역할: {user.role}")
            
            # 조직 정보 조회
            organization = self.db.query(Organization).filter(Organization.org_id == user.org_id).first()
            
            # 액세스 토큰 데이터 (조직 정보 포함)
            access_token_data = {
                "sub": str(user.user_uuid),
                "email": user.email,
                "username": user.username,
                "is_admin": user.role in ["admin", "system_admin"],
                "role": user.role,
                "org_id": user.org_id,
                "org_name": organization.name if organization else None,
                "org_domain": organization.domain if organization else None
            }
            
            # 리프레시 토큰 데이터
            refresh_token_data = {
                "sub": str(user.user_uuid),
                "org_id": user.org_id
            }
            
            logger.info(f"🔍 토큰 데이터 생성 - access_token_data: {access_token_data}")
            logger.info(f"🔍 토큰 데이터 생성 - refresh_token_data: {refresh_token_data}")
            
            # 토큰 생성 (정적 메서드 사용)
            access_token = AuthService.create_access_token(access_token_data)
            refresh_token = AuthService.create_refresh_token(refresh_token_data)
            
            # 기존 리프레시 토큰 무효화
            self.db.query(RefreshToken).filter(
                RefreshToken.user_uuid == user.user_uuid,
                RefreshToken.is_revoked == False
            ).update({"is_revoked": True})
            
            # 새 리프레시 토큰 저장
            new_refresh_token = RefreshToken(
                user_uuid=user.user_uuid,
                token=refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                is_revoked=False,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(new_refresh_token)
            self.db.commit()
            
            logger.info(f"✅ 토큰 생성 완료 - 사용자 UUID: {user.user_uuid}, 조직 ID: {user.org_id}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": user.user_uuid,
                    "email": user.email,
                    "username": user.username,
                    "is_admin": user.role == "admin",
                    "org_id": user.org_id,
                    "org_name": organization.name if organization else None
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 토큰 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="토큰 생성 중 오류가 발생했습니다."
            )
    
    def authenticate_user(self, email: str, password: str, org_id: Optional[str] = None):
        """
        사용자 인증을 수행합니다.
        
        Args:
            email: 사용자 이메일
            password: 비밀번호
            org_id: 조직 ID (선택사항)
            
        Returns:
            인증된 사용자 객체 또는 None
        """
        try:
            logger.info(f"🔐 사용자 인증 시도 - 이메일: {email}, 조직 ID: {org_id}")
            
            # 사용자 조회 (조직 ID가 있으면 조직 내에서만 검색)
            query = self.db.query(User).filter(User.email == email)
            if org_id:
                query = query.filter(User.org_id == org_id)
            
            user = query.first()
            if not user:
                logger.warning(f"❌ 사용자를 찾을 수 없음 - 이메일: {email}, 조직 ID: {org_id}")
                return None
            
            # 조직 활성화 상태 확인
            organization = self.db.query(Organization).filter(Organization.org_id == user.org_id).first()
            if not organization or not organization.is_active:
                logger.warning(f"❌ 조직이 비활성화됨 - 조직 ID: {user.org_id}")
                return None
            
            # 비밀번호 검증
            if not AuthService.verify_password(password, user.hashed_password):
                logger.warning(f"❌ 비밀번호 불일치 - 이메일: {email}")
                return None
            
            # 사용자 활성화 상태 확인
            if not user.is_active:
                logger.warning(f"❌ 비활성화된 사용자 - 이메일: {email}")
                return None
            
            logger.info(f"✅ 사용자 인증 성공 - 이메일: {email}, 조직 ID: {user.org_id}")
            return user
            
        except Exception as e:
            logger.error(f"❌ 사용자 인증 실패: {str(e)}")
            return None

def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시화합니다.
    
    Args:
        password: 원본 비밀번호
        
    Returns:
        해시화된 비밀번호
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호를 검증합니다.
    
    Args:
        plain_password: 원본 비밀번호
        hashed_password: 해시화된 비밀번호
        
    Returns:
        비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    액세스 토큰을 생성합니다.
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간
        
    Returns:
        JWT 액세스 토큰
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(db: Session, user_id: str) -> str:
    """
    리프레시 토큰을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        
    Returns:
        JWT 리프레시 토큰
    """
    # 기존 리프레시 토큰 무효화
    db.query(RefreshToken).filter(
        RefreshToken.user_uuid == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    
    # 새 리프레시 토큰 생성
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    
    refresh_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    # 데이터베이스에 리프레시 토큰 저장
    db_token = RefreshToken(
        user_uuid=user_id,
        token=refresh_token,
        expires_at=expire
    )
    db.add(db_token)
    db.commit()
    
    return refresh_token

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    토큰을 검증합니다.
    
    Args:
        token: JWT 토큰
        token_type: 토큰 타입 (access 또는 refresh)
        
    Returns:
        토큰 페이로드 또는 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자를 반환합니다.
    
    Args:
        credentials: HTTP Authorization 헤더
        db: 데이터베이스 세션
        
    Returns:
        현재 사용자 객체
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 검증
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        org_id: int = payload.get("org_id")
        
        if user_id is None or org_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 사용자 조회 (조직 컨텍스트 포함)
    user = db.query(User).filter(
        User.user_uuid == user_id,
        User.org_id == org_id
    ).first()
    
    if user is None:
        raise credentials_exception
    
    # 조직 활성화 상태 확인
    organization = db.query(Organization).filter(Organization.org_id == org_id).first()
    if not organization or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="조직이 비활성화되었습니다."
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    현재 활성화된 사용자를 반환합니다.
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        활성화된 사용자 객체
        
    Raises:
        HTTPException: 사용자가 비활성화된 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다."
        )
    return current_user

# auth.py에서 가져온 권한 확인 데코레이터
def check_permission(required_role: str = None):
    """
    권한 확인 데코레이터
    
    Args:
        required_role: 필요한 역할 (admin, user 등)
    
    Returns:
        데코레이터 함수
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 현재 사용자 정보 가져오기 (FastAPI 의존성에서)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증이 필요합니다."
                )
            
            # 역할 확인
            if required_role:
                if required_role == "admin" and current_user.role not in ["admin", "system_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="관리자 권한이 필요합니다."
                    )
                elif required_role == "user" and not current_user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="활성화된 사용자 권한이 필요합니다."
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 조직별 격리를 위한 추가 의존성 함수들
async def get_current_user_with_org(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id)
) -> User:
    """
    조직 컨텍스트와 함께 현재 사용자를 반환합니다.
    
    Args:
        credentials: HTTP Authorization 헤더
        db: 데이터베이스 세션
        org_id: 현재 조직 ID
        
    Returns:
        현재 사용자 객체
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 검증
        payload = AuthService.verify_token(credentials.credentials)
        if not payload:
            raise credentials_exception
            
        user_uuid: str = payload.get("sub")
        token_org_id: str = payload.get("org_id")
        
        if user_uuid is None or token_org_id is None:
            raise credentials_exception
        
        # 조직 ID 일치 확인
        if token_org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="조직 접근 권한이 없습니다."
            )
            
    except Exception as e:
        logger.error(f"❌ 토큰 검증 오류: {str(e)}")
        raise credentials_exception
    
    # 사용자 조회 (조직별 격리)
    user = AuthService.get_user_by_token(db, org_id, user_uuid)
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user_with_org(
    current_user: User = Depends(get_current_user_with_org)
) -> User:
    """
    조직 컨텍스트와 함께 현재 활성화된 사용자를 반환합니다.
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        활성화된 사용자 객체
        
    Raises:
        HTTPException: 사용자가 비활성화된 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다."
        )
    return current_user

async def get_admin_user_with_org(
    current_user: User = Depends(get_current_active_user_with_org)
) -> User:
    """
    조직 컨텍스트와 함께 현재 관리자 사용자를 반환합니다.
    
    Args:
        current_user: 현재 활성화된 사용자
        
    Returns:
        관리자 사용자 객체
        
    Raises:
        HTTPException: 관리자가 아닌 경우
    """
    if current_user.role not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    현재 관리자 사용자를 반환합니다.
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        관리자 사용자 객체
        
    Raises:
        HTTPException: 관리자가 아닌 경우
    """
    if current_user.role not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user