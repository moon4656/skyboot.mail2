"""
조직 관련 Pydantic 스키마

SaaS 다중 조직 지원을 위한 데이터 검증 및 직렬화 스키마
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, EmailStr
import uuid


class OrganizationBase(BaseModel):
    """조직 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="조직명")
    domain: Optional[str] = Field(None, max_length=100, description="조직 도메인")
    description: Optional[str] = Field(None, max_length=500, description="조직 설명")
    max_users: Optional[int] = Field(None, ge=1, le=10000, description="최대 사용자 수")
    max_storage_gb: Optional[int] = Field(None, ge=1, le=10000, description="최대 저장 공간 (GB)")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="조직 설정")

    @validator('name')
    def validate_name(cls, v):
        """조직명 검증"""
        if not v or not v.strip():
            raise ValueError('조직명은 필수입니다.')
        
        # 특수문자 제한
        forbidden_chars = ['<', '>', '"', "'", '&', '\\', '/', '|']
        if any(char in v for char in forbidden_chars):
            raise ValueError('조직명에 특수문자를 사용할 수 없습니다.')
        
        return v.strip()

    @validator('domain')
    def validate_domain(cls, v):
        """도메인 검증"""
        if v:
            v = v.strip().lower()
            
            # 기본 도메인 형식 검증
            import re
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(domain_pattern, v):
                raise ValueError('올바른 도메인 형식이 아닙니다.')
            
            # 길이 제한
            if len(v) > 253:
                raise ValueError('도메인이 너무 깁니다.')
        
        return v

    @validator('settings')
    def validate_settings(cls, v):
        """설정 검증"""
        if v is None:
            return {}
        
        # 설정 키 검증
        allowed_keys = {
            'mail_retention_days',
            'max_attachment_size_mb',
            'enable_spam_filter',
            'enable_virus_scan',
            'enable_encryption',
            'backup_enabled',
            'backup_retention_days',
            'notification_settings',
            'security_settings',
            'feature_flags'
        }
        
        for key in v.keys():
            if key not in allowed_keys:
                raise ValueError(f'허용되지 않은 설정 키입니다: {key}')
        
        return v


class OrganizationCreate(OrganizationBase):
    """조직 생성 스키마"""
    org_code: str = Field(..., min_length=2, max_length=50, description="조직 코드 (subdomain용)")
    subdomain: str = Field(..., min_length=2, max_length=50, description="서브도메인")
    
    @validator('org_code')
    def validate_org_code(cls, v):
        """조직 코드 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('조직 코드는 필수입니다.')
        # 영문자, 숫자, 하이픈만 허용
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('조직 코드는 영문자, 숫자, 하이픈만 사용할 수 있습니다.')
        return v
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        """서브도메인 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('서브도메인은 필수입니다.')
        # 영문자, 숫자, 하이픈만 허용 (DNS 규칙)
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('서브도메인은 영문자, 숫자, 하이픈만 사용할 수 있습니다.')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('서브도메인은 하이픈으로 시작하거나 끝날 수 없습니다.')
        return v.lower()


class OrganizationUpdate(BaseModel):
    """조직 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="조직명")
    domain: Optional[str] = Field(None, max_length=100, description="조직 도메인")
    description: Optional[str] = Field(None, max_length=500, description="조직 설명")
    max_users: Optional[int] = Field(None, ge=1, le=10000, description="최대 사용자 수")
    max_storage_gb: Optional[int] = Field(None, ge=1, le=10000, description="최대 저장 공간 (GB)")
    settings: Optional[Dict[str, Any]] = Field(None, description="조직 설정")
    is_active: Optional[bool] = Field(None, description="활성 상태")

    @validator('name')
    def validate_name(cls, v):
        """조직명 검증"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('조직명은 필수입니다.')
            
            # 특수문자 제한
            forbidden_chars = ['<', '>', '"', "'", '&', '\\', '/', '|']
            if any(char in v for char in forbidden_chars):
                raise ValueError('조직명에 특수문자를 사용할 수 없습니다.')
            
            return v.strip()
        return v

    @validator('domain')
    def validate_domain(cls, v):
        """도메인 검증"""
        if v is not None:
            v = v.strip().lower()
            
            # 기본 도메인 형식 검증
            import re
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(domain_pattern, v):
                raise ValueError('올바른 도메인 형식이 아닙니다.')
            
            # 길이 제한
            if len(v) > 253:
                raise ValueError('도메인이 너무 깁니다.')
        
        return v


