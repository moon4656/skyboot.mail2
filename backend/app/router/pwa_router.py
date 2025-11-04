"""
PWA (Progressive Web App) API 라우터

SkyBoot Mail SaaS 프로젝트의 PWA 기능을 위한 API 엔드포인트입니다.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.schemas.pwa_schema import (
    PWAIcon, PWAShortcut, PWAScreenshot, PWAManifest, OrganizationPWASettings,
    UserPWAState, PWAConfigRequest, PWAConfigResponse, PWAManifestResponse,
    PWAInstallRequest, PWAInstallResponse, PWAStatsResponse,
    PWAUpdateRequest, PWAServiceWorkerResponse, PWAOfflinePageRequest,
    PWADisplayMode, PWAOrientation, IconPurpose, ShortcutCategory
)
from app.service.pwa_service import PWAService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_organization
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import get_db

router = APIRouter()


@router.get("/manifest", summary="PWA 매니페스트 조회")
async def get_pwa_manifest(
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Response:
    """
    PWA 매니페스트 파일을 조회합니다.
    
    - **name**: 앱 이름
    - **short_name**: 짧은 앱 이름
    - **description**: 앱 설명
    - **icons**: 앱 아이콘 목록
    - **start_url**: 시작 URL
    - **display**: 디스플레이 모드
    - **theme_color**: 테마 색상
    - **background_color**: 배경 색상
    """
    service = PWAService(db)
    manifest = await service.get_pwa_manifest(
        organization.id,
        str(request.base_url)
    )
    
    return Response(
        content=manifest.json(exclude_none=True),
        media_type="application/manifest+json",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline; filename=manifest.json"
        }
    )


@router.get("/config", summary="PWA 설정 조회")
async def get_pwa_config(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> PWAConfigResponse:
    """
    조직의 PWA 설정을 조회합니다.
    
    - **enabled**: PWA 활성화 여부
    - **app_name**: 앱 이름
    - **app_description**: 앱 설명
    - **theme_color**: 테마 색상
    - **background_color**: 배경 색상
    - **display_mode**: 디스플레이 모드
    - **orientation**: 화면 방향
    """
    service = PWAService(db)
    return await service.get_pwa_config(organization.id)


@router.put("/config", summary="PWA 설정 업데이트")
async def update_pwa_config(
    config_request: PWAConfigRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> PWAConfigResponse:
    """
    조직의 PWA 설정을 업데이트합니다.
    
    - **enabled**: PWA 활성화/비활성화
    - **app_name**: 앱 이름 변경
    - **app_description**: 앱 설명 변경
    - **theme_color**: 테마 색상 변경
    - **background_color**: 배경 색상 변경
    - **display_mode**: 디스플레이 모드 변경
    - **orientation**: 화면 방향 변경
    """
    service = PWAService(db)
    return await service.update_pwa_config(
        organization.id,
        config_request,
        current_user.id
    )


@router.post("/install", summary="PWA 설치 기록")
async def record_pwa_install(
    install_request: PWAInstallRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> PWAInstallResponse:
    """
    PWA 설치를 기록합니다.
    
    - **platform**: 설치 플랫폼 (android, ios, desktop)
    - **user_agent**: 사용자 에이전트
    - **install_source**: 설치 소스 (browser, store, direct)
    - **install_prompt**: 설치 프롬프트 표시 여부
    """
    service = PWAService(db)
    user_agent = request.headers.get("User-Agent", "")
    client_ip = request.client.host if request.client else ""
    
    return await service.record_pwa_install(
        organization.id,
        current_user.id,
        install_request,
        user_agent,
        client_ip
    )


@router.get("/install/check", summary="PWA 설치 가능 여부 확인")
async def check_pwa_installable(
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 설치 가능 여부를 확인합니다.
    
    - **installable**: 설치 가능 여부
    - **platform**: 현재 플랫폼
    - **requirements**: 설치 요구사항
    - **missing_features**: 누락된 기능
    """
    service = PWAService(db)
    user_agent = request.headers.get("User-Agent", "")
    
    return await service.check_pwa_installable(
        organization.id,
        user_agent
    )


@router.get("/service-worker.js", summary="서비스 워커 스크립트")
async def get_service_worker(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Response:
    """
    PWA 서비스 워커 스크립트를 조회합니다.
    
    - **cache_strategy**: 캐시 전략
    - **offline_fallback**: 오프라인 대체 페이지
    - **background_sync**: 백그라운드 동기화
    - **push_notifications**: 푸시 알림 처리
    """
    service = PWAService(db)
    service_worker_script = await service.get_service_worker_script(organization.id)
    
    return Response(
        content=service_worker_script,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Service-Worker-Allowed": "/",
            "Content-Disposition": "inline; filename=service-worker.js"
        }
    )


@router.get("/offline", summary="오프라인 페이지")
async def get_offline_page(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Response:
    """
    PWA 오프라인 페이지를 조회합니다.
    
    - **offline_content**: 오프라인 상태 안내
    - **cached_data**: 캐시된 데이터 표시
    - **retry_options**: 재시도 옵션
    """
    service = PWAService(db)
    offline_html = await service.get_offline_page(organization.id)
    
    return Response(
        content=offline_html,
        media_type="text/html",
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )


@router.put("/offline", summary="오프라인 페이지 업데이트")
async def update_offline_page(
    offline_request: PWAOfflinePageRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 오프라인 페이지를 업데이트합니다.
    
    - **title**: 오프라인 페이지 제목
    - **message**: 오프라인 메시지
    - **custom_html**: 커스텀 HTML 콘텐츠
    - **show_cached_data**: 캐시된 데이터 표시 여부
    """
    service = PWAService(db)
    return await service.update_offline_page(
        organization.id,
        offline_request,
        current_user.id
    )


@router.get("/user/state", summary="사용자 PWA 상태 조회")
async def get_user_pwa_state(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserPWAState:
    """
    사용자의 PWA 상태를 조회합니다.
    
    - **installed**: PWA 설치 여부
    - **install_date**: 설치 날짜
    - **last_used**: 마지막 사용 날짜
    - **platform**: 설치된 플랫폼
    - **version**: PWA 버전
    """
    service = PWAService(db)
    return await service.get_user_pwa_state(
        current_user.id,
        organization.id
    )


@router.put("/user/state", summary="사용자 PWA 상태 업데이트")
async def update_user_pwa_state(
    pwa_state: UserPWAState,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserPWAState:
    """
    사용자의 PWA 상태를 업데이트합니다.
    
    - **installed**: PWA 설치 상태 변경
    - **last_used**: 마지막 사용 시간 업데이트
    - **preferences**: PWA 사용자 설정
    """
    service = PWAService(db)
    return await service.update_user_pwa_state(
        current_user.id,
        organization.id,
        pwa_state
    )


@router.get("/stats", summary="PWA 통계 조회")
async def get_pwa_statistics(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> PWAStatsResponse:
    """
    PWA 사용 통계를 조회합니다.
    
    - **total_installs**: 총 설치 수
    - **active_users**: 활성 사용자 수
    - **platform_breakdown**: 플랫폼별 분석
    - **install_trends**: 설치 트렌드
    - **engagement_metrics**: 참여도 메트릭
    """
    service = PWAService(db)
    return await service.get_pwa_statistics(organization.id)


@router.post("/update", summary="PWA 업데이트 알림")
async def notify_pwa_update(
    update_request: PWAUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 업데이트를 알립니다.
    
    - **version**: 새 버전 정보
    - **changes**: 변경 사항
    - **force_update**: 강제 업데이트 여부
    - **rollout_percentage**: 점진적 배포 비율
    """
    service = PWAService(db)
    return await service.notify_pwa_update(
        organization.id,
        update_request,
        current_user.id
    )


@router.get("/icons", summary="PWA 아이콘 목록")
async def get_pwa_icons(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 아이콘 목록을 조회합니다.
    
    - **icons**: 아이콘 목록
    - **sizes**: 지원 크기
    - **formats**: 지원 형식
    - **purposes**: 아이콘 용도
    """
    service = PWAService(db)
    return await service.get_pwa_icons(organization.id)


@router.post("/icons", summary="PWA 아이콘 업로드")
async def upload_pwa_icon(
    icon_data: PWAIcon,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 아이콘을 업로드합니다.
    
    - **src**: 아이콘 URL
    - **sizes**: 아이콘 크기
    - **type**: 파일 형식
    - **purpose**: 아이콘 용도 (any, maskable, monochrome)
    """
    service = PWAService(db)
    return await service.upload_pwa_icon(
        organization.id,
        icon_data,
        current_user.id
    )


@router.get("/shortcuts", summary="PWA 바로가기 목록")
async def get_pwa_shortcuts(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 바로가기 목록을 조회합니다.
    
    - **shortcuts**: 바로가기 목록
    - **categories**: 바로가기 카테고리
    - **icons**: 바로가기 아이콘
    """
    service = PWAService(db)
    return await service.get_pwa_shortcuts(organization.id)


@router.post("/shortcuts", summary="PWA 바로가기 추가")
async def add_pwa_shortcut(
    shortcut_data: PWAShortcut,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 바로가기를 추가합니다.
    
    - **name**: 바로가기 이름
    - **short_name**: 짧은 이름
    - **description**: 설명
    - **url**: 대상 URL
    - **icons**: 바로가기 아이콘
    """
    service = PWAService(db)
    return await service.add_pwa_shortcut(
        organization.id,
        shortcut_data,
        current_user.id
    )


@router.delete("/shortcuts/{shortcut_id}", summary="PWA 바로가기 삭제")
async def delete_pwa_shortcut(
    shortcut_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 바로가기를 삭제합니다.
    
    - **shortcut_id**: 삭제할 바로가기 ID
    """
    service = PWAService(db)
    return await service.delete_pwa_shortcut(
        organization.id,
        shortcut_id,
        current_user.id
    )


@router.get("/screenshots", summary="PWA 스크린샷 목록")
async def get_pwa_screenshots(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 스크린샷 목록을 조회합니다.
    
    - **screenshots**: 스크린샷 목록
    - **form_factor**: 폼 팩터 (narrow, wide)
    - **label**: 스크린샷 라벨
    """
    service = PWAService(db)
    return await service.get_pwa_screenshots(organization.id)


@router.post("/screenshots", summary="PWA 스크린샷 추가")
async def add_pwa_screenshot(
    screenshot_data: PWAScreenshot,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 스크린샷을 추가합니다.
    
    - **src**: 스크린샷 URL
    - **sizes**: 스크린샷 크기
    - **type**: 파일 형식
    - **form_factor**: 폼 팩터
    - **label**: 스크린샷 라벨
    """
    service = PWAService(db)
    return await service.add_pwa_screenshot(
        organization.id,
        screenshot_data,
        current_user.id
    )


@router.get("/cache/status", summary="PWA 캐시 상태")
async def get_pwa_cache_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 캐시 상태를 조회합니다.
    
    - **cache_size**: 캐시 크기
    - **cached_resources**: 캐시된 리소스 수
    - **last_updated**: 마지막 업데이트 시간
    - **cache_strategy**: 캐시 전략
    """
    service = PWAService(db)
    return await service.get_pwa_cache_status(organization.id)


@router.post("/cache/clear", summary="PWA 캐시 초기화")
async def clear_pwa_cache(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PWA 캐시를 초기화합니다.
    
    - **cleared_items**: 초기화된 항목 수
    - **cache_size_freed**: 확보된 캐시 크기
    """
    service = PWAService(db)
    return await service.clear_pwa_cache(organization.id)


@router.get("/features", summary="PWA 기능 지원 여부")
async def get_pwa_features(
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    브라우저의 PWA 기능 지원 여부를 확인합니다.
    
    - **service_worker**: 서비스 워커 지원
    - **web_app_manifest**: 웹 앱 매니페스트 지원
    - **push_notifications**: 푸시 알림 지원
    - **background_sync**: 백그라운드 동기화 지원
    - **install_prompt**: 설치 프롬프트 지원
    """
    service = PWAService(db)
    user_agent = request.headers.get("User-Agent", "")
    
    return await service.get_pwa_features(user_agent)