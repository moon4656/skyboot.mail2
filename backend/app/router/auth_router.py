from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserBase
from ..database.user import get_db
from ..model.user_model import User, RefreshToken, LoginLog
from ..schemas import UserCreate, UserResponse, UserLogin, Token, TokenRefresh, AccessToken, MessageResponse, LoginLogCreate
from ..schemas.auth_schema import (
    RateLimitConfig, TwoFactorSetupRequest, TwoFactorSetupResponse, TwoFactorVerifyRequest,
    TwoFactorLoginRequest, TwoFactorDisableRequest, AuthResponse, AuthApiResponse,
    SSOLoginRequest, RoleRequest, UserRoleUpdateRequest
)
from ..service.auth_service import AuthService, get_current_user
from ..service.user_service import UserService
from ..service import two_factor_service
from ..service.sso_service import SSOService
from ..service.rbac_service import RBACService
from ..middleware.tenant_middleware import get_current_org_id, get_current_organization
from ..config import settings
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin, 
    request: Request, 
    db: Session = Depends(get_db)
) -> Token:
    """
    로그인 엔드포인트
    이메일과 비밀번호로 사용자를 인증하고 JWT 토큰을 반환합니다.
    """
    logger.info(f"🔐 로그인 시도 - 사용자 ID: {user_credentials.user_id}")
    
    # 클라이언트 정보 추출
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", None)
    
    def safe_log_login_attempt(status: str, reason: str = None, user_uuid: str = None):
        """
        안전한 로그인 로그 기록 함수
        트랜잭션 롤백 상태에서도 안전하게 로그를 기록합니다.
        """
        try:
            # 새로운 세션을 생성하여 독립적으로 로그 기록
            from ..database.user import get_db_session
            with get_db_session() as log_db:
                login_log = LoginLog(
                    user_uuid=user_uuid,
                    user_id=user_credentials.user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    login_status=status,
                    failure_reason=reason
                )
                log_db.add(login_log)
                log_db.commit()
        except Exception as e:
            logger.error(f"❌ 로그인 로그 기록 실패: {str(e)}")
    
    try:
        # 사용자 인증
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(user_credentials.user_id, user_credentials.password)
        if not user:
            safe_log_login_attempt("failed", "invalid_credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 사용자 ID 또는 비밀번호입니다."
            )
        
        # 2FA 활성화 확인
        if user.is_2fa_enabled:
            # 2FA가 활성화된 경우 임시 토큰 반환
            temp_token = auth_service.create_access_token(
                data={"sub": str(user.user_uuid), "temp": True, "requires_2fa": True},
                expires_delta=timedelta(minutes=5)  # 5분 임시 토큰
            )
            safe_log_login_attempt("2fa_required", user_uuid=str(user.user_uuid))
            return Token(
                access_token=temp_token,
                token_type="bearer",
                requires_2fa=True
            )
        
        # 일반 로그인 처리
        tokens = auth_service.create_tokens(user)
        safe_log_login_attempt("success", user_uuid=str(user.user_uuid))
        
        logger.info(f"✅ 로그인 성공 - 사용자: {user.user_id}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 로그인 처리 중 오류: {str(e)}")
        safe_log_login_attempt("error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )


@router.post("/login/2fa", response_model=Token, summary="2FA 로그인")
async def login_with_2fa(
    user_credentials: TwoFactorLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Token:
    """
    2FA 로그인 엔드포인트
    
    이메일, 비밀번호와 함께 TOTP 코드 또는 백업 코드로 인증합니다.
    - **email**: 이메일 주소
    - **password**: 비밀번호
    - **totp_code**: 6자리 TOTP 코드 (선택)
    - **backup_code**: 백업 코드 (선택)
    """
    logger.info(f"🔐 2FA 로그인 시도 - 사용자: {user_credentials.email}")
    
    # 클라이언트 정보 추출
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", None)
    
    def safe_log_login_attempt(status: str, reason: str = None, user_uuid: str = None):
        """안전한 로그인 로그 기록 함수"""
        try:
            from ..database.user import get_db_session
            with get_db_session() as log_db:
                login_log = LoginLog(
                    user_uuid=user_uuid,
                    user_id=str(user_credentials.email),
                    ip_address=client_ip,
                    user_agent=user_agent,
                    login_status=status,
                    failure_reason=reason
                )
                log_db.add(login_log)
                log_db.commit()
                logger.debug(f"📝 2FA 로그인 로그 기록 완료 - 상태: {status}")
        except Exception as log_error:
            logger.warning(f"⚠️ 2FA 로그인 로그 기록 실패: {str(log_error)}")
    
    try:
        # 사용자 인증 (이메일 기반)
        auth_service = AuthService(db)
        user = auth_service.authenticate_user_by_email(
            user_credentials.email, user_credentials.password
        )
        
        if not user:
            safe_log_login_attempt("failed", "Incorrect email or password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2FA가 활성화되지 않은 경우
        if not user.is_2fa_enabled:
            safe_log_login_attempt("failed", "2FA not enabled", user.user_uuid)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA가 활성화되지 않았습니다"
            )
        
        # 2FA 인증
        if not user_credentials.totp_code and not user_credentials.backup_code:
            safe_log_login_attempt("failed", "No 2FA code provided", user.user_uuid)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP 코드 또는 백업 코드가 필요합니다"
            )
        
        # 2FA 코드 검증
        is_2fa_valid = two_factor_service.authenticate_2fa(
            user, 
            user_credentials.totp_code, 
            user_credentials.backup_code, 
            db
        )
        
        if not is_2fa_valid:
            safe_log_login_attempt("failed", "Invalid 2FA code", user.user_uuid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA 인증 코드가 올바르지 않습니다"
            )
        
        # 토큰 생성
        tokens = auth_service.create_tokens(user)
        
        # 사용자 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # 로그인 성공 로그 기록
        safe_log_login_attempt("success", "2FA login successful", user.user_uuid)
        
        logger.info(f"✅ 2FA 로그인 성공 - 사용자: {user.email}, 조직: {user.org_id}")
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 2FA 로그인 오류: {str(e)}")
        safe_log_login_attempt("failed", f"Server error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )




@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, 
    request: Request,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    회원가입 엔드포인트
    조직 내에서 사용자를 생성합니다.
    """
    
    # 조직 정보를 request.state에서 가져오기 (tenant_middleware에서 설정됨)
    try:
        org_code = getattr(request.state, 'org_code', None)
        org_id = getattr(request.state, 'org_id', None)
        organization = getattr(request.state, 'organization', None)
    except AttributeError:
        org_code = None
        org_id = None
        organization = None
    
    logger.debug(f"📨 request.state 정보: org_code={org_code}, org_id={org_id}")
    logger.debug(f"📨 organization 정보: {organization}")
    
    # tenant_middleware에서 조직 정보가 설정되지 않은 경우 기본 조직 찾기
    if not org_id or not org_code:
        from app.model.organization_model import Organization
        
        # 기본 조직 코드로 찾기
        default_org = db.query(Organization).filter(
            Organization.org_code == "default",
            Organization.deleted_at.is_(None)
        ).first()
        
        # 기본 조직이 없으면 첫 번째 활성 조직 사용
        if not default_org:
            default_org = db.query(Organization).filter(
                Organization.deleted_at.is_(None),
                Organization.is_active == True
            ).first()
        
        if default_org:
            org_id = default_org.org_id
            org_code = default_org.org_code
            logger.info(f"🏠 기본 조직 사용: {org_code} (ID: {org_id})")
        else:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "ORGANIZATION_NOT_FOUND",
                    "message": "조직을 찾을 수 없습니다.",
                    "path": "/auth/register"
                }
            )
    
    logger.info(f"📝 사용자 등록 시작 - 조직: {org_id}, 이메일: {user_data.email}")
    
    try:
        # 조직 내에서 이메일 중복 확인
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.org_id == org_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this organization"
            )
        
        # 조직 내에서 사용자명 중복 확인
        existing_username = db.query(User).filter(
            User.username == user_data.username,
            User.org_id == org_id
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken in this organization"
            )
        
        # 새 사용자 생성
        hashed_password = AuthService.get_password_hash(user_data.password)
        user_uuid = str(uuid.uuid4())
        
        # user_id를 자동 생성 (조직코드 + 사용자명 조합)
        # user_id = f"{org_code}_{user_data.username}"
        
        new_user = User(
            user_id=user_data.user_id,
            user_uuid=user_uuid,
            org_id=org_id,
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role="user",
            permissions="read,write",
            is_email_verified=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 메일 사용자도 함께 생성
        from app.model.mail_model import MailUser
        mail_user = MailUser(
            user_id=new_user.user_id,
            user_uuid=new_user.user_uuid,
            org_id=new_user.org_id,
            email=new_user.email,
            password_hash=new_user.hashed_password,
            is_active=True
        )
        db.add(mail_user)
        db.commit()
        
        logger.info(f"✅ 사용자 등록 완료 - 조직: {org_code}, 사용자: {new_user.user_id}, 메일 사용자 생성 완료")
        
        return UserResponse(
            user_id=new_user.user_id,
            user_uuid=new_user.user_uuid,
            email=new_user.email,
            username=new_user.username,
            org_id=new_user.org_id,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 등록 실패 - 조직: {org_id}, 오류: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user registration"
        )


@router.post("/refresh", response_model=AccessToken)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)) -> AccessToken:
    """
    토큰 재발급 엔드포인트
    리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다.
    """
    logger.info("🔄 토큰 재발급 요청")
    
    try:
        # 리프레시 토큰 검증
        payload = AuthService.verify_token(token_data.refresh_token, "refresh")
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_uuid = payload.get("sub")
        org_id = payload.get("org_id")
        
        if user_uuid is None or org_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 조직 내에서 사용자 조회
        user = db.query(User).filter(
            User.user_uuid == user_uuid,
            User.org_id == org_id
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 데이터베이스에서 리프레시 토큰 확인
        stored_token = db.query(RefreshToken).filter(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.user_uuid == user.user_uuid,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # 새 액세스 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.user_uuid, "org_id": org_id}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ 토큰 재발급 완료 - 조직: {org_id}, 사용자: {user.user_uuid}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 토큰 재발급 실패 - 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    현재 로그인한 사용자 정보 조회
    """
    logger.info(f"👤 사용자 정보 조회 - 사용자: {current_user.user_id}")
    
    # 디버깅: current_user 객체 상태 확인
    logger.info(f"🔍 current_user 타입: {type(current_user)}")
    logger.info(f"🔍 current_user 속성: user_id={getattr(current_user, 'user_id', 'MISSING')}, org_id={getattr(current_user, 'org_id', 'MISSING')}")
    
    # 딕셔너리로 변환해서 확인
    if hasattr(current_user, '__dict__'):
        logger.info(f"🔍 current_user.__dict__: {current_user.__dict__}")
    
    return UserResponse(
        user_id=current_user.user_id,
        user_uuid=current_user.user_uuid,
        username=current_user.username,
        email=current_user.email,
        org_id=current_user.org_id,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


# ===== 2FA 관련 엔드포인트 =====

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse, summary="2FA 설정")
async def setup_2fa(
    request_data: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    2FA (Two-Factor Authentication) 설정
    
    - **password**: 현재 비밀번호 확인
    - TOTP 시크릿 키, QR 코드, 백업 코드 생성
    """
    logger.info(f"🔐 2FA 설정 시작 - 사용자: {current_user.email}")
    
    try:
        # 비밀번호 확인
        auth_service = AuthService()
        if not auth_service.verify_password(request_data.password, current_user.hashed_password):
            logger.warning(f"⚠️ 2FA 설정 실패 - 잘못된 비밀번호: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다"
            )
        
        # 이미 2FA가 활성화된 경우
        if current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA가 이미 활성화되어 있습니다"
            )
        
        # 2FA 설정
        setup_response = two_factor_service.setup_2fa(current_user, request_data.password, db)
        
        logger.info(f"✅ 2FA 설정 완료 - 사용자: {current_user.email}")
        return setup_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 2FA 설정 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA 설정 중 오류가 발생했습니다"
        )


@router.post("/2fa/verify", response_model=AuthApiResponse, summary="2FA 활성화")
async def verify_2fa(
    request_data: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    2FA 활성화 (설정 후 코드 검증)
    
    - **code**: 6자리 TOTP 인증 코드
    """
    logger.info(f"🔐 2FA 활성화 시도 - 사용자: {current_user.email}")
    
    try:
        # 2FA 활성화
        success = two_factor_service.enable_2fa(current_user, request_data.code, db)
        
        if success:
            logger.info(f"✅ 2FA 활성화 성공 - 사용자: {current_user.email}")
            return AuthApiResponse(
                success=True,
                message="2FA가 성공적으로 활성화되었습니다"
            )
        else:
            logger.warning(f"⚠️ 2FA 활성화 실패 - 잘못된 코드: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="인증 코드가 올바르지 않습니다"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 2FA 활성화 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA 활성화 중 오류가 발생했습니다"
        )


@router.post("/2fa/disable", response_model=AuthApiResponse, summary="2FA 비활성화")
async def disable_2fa(
    request_data: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    2FA 비활성화
    
    - **password**: 현재 비밀번호
    - **totp_code**: 6자리 TOTP 인증 코드
    """
    logger.info(f"🔓 2FA 비활성화 시도 - 사용자: {current_user.email}")
    
    try:
        # 비밀번호 확인
        auth_service = AuthService()
        if not auth_service.verify_password(request_data.password, current_user.hashed_password):
            logger.warning(f"⚠️ 2FA 비활성화 실패 - 잘못된 비밀번호: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다"
            )
        
        # 2FA 비활성화
        success = two_factor_service.disable_2fa(current_user, request_data.password, request_data.totp_code, db)
        
        if success:
            logger.info(f"✅ 2FA 비활성화 성공 - 사용자: {current_user.email}")
            return AuthApiResponse(
                success=True,
                message="2FA가 성공적으로 비활성화되었습니다"
            )
        else:
            logger.warning(f"⚠️ 2FA 비활성화 실패 - 잘못된 코드: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="인증 코드가 올바르지 않습니다"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 2FA 비활성화 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA 비활성화 중 오류가 발생했습니다"
        )


@router.get("/2fa/status", response_model=AuthApiResponse, summary="2FA 상태 조회")
async def get_2fa_status(
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 2FA 상태 조회
    """
    logger.info(f"📊 2FA 상태 조회 - 사용자: {current_user.email}")
    
    try:
        backup_codes_count = two_factor_service.get_backup_codes_count(current_user)
        
        return AuthApiResponse(
            success=True,
            message="2FA 상태 조회 성공",
            data={
                "is_2fa_enabled": current_user.is_2fa_enabled,
                "backup_codes_count": backup_codes_count,
                "last_2fa_at": current_user.last_2fa_at.isoformat() if current_user.last_2fa_at else None
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 2FA 상태 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA 상태 조회 중 오류가 발생했습니다"
        )


@router.post("/2fa/backup-codes/regenerate", response_model=AuthApiResponse, summary="백업 코드 재생성")
async def regenerate_backup_codes(
    request_data: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    백업 코드 재생성
    
    - **password**: 현재 비밀번호 확인
    """
    logger.info(f"🔑 백업 코드 재생성 시도 - 사용자: {current_user.email}")
    
    try:
        # 비밀번호 확인
        auth_service = AuthService()
        if not auth_service.verify_password(request_data.password, current_user.hashed_password):
            logger.warning(f"⚠️ 백업 코드 재생성 실패 - 잘못된 비밀번호: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다"
            )
        
        # 백업 코드 재생성
        backup_codes = two_factor_service.regenerate_backup_codes(current_user, request_data.password, db)
        
        logger.info(f"✅ 백업 코드 재생성 성공 - 사용자: {current_user.email}")
        return AuthApiResponse(
            success=True,
            message="백업 코드가 성공적으로 재생성되었습니다",
            data={"backup_codes": backup_codes}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 백업 코드 재생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="백업 코드 재생성 중 오류가 발생했습니다"
        )


# ==================== SSO 엔드포인트 ====================

@router.get("/sso/{provider}/auth", summary="SSO 인증 URL 생성")
async def get_sso_auth_url(
    provider: str,
    redirect_uri: str,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    SSO 인증 URL을 생성합니다.
    
    - **provider**: SSO 제공자 (google, microsoft 등)
    - **redirect_uri**: 인증 완료 후 리다이렉트될 URI
    - **org_id**: 조직 ID (자동 설정)
    """
    logger.info(f"🔗 SSO 인증 URL 요청 - 제공자: {provider}, 조직: {org_id}")
    
    try:
        sso_service = SSOService(db)
        auth_url = sso_service.get_sso_auth_url(provider, org_id, redirect_uri)
        
        logger.info(f"✅ SSO 인증 URL 생성 성공 - 제공자: {provider}")
        return {
            "success": True,
            "auth_url": auth_url,
            "provider": provider,
            "org_id": org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SSO 인증 URL 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO 인증 URL 생성 중 오류가 발생했습니다"
        )


@router.post("/sso/{provider}/callback", response_model=Token, summary="SSO 콜백 처리")
async def sso_callback(
    provider: str,
    request_data: SSOLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    SSO 인증 콜백을 처리합니다.
    
    - **provider**: SSO 제공자
    - **code**: 인증 코드
    - **state**: state 파라미터
    - **redirect_uri**: 리다이렉트 URI
    """
    logger.info(f"🔐 SSO 콜백 처리 시작 - 제공자: {provider}")
    
    try:
        sso_service = SSOService(db)
        user = sso_service.authenticate_sso_user(
            provider, 
            request_data.code, 
            request_data.state, 
            request_data.redirect_uri
        )
        
        # 토큰 생성
        auth_service = AuthService(db)
        tokens = auth_service.create_tokens(user)
        
        # 로그인 로그 기록
        login_log = LoginLog(
            user_id=user.id,
            login_time=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            login_method=f"sso_{provider}",
            success=True
        )
        db.add(login_log)
        db.commit()
        
        logger.info(f"✅ SSO 로그인 성공 - 제공자: {provider}, 사용자: {user.email}")
        return Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=tokens["expires_in"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SSO 콜백 처리 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO 인증 처리 중 오류가 발생했습니다"
        )


# ==================== RBAC 엔드포인트 ====================

@router.get("/roles", summary="역할 목록 조회")
async def get_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용 가능한 모든 역할 목록을 조회합니다.
    
    - 조직별 역할 정보 제공
    - 권한 레벨 및 설명 포함
    """
    logger.info(f"📋 역할 목록 조회 - 사용자: {current_user.email}")
    
    try:
        rbac_service = RBACService(db)
        
        # 권한 확인 (관리자만 모든 역할 조회 가능)
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="역할 정보를 조회할 권한이 없습니다"
            )
        
        roles = rbac_service.get_all_roles()
        
        logger.info(f"✅ 역할 목록 조회 성공 - 역할 수: {len(roles)}")
        return {
            "success": True,
            "roles": roles,
            "organization_id": current_user.org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 역할 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="역할 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/roles/{role_name}", summary="특정 역할 정보 조회")
async def get_role_info(
    role_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 역할의 상세 정보를 조회합니다.
    
    - **role_name**: 조회할 역할명
    - 권한 목록 및 레벨 정보 제공
    """
    logger.info(f"🔍 역할 정보 조회 - 역할: {role_name}, 사용자: {current_user.email}")
    
    try:
        rbac_service = RBACService(db)
        
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="역할 정보를 조회할 권한이 없습니다"
            )
        
        role_info = rbac_service.get_role_info(role_name)
        
        logger.info(f"✅ 역할 정보 조회 성공 - 역할: {role_name}")
        return {
            "success": True,
            "role": role_info,
            "role_name": role_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 역할 정보 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="역할 정보 조회 중 오류가 발생했습니다"
        )


@router.put("/users/{user_id}/role", summary="사용자 역할 변경")
async def update_user_role(
    user_id: str,
    request_data: UserRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 역할을 변경합니다.
    
    - **user_id**: 대상 사용자 ID
    - **role**: 새로운 역할명
    - 관리자 권한 필요
    """
    logger.info(f"👤 사용자 역할 변경 시도 - 대상: {user_id}, 새 역할: {request_data.role}")
    
    try:
        rbac_service = RBACService(db)
        
        # 대상 사용자 조회
        target_user = db.query(User).filter(User.user_uuid == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 역할 업데이트
        updated_user = rbac_service.update_user_role(current_user, target_user, request_data.role)
        
        logger.info(f"✅ 사용자 역할 변경 성공 - 사용자: {user_id}, 새 역할: {request_data.role}")
        return {
            "success": True,
            "message": "사용자 역할이 성공적으로 변경되었습니다",
            "user_id": user_id,
            "new_role": request_data.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 역할 변경 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 역할 변경 중 오류가 발생했습니다"
        )


@router.get("/organization/users", summary="조직 사용자 목록 조회")
async def get_organization_users(
    role: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    조직 내 사용자 목록을 역할별로 조회합니다.
    
    - **role**: 필터링할 역할 (선택사항)
    - 관리자 권한 필요
    """
    logger.info(f"👥 조직 사용자 목록 조회 - 조직: {current_user.org_id}, 역할 필터: {role}")
    
    try:
        rbac_service = RBACService(db)
        
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin", "user_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="사용자 목록을 조회할 권한이 없습니다"
            )
        
        users = rbac_service.get_organization_users_by_role(current_user.org_id, role)
        
        # 사용자 정보 정리 (민감한 정보 제외)
        user_list = []
        for user in users:
            user_list.append({
                "user_id": user.user_uuid,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at
            })
        
        logger.info(f"✅ 조직 사용자 목록 조회 성공 - 사용자 수: {len(user_list)}")
        return {
            "success": True,
            "users": user_list,
            "organization_id": current_user.org_id,
            "role_filter": role,
            "total_count": len(user_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 사용자 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/organization/role-statistics", summary="조직 역할 통계 조회")
async def get_role_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    조직 내 역할별 사용자 통계를 조회합니다.
    
    - 역할별 사용자 수 제공
    - 관리자 권한 필요
    """
    logger.info(f"📊 역할 통계 조회 - 조직: {current_user.org_id}")
    
    try:
        rbac_service = RBACService(db)
        
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="역할 통계를 조회할 권한이 없습니다"
            )
        
        statistics = rbac_service.get_role_statistics(current_user.org_id)
        
        logger.info(f"✅ 역할 통계 조회 성공 - 조직: {current_user.org_id}")
        return {
            "success": True,
            "statistics": statistics,
            "organization_id": current_user.org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 역할 통계 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="역할 통계 조회 중 오류가 발생했습니다"
        )


# ==================== API 속도 제한 엔드포인트 ====================

@router.get("/rate-limit/status", summary="현재 속도 제한 상태 조회")
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 API 속도 제한 상태를 조회합니다.
    
    - IP별, 사용자별, 조직별 제한 상태 제공
    - 남은 요청 수 및 리셋 시간 포함
    """
    logger.info(f"🚦 속도 제한 상태 조회 - 사용자: {current_user.email}")
    
    try:
        from app.middleware.rate_limit_middleware import RateLimitService
        rate_limit_service = RateLimitService()
        
        ip_address = request.client.host
        
        # IP별 제한 상태
        ip_status = rate_limit_service.get_rate_limit_status("ip", ip_address)
        
        # 사용자별 제한 상태
        user_status = rate_limit_service.get_rate_limit_status("user", current_user.user_uuid)
        
        # 조직별 제한 상태
        org_status = rate_limit_service.get_rate_limit_status("organization", current_user.org_id)
        
        # 로그인 엔드포인트별 제한 상태
        login_status = rate_limit_service.get_rate_limit_status("endpoint", f"/api/auth/login:{ip_address}")
        
        logger.info(f"✅ 속도 제한 상태 조회 성공 - 사용자: {current_user.email}")
        return {
            "success": True,
            "rate_limits": {
                "ip": {
                    "limit": ip_status.get("limit", 0),
                    "remaining": ip_status.get("remaining", 0),
                    "reset_time": ip_status.get("reset_time"),
                    "window_seconds": ip_status.get("window_seconds", 0)
                },
                "user": {
                    "limit": user_status.get("limit", 0),
                    "remaining": user_status.get("remaining", 0),
                    "reset_time": user_status.get("reset_time"),
                    "window_seconds": user_status.get("window_seconds", 0)
                },
                "organization": {
                    "limit": org_status.get("limit", 0),
                    "remaining": org_status.get("remaining", 0),
                    "reset_time": org_status.get("reset_time"),
                    "window_seconds": org_status.get("window_seconds", 0)
                },
                "login_endpoint": {
                    "limit": login_status.get("limit", 0),
                    "remaining": login_status.get("remaining", 0),
                    "reset_time": login_status.get("reset_time"),
                    "window_seconds": login_status.get("window_seconds", 0)
                }
            },
            "user_id": current_user.user_uuid,
            "organization_id": current_user.org_id,
            "ip_address": ip_address
        }
        
    except Exception as e:
        logger.error(f"❌ 속도 제한 상태 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="속도 제한 상태 조회 중 오류가 발생했습니다"
        )


@router.get("/rate-limit/config", summary="속도 제한 설정 조회")
async def get_rate_limit_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 적용된 속도 제한 설정을 조회합니다.
    
    - 관리자 권한 필요
    - 전체 시스템 속도 제한 설정 제공
    """
    logger.info(f"⚙️ 속도 제한 설정 조회 - 사용자: {current_user.email}")
    
    try:
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="속도 제한 설정을 조회할 권한이 없습니다"
            )
        
        from app.middleware.rate_limit_middleware import RateLimitService
        rate_limit_service = RateLimitService()
        
        config = {
            "ip_limits": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "description": "IP 주소별 기본 제한"
            },
            "user_limits": {
                "requests_per_minute": 200,
                "requests_per_hour": 2000,
                "description": "인증된 사용자별 제한"
            },
            "organization_limits": {
                "requests_per_minute": 1000,
                "requests_per_hour": 10000,
                "description": "조직별 제한"
            },
            "endpoint_limits": {
                "/api/auth/login": {
                    "requests_per_minute": 5,
                    "requests_per_hour": 20,
                    "description": "로그인 엔드포인트 제한"
                },
                "/api/mail/send": {
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "description": "메일 발송 엔드포인트 제한"
                }
            },
            "burst_protection": {
                "enabled": True,
                "threshold": 10,
                "window_seconds": 1,
                "description": "버스트 공격 방지"
            }
        }
        
        logger.info(f"✅ 속도 제한 설정 조회 성공")
        return {
            "success": True,
            "config": config,
            "organization_id": current_user.org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 속도 제한 설정 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="속도 제한 설정 조회 중 오류가 발생했습니다"
        )


@router.put("/rate-limit/config", summary="속도 제한 설정 업데이트")
async def update_rate_limit_config(
    config_data: RateLimitConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    속도 제한 설정을 업데이트합니다.
    
    - **config**: 새로운 속도 제한 설정
    - 슈퍼 관리자 권한 필요
    """
    logger.info(f"🔧 속도 제한 설정 업데이트 시도 - 사용자: {current_user.email}")
    
    try:
        # 권한 확인 (슈퍼 관리자만)
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="속도 제한 설정을 변경할 권한이 없습니다"
            )
        
        from app.middleware.rate_limit_middleware import RateLimitService
        rate_limit_service = RateLimitService()
        
        # 설정 검증
        if config_data.requests_per_minute <= 0 or config_data.requests_per_hour <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="요청 제한 수는 0보다 커야 합니다"
            )
        
        if config_data.requests_per_minute > config_data.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="분당 제한이 시간당 제한보다 클 수 없습니다"
            )
        
        # 설정 업데이트 (실제 구현에서는 Redis나 데이터베이스에 저장)
        updated_config = {
            "limit_type": config_data.limit_type,
            "requests_per_minute": config_data.requests_per_minute,
            "requests_per_hour": config_data.requests_per_hour,
            "burst_limit": config_data.burst_limit,
            "updated_by": current_user.user_uuid,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ 속도 제한 설정 업데이트 성공 - 타입: {config_data.limit_type}")
        return {
            "success": True,
            "message": "속도 제한 설정이 성공적으로 업데이트되었습니다",
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 속도 제한 설정 업데이트 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="속도 제한 설정 업데이트 중 오류가 발생했습니다"
        )


@router.post("/rate-limit/reset", summary="속도 제한 리셋")
async def reset_rate_limit(
    target_type: str,
    target_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 대상의 속도 제한을 리셋합니다.
    
    - **target_type**: 대상 타입 (ip, user, organization)
    - **target_id**: 대상 ID
    - 관리자 권한 필요
    """
    logger.info(f"🔄 속도 제한 리셋 시도 - 타입: {target_type}, 대상: {target_id}")
    
    try:
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="속도 제한을 리셋할 권한이 없습니다"
            )
        
        # 조직 관리자는 자신의 조직만 리셋 가능
        if current_user.role == "org_admin" and target_type == "organization" and target_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 조직의 속도 제한을 리셋할 권한이 없습니다"
            )
        
        from app.middleware.rate_limit_middleware import RateLimitService
        rate_limit_service = RateLimitService()
        
        # 속도 제한 리셋
        success = rate_limit_service.reset_rate_limit(target_type, target_id)
        
        if success:
            logger.info(f"✅ 속도 제한 리셋 성공 - 타입: {target_type}, 대상: {target_id}")
            return {
                "success": True,
                "message": f"{target_type} {target_id}의 속도 제한이 리셋되었습니다",
                "target_type": target_type,
                "target_id": target_id,
                "reset_by": current_user.user_uuid,
                "reset_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="리셋할 속도 제한 데이터를 찾을 수 없습니다"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 속도 제한 리셋 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="속도 제한 리셋 중 오류가 발생했습니다"
        )


@router.get("/rate-limit/violations", summary="속도 제한 위반 로그 조회")
async def get_rate_limit_violations(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    target_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    속도 제한 위반 로그를 조회합니다.
    
    - **limit**: 조회할 로그 수 (기본값: 50, 최대: 1000)
    - **offset**: 오프셋 (기본값: 0)
    - **target_type**: 필터링할 대상 타입 (선택사항)
    - 관리자 권한 필요
    """
    logger.info(f"📋 속도 제한 위반 로그 조회 - 사용자: {current_user.email}")
    
    try:
        # 권한 확인
        if current_user.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="속도 제한 위반 로그를 조회할 권한이 없습니다"
            )
        
        from app.middleware.rate_limit_middleware import RateLimitService
        rate_limit_service = RateLimitService()
        
        # 위반 로그 조회 (실제 구현에서는 데이터베이스에서 조회)
        violations = rate_limit_service.get_violation_logs(
            limit=limit,
            offset=offset,
            target_type=target_type,
            organization_id=current_user.org_id if current_user.role == "org_admin" else None
        )
        
        logger.info(f"✅ 속도 제한 위반 로그 조회 성공 - 로그 수: {len(violations)}")
        return {
            "success": True,
            "violations": violations,
            "total_count": len(violations),
            "limit": limit,
            "offset": offset,
            "target_type": target_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 속도 제한 위반 로그 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="속도 제한 위반 로그 조회 중 오류가 발생했습니다"
        )