class OrganizationResponse(OrganizationBase):
    """조직 응답 스키마"""
    org_id: str = Field(..., description="조직 ID")
    org_code: str = Field(..., description="조직 코드")
    subdomain: str = Field(..., description="서브도메인")
    admin_email: str = Field(..., description="관리자 이메일")
    is_active: bool = Field(..., description="활성 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True


class OrganizationSettings(BaseModel):
    """조직 설정 스키마"""
    mail_retention_days: Optional[int] = Field(365, ge=1, le=3650, description="메일 보관 기간 (일)")
    max_attachment_size_mb: Optional[int] = Field(25, ge=1, le=100, description="최대 첨부파일 크기 (MB)")
    enable_spam_filter: Optional[bool] = Field(True, description="스팸 필터 활성화")
    enable_virus_scan: Optional[bool] = Field(True, description="바이러스 검사 활성화")
    enable_encryption: Optional[bool] = Field(False, description="메일 암호화 활성화")
    backup_enabled: Optional[bool] = Field(True, description="백업 활성화")
    backup_retention_days: Optional[int] = Field(30, ge=1, le=365, description="백업 보관 기간 (일)")
    
    # 알림 설정
    notification_settings: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "email_notifications": True,
            "system_alerts": True,
            "security_alerts": True,
            "maintenance_notifications": True
        },
        description="알림 설정"
    )
    
    # 보안 설정
    security_settings: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True
            },
            "session_timeout_minutes": 480,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 30,
            "require_2fa": False
        },
        description="보안 설정"
    )
    
    # 기능 플래그
    feature_flags: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {
            "advanced_search": True,
            "mail_templates": True,
            "auto_reply": True,
            "mail_forwarding": True,
            "calendar_integration": False,
            "mobile_app": True,
            "api_access": True
        },
        description="기능 플래그"
    )


