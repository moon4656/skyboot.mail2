"""
PWA (Progressive Web App) 서비스

SkyBoot Mail SaaS 프로젝트의 PWA 기능을 위한 서비스 로직입니다.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import base64

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import redis

from app.schemas.pwa_schema import (
    PWAManifest, PWAIcon, PWAShortcut, PWAScreenshot,
    OrganizationPWASettings, UserPWAState,
    PWAManifestRequest, PWAManifestResponse,
    PWASettingsRequest, PWASettingsResponse,
    PWAInstallRequest, PWAInstallResponse,
    PWAInstallPromptRequest, PWAInstallPromptResponse,
    PWAStatusResponse, PWAStatsResponse,
    ServiceWorkerUpdateRequest, ServiceWorkerUpdateResponse,
    PWACapabilitiesResponse,
    PWADisplayMode, PWAOrientation, IconPurpose, ShortcutCategory,
    InstallPromptResult,
    PWAValidationError, PWANotSupportedError, PWAInstallationError
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


class PWAService:
    """PWA 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 3600  # 1시간
        self.manifest_cache_key = "pwa:manifest:{org_id}"
        self.settings_cache_key = "pwa:settings:{org_id}"
        self.user_state_cache_key = "pwa:user_state:{user_id}"
        
    async def get_organization_pwa_settings(self, organization_id: int) -> Optional[OrganizationPWASettings]:
        """
        조직의 PWA 설정을 조회합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            조직 PWA 설정 또는 None
        """
        try:
            logger.info(f"📱 조직 PWA 설정 조회 시작 - 조직: {organization_id}")
            
            # 캐시에서 먼저 확인
            cache_key = self.settings_cache_key.format(org_id=organization_id)
            cached_settings = redis_client.get(cache_key)
            
            if cached_settings:
                logger.info(f"✅ 캐시에서 PWA 설정 조회 - 조직: {organization_id}")
                return OrganizationPWASettings.parse_raw(cached_settings)
            
            # 데이터베이스에서 조회 (실제 구현에서는 PWA 설정 테이블 필요)
            # 현재는 기본 설정 반환
            default_manifest = self._create_default_manifest(organization_id)
            
            settings_data = OrganizationPWASettings(
                organization_id=organization_id,
                enabled=True,
                manifest=default_manifest,
                install_prompt_enabled=True,
                install_prompt_delay=3,
                auto_update_enabled=True,
                offline_enabled=True,
                push_notifications_enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 캐시에 저장
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                settings_data.json()
            )
            
            logger.info(f"✅ 조직 PWA 설정 조회 완료 - 조직: {organization_id}")
            return settings_data
            
        except Exception as e:
            logger.error(f"❌ 조직 PWA 설정 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 설정 조회 중 오류가 발생했습니다."
            )
    
    async def update_organization_pwa_settings(
        self,
        organization_id: int,
        settings_request: PWASettingsRequest
    ) -> PWASettingsResponse:
        """
        조직의 PWA 설정을 업데이트합니다.
        
        Args:
            organization_id: 조직 ID
            settings_request: PWA 설정 요청
            
        Returns:
            업데이트된 PWA 설정
        """
        try:
            logger.info(f"📱 조직 PWA 설정 업데이트 시작 - 조직: {organization_id}")
            
            # 매니페스트 생성
            manifest = PWAManifest(
                name=settings_request.manifest.name,
                short_name=settings_request.manifest.short_name,
                description=settings_request.manifest.description,
                theme_color=settings_request.manifest.theme_color,
                background_color=settings_request.manifest.background_color,
                display=settings_request.manifest.display,
                orientation=settings_request.manifest.orientation,
                lang=settings_request.manifest.lang,
                icons=settings_request.manifest.icons,
                shortcuts=settings_request.manifest.shortcuts,
                start_url=f"/org/{organization_id}/",
                scope=f"/org/{organization_id}/"
            )
            
            # 설정 데이터 생성
            settings_data = OrganizationPWASettings(
                organization_id=organization_id,
                enabled=settings_request.enabled,
                manifest=manifest,
                install_prompt_enabled=settings_request.install_prompt_enabled,
                install_prompt_delay=settings_request.install_prompt_delay,
                auto_update_enabled=settings_request.auto_update_enabled,
                offline_enabled=settings_request.offline_enabled,
                push_notifications_enabled=settings_request.push_notifications_enabled,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 데이터베이스 저장 (실제 구현에서는 PWA 설정 테이블에 저장)
            
            # 캐시 업데이트
            cache_key = self.settings_cache_key.format(org_id=organization_id)
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                settings_data.json()
            )
            
            # 매니페스트 캐시도 무효화
            manifest_cache_key = self.manifest_cache_key.format(org_id=organization_id)
            redis_client.delete(manifest_cache_key)
            
            logger.info(f"✅ 조직 PWA 설정 업데이트 완료 - 조직: {organization_id}")
            
            return PWASettingsResponse(
                organization_id=organization_id,
                enabled=settings_data.enabled,
                manifest=settings_data.manifest,
                install_prompt_enabled=settings_data.install_prompt_enabled,
                install_prompt_delay=settings_data.install_prompt_delay,
                auto_update_enabled=settings_data.auto_update_enabled,
                offline_enabled=settings_data.offline_enabled,
                push_notifications_enabled=settings_data.push_notifications_enabled,
                created_at=settings_data.created_at,
                updated_at=settings_data.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 PWA 설정 업데이트 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 설정 업데이트 중 오류가 발생했습니다."
            )
    
    async def get_pwa_manifest(self, organization_id: int) -> PWAManifestResponse:
        """
        조직의 PWA 매니페스트를 조회합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            PWA 매니페스트 응답
        """
        try:
            logger.info(f"📱 PWA 매니페스트 조회 시작 - 조직: {organization_id}")
            
            # 캐시에서 먼저 확인
            cache_key = self.manifest_cache_key.format(org_id=organization_id)
            cached_manifest = redis_client.get(cache_key)
            
            if cached_manifest:
                logger.info(f"✅ 캐시에서 PWA 매니페스트 조회 - 조직: {organization_id}")
                return PWAManifestResponse.parse_raw(cached_manifest)
            
            # PWA 설정 조회
            pwa_settings = await self.get_organization_pwa_settings(organization_id)
            if not pwa_settings or not pwa_settings.enabled:
                raise PWANotSupportedError("PWA가 비활성화되어 있습니다.")
            
            # 매니페스트 응답 생성
            manifest_response = PWAManifestResponse(
                manifest=pwa_settings.manifest,
                manifest_url=f"/api/v1/pwa/manifest/{organization_id}",
                service_worker_url=f"/api/v1/pwa/service-worker/{organization_id}",
                generated_at=datetime.utcnow()
            )
            
            # 캐시에 저장
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                manifest_response.json()
            )
            
            logger.info(f"✅ PWA 매니페스트 조회 완료 - 조직: {organization_id}")
            return manifest_response
            
        except PWANotSupportedError:
            raise
        except Exception as e:
            logger.error(f"❌ PWA 매니페스트 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 매니페스트 조회 중 오류가 발생했습니다."
            )
    
    async def install_pwa(
        self,
        user_id: int,
        organization_id: int,
        install_request: PWAInstallRequest
    ) -> PWAInstallResponse:
        """
        사용자의 PWA 설치를 기록합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            install_request: PWA 설치 요청
            
        Returns:
            PWA 설치 응답
        """
        try:
            logger.info(f"📱 PWA 설치 시작 - 사용자: {user_id}, 조직: {organization_id}")
            
            # PWA 설정 확인
            pwa_settings = await self.get_organization_pwa_settings(organization_id)
            if not pwa_settings or not pwa_settings.enabled:
                raise PWANotSupportedError("PWA가 비활성화되어 있습니다.")
            
            # 사용자 PWA 상태 업데이트
            install_date = datetime.utcnow()
            user_state = UserPWAState(
                user_id=user_id,
                organization_id=organization_id,
                is_installed=True,
                install_date=install_date,
                last_used=install_date,
                user_agent=install_request.user_agent,
                platform=install_request.platform,
                standalone_mode=True
            )
            
            # 데이터베이스 저장 (실제 구현에서는 사용자 PWA 상태 테이블에 저장)
            
            # 캐시 업데이트
            cache_key = self.user_state_cache_key.format(user_id=user_id)
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                user_state.json()
            )
            
            logger.info(f"✅ PWA 설치 완료 - 사용자: {user_id}, 조직: {organization_id}")
            
            return PWAInstallResponse(
                success=True,
                message="PWA가 성공적으로 설치되었습니다.",
                install_date=install_date,
                manifest_url=f"/api/v1/pwa/manifest/{organization_id}"
            )
            
        except PWANotSupportedError:
            raise
        except Exception as e:
            logger.error(f"❌ PWA 설치 실패 - 사용자: {user_id}, 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 설치 중 오류가 발생했습니다."
            )
    
    async def handle_install_prompt(
        self,
        user_id: int,
        organization_id: int,
        prompt_request: PWAInstallPromptRequest
    ) -> PWAInstallPromptResponse:
        """
        PWA 설치 프롬프트 결과를 처리합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            prompt_request: 설치 프롬프트 요청
            
        Returns:
            설치 프롬프트 응답
        """
        try:
            logger.info(f"📱 PWA 설치 프롬프트 처리 시작 - 사용자: {user_id}, 결과: {prompt_request.result}")
            
            # PWA 설정 조회
            pwa_settings = await self.get_organization_pwa_settings(organization_id)
            if not pwa_settings or not pwa_settings.install_prompt_enabled:
                raise PWANotSupportedError("설치 프롬프트가 비활성화되어 있습니다.")
            
            # 사용자 상태 업데이트
            show_again = False
            next_prompt_date = None
            
            if prompt_request.result == InstallPromptResult.DISMISSED:
                # 거부한 경우 지연 시간 후 다시 표시
                show_again = True
                next_prompt_date = datetime.utcnow() + timedelta(days=pwa_settings.install_prompt_delay)
            elif prompt_request.result == InstallPromptResult.DEFERRED:
                # 연기한 경우 1일 후 다시 표시
                show_again = True
                next_prompt_date = datetime.utcnow() + timedelta(days=1)
            
            # 데이터베이스 업데이트 (실제 구현에서는 사용자 PWA 상태 테이블 업데이트)
            
            logger.info(f"✅ PWA 설치 프롬프트 처리 완료 - 사용자: {user_id}, 다시표시: {show_again}")
            
            return PWAInstallPromptResponse(
                success=True,
                show_again=show_again,
                next_prompt_date=next_prompt_date
            )
            
        except PWANotSupportedError:
            raise
        except Exception as e:
            logger.error(f"❌ PWA 설치 프롬프트 처리 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="설치 프롬프트 처리 중 오류가 발생했습니다."
            )
    
    async def get_user_pwa_status(self, user_id: int, organization_id: int) -> PWAStatusResponse:
        """
        사용자의 PWA 상태를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            organization_id: 조직 ID
            
        Returns:
            PWA 상태 응답
        """
        try:
            logger.info(f"📱 사용자 PWA 상태 조회 시작 - 사용자: {user_id}, 조직: {organization_id}")
            
            # PWA 설정 조회
            pwa_settings = await self.get_organization_pwa_settings(organization_id)
            pwa_enabled = pwa_settings is not None and pwa_settings.enabled
            
            # 사용자 PWA 상태 조회 (캐시 또는 데이터베이스)
            cache_key = self.user_state_cache_key.format(user_id=user_id)
            cached_state = redis_client.get(cache_key)
            
            if cached_state:
                user_state = UserPWAState.parse_raw(cached_state)
            else:
                # 기본 상태
                user_state = UserPWAState(
                    user_id=user_id,
                    organization_id=organization_id,
                    is_installed=False,
                    standalone_mode=False
                )
            
            # 설치 프롬프트 사용 가능 여부 확인
            install_prompt_available = (
                pwa_enabled and
                pwa_settings.install_prompt_enabled and
                not user_state.is_installed
            )
            
            logger.info(f"✅ 사용자 PWA 상태 조회 완료 - 사용자: {user_id}, 설치됨: {user_state.is_installed}")
            
            return PWAStatusResponse(
                user_id=user_id,
                organization_id=organization_id,
                pwa_enabled=pwa_enabled,
                is_installed=user_state.is_installed,
                install_date=user_state.install_date,
                last_used=user_state.last_used,
                standalone_mode=user_state.standalone_mode,
                install_prompt_available=install_prompt_available,
                offline_available=pwa_enabled and pwa_settings.offline_enabled,
                push_notifications_available=pwa_enabled and pwa_settings.push_notifications_enabled
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 PWA 상태 조회 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 상태 조회 중 오류가 발생했습니다."
            )
    
    async def get_pwa_statistics(self, organization_id: int) -> PWAStatsResponse:
        """
        조직의 PWA 통계를 조회합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            PWA 통계 응답
        """
        try:
            logger.info(f"📊 PWA 통계 조회 시작 - 조직: {organization_id}")
            
            # 실제 구현에서는 데이터베이스에서 통계 조회
            # 현재는 샘플 데이터 반환
            
            total_users = 100
            installed_users = 35
            installation_rate = (installed_users / total_users) * 100 if total_users > 0 else 0
            
            stats = PWAStatsResponse(
                total_users=total_users,
                installed_users=installed_users,
                installation_rate=installation_rate,
                daily_active_users=25,
                monthly_active_users=80,
                platform_stats={
                    "android": 20,
                    "ios": 10,
                    "desktop": 5
                },
                install_prompt_stats={
                    "accepted": 35,
                    "dismissed": 45,
                    "deferred": 20
                },
                last_updated=datetime.utcnow()
            )
            
            logger.info(f"✅ PWA 통계 조회 완료 - 조직: {organization_id}, 설치율: {installation_rate:.1f}%")
            return stats
            
        except Exception as e:
            logger.error(f"❌ PWA 통계 조회 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 통계 조회 중 오류가 발생했습니다."
            )
    
    async def update_service_worker(
        self,
        organization_id: int,
        update_request: ServiceWorkerUpdateRequest
    ) -> ServiceWorkerUpdateResponse:
        """
        서비스 워커를 업데이트합니다.
        
        Args:
            organization_id: 조직 ID
            update_request: 서비스 워커 업데이트 요청
            
        Returns:
            서비스 워커 업데이트 응답
        """
        try:
            logger.info(f"🔄 서비스 워커 업데이트 시작 - 조직: {organization_id}, 버전: {update_request.version}")
            
            # 캐시 클리어
            cache_cleared = False
            if update_request.force_update:
                # 관련 캐시 모두 클리어
                manifest_cache_key = self.manifest_cache_key.format(org_id=organization_id)
                settings_cache_key = self.settings_cache_key.format(org_id=organization_id)
                
                redis_client.delete(manifest_cache_key)
                redis_client.delete(settings_cache_key)
                cache_cleared = True
            
            # 서비스 워커 업데이트 (실제 구현에서는 파일 생성/업데이트)
            
            logger.info(f"✅ 서비스 워커 업데이트 완료 - 조직: {organization_id}, 버전: {update_request.version}")
            
            return ServiceWorkerUpdateResponse(
                success=True,
                version=update_request.version,
                cache_cleared=cache_cleared,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 서비스 워커 업데이트 실패 - 조직: {organization_id}, 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="서비스 워커 업데이트 중 오류가 발생했습니다."
            )
    
    async def get_pwa_capabilities(self, user_agent: Optional[str] = None) -> PWACapabilitiesResponse:
        """
        PWA 기능 지원 여부를 조회합니다.
        
        Args:
            user_agent: 사용자 에이전트 문자열
            
        Returns:
            PWA 기능 응답
        """
        try:
            logger.info(f"🔍 PWA 기능 지원 여부 조회 시작")
            
            # 사용자 에이전트 기반 기능 지원 여부 판단
            # 실제 구현에서는 더 정교한 판단 로직 필요
            
            is_mobile = False
            is_ios = False
            is_android = False
            is_desktop = True
            
            if user_agent:
                user_agent_lower = user_agent.lower()
                is_mobile = any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone', 'ipad'])
                is_ios = any(ios in user_agent_lower for ios in ['iphone', 'ipad', 'ipod'])
                is_android = 'android' in user_agent_lower
                is_desktop = not is_mobile
            
            capabilities = PWACapabilitiesResponse(
                install_available=True,
                standalone_available=True,
                offline_available=True,
                push_notifications_available=not is_ios,  # iOS는 제한적 지원
                background_sync_available=not is_ios,
                file_system_access_available=is_desktop,
                share_api_available=is_mobile,
                web_share_target_available=is_mobile,
                badging_api_available=is_desktop or is_android,
                contact_picker_available=is_mobile
            )
            
            logger.info(f"✅ PWA 기능 지원 여부 조회 완료")
            return capabilities
            
        except Exception as e:
            logger.error(f"❌ PWA 기능 지원 여부 조회 실패 - 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PWA 기능 조회 중 오류가 발생했습니다."
            )
    
    def _create_default_manifest(self, organization_id: int) -> PWAManifest:
        """
        기본 PWA 매니페스트를 생성합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            기본 PWA 매니페스트
        """
        # 조직 정보 조회 (실제 구현에서는 데이터베이스에서 조회)
        org_name = f"SkyBoot Mail - Organization {organization_id}"
        
        default_icons = [
            PWAIcon(
                src=f"/static/icons/icon-192x192.png",
                sizes="192x192",
                type="image/png",
                purpose=IconPurpose.ANY
            ),
            PWAIcon(
                src=f"/static/icons/icon-512x512.png",
                sizes="512x512",
                type="image/png",
                purpose=IconPurpose.ANY
            ),
            PWAIcon(
                src=f"/static/icons/icon-maskable-192x192.png",
                sizes="192x192",
                type="image/png",
                purpose=IconPurpose.MASKABLE
            )
        ]
        
        default_shortcuts = [
            PWAShortcut(
                name="새 메일 작성",
                short_name="작성",
                description="새 메일을 작성합니다",
                url=f"/org/{organization_id}/compose",
                category=ShortcutCategory.COMPOSE,
                icons=[PWAIcon(
                    src="/static/icons/compose-icon.png",
                    sizes="96x96",
                    type="image/png"
                )]
            ),
            PWAShortcut(
                name="받은 메일함",
                short_name="받은편지함",
                description="받은 메일을 확인합니다",
                url=f"/org/{organization_id}/inbox",
                category=ShortcutCategory.INBOX,
                icons=[PWAIcon(
                    src="/static/icons/inbox-icon.png",
                    sizes="96x96",
                    type="image/png"
                )]
            )
        ]
        
        return PWAManifest(
            name=org_name,
            short_name=f"SkyBoot {organization_id}",
            description="SkyBoot Mail - 기업용 메일 서비스",
            start_url=f"/org/{organization_id}/",
            scope=f"/org/{organization_id}/",
            display=PWADisplayMode.STANDALONE,
            orientation=PWAOrientation.PORTRAIT,
            theme_color="#1976d2",
            background_color="#ffffff",
            lang="ko",
            dir="ltr",
            icons=default_icons,
            shortcuts=default_shortcuts,
            categories=["productivity", "business", "communication"]
        )
    
    def generate_service_worker_script(self, organization_id: int) -> str:
        """
        조직별 서비스 워커 스크립트를 생성합니다.
        
        Args:
            organization_id: 조직 ID
            
        Returns:
            서비스 워커 JavaScript 코드
        """
        cache_name = f"skyboot-mail-v1-org-{organization_id}"
        
        service_worker_script = f"""
// SkyBoot Mail PWA Service Worker - Organization {organization_id}
const CACHE_NAME = '{cache_name}';
const urlsToCache = [
  '/org/{organization_id}/',
  '/org/{organization_id}/inbox',
  '/org/{organization_id}/compose',
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// 설치 이벤트
self.addEventListener('install', function(event) {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {{
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      }})
  );
}});

// 활성화 이벤트
self.addEventListener('activate', function(event) {{
  event.waitUntil(
    caches.keys().then(function(cacheNames) {{
      return Promise.all(
        cacheNames.map(function(cacheName) {{
          if (cacheName !== CACHE_NAME) {{
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }}
        }})
      );
    }})
  );
}});

// 페치 이벤트
self.addEventListener('fetch', function(event) {{
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {{
        // 캐시에서 찾으면 반환
        if (response) {{
          return response;
        }}
        
        // 네트워크에서 가져오기
        return fetch(event.request).then(
          function(response) {{
            // 유효한 응답인지 확인
            if(!response || response.status !== 200 || response.type !== 'basic') {{
              return response;
            }}
            
            // 응답 복사
            var responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(function(cache) {{
                cache.put(event.request, responseToCache);
              }});
            
            return response;
          }}
        );
      }}
    )
  );
}});

// 백그라운드 동기화
self.addEventListener('sync', function(event) {{
  if (event.tag === 'background-sync') {{
    event.waitUntil(doBackgroundSync());
  }}
}});

// 푸시 알림
self.addEventListener('push', function(event) {{
  const options = {{
    body: event.data ? event.data.text() : 'New mail received',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    tag: 'mail-notification',
    data: {{
      url: '/org/{organization_id}/inbox'
    }}
  }};
  
  event.waitUntil(
    self.registration.showNotification('SkyBoot Mail', options)
  );
}});

// 알림 클릭
self.addEventListener('notificationclick', function(event) {{
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
}});

function doBackgroundSync() {{
  // 백그라운드 동기화 로직
  return fetch('/api/v1/mail/sync', {{
    method: 'POST',
    headers: {{
      'Content-Type': 'application/json'
    }}
  }});
}}
"""
        
        return service_worker_script