from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserBase
from ..database.user import get_db
from ..model.user_model import User, RefreshToken, LoginLog
from ..schemas import UserCreate, UserResponse, UserLogin, Token, TokenRefresh, AccessToken, MessageResponse, LoginLogCreate
from ..service.auth_service import AuthService, get_current_user
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
                logger.debug(f"📝 로그인 로그 기록 완료 - 상태: {status}")
        except Exception as log_error:
            # 로그 기록 실패는 메인 로직에 영향을 주지 않음
            logger.warning(f"⚠️ 로그인 로그 기록 실패: {str(log_error)}")
    
    try:
        # 사용자 인증 (조직 ID 없이)
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(
            user_credentials.user_id, user_credentials.password
        )
        if not user:
            # 로그인 실패 로그 기록 (안전한 방식)
            safe_log_login_attempt("failed", "Incorrect user id or password")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user id or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 토큰 생성 (create_tokens 메서드에서 리프레시 토큰 저장까지 처리됨)
        tokens = auth_service.create_tokens(user)
        
        # 사용자 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # 로그인 성공 로그 기록 (안전한 방식)
        safe_log_login_attempt("success", None, user.user_uuid)
        
        logger.info(f"✅ 로그인 성공 - 사용자: {user.user_id}, 조직: {user.org_id}")
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        # HTTPException은 다시 발생시킴 (로그는 이미 기록됨)
        raise
    except Exception as e:
        # 기타 예외 발생 시 로그 기록 (안전한 방식)
        logger.error(f"❌ 로그인 시스템 오류 - 사용자 ID: {user_credentials.user_id}, 오류: {str(e)}")
        safe_log_login_attempt("failed", f"System error: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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