class OrganizationStats(BaseModel):
    """조직 통계 스키마"""
    org_id: str = Field(..., description="조직 ID")
    total_users: int = Field(..., description="총 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    mail_users: int = Field(..., description="메일 사용자 수")
    storage_used_mb: int = Field(..., description="사용된 저장 공간 (MB)")
    storage_limit_mb: int = Field(..., description="저장 공간 제한 (MB)")
    storage_usage_percent: float = Field(..., description="저장 공간 사용률 (%)")
    user_usage_percent: float = Field(..., description="사용자 사용률 (%)")


class OrganizationCreateRequest(BaseModel):
    """조직 생성 요청 스키마"""
    organization: OrganizationCreate = Field(..., description="조직 정보")
    admin_email: EmailStr = Field(..., description="관리자 이메일")
    admin_password: str = Field(..., min_length=8, max_length=100, description="관리자 비밀번호")
    admin_name: Optional[str] = Field(None, max_length=100, description="관리자 이름")

    @validator('admin_password')
    def validate_admin_password(cls, v):
        """관리자 비밀번호 검증"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        
        # 비밀번호 강도 검증
        import re
        
        # 대문자 포함 확인
        if not re.search(r'[A-Z]', v):
            raise ValueError('비밀번호에 대문자가 포함되어야 합니다.')
        
        # 소문자 포함 확인
        if not re.search(r'[a-z]', v):
            raise ValueError('비밀번호에 소문자가 포함되어야 합니다.')
        
        # 숫자 포함 확인
        if not re.search(r'\d', v):
            raise ValueError('비밀번호에 숫자가 포함되어야 합니다.')
        
        # 특수문자 포함 확인
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('비밀번호에 특수문자가 포함되어야 합니다.')
        
        return v


class OrganizationInvite(BaseModel):
    """조직 초대 스키마"""
    email: EmailStr = Field(..., description="초대할 이메일")
    role: str = Field("user", description="사용자 역할")
    message: Optional[str] = Field(None, max_length=500, description="초대 메시지")

    @validator('role')
    def validate_role(cls, v):
        """역할 검증"""
        allowed_roles = ['user', 'admin', 'moderator']
        if v not in allowed_roles:
            raise ValueError(f'허용되지 않은 역할입니다. 허용된 역할: {", ".join(allowed_roles)}')
        return v


class OrganizationMember(BaseModel):
    """조직 구성원 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    user_uuid: str = Field(..., description="사용자 UUID")
    email: str = Field(..., description="이메일")
    full_name: Optional[str] = Field(None, description="전체 이름")
    role: str = Field(..., description="역할")
    is_active: bool = Field(..., description="활성 상태")
    joined_at: datetime = Field(..., description="가입 시간")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")

    class Config:
        from_attributes = True


class OrganizationMemberUpdate(BaseModel):
    """조직 구성원 수정 스키마"""
    role: Optional[str] = Field(None, description="역할")
    is_active: Optional[bool] = Field(None, description="활성 상태")

    @validator('role')
    def validate_role(cls, v):
        """역할 검증"""
        if v is not None:
            allowed_roles = ['user', 'admin', 'moderator']
            if v not in allowed_roles:
                raise ValueError(f'허용되지 않은 역할입니다. 허용된 역할: {", ".join(allowed_roles)}')
        return v


class OrganizationUsage(BaseModel):
    """조직 사용량 스키마"""
    org_id: int = Field(..., description="조직 ID")
    date: datetime = Field(..., description="날짜")
    total_emails_sent: int = Field(0, description="발송된 메일 수")
    total_emails_received: int = Field(0, description="수신된 메일 수")
    storage_used_mb: int = Field(0, description="사용된 저장 공간 (MB)")
    active_users: int = Field(0, description="활성 사용자 수")
    api_requests: int = Field(0, description="API 요청 수")

    class Config:
        from_attributes = True


class OrganizationBilling(BaseModel):
    """조직 청구 정보 스키마"""
    org_id: int = Field(..., description="조직 ID")
    plan_name: str = Field(..., description="요금제명")
    billing_cycle: str = Field(..., description="청구 주기")
    monthly_cost: float = Field(..., description="월 비용")
    next_billing_date: datetime = Field(..., description="다음 청구일")
    payment_status: str = Field(..., description="결제 상태")
    
    # 사용량 기반 청구
    included_users: int = Field(..., description="포함된 사용자 수")
    included_storage_gb: int = Field(..., description="포함된 저장 공간 (GB)")
    additional_user_cost: float = Field(0, description="추가 사용자 비용")
    additional_storage_cost: float = Field(0, description="추가 저장 공간 비용")

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """조직 목록 응답 스키마"""
    organizations: List[OrganizationResponse] = Field(..., description="조직 목록")
    total: int = Field(..., description="전체 조직 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")


class OrganizationStatsResponse(BaseModel):
    """조직 통계 응답 스키마"""
    organization: OrganizationResponse = Field(..., description="조직 정보")
    stats: OrganizationStats = Field(..., description="통계 정보")


class OrganizationSettingsResponse(BaseModel):
    """조직 설정 응답 스키마"""
    organization: OrganizationResponse = Field(..., description="조직 정보")
    settings: OrganizationSettings = Field(..., description="설정 정보")


class OrganizationSettingsUpdate(BaseModel):
    """조직 설정 수정 스키마"""
    mail_retention_days: Optional[int] = Field(None, ge=1, le=3650, description="메일 보관 기간 (일)")
    max_attachment_size_mb: Optional[int] = Field(None, ge=1, le=100, description="최대 첨부파일 크기 (MB)")
    enable_spam_filter: Optional[bool] = Field(None, description="스팸 필터 활성화")
    enable_virus_scan: Optional[bool] = Field(None, description="바이러스 검사 활성화")
    enable_encryption: Optional[bool] = Field(None, description="메일 암호화 활성화")
    backup_enabled: Optional[bool] = Field(None, description="백업 활성화")
    backup_retention_days: Optional[int] = Field(None, ge=1, le=365, description="백업 보관 기간 (일)")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="알림 설정")
    security_settings: Optional[Dict[str, Any]] = Field(None, description="보안 설정")
    feature_flags: Optional[Dict[str, bool]] = Field(None, description="기능 플래그")