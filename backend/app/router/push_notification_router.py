"""
푸시 알림 API 라우터

SkyBoot Mail SaaS 프로젝트의 푸시 알림 기능을 위한 API 엔드포인트입니다.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas.push_notification_schema import (
    NotificationAction, NotificationPayload, DeviceSubscription, NotificationPreference,
    PushNotification, NotificationTemplate, SubscriptionRequest, SubscriptionResponse,
    NotificationSendRequest, NotificationSendResponse, NotificationStatusResponse,
    NotificationPreferenceRequest, NotificationPreferenceResponse,
    NotificationTemplateRequest, NotificationTemplateResponse,
    NotificationHistoryResponse, NotificationStatsResponse,
    WebPushConfigRequest, WebPushConfigResponse, NotificationTestRequest,
    NotificationType, NotificationPriority, DeliveryStatus, DeviceType,
    SubscriptionStatus, NotificationChannel
)
from app.service.push_notification_service import PushNotificationService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_organization
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import get_db

router = APIRouter()

@router.post("/subscribe", summary="푸시 알림 구독")
async def subscribe_to_notifications(
    subscription_request: SubscriptionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> SubscriptionResponse:
    """
    푸시 알림을 구독합니다.
    
    - **endpoint**: 푸시 서비스 엔드포인트
    - **keys**: 암호화 키 (p256dh, auth)
    - **device_type**: 디바이스 타입 (web, android, ios)
    - **device_name**: 디바이스 이름
    - **user_agent**: 사용자 에이전트
    """
    service = PushNotificationService(db)
    user_agent = request.headers.get("User-Agent", "")
    client_ip = request.client.host if request.client else ""
    
    return await service.subscribe_device(
        organization.id,
        current_user.id,
        subscription_request,
        user_agent,
        client_ip
    )


@router.delete("/subscribe/{subscription_id}", summary="푸시 알림 구독 해제")
async def unsubscribe_from_notifications(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    푸시 알림 구독을 해제합니다.
    
    - **subscription_id**: 구독 해제할 구독 ID
    """
    service = PushNotificationService(db)
    return await service.unsubscribe_device(
        organization.id,
        current_user.id,
        subscription_id
    )


@router.get("/subscriptions", summary="구독 목록 조회")
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 푸시 알림 구독 목록을 조회합니다.
    
    - **subscriptions**: 구독 목록
    - **active_count**: 활성 구독 수
    - **total_count**: 전체 구독 수
    """
    service = PushNotificationService(db)
    return await service.get_user_subscriptions(
        organization.id,
        current_user.id
    )


@router.post("/send", summary="푸시 알림 발송")
async def send_notification(
    notification_request: NotificationSendRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationSendResponse:
    """
    푸시 알림을 발송합니다.
    
    - **recipient_ids**: 수신자 ID 목록
    - **title**: 알림 제목
    - **body**: 알림 내용
    - **type**: 알림 타입 (email, calendar, task, system)
    - **priority**: 알림 우선순위 (low, normal, high, urgent)
    - **data**: 추가 데이터
    - **actions**: 알림 액션 버튼
    """
    service = PushNotificationService(db)
    return await service.send_notification(
        organization.id,
        current_user.id,
        notification_request
    )


@router.post("/send/broadcast", summary="브로드캐스트 알림 발송")
async def send_broadcast_notification(
    notification_request: NotificationSendRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationSendResponse:
    """
    조직 전체에 브로드캐스트 알림을 발송합니다.
    
    - **title**: 알림 제목
    - **body**: 알림 내용
    - **type**: 알림 타입
    - **priority**: 알림 우선순위
    - **data**: 추가 데이터
    """
    service = PushNotificationService(db)
    return await service.send_broadcast_notification(
        organization.id,
        current_user.id,
        notification_request
    )


@router.post("/send/scheduled", summary="예약 알림 발송")
async def send_scheduled_notification(
    notification_request: NotificationSendRequest,
    scheduled_at: str = Query(..., description="발송 예약 시간 (ISO 8601)"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationSendResponse:
    """
    예약된 시간에 푸시 알림을 발송합니다.
    
    - **scheduled_at**: 발송 예약 시간
    - **notification_request**: 알림 요청 데이터
    """
    service = PushNotificationService(db)
    return await service.send_scheduled_notification(
        organization.id,
        current_user.id,
        notification_request,
        scheduled_at
    )


@router.get("/status/{notification_id}", summary="알림 발송 상태 조회")
async def get_notification_status(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationStatusResponse:
    """
    특정 알림의 발송 상태를 조회합니다.
    
    - **notification_id**: 조회할 알림 ID
    - **status**: 발송 상태 (pending, sent, delivered, failed)
    - **sent_count**: 발송된 수
    - **delivered_count**: 전달된 수
    - **failed_count**: 실패한 수
    """
    service = PushNotificationService(db)
    return await service.get_notification_status(
        organization.id,
        notification_id
    )


@router.get("/preferences", summary="알림 설정 조회")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationPreferenceResponse:
    """
    사용자의 알림 설정을 조회합니다.
    
    - **enabled**: 알림 활성화 여부
    - **channels**: 활성화된 알림 채널
    - **types**: 수신할 알림 타입
    - **quiet_hours**: 무음 시간대
    - **frequency**: 알림 빈도 설정
    """
    service = PushNotificationService(db)
    return await service.get_notification_preferences(
        organization.id,
        current_user.id
    )


@router.put("/preferences", summary="알림 설정 업데이트")
async def update_notification_preferences(
    preference_request: NotificationPreferenceRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationPreferenceResponse:
    """
    사용자의 알림 설정을 업데이트합니다.
    
    - **enabled**: 알림 활성화/비활성화
    - **channels**: 알림 채널 설정
    - **types**: 수신할 알림 타입 설정
    - **quiet_hours**: 무음 시간대 설정
    - **frequency**: 알림 빈도 설정
    """
    service = PushNotificationService(db)
    return await service.update_notification_preferences(
        organization.id,
        current_user.id,
        preference_request
    )


@router.get("/templates", summary="알림 템플릿 목록")
async def get_notification_templates(
    template_type: Optional[NotificationType] = Query(None, description="템플릿 타입 필터"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 템플릿 목록을 조회합니다.
    
    - **template_type**: 템플릿 타입으로 필터링
    - **templates**: 템플릿 목록
    - **total_count**: 전체 템플릿 수
    """
    service = PushNotificationService(db)
    return await service.get_notification_templates(
        organization.id,
        template_type
    )


@router.post("/templates", summary="알림 템플릿 생성")
async def create_notification_template(
    template_request: NotificationTemplateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationTemplateResponse:
    """
    새로운 알림 템플릿을 생성합니다.
    
    - **name**: 템플릿 이름
    - **type**: 알림 타입
    - **title_template**: 제목 템플릿
    - **body_template**: 내용 템플릿
    - **variables**: 템플릿 변수
    """
    service = PushNotificationService(db)
    return await service.create_notification_template(
        organization.id,
        current_user.id,
        template_request
    )


@router.get("/templates/{template_id}", summary="알림 템플릿 조회")
async def get_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationTemplateResponse:
    """
    특정 알림 템플릿을 조회합니다.
    
    - **template_id**: 조회할 템플릿 ID
    """
    service = PushNotificationService(db)
    return await service.get_notification_template(
        organization.id,
        template_id
    )


@router.put("/templates/{template_id}", summary="알림 템플릿 업데이트")
async def update_notification_template(
    template_id: str,
    template_request: NotificationTemplateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationTemplateResponse:
    """
    알림 템플릿을 업데이트합니다.
    
    - **template_id**: 업데이트할 템플릿 ID
    - **template_request**: 업데이트할 템플릿 데이터
    """
    service = PushNotificationService(db)
    return await service.update_notification_template(
        organization.id,
        template_id,
        template_request,
        current_user.id
    )


@router.delete("/templates/{template_id}", summary="알림 템플릿 삭제")
async def delete_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 템플릿을 삭제합니다.
    
    - **template_id**: 삭제할 템플릿 ID
    """
    service = PushNotificationService(db)
    return await service.delete_notification_template(
        organization.id,
        template_id,
        current_user.id
    )


@router.get("/history", summary="알림 히스토리")
async def get_notification_history(
    notification_type: Optional[NotificationType] = Query(None, description="알림 타입 필터"),
    status: Optional[DeliveryStatus] = Query(None, description="발송 상태 필터"),
    limit: int = Query(50, ge=1, le=200, description="조회할 알림 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationHistoryResponse:
    """
    알림 발송 히스토리를 조회합니다.
    
    - **notification_type**: 알림 타입으로 필터링
    - **status**: 발송 상태로 필터링
    - **limit**: 조회할 알림 수
    - **offset**: 페이지네이션 오프셋
    """
    service = PushNotificationService(db)
    return await service.get_notification_history(
        organization.id,
        current_user.id,
        notification_type,
        status,
        limit,
        offset
    )


@router.get("/stats", summary="알림 통계")
async def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> NotificationStatsResponse:
    """
    알림 발송 통계를 조회합니다.
    
    - **total_sent**: 총 발송 수
    - **total_delivered**: 총 전달 수
    - **total_failed**: 총 실패 수
    - **delivery_rate**: 전달률
    - **type_breakdown**: 타입별 분석
    - **channel_breakdown**: 채널별 분석
    """
    service = PushNotificationService(db)
    return await service.get_notification_statistics(
        organization.id,
        current_user.id
    )


@router.get("/webpush/config", summary="웹 푸시 설정 조회")
async def get_webpush_config(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> WebPushConfigResponse:
    """
    웹 푸시 설정을 조회합니다.
    
    - **vapid_public_key**: VAPID 공개 키
    - **application_server_key**: 애플리케이션 서버 키
    - **enabled**: 웹 푸시 활성화 여부
    """
    service = PushNotificationService(db)
    return await service.get_webpush_config(organization.id)


@router.put("/webpush/config", summary="웹 푸시 설정 업데이트")
async def update_webpush_config(
    config_request: WebPushConfigRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> WebPushConfigResponse:
    """
    웹 푸시 설정을 업데이트합니다.
    
    - **enabled**: 웹 푸시 활성화/비활성화
    - **vapid_subject**: VAPID 주체 (이메일 또는 URL)
    - **generate_new_keys**: 새 VAPID 키 생성 여부
    """
    service = PushNotificationService(db)
    return await service.update_webpush_config(
        organization.id,
        config_request,
        current_user.id
    )


@router.post("/test", summary="테스트 알림 발송")
async def send_test_notification(
    test_request: NotificationTestRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테스트 알림을 발송합니다.
    
    - **title**: 테스트 알림 제목
    - **body**: 테스트 알림 내용
    - **type**: 알림 타입
    - **target_user_id**: 대상 사용자 ID (선택사항, 기본값: 현재 사용자)
    """
    service = PushNotificationService(db)
    return await service.send_test_notification(
        organization.id,
        current_user.id,
        test_request
    )


@router.post("/mark-read/{notification_id}", summary="알림 읽음 처리")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림을 읽음으로 처리합니다.
    
    - **notification_id**: 읽음 처리할 알림 ID
    """
    service = PushNotificationService(db)
    return await service.mark_notification_as_read(
        organization.id,
        current_user.id,
        notification_id
    )


@router.post("/mark-read/all", summary="모든 알림 읽음 처리")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 모든 알림을 읽음으로 처리합니다.
    
    - **marked_count**: 읽음 처리된 알림 수
    """
    service = PushNotificationService(db)
    return await service.mark_all_notifications_as_read(
        organization.id,
        current_user.id
    )


@router.get("/unread/count", summary="읽지 않은 알림 수")
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 읽지 않은 알림 수를 조회합니다.
    
    - **unread_count**: 읽지 않은 알림 수
    - **by_type**: 타입별 읽지 않은 알림 수
    """
    service = PushNotificationService(db)
    return await service.get_unread_notification_count(
        organization.id,
        current_user.id
    )


@router.delete("/clear/old", summary="오래된 알림 정리")
async def clear_old_notifications(
    days: int = Query(30, ge=1, le=365, description="보관 기간 (일)"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오래된 알림을 정리합니다.
    
    - **days**: 보관 기간 (일)
    - **cleared_count**: 정리된 알림 수
    """
    service = PushNotificationService(db)
    return await service.clear_old_notifications(
        organization.id,
        current_user.id,
        days
    )


@router.get("/channels", summary="알림 채널 목록")
async def get_notification_channels(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용 가능한 알림 채널 목록을 조회합니다.
    
    - **channels**: 알림 채널 목록
    - **supported_features**: 채널별 지원 기능
    """
    service = PushNotificationService(db)
    return await service.get_notification_channels(organization.id)


@router.post("/bulk/send", summary="대량 알림 발송")
async def send_bulk_notifications(
    notifications: List[NotificationSendRequest],
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    대량 알림을 발송합니다.
    
    - **notifications**: 발송할 알림 목록
    - **sent_count**: 발송된 알림 수
    - **failed_count**: 실패한 알림 수
    """
    service = PushNotificationService(db)
    return await service.send_bulk_notifications(
        organization.id,
        current_user.id,
        notifications
    )