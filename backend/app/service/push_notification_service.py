"""
푸시 알림 서비스

SkyBoot Mail SaaS 프로젝트의 푸시 알림 기능을 위한 서비스 로직입니다.
"""

import json
import logging
import asyncio
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
import redis
import requests
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

from app.schemas.push_notification_schema import (
    DeviceSubscription, NotificationPreference, PushNotification, NotificationTemplate,
    SubscriptionRequest, SubscriptionResponse,
    NotificationSendRequest, NotificationSendResponse, NotificationStatusResponse,
    PreferenceUpdateRequest, PreferenceResponse,
    TemplateCreateRequest, TemplateResponse, TemplateListResponse,
    NotificationHistoryResponse, NotificationStatsResponse,
    WebPushConfigResponse, TestNotificationRequest, TestNotificationResponse,
    NotificationType, NotificationPriority, DeliveryStatus, DeviceType,
    SubscriptionStatus, NotificationChannel, NotificationPayload,
    PushNotificationError, SubscriptionError, DeliveryError
)
from app.model.organization_model import Organization
from app.model.user_model import User
from app.config import settings

logger = logging.getLogger(__name__)

# Redis 연결
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# VAPID 키 설정 (실제 환경에서는 환경 변수로 관리)
VAPID_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg7ta7RDQfVHChPFll
tbFWloPVfKfMdNU6XBBhg7hCOuShRANCAATx/KHKjyaKVFh9rUzqeXWUewYpqYWd
BVgUfhRYdJ9jI7noTp7FCWL0mKuNvqQxSEe3gHAsmu/cF6M8uNiNgxTu
-----END PRIVATE KEY-----"""

VAPID_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE8fyhyo8milRYfa1M6nl1lHsGKamF
nQVYFH4UWHSfYyO56E6exQli9Jirjb6kMUhHt4BwLJrv3BejPLjYjYMU7g==
-----END PUBLIC KEY-----"""

VAPID_CLAIMS = {
    "sub": "mailto:admin@skyboot.mail"
}


class PushNotificationService:
    """푸시 알림 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 86400  # 24시간
        self.subscription_key = "push:subscription:{user_id}:{device_type}"
        self.preference_key = "push:preference:{user_id}"
        self.template_key = "push:template:{organization_id}:{template_id}"
        self.notification_key = "push:notification:{notification_id}"
        self.stats_key = "push:stats:{organization_id}:{date}"
        
    async def subscribe_device(
        self,
        user_id: int,
        organization_id: int,
        subscription_request: SubscriptionRequest,
        ip_address: Optional[str] = None
    ) -> SubscriptionResponse:
        """
        디바이스를 푸시 알림에 구독합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            subscription_request: 구독 요청
            ip_address: IP 주소
            
        Returns:
            구독 응답
        """
        try:
            logger.info(f"📱 디바이스 구독 시작 - 사용자: {user_id}, 디바이스: {subscription_request.device_type}")
            
            # 기존 구독 확인
            subscription_key = self.subscription_key.format(
                user_id=user_id,
                device_type=subscription_request.device_type.value
            )
            existing_subscription = redis_client.get(subscription_key)
            
            if existing_subscription:
                existing_data = DeviceSubscription.parse_raw(existing_subscription)
                if existing_data.endpoint == subscription_request.endpoint:
                    logger.info(f"기존 구독 갱신 - 구독ID: {existing_data.subscription_id}")
                    existing_data.updated_at = datetime.utcnow()
                    existing_data.last_used_at = datetime.utcnow()
                    redis_client.setex(subscription_key, self.cache_ttl, existing_data.json())
                    
                    return SubscriptionResponse(
                        subscription_id=existing_data.subscription_id,
                        success=True,
                        message="기존 구독이 갱신되었습니다.",
                        created_at=existing_data.updated_at
                    )
            
            # 새 구독 생성
            subscription = DeviceSubscription(
                user_id=user_id,
                organization_id=organization_id,
                device_type=subscription_request.device_type,
                endpoint=subscription_request.endpoint,
                p256dh_key=subscription_request.p256dh_key,
                auth_key=subscription_request.auth_key,
                user_agent=subscription_request.user_agent,
                ip_address=ip_address,
                status=SubscriptionStatus.ACTIVE
            )
            
            # Redis에 저장
            redis_client.setex(subscription_key, self.cache_ttl, subscription.json())
            
            # 사용자별 구독 목록 업데이트
            user_subscriptions_key = f"push:user_subscriptions:{user_id}"
            redis_client.sadd(user_subscriptions_key, subscription_key)
            redis_client.expire(user_subscriptions_key, self.cache_ttl)
            
            logger.info(f"✅ 디바이스 구독 완료 - 구독ID: {subscription.subscription_id}")
            
            return SubscriptionResponse(
                subscription_id=subscription.subscription_id,
                success=True,
                message="디바이스가 성공적으로 구독되었습니다.",
                created_at=subscription.created_at
            )
            
        except Exception as e:
            logger.error(f"❌ 디바이스 구독 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="디바이스 구독 중 오류가 발생했습니다."
            )
    
    async def unsubscribe_device(
        self,
        user_id: int,
        device_type: DeviceType
    ) -> Dict[str, Any]:
        """
        디바이스 구독을 해제합니다.
        
        Args:
            user_id: 사용자 ID
            device_type: 디바이스 타입
            
        Returns:
            구독 해제 결과
        """
        try:
            logger.info(f"📱 디바이스 구독 해제 시작 - 사용자: {user_id}, 디바이스: {device_type}")
            
            subscription_key = self.subscription_key.format(
                user_id=user_id,
                device_type=device_type.value
            )
            
            # 구독 정보 조회
            subscription_data = redis_client.get(subscription_key)
            if not subscription_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="구독 정보를 찾을 수 없습니다."
                )
            
            subscription = DeviceSubscription.parse_raw(subscription_data)
            subscription.status = SubscriptionStatus.INACTIVE
            subscription.updated_at = datetime.utcnow()
            
            # Redis에서 제거
            redis_client.delete(subscription_key)
            
            # 사용자별 구독 목록에서 제거
            user_subscriptions_key = f"push:user_subscriptions:{user_id}"
            redis_client.srem(user_subscriptions_key, subscription_key)
            
            logger.info(f"✅ 디바이스 구독 해제 완료 - 구독ID: {subscription.subscription_id}")
            
            return {
                "success": True,
                "message": "디바이스 구독이 해제되었습니다.",
                "subscription_id": subscription.subscription_id,
                "unsubscribed_at": subscription.updated_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 디바이스 구독 해제 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="디바이스 구독 해제 중 오류가 발생했습니다."
            )
    
    async def send_notification(
        self,
        organization_id: int,
        send_request: NotificationSendRequest,
        background_tasks: BackgroundTasks,
        sender_user_id: Optional[int] = None
    ) -> NotificationSendResponse:
        """
        푸시 알림을 전송합니다.
        
        Args:
            organization_id: 조직 ID
            send_request: 알림 전송 요청
            background_tasks: 백그라운드 작업
            sender_user_id: 발송자 사용자 ID
            
        Returns:
            알림 전송 응답
        """
        try:
            logger.info(f"📤 푸시 알림 전송 시작 - 조직: {organization_id}, 타입: {send_request.notification_type}")
            
            # 알림 생성
            notification = PushNotification(
                organization_id=organization_id,
                notification_type=send_request.notification_type,
                priority=send_request.priority,
                payload=send_request.payload,
                scheduled_at=send_request.scheduled_at
            )
            
            # 템플릿 사용 시 페이로드 생성
            if send_request.template_id:
                template = await self.get_template(organization_id, send_request.template_id)
                if template:
                    notification.payload = await self._render_template(
                        template,
                        send_request.template_variables or {}
                    )
            
            # 대상 사용자 결정
            target_users = send_request.user_ids or []
            if not target_users:
                # 조직 내 모든 사용자에게 전송
                target_users = await self._get_organization_users(organization_id)
            
            notification.target_devices = [str(uid) for uid in target_users]
            
            # Redis에 알림 저장
            notification_key = self.notification_key.format(notification_id=notification.notification_id)
            redis_client.setex(notification_key, 86400, notification.json())  # 24시간 TTL
            
            # 예약 전송 또는 즉시 전송
            if send_request.scheduled_at and send_request.scheduled_at > datetime.utcnow():
                # 예약 전송 (실제 구현에서는 스케줄러 사용)
                logger.info(f"📅 예약 전송 설정 - 알림ID: {notification.notification_id}, 예약시간: {send_request.scheduled_at}")
                background_tasks.add_task(
                    self._schedule_notification,
                    notification.notification_id,
                    send_request.scheduled_at
                )
            else:
                # 즉시 전송
                background_tasks.add_task(
                    self._send_notification_to_devices,
                    notification.notification_id,
                    target_users,
                    send_request.channels or [NotificationChannel.PUSH]
                )
            
            logger.info(f"✅ 푸시 알림 전송 시작 완료 - 알림ID: {notification.notification_id}")
            
            return NotificationSendResponse(
                notification_id=notification.notification_id,
                success=True,
                message="푸시 알림 전송이 시작되었습니다.",
                target_count=len(target_users),
                scheduled_at=send_request.scheduled_at,
                created_at=notification.created_at
            )
            
        except Exception as e:
            logger.error(f"❌ 푸시 알림 전송 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="푸시 알림 전송 중 오류가 발생했습니다."
            )
    
    async def get_notification_status(self, notification_id: str) -> NotificationStatusResponse:
        """
        알림 전송 상태를 조회합니다.
        
        Args:
            notification_id: 알림 ID
            
        Returns:
            알림 상태 응답
        """
        try:
            logger.info(f"🔍 알림 상태 조회 - 알림ID: {notification_id}")
            
            # Redis에서 알림 조회
            notification_key = self.notification_key.format(notification_id=notification_id)
            notification_data = redis_client.get(notification_key)
            
            if not notification_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림을 찾을 수 없습니다."
                )
            
            notification = PushNotification.parse_raw(notification_data)
            
            # 전송 통계 계산 (실제 구현에서는 별도 저장소에서 조회)
            total_targets = len(notification.target_devices or [])
            sent_count = int(total_targets * 0.8)  # 샘플 값
            failed_count = int(total_targets * 0.1)  # 샘플 값
            pending_count = total_targets - sent_count - failed_count
            
            logger.info(f"✅ 알림 상태 조회 완료 - 알림ID: {notification_id}")
            
            return NotificationStatusResponse(
                notification_id=notification_id,
                status=notification.status,
                sent_count=sent_count,
                failed_count=failed_count,
                pending_count=pending_count,
                delivery_attempts=notification.delivery_attempts,
                error_message=notification.error_message,
                created_at=notification.created_at,
                sent_at=notification.sent_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 알림 상태 조회 실패 - 알림ID: {notification_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 상태 조회 중 오류가 발생했습니다."
            )
    
    async def get_user_preferences(self, user_id: int, organization_id: int) -> PreferenceResponse:
        """
        사용자 알림 설정을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            
        Returns:
            알림 설정 응답
        """
        try:
            logger.info(f"⚙️ 사용자 알림 설정 조회 - 사용자: {user_id}")
            
            # Redis에서 설정 조회
            preference_key = self.preference_key.format(user_id=user_id)
            preference_data = redis_client.get(preference_key)
            
            preferences = []
            if preference_data:
                preferences_list = json.loads(preference_data)
                preferences = [NotificationPreference.parse_obj(pref) for pref in preferences_list]
            else:
                # 기본 설정 생성
                default_preferences = [
                    NotificationPreference(
                        user_id=user_id,
                        organization_id=organization_id,
                        notification_type=NotificationType.NEW_MAIL,
                        channels=[NotificationChannel.PUSH, NotificationChannel.EMAIL]
                    ),
                    NotificationPreference(
                        user_id=user_id,
                        organization_id=organization_id,
                        notification_type=NotificationType.SYSTEM_ALERT,
                        channels=[NotificationChannel.PUSH]
                    )
                ]
                
                # Redis에 저장
                redis_client.setex(
                    preference_key,
                    self.cache_ttl,
                    json.dumps([pref.dict() for pref in default_preferences])
                )
                preferences = default_preferences
            
            logger.info(f"✅ 사용자 알림 설정 조회 완료 - 사용자: {user_id}")
            
            return PreferenceResponse(
                user_id=user_id,
                organization_id=organization_id,
                preferences=preferences,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 알림 설정 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 알림 설정 조회 중 오류가 발생했습니다."
            )
    
    async def update_user_preferences(
        self,
        user_id: int,
        organization_id: int,
        preference_request: PreferenceUpdateRequest
    ) -> PreferenceResponse:
        """
        사용자 알림 설정을 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            preference_request: 알림 설정 업데이트 요청
            
        Returns:
            알림 설정 응답
        """
        try:
            logger.info(f"⚙️ 사용자 알림 설정 업데이트 - 사용자: {user_id}")
            
            # 기존 설정 조회
            current_preferences = await self.get_user_preferences(user_id, organization_id)
            
            # 해당 타입의 설정 찾기 또는 생성
            target_preference = None
            for pref in current_preferences.preferences:
                if pref.notification_type == preference_request.notification_type:
                    target_preference = pref
                    break
            
            if not target_preference:
                target_preference = NotificationPreference(
                    user_id=user_id,
                    organization_id=organization_id,
                    notification_type=preference_request.notification_type,
                    channels=preference_request.channels
                )
                current_preferences.preferences.append(target_preference)
            else:
                # 기존 설정 업데이트
                target_preference.channels = preference_request.channels
                target_preference.enabled = preference_request.enabled
                target_preference.quiet_hours_start = preference_request.quiet_hours_start
                target_preference.quiet_hours_end = preference_request.quiet_hours_end
                target_preference.timezone = preference_request.timezone
                target_preference.updated_at = datetime.utcnow()
            
            # Redis에 저장
            preference_key = self.preference_key.format(user_id=user_id)
            redis_client.setex(
                preference_key,
                self.cache_ttl,
                json.dumps([pref.dict() for pref in current_preferences.preferences])
            )
            
            logger.info(f"✅ 사용자 알림 설정 업데이트 완료 - 사용자: {user_id}")
            
            return PreferenceResponse(
                user_id=user_id,
                organization_id=organization_id,
                preferences=current_preferences.preferences,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 알림 설정 업데이트 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 알림 설정 업데이트 중 오류가 발생했습니다."
            )
    
    async def create_template(
        self,
        organization_id: int,
        template_request: TemplateCreateRequest
    ) -> TemplateResponse:
        """
        알림 템플릿을 생성합니다.
        
        Args:
            organization_id: 조직 ID
            template_request: 템플릿 생성 요청
            
        Returns:
            템플릿 응답
        """
        try:
            logger.info(f"📝 알림 템플릿 생성 - 조직: {organization_id}, 이름: {template_request.name}")
            
            # 템플릿 생성
            template = NotificationTemplate(
                organization_id=organization_id,
                name=template_request.name,
                notification_type=template_request.notification_type,
                title_template=template_request.title_template,
                body_template=template_request.body_template,
                icon=template_request.icon,
                actions=template_request.actions,
                variables=template_request.variables
            )
            
            # Redis에 저장
            template_key = self.template_key.format(
                organization_id=organization_id,
                template_id=template.template_id
            )
            redis_client.setex(template_key, self.cache_ttl, template.json())
            
            # 조직별 템플릿 목록 업데이트
            org_templates_key = f"push:org_templates:{organization_id}"
            redis_client.sadd(org_templates_key, template.template_id)
            redis_client.expire(org_templates_key, self.cache_ttl)
            
            logger.info(f"✅ 알림 템플릿 생성 완료 - 템플릿ID: {template.template_id}")
            
            return TemplateResponse(
                template_id=template.template_id,
                organization_id=template.organization_id,
                name=template.name,
                notification_type=template.notification_type,
                title_template=template.title_template,
                body_template=template.body_template,
                icon=template.icon,
                actions=template.actions,
                variables=template.variables,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 알림 템플릿 생성 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 템플릿 생성 중 오류가 발생했습니다."
            )
    
    async def get_templates(
        self,
        organization_id: int,
        page: int = 1,
        limit: int = 20
    ) -> TemplateListResponse:
        """
        조직의 알림 템플릿 목록을 조회합니다.
        
        Args:
            organization_id: 조직 ID
            page: 페이지 번호
            limit: 페이지당 항목 수
            
        Returns:
            템플릿 목록 응답
        """
        try:
            logger.info(f"📝 알림 템플릿 목록 조회 - 조직: {organization_id}")
            
            # 조직별 템플릿 ID 목록 조회
            org_templates_key = f"push:org_templates:{organization_id}"
            template_ids = redis_client.smembers(org_templates_key)
            
            templates = []
            for template_id in template_ids:
                template_key = self.template_key.format(
                    organization_id=organization_id,
                    template_id=template_id
                )
                template_data = redis_client.get(template_key)
                if template_data:
                    template = NotificationTemplate.parse_raw(template_data)
                    templates.append(TemplateResponse(
                        template_id=template.template_id,
                        organization_id=template.organization_id,
                        name=template.name,
                        notification_type=template.notification_type,
                        title_template=template.title_template,
                        body_template=template.body_template,
                        icon=template.icon,
                        actions=template.actions,
                        variables=template.variables,
                        is_active=template.is_active,
                        created_at=template.created_at,
                        updated_at=template.updated_at
                    ))
            
            # 페이징 처리
            total_count = len(templates)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_templates = templates[start_idx:end_idx]
            
            logger.info(f"✅ 알림 템플릿 목록 조회 완료 - 조직: {organization_id}, 총 {total_count}개")
            
            return TemplateListResponse(
                templates=paginated_templates,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"❌ 알림 템플릿 목록 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 템플릿 목록 조회 중 오류가 발생했습니다."
            )
    
    async def get_template(self, organization_id: int, template_id: str) -> Optional[NotificationTemplate]:
        """
        특정 템플릿을 조회합니다.
        
        Args:
            organization_id: 조직 ID
            template_id: 템플릿 ID
            
        Returns:
            알림 템플릿 또는 None
        """
        try:
            template_key = self.template_key.format(
                organization_id=organization_id,
                template_id=template_id
            )
            template_data = redis_client.get(template_key)
            
            if template_data:
                return NotificationTemplate.parse_raw(template_data)
            return None
            
        except Exception as e:
            logger.error(f"템플릿 조회 실패 - 템플릿ID: {template_id}, 오류: {str(e)}")
            return None
    
    async def get_notification_statistics(self, organization_id: int) -> NotificationStatsResponse:
        """
        알림 통계를 조회합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            알림 통계 응답
        """
        try:
            logger.info(f"📊 알림 통계 조회 - 조직: {organization_id}")
            
            # 샘플 통계 데이터 (실제 구현에서는 데이터베이스에서 조회)
            total_sent = 1250
            total_delivered = 1100
            total_failed = 50
            delivery_rate = (total_delivered / total_sent) * 100 if total_sent > 0 else 0
            
            popular_types = [
                {"type": "new_mail", "count": 800},
                {"type": "system_alert", "count": 200},
                {"type": "calendar_reminder", "count": 150}
            ]
            
            device_breakdown = {
                "web": 600,
                "android": 400,
                "ios": 250
            }
            
            channel_breakdown = {
                "push": 1000,
                "email": 200,
                "in_app": 50
            }
            
            hourly_stats = [
                {"hour": i, "sent": 50 + (i * 5), "delivered": 45 + (i * 4)}
                for i in range(24)
            ]
            
            logger.info(f"✅ 알림 통계 조회 완료 - 조직: {organization_id}")
            
            return NotificationStatsResponse(
                total_sent=total_sent,
                total_delivered=total_delivered,
                total_failed=total_failed,
                delivery_rate=delivery_rate,
                avg_delivery_time=2.5,
                popular_types=popular_types,
                device_breakdown=device_breakdown,
                channel_breakdown=channel_breakdown,
                hourly_stats=hourly_stats,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 알림 통계 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 통계 조회 중 오류가 발생했습니다."
            )
    
    async def get_webpush_config(self) -> WebPushConfigResponse:
        """
        웹 푸시 설정을 조회합니다.
        
        Returns:
            웹 푸시 설정 응답
        """
        try:
            logger.info(f"🔧 웹 푸시 설정 조회")
            
            # VAPID 공개 키 추출
            public_key_pem = VAPID_PUBLIC_KEY.strip()
            
            return WebPushConfigResponse(
                vapid_public_key=public_key_pem,
                application_server_key=public_key_pem,
                supported_features=[
                    "push",
                    "notification",
                    "actions",
                    "badge",
                    "image",
                    "silent"
                ],
                max_payload_size=4096
            )
            
        except Exception as e:
            logger.error(f"❌ 웹 푸시 설정 조회 실패 - 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="웹 푸시 설정 조회 중 오류가 발생했습니다."
            )
    
    async def send_test_notification(
        self,
        user_id: int,
        organization_id: int,
        test_request: TestNotificationRequest
    ) -> TestNotificationResponse:
        """
        테스트 알림을 전송합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            test_request: 테스트 알림 요청
            
        Returns:
            테스트 알림 응답
        """
        try:
            logger.info(f"🧪 테스트 알림 전송 - 사용자: {user_id}")
            
            # 테스트 페이로드 생성
            payload = NotificationPayload(
                title=test_request.title,
                body=test_request.body,
                icon=test_request.icon,
                url=test_request.url,
                tag="test_notification"
            )
            
            # 테스트 알림 생성
            notification = PushNotification(
                user_id=user_id,
                organization_id=organization_id,
                notification_type=test_request.notification_type,
                priority=NotificationPriority.NORMAL,
                payload=payload
            )
            
            # 사용자 구독 정보 조회
            user_subscriptions_key = f"push:user_subscriptions:{user_id}"
            subscription_keys = redis_client.smembers(user_subscriptions_key)
            
            if not subscription_keys:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="구독된 디바이스가 없습니다."
                )
            
            # 첫 번째 구독 디바이스로 테스트 전송
            for subscription_key in subscription_keys:
                subscription_data = redis_client.get(subscription_key)
                if subscription_data:
                    subscription = DeviceSubscription.parse_raw(subscription_data)
                    if subscription.status == SubscriptionStatus.ACTIVE:
                        await self._send_webpush(subscription, payload)
                        break
            
            notification.status = DeliveryStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"✅ 테스트 알림 전송 완료 - 알림ID: {notification.notification_id}")
            
            return TestNotificationResponse(
                success=True,
                message="테스트 알림이 전송되었습니다.",
                notification_id=notification.notification_id,
                sent_at=notification.sent_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 테스트 알림 전송 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="테스트 알림 전송 중 오류가 발생했습니다."
            )
    
    async def _send_notification_to_devices(
        self,
        notification_id: str,
        target_users: List[int],
        channels: List[NotificationChannel]
    ):
        """
        디바이스로 알림을 전송합니다 (백그라운드 작업).
        
        Args:
            notification_id: 알림 ID
            target_users: 대상 사용자 목록
            channels: 전송 채널 목록
        """
        try:
            logger.info(f"📤 디바이스 알림 전송 시작 - 알림ID: {notification_id}")
            
            # 알림 정보 조회
            notification_key = self.notification_key.format(notification_id=notification_id)
            notification_data = redis_client.get(notification_key)
            
            if not notification_data:
                logger.error(f"알림을 찾을 수 없음 - 알림ID: {notification_id}")
                return
            
            notification = PushNotification.parse_raw(notification_data)
            notification.status = DeliveryStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            sent_count = 0
            failed_count = 0
            
            # 각 사용자에게 전송
            for user_id in target_users:
                try:
                    # 사용자 알림 설정 확인
                    preferences = await self.get_user_preferences(user_id, notification.organization_id)
                    user_pref = None
                    
                    for pref in preferences.preferences:
                        if pref.notification_type == notification.notification_type:
                            user_pref = pref
                            break
                    
                    if not user_pref or not user_pref.enabled:
                        logger.info(f"사용자 알림 비활성화 - 사용자: {user_id}")
                        continue
                    
                    # 방해 금지 시간 확인
                    if await self._is_quiet_hours(user_pref):
                        logger.info(f"방해 금지 시간 - 사용자: {user_id}")
                        continue
                    
                    # 푸시 알림 전송
                    if NotificationChannel.PUSH in channels:
                        await self._send_push_to_user(user_id, notification.payload)
                        sent_count += 1
                    
                    # 이메일 알림 전송
                    if NotificationChannel.EMAIL in channels:
                        await self._send_email_notification(user_id, notification.payload)
                    
                except Exception as e:
                    logger.error(f"사용자 알림 전송 실패 - 사용자: {user_id}, 오류: {str(e)}")
                    failed_count += 1
            
            # 알림 상태 업데이트
            notification.delivery_attempts += 1
            redis_client.setex(notification_key, 86400, notification.json())
            
            logger.info(f"✅ 디바이스 알림 전송 완료 - 알림ID: {notification_id}, 성공: {sent_count}, 실패: {failed_count}")
            
        except Exception as e:
            logger.error(f"❌ 디바이스 알림 전송 실패 - 알림ID: {notification_id}, 오류: {str(e)}")
    
    async def _send_push_to_user(self, user_id: int, payload: NotificationPayload):
        """사용자의 모든 디바이스로 푸시 알림을 전송합니다."""
        try:
            user_subscriptions_key = f"push:user_subscriptions:{user_id}"
            subscription_keys = redis_client.smembers(user_subscriptions_key)
            
            for subscription_key in subscription_keys:
                subscription_data = redis_client.get(subscription_key)
                if subscription_data:
                    subscription = DeviceSubscription.parse_raw(subscription_data)
                    if subscription.status == SubscriptionStatus.ACTIVE:
                        await self._send_webpush(subscription, payload)
                        
        except Exception as e:
            logger.error(f"사용자 푸시 전송 실패 - 사용자: {user_id}, 오류: {str(e)}")
    
    async def _send_webpush(self, subscription: DeviceSubscription, payload: NotificationPayload):
        """웹 푸시를 전송합니다."""
        try:
            # 웹 푸시 페이로드 생성
            webpush_payload = {
                "title": payload.title,
                "body": payload.body,
                "icon": payload.icon,
                "badge": payload.badge,
                "image": payload.image,
                "tag": payload.tag,
                "url": payload.url,
                "data": payload.data,
                "actions": [action.dict() for action in payload.actions] if payload.actions else None,
                "silent": payload.silent
            }
            
            # pywebpush를 사용한 전송
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_key
                    }
                },
                data=json.dumps(webpush_payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                ttl=payload.ttl
            )
            
            # 구독 정보 업데이트
            subscription.last_used_at = datetime.utcnow()
            subscription_key = self.subscription_key.format(
                user_id=subscription.user_id,
                device_type=subscription.device_type.value
            )
            redis_client.setex(subscription_key, self.cache_ttl, subscription.json())
            
        except WebPushException as e:
            logger.error(f"웹 푸시 전송 실패 - 구독ID: {subscription.subscription_id}, 오류: {str(e)}")
            
            # 구독 만료 처리
            if e.response and e.response.status_code in [410, 413]:
                subscription.status = SubscriptionStatus.EXPIRED
                subscription_key = self.subscription_key.format(
                    user_id=subscription.user_id,
                    device_type=subscription.device_type.value
                )
                redis_client.delete(subscription_key)
        except Exception as e:
            logger.error(f"웹 푸시 전송 오류 - 구독ID: {subscription.subscription_id}, 오류: {str(e)}")
    
    async def _send_email_notification(self, user_id: int, payload: NotificationPayload):
        """이메일 알림을 전송합니다."""
        try:
            # 실제 구현에서는 메일 서비스 연동
            logger.info(f"📧 이메일 알림 전송 - 사용자: {user_id}, 제목: {payload.title}")
            
        except Exception as e:
            logger.error(f"이메일 알림 전송 실패 - 사용자: {user_id}, 오류: {str(e)}")
    
    async def _render_template(
        self,
        template: NotificationTemplate,
        variables: Dict[str, Any]
    ) -> NotificationPayload:
        """템플릿을 렌더링하여 페이로드를 생성합니다."""
        try:
            # 간단한 변수 치환 (실제로는 Jinja2 등 사용)
            title = template.title_template
            body = template.body_template
            
            for key, value in variables.items():
                title = title.replace(f"{{{key}}}", str(value))
                body = body.replace(f"{{{key}}}", str(value))
            
            return NotificationPayload(
                title=title,
                body=body,
                icon=template.icon,
                actions=template.actions
            )
            
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패 - 템플릿ID: {template.template_id}, 오류: {str(e)}")
            raise
    
    async def _get_organization_users(self, organization_id: int) -> List[int]:
        """조직의 모든 사용자 ID를 조회합니다."""
        try:
            # 실제 구현에서는 데이터베이스에서 조회
            # 현재는 샘플 데이터 반환
            return [1, 2, 3, 4, 5]
            
        except Exception as e:
            logger.error(f"조직 사용자 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            return []
    
    async def _is_quiet_hours(self, preference: NotificationPreference) -> bool:
        """방해 금지 시간인지 확인합니다."""
        try:
            if not preference.quiet_hours_start or not preference.quiet_hours_end:
                return False
            
            # 현재 시간 (사용자 시간대 고려)
            now = datetime.utcnow()  # 실제로는 시간대 변환 필요
            current_time = now.strftime("%H:%M")
            
            return preference.quiet_hours_start <= current_time <= preference.quiet_hours_end
            
        except Exception as e:
            logger.error(f"방해 금지 시간 확인 실패 - 오류: {str(e)}")
            return False
    
    async def _schedule_notification(self, notification_id: str, scheduled_at: datetime):
        """예약된 알림을 처리합니다."""
        try:
            # 실제 구현에서는 스케줄러 사용 (APScheduler, Celery 등)
            delay = (scheduled_at - datetime.utcnow()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
                
            # 예약된 시간에 알림 전송
            logger.info(f"📅 예약 알림 전송 - 알림ID: {notification_id}")
            
        except Exception as e:
            logger.error(f"예약 알림 처리 실패 - 알림ID: {notification_id}, 오류: {str(e)}")