"""
푸시 알림 스키마

SkyBoot Mail SaaS 프로젝트의 푸시 알림 기능을 위한 Pydantic 스키마입니다.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl, model_validator
import uuid


class NotificationType(str, Enum):
    """알림 타입"""
    NEW_MAIL = "new_mail"
    MAIL_SENT = "mail_sent"
    MAIL_FAILED = "mail_failed"
    CALENDAR_REMINDER = "calendar_reminder"
    TASK_REMINDER = "task_reminder"
    SYSTEM_ALERT = "system_alert"
    SECURITY_ALERT = "security_alert"
    QUOTA_WARNING = "quota_warning"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


class NotificationPriority(str, Enum):
    """알림 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(str, Enum):
    """전송 상태"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


class DeviceType(str, Enum):
    """디바이스 타입"""
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"


class SubscriptionStatus(str, Enum):
    """구독 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class NotificationChannel(str, Enum):
    """알림 채널"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class PushNotificationError(Exception):
    """푸시 알림 관련 예외"""
    pass


class SubscriptionError(Exception):
    """구독 관련 예외"""
    pass


class DeliveryError(Exception):
    """전송 관련 예외"""
    pass


# 기본 모델들
class NotificationAction(BaseModel):
    """알림 액션"""
    action_id: str = Field(..., description="액션 ID")
    title: str = Field(..., description="액션 제목")
    icon: Optional[str] = Field(None, description="액션 아이콘")
    url: Optional[str] = Field(None, description="액션 URL")
    data: Optional[Dict[str, Any]] = Field(None, description="액션 데이터")


class NotificationPayload(BaseModel):
    """알림 페이로드"""
    title: str = Field(..., description="알림 제목")
    body: str = Field(..., description="알림 본문")
    icon: Optional[str] = Field(None, description="알림 아이콘")
    badge: Optional[str] = Field(None, description="배지 아이콘")
    image: Optional[str] = Field(None, description="알림 이미지")
    tag: Optional[str] = Field(None, description="알림 태그")
    url: Optional[str] = Field(None, description="클릭 시 이동할 URL")
    actions: Optional[List[NotificationAction]] = Field(None, description="알림 액션 목록")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")
    ttl: Optional[int] = Field(3600, description="TTL (초)")
    silent: Optional[bool] = Field(False, description="무음 알림 여부")
    
    @validator('ttl')
    def validate_ttl(cls, v):
        if v is not None and (v < 0 or v > 86400):  # 최대 24시간
            raise ValueError('TTL은 0-86400 사이여야 합니다.')
        return v


class DeviceSubscription(BaseModel):
    """디바이스 구독 정보"""
    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="구독 ID")
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    device_type: DeviceType = Field(..., description="디바이스 타입")
    endpoint: str = Field(..., description="푸시 서비스 엔드포인트")
    p256dh_key: Optional[str] = Field(None, description="P256DH 키")
    auth_key: Optional[str] = Field(None, description="인증 키")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    status: SubscriptionStatus = Field(SubscriptionStatus.ACTIVE, description="구독 상태")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")


class NotificationPreference(BaseModel):
    """알림 설정"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    notification_type: NotificationType = Field(..., description="알림 타입")
    channels: List[NotificationChannel] = Field(..., description="알림 채널 목록")
    enabled: bool = Field(True, description="활성화 여부")
    quiet_hours_start: Optional[str] = Field(None, description="방해 금지 시작 시간 (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="방해 금지 종료 시간 (HH:MM)")
    timezone: str = Field("UTC", description="시간대")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")
    
    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError('시간 형식은 HH:MM이어야 합니다.')
        return v


class PushNotification(BaseModel):
    """푸시 알림"""
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="알림 ID")
    user_id: Optional[int] = Field(None, description="대상 사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    notification_type: NotificationType = Field(..., description="알림 타입")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="우선순위")
    payload: NotificationPayload = Field(..., description="알림 페이로드")
    target_devices: Optional[List[str]] = Field(None, description="대상 디바이스 ID 목록")
    scheduled_at: Optional[datetime] = Field(None, description="예약 전송 시간")
    sent_at: Optional[datetime] = Field(None, description="전송 시간")
    status: DeliveryStatus = Field(DeliveryStatus.PENDING, description="전송 상태")
    delivery_attempts: int = Field(0, description="전송 시도 횟수")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")


class NotificationTemplate(BaseModel):
    """알림 템플릿"""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="템플릿 ID")
    organization_id: int = Field(..., description="조직 ID")
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")
    is_active: bool = Field(True, description="활성화 여부")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")


# 요청/응답 모델들
class SubscriptionRequest(BaseModel):
    """구독 요청"""
    device_type: DeviceType = Field(..., description="디바이스 타입")
    endpoint: str = Field(..., description="푸시 서비스 엔드포인트")
    p256dh_key: Optional[str] = Field(None, description="P256DH 키")
    auth_key: Optional[str] = Field(None, description="인증 키")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")


class SubscriptionResponse(BaseModel):
    """구독 응답"""
    subscription_id: str = Field(..., description="구독 ID")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    created_at: datetime = Field(..., description="생성 시간")


class NotificationSendRequest(BaseModel):
    """알림 전송 요청"""
    user_ids: Optional[List[int]] = Field(None, description="대상 사용자 ID 목록")
    notification_type: NotificationType = Field(..., description="알림 타입")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="우선순위")
    payload: NotificationPayload = Field(..., description="알림 페이로드")
    channels: Optional[List[NotificationChannel]] = Field(None, description="전송 채널")
    scheduled_at: Optional[datetime] = Field(None, description="예약 전송 시간")
    template_id: Optional[str] = Field(None, description="템플릿 ID")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="템플릿 변수")
    
    @model_validator(mode='before')
    @classmethod
    def validate_request(cls, values):
        if not values.get('user_ids') and not values.get('template_id'):
            if not values.get('payload'):
                raise ValueError('user_ids 또는 template_id가 필요합니다.')
        return values


class NotificationSendResponse(BaseModel):
    """알림 전송 응답"""
    notification_id: str = Field(..., description="알림 ID")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    target_count: int = Field(..., description="대상 수")
    scheduled_at: Optional[datetime] = Field(None, description="예약 전송 시간")
    created_at: datetime = Field(..., description="생성 시간")


class NotificationStatusResponse(BaseModel):
    """알림 상태 응답"""
    notification_id: str = Field(..., description="알림 ID")
    status: DeliveryStatus = Field(..., description="전송 상태")
    sent_count: int = Field(..., description="전송 성공 수")
    failed_count: int = Field(..., description="전송 실패 수")
    pending_count: int = Field(..., description="전송 대기 수")
    delivery_attempts: int = Field(..., description="전송 시도 횟수")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    created_at: datetime = Field(..., description="생성 시간")
    sent_at: Optional[datetime] = Field(None, description="전송 시간")


class PreferenceUpdateRequest(BaseModel):
    """알림 설정 업데이트 요청"""
    notification_type: NotificationType = Field(..., description="알림 타입")
    channels: List[NotificationChannel] = Field(..., description="알림 채널 목록")
    enabled: bool = Field(True, description="활성화 여부")
    quiet_hours_start: Optional[str] = Field(None, description="방해 금지 시작 시간")
    quiet_hours_end: Optional[str] = Field(None, description="방해 금지 종료 시간")
    timezone: str = Field("UTC", description="시간대")


class PreferenceResponse(BaseModel):
    """알림 설정 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    preferences: List[NotificationPreference] = Field(..., description="알림 설정 목록")
    updated_at: datetime = Field(..., description="수정 시간")


class TemplateCreateRequest(BaseModel):
    """템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")


class NotificationTemplateResponse(BaseModel):
    """알림 템플릿 응답"""
    template_id: str = Field(..., description="템플릿 ID")
    organization_id: int = Field(..., description="조직 ID")
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")
    is_active: bool = Field(..., description="활성화 여부")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[NotificationTemplateResponse] = Field(..., description="템플릿 목록")
    total_count: int = Field(..., description="전체 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


class NotificationHistoryResponse(BaseModel):
    """알림 히스토리 응답"""
    notifications: List[PushNotification] = Field(..., description="알림 목록")
    total_count: int = Field(..., description="전체 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


class NotificationStatsResponse(BaseModel):
    """알림 통계 응답"""
    total_sent: int = Field(..., description="총 전송 수")
    total_delivered: int = Field(..., description="총 전달 수")
    total_failed: int = Field(..., description="총 실패 수")
    delivery_rate: float = Field(..., description="전달률 (%)")
    avg_delivery_time: float = Field(..., description="평균 전달 시간 (초)")
    popular_types: List[Dict[str, Any]] = Field(..., description="인기 알림 타입")
    device_breakdown: Dict[str, int] = Field(..., description="디바이스별 분류")
    channel_breakdown: Dict[str, int] = Field(..., description="채널별 분류")
    hourly_stats: List[Dict[str, Any]] = Field(..., description="시간별 통계")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class WebPushConfigResponse(BaseModel):
    """웹 푸시 설정 응답"""
    vapid_public_key: str = Field(..., description="VAPID 공개 키")
    application_server_key: str = Field(..., description="애플리케이션 서버 키")
    supported_features: List[str] = Field(..., description="지원 기능 목록")
    max_payload_size: int = Field(..., description="최대 페이로드 크기")


class TestNotificationRequest(BaseModel):
    """테스트 알림 요청"""
    notification_type: NotificationType = Field(..., description="알림 타입")
    title: str = Field(..., description="테스트 제목")
    body: str = Field(..., description="테스트 본문")
    icon: Optional[str] = Field(None, description="테스트 아이콘")
    url: Optional[str] = Field(None, description="테스트 URL")


class TestNotificationResponse(BaseModel):
    """테스트 알림 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    notification_id: str = Field(..., description="알림 ID")
    sent_at: datetime = Field(..., description="전송 시간")


class NotificationTestRequest(BaseModel):
    """알림 테스트 요청"""
    notification_type: NotificationType = Field(..., description="알림 타입")
    title: str = Field(..., description="테스트 제목")
    body: str = Field(..., description="테스트 본문")
    icon: Optional[str] = Field(None, description="테스트 아이콘")
    url: Optional[str] = Field(None, description="테스트 URL")
    target_devices: Optional[List[str]] = Field(None, description="대상 디바이스 ID 목록")


class WebPushConfigRequest(BaseModel):
    """웹 푸시 설정 요청"""
    vapid_subject: str = Field(..., description="VAPID 주체")
    vapid_public_key: str = Field(..., description="VAPID 공개 키")
    vapid_private_key: str = Field(..., description="VAPID 개인 키")
    gcm_api_key: Optional[str] = Field(None, description="GCM API 키")


# 예외 클래스들

class NotificationError(Exception):
    """알림 오류"""
    pass


class SubscriptionError(Exception):
    """구독 오류"""
    pass


class DeliveryError(Exception):
    """전달 오류"""
    pass


class TemplateError(Exception):
    """템플릿 오류"""
    pass


class NotificationPreferenceRequest(BaseModel):
    """알림 설정 요청"""
    notification_types: List[NotificationType] = Field(..., description="활성화할 알림 타입 목록")
    channels: List[NotificationChannel] = Field(..., description="사용할 채널 목록")
    quiet_hours_start: Optional[str] = Field(None, description="방해 금지 시작 시간 (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="방해 금지 종료 시간 (HH:MM)")
    timezone: str = Field(default="Asia/Seoul", description="시간대")
    language: str = Field(default="ko", description="언어 설정")


class NotificationPreferenceResponse(BaseModel):
    """알림 설정 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    notification_types: List[NotificationType] = Field(..., description="활성화된 알림 타입 목록")
    channels: List[NotificationChannel] = Field(..., description="사용 중인 채널 목록")
    quiet_hours_start: Optional[str] = Field(None, description="방해 금지 시작 시간")
    quiet_hours_end: Optional[str] = Field(None, description="방해 금지 종료 시간")
    timezone: str = Field(..., description="시간대")
    language: str = Field(..., description="언어 설정")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class TemplateCreateRequest(BaseModel):
    """템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")


class TemplateResponse(BaseModel):
    """템플릿 응답"""
    template_id: str = Field(..., description="템플릿 ID")
    organization_id: int = Field(..., description="조직 ID")
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")
    is_active: bool = Field(..., description="활성화 여부")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[TemplateResponse] = Field(..., description="템플릿 목록")
    total_count: int = Field(..., description="전체 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


class NotificationHistoryResponse(BaseModel):
    """알림 히스토리 응답"""
    notifications: List[PushNotification] = Field(..., description="알림 목록")
    total_count: int = Field(..., description="전체 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


class NotificationStatsResponse(BaseModel):
    """알림 통계 응답"""
    total_sent: int = Field(..., description="총 전송 수")
    total_delivered: int = Field(..., description="총 전달 수")
    total_failed: int = Field(..., description="총 실패 수")
    delivery_rate: float = Field(..., description="전달률 (%)")
    avg_delivery_time: float = Field(..., description="평균 전달 시간 (초)")
    popular_types: List[Dict[str, Any]] = Field(..., description="인기 알림 타입")
    device_breakdown: Dict[str, int] = Field(..., description="디바이스별 분류")
    channel_breakdown: Dict[str, int] = Field(..., description="채널별 분류")
    hourly_stats: List[Dict[str, Any]] = Field(..., description="시간별 통계")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class WebPushConfigResponse(BaseModel):
    """웹 푸시 설정 응답"""
    vapid_public_key: str = Field(..., description="VAPID 공개 키")
    application_server_key: str = Field(..., description="애플리케이션 서버 키")
    supported_features: List[str] = Field(..., description="지원 기능 목록")
    max_payload_size: int = Field(..., description="최대 페이로드 크기")


class TestNotificationRequest(BaseModel):
    """테스트 알림 요청"""
    notification_type: NotificationType = Field(..., description="알림 타입")
    title: str = Field(..., description="테스트 제목")
    body: str = Field(..., description="테스트 본문")
    icon: Optional[str] = Field(None, description="테스트 아이콘")
    url: Optional[str] = Field(None, description="테스트 URL")


class TestNotificationResponse(BaseModel):
    """테스트 알림 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    notification_id: str = Field(..., description="알림 ID")
    sent_at: datetime = Field(..., description="전송 시간")


class NotificationTestRequest(BaseModel):
    """알림 테스트 요청"""
    notification_type: NotificationType = Field(..., description="알림 타입")
    title: str = Field(..., description="테스트 제목")
    body: str = Field(..., description="테스트 본문")
    icon: Optional[str] = Field(None, description="테스트 아이콘")
    url: Optional[str] = Field(None, description="테스트 URL")
    target_devices: Optional[List[str]] = Field(None, description="대상 디바이스 ID 목록")


class WebPushConfigRequest(BaseModel):
    """웹 푸시 설정 요청"""
    vapid_subject: str = Field(..., description="VAPID 주체")
    vapid_public_key: str = Field(..., description="VAPID 공개 키")
    vapid_private_key: str = Field(..., description="VAPID 개인 키")
    gcm_api_key: Optional[str] = Field(None, description="GCM API 키")


# 예외 클래스들

class NotificationError(Exception):
    """알림 오류"""
    pass


class SubscriptionError(Exception):
    """구독 오류"""
    pass


class DeliveryError(Exception):
    """전달 오류"""
    pass


class TemplateError(Exception):
    """템플릿 오류"""
    pass


class NotificationTemplateRequest(BaseModel):
    """알림 템플릿 요청"""
    name: str = Field(..., description="템플릿 이름")
    notification_type: NotificationType = Field(..., description="알림 타입")
    title_template: str = Field(..., description="제목 템플릿")
    body_template: str = Field(..., description="본문 템플릿")
    icon: Optional[str] = Field(None, description="기본 아이콘")
    actions: Optional[List[NotificationAction]] = Field(None, description="기본 액션 목록")
    variables: Optional[List[str]] = Field(None, description="사용 가능한 변수 목록")
    is_active: bool = Field(default=True, description="활성화 여부")


# 예외 클래스들

class NotificationError(Exception):
    """알림 오류"""
    pass


class SubscriptionError(Exception):
    """구독 오류"""
    pass


class DeliveryError(Exception):
    """전달 오류"""
    pass


class TemplateError(Exception):
    """템플릿 오류"""
    pass