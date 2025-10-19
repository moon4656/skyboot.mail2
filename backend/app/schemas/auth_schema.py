"""
인증 관련 스키마 정의

2FA, SSO, RBAC 등 보안 인증 기능을 위한 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """사용자 역할 열거형"""
    SUPER_ADMIN = "super_admin"      # 시스템 관리자
    ORG_ADMIN = "org_admin"          # 조직 관리자
    USER = "user"                    # 일반 사용자
    VIEWER = "viewer"                # 읽기 전용 사용자
    GUEST = "guest"                  # 게스트 사용자


class Permission(str, Enum):
    """권한 열거형"""
    # 사용자 관리
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 메일 관리
    MAIL_SEND = "mail:send"
    MAIL_READ = "mail:read"
    MAIL_DELETE = "mail:delete"
    MAIL_ADMIN = "mail:admin"
    
    # 조직 관리
    ORG_MANAGE = "org:manage"
    ORG_SETTINGS = "org:settings"
    
    # 시스템 관리
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"


# ===== 2FA 관련 스키마 =====

class TwoFactorSetupRequest(BaseModel):
    """2FA 설정 요청"""
    password: str = Field(..., description="현재 비밀번호")


class TwoFactorSetupResponse(BaseModel):
    """2FA 설정 응답"""
    secret: str = Field(..., description="TOTP 시크릿 키")
    qr_code_url: str = Field(..., description="QR 코드 URL")
    backup_codes: List[str] = Field(..., description="백업 코드 목록")


class TwoFactorVerifyRequest(BaseModel):
    """2FA 인증 요청"""
    code: str = Field(..., min_length=6, max_length=6, description="6자리 인증 코드")


class TwoFactorLoginRequest(BaseModel):
    """2FA 로그인 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="TOTP 코드")
    backup_code: Optional[str] = Field(None, description="백업 코드")


class TwoFactorDisableRequest(BaseModel):
    """2FA 비활성화 요청"""
    password: str = Field(..., description="현재 비밀번호")
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP 코드")


# ===== SSO 관련 스키마 =====

class SSOProvider(str, Enum):
    """SSO 제공자 열거형"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    OKTA = "okta"
    SAML = "saml"


class SSOLoginRequest(BaseModel):
    """SSO 로그인 요청"""
    provider: SSOProvider = Field(..., description="SSO 제공자")
    code: Optional[str] = Field(None, description="인증 코드")
    state: Optional[str] = Field(None, description="상태 값")
    redirect_uri: Optional[str] = Field(None, description="리다이렉트 URI")


class SSOConfigRequest(BaseModel):
    """SSO 설정 요청"""
    provider: SSOProvider = Field(..., description="SSO 제공자")
    client_id: str = Field(..., description="클라이언트 ID")
    client_secret: str = Field(..., description="클라이언트 시크릿")
    redirect_uri: str = Field(..., description="리다이렉트 URI")
    domain: Optional[str] = Field(None, description="도메인 제한")
    is_enabled: bool = Field(True, description="활성화 여부")


class SSOConfigResponse(BaseModel):
    """SSO 설정 응답"""
    provider: SSOProvider
    client_id: str
    redirect_uri: str
    domain: Optional[str]
    is_enabled: bool
    auth_url: str = Field(..., description="인증 URL")


# ===== RBAC 관련 스키마 =====

class RoleRequest(BaseModel):
    """역할 요청"""
    name: str = Field(..., min_length=1, max_length=50, description="역할명")
    description: Optional[str] = Field(None, max_length=255, description="역할 설명")
    permissions: List[Permission] = Field(..., description="권한 목록")


class RoleResponse(BaseModel):
    """역할 응답"""
    id: int
    name: str
    description: Optional[str]
    permissions: List[Permission]
    created_at: datetime
    updated_at: Optional[datetime]


class UserRoleAssignRequest(BaseModel):
    """사용자 역할 할당 요청"""
    user_id: str = Field(..., description="사용자 ID")
    role: UserRole = Field(..., description="할당할 역할")
    permissions: Optional[List[Permission]] = Field(None, description="추가 권한")


class UserPermissionResponse(BaseModel):
    """사용자 권한 응답"""
    user_id: str
    role: UserRole
    permissions: List[Permission]
    effective_permissions: List[Permission] = Field(..., description="실제 적용되는 권한")


# ===== 속도 제한 관련 스키마 =====

class RateLimitConfig(BaseModel):
    """속도 제한 설정"""
    endpoint: str = Field(..., description="엔드포인트 경로")
    requests_per_minute: int = Field(..., gt=0, description="분당 요청 수")
    requests_per_hour: int = Field(..., gt=0, description="시간당 요청 수")
    burst_limit: Optional[int] = Field(None, description="버스트 제한")
    is_enabled: bool = Field(True, description="활성화 여부")


class RateLimitStatus(BaseModel):
    """속도 제한 상태"""
    endpoint: str
    current_requests: int = Field(..., description="현재 요청 수")
    limit: int = Field(..., description="제한 수")
    remaining: int = Field(..., description="남은 요청 수")
    reset_time: datetime = Field(..., description="리셋 시간")
    is_limited: bool = Field(..., description="제한 적용 여부")


# ===== 공통 응답 스키마 =====

class AuthResponse(BaseModel):
    """인증 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간(초)")
    user_info: Dict[str, Any] = Field(..., description="사용자 정보")
    requires_2fa: bool = Field(False, description="2FA 필요 여부")


class SecurityEventLog(BaseModel):
    """보안 이벤트 로그"""
    event_type: str = Field(..., description="이벤트 타입")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    ip_address: str = Field(..., description="IP 주소")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    details: Dict[str, Any] = Field(..., description="상세 정보")
    timestamp: datetime = Field(..., description="발생 시간")
    severity: str = Field(..., description="심각도 (low, medium, high, critical)")


class UserRoleUpdateRequest(BaseModel):
    """사용자 역할 변경 요청"""
    role: str = Field(..., min_length=1, max_length=50, description="새로운 역할명")


class AuthApiResponse(BaseModel):
    """인증 API 응답 기본 형식"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    error_code: Optional[str] = Field(None, description="에러 코드")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")