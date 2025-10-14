"""
PWA (Progressive Web App) 스키마

SkyBoot Mail SaaS 프로젝트의 PWA 기능을 위한 Pydantic 스키마입니다.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl


class PWADisplayMode(str, Enum):
    """PWA 디스플레이 모드"""
    FULLSCREEN = "fullscreen"
    STANDALONE = "standalone"
    MINIMAL_UI = "minimal-ui"
    BROWSER = "browser"


class PWAOrientation(str, Enum):
    """PWA 화면 방향"""
    ANY = "any"
    NATURAL = "natural"
    LANDSCAPE = "landscape"
    LANDSCAPE_PRIMARY = "landscape-primary"
    LANDSCAPE_SECONDARY = "landscape-secondary"
    PORTRAIT = "portrait"
    PORTRAIT_PRIMARY = "portrait-primary"
    PORTRAIT_SECONDARY = "portrait-secondary"


class IconPurpose(str, Enum):
    """아이콘 용도"""
    ANY = "any"
    MASKABLE = "maskable"
    MONOCHROME = "monochrome"


class ShortcutCategory(str, Enum):
    """바로가기 카테고리"""
    COMPOSE = "compose"
    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    SEARCH = "search"
    SETTINGS = "settings"


class InstallPromptResult(str, Enum):
    """설치 프롬프트 결과"""
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"


# PWA 아이콘 모델
class PWAIcon(BaseModel):
    """PWA 아이콘"""
    src: HttpUrl = Field(..., description="아이콘 URL")
    sizes: str = Field(..., description="아이콘 크기 (예: 192x192)")
    type: str = Field(default="image/png", description="MIME 타입")
    purpose: Optional[IconPurpose] = Field(IconPurpose.ANY, description="아이콘 용도")


# PWA 바로가기 모델
class PWAShortcut(BaseModel):
    """PWA 바로가기"""
    name: str = Field(..., max_length=100, description="바로가기 이름")
    short_name: Optional[str] = Field(None, max_length=50, description="짧은 이름")
    description: Optional[str] = Field(None, max_length=200, description="설명")
    url: str = Field(..., description="바로가기 URL")
    category: ShortcutCategory = Field(..., description="카테고리")
    icons: List[PWAIcon] = Field(default_factory=list, description="아이콘 목록")


# PWA 스크린샷 모델
class PWAScreenshot(BaseModel):
    """PWA 스크린샷"""
    src: HttpUrl = Field(..., description="스크린샷 URL")
    sizes: str = Field(..., description="스크린샷 크기")
    type: str = Field(default="image/png", description="MIME 타입")
    form_factor: Optional[str] = Field(None, description="폼 팩터 (wide, narrow)")
    label: Optional[str] = Field(None, description="라벨")


# PWA 매니페스트 모델
class PWAManifest(BaseModel):
    """PWA 매니페스트"""
    name: str = Field(..., max_length=200, description="앱 이름")
    short_name: str = Field(..., max_length=50, description="짧은 앱 이름")
    description: Optional[str] = Field(None, max_length=500, description="앱 설명")
    start_url: str = Field(default="/", description="시작 URL")
    scope: str = Field(default="/", description="앱 범위")
    display: PWADisplayMode = Field(default=PWADisplayMode.STANDALONE, description="디스플레이 모드")
    orientation: PWAOrientation = Field(default=PWAOrientation.PORTRAIT, description="화면 방향")
    theme_color: str = Field(default="#1976d2", pattern=r"^#[0-9A-Fa-f]{6}$", description="테마 색상")
    background_color: str = Field(default="#ffffff", pattern=r"^#[0-9A-Fa-f]{6}$", description="배경 색상")
    lang: str = Field(default="ko", description="언어 코드")
    dir: str = Field(default="ltr", description="텍스트 방향")
    icons: List[PWAIcon] = Field(..., min_items=1, description="아이콘 목록")
    shortcuts: List[PWAShortcut] = Field(default_factory=list, description="바로가기 목록")
    screenshots: List[PWAScreenshot] = Field(default_factory=list, description="스크린샷 목록")
    categories: List[str] = Field(default_factory=lambda: ["productivity", "business"], description="앱 카테고리")
    iarc_rating_id: Optional[str] = Field(None, description="IARC 등급 ID")


# 조직 PWA 설정 모델
class OrganizationPWASettings(BaseModel):
    """조직 PWA 설정"""
    organization_id: int = Field(..., description="조직 ID")
    enabled: bool = Field(default=True, description="PWA 활성화")
    manifest: PWAManifest = Field(..., description="PWA 매니페스트")
    install_prompt_enabled: bool = Field(default=True, description="설치 프롬프트 활성화")
    install_prompt_delay: int = Field(default=3, ge=0, le=30, description="설치 프롬프트 지연 시간 (일)")
    auto_update_enabled: bool = Field(default=True, description="자동 업데이트 활성화")
    offline_enabled: bool = Field(default=True, description="오프라인 기능 활성화")
    push_notifications_enabled: bool = Field(default=True, description="푸시 알림 활성화")
    custom_service_worker: Optional[str] = Field(None, description="커스텀 서비스 워커 스크립트")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")


# 사용자 PWA 상태 모델
class UserPWAState(BaseModel):
    """사용자 PWA 상태"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    is_installed: bool = Field(default=False, description="PWA 설치 여부")
    install_date: Optional[datetime] = Field(None, description="설치 날짜")
    last_used: Optional[datetime] = Field(None, description="마지막 사용 시간")
    install_prompt_shown: bool = Field(default=False, description="설치 프롬프트 표시 여부")
    install_prompt_result: Optional[InstallPromptResult] = Field(None, description="설치 프롬프트 결과")
    install_prompt_count: int = Field(default=0, description="설치 프롬프트 표시 횟수")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    platform: Optional[str] = Field(None, description="플랫폼")
    standalone_mode: bool = Field(default=False, description="독립 실행 모드")


# 요청/응답 모델들

class PWAManifestRequest(BaseModel):
    """PWA 매니페스트 요청"""
    name: str = Field(..., max_length=200, description="앱 이름")
    short_name: str = Field(..., max_length=50, description="짧은 앱 이름")
    description: Optional[str] = Field(None, max_length=500, description="앱 설명")
    theme_color: str = Field(default="#1976d2", pattern=r"^#[0-9A-Fa-f]{6}$", description="테마 색상")
    background_color: str = Field(default="#ffffff", pattern=r"^#[0-9A-Fa-f]{6}$", description="배경 색상")
    display: PWADisplayMode = Field(default=PWADisplayMode.STANDALONE, description="디스플레이 모드")
    orientation: PWAOrientation = Field(default=PWAOrientation.PORTRAIT, description="화면 방향")
    lang: str = Field(default="ko", description="언어 코드")
    icons: List[PWAIcon] = Field(..., min_items=1, description="아이콘 목록")
    shortcuts: List[PWAShortcut] = Field(default_factory=list, description="바로가기 목록")


class PWAManifestResponse(BaseModel):
    """PWA 매니페스트 응답"""
    manifest: PWAManifest = Field(..., description="PWA 매니페스트")
    manifest_url: str = Field(..., description="매니페스트 URL")
    service_worker_url: str = Field(..., description="서비스 워커 URL")
    generated_at: datetime = Field(..., description="생성 시간")


class PWASettingsRequest(BaseModel):
    """PWA 설정 요청"""
    enabled: bool = Field(default=True, description="PWA 활성화")
    manifest: PWAManifestRequest = Field(..., description="PWA 매니페스트")
    install_prompt_enabled: bool = Field(default=True, description="설치 프롬프트 활성화")
    install_prompt_delay: int = Field(default=3, ge=0, le=30, description="설치 프롬프트 지연 시간 (일)")
    auto_update_enabled: bool = Field(default=True, description="자동 업데이트 활성화")
    offline_enabled: bool = Field(default=True, description="오프라인 기능 활성화")
    push_notifications_enabled: bool = Field(default=True, description="푸시 알림 활성화")


class PWASettingsResponse(BaseModel):
    """PWA 설정 응답"""
    organization_id: int = Field(..., description="조직 ID")
    enabled: bool = Field(..., description="PWA 활성화")
    manifest: PWAManifest = Field(..., description="PWA 매니페스트")
    install_prompt_enabled: bool = Field(..., description="설치 프롬프트 활성화")
    install_prompt_delay: int = Field(..., description="설치 프롬프트 지연 시간 (일)")
    auto_update_enabled: bool = Field(..., description="자동 업데이트 활성화")
    offline_enabled: bool = Field(..., description="오프라인 기능 활성화")
    push_notifications_enabled: bool = Field(..., description="푸시 알림 활성화")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class PWAInstallRequest(BaseModel):
    """PWA 설치 요청"""
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    platform: Optional[str] = Field(None, description="플랫폼")
    referrer: Optional[str] = Field(None, description="리퍼러")


class PWAInstallResponse(BaseModel):
    """PWA 설치 응답"""
    success: bool = Field(..., description="설치 성공 여부")
    message: str = Field(..., description="결과 메시지")
    install_date: datetime = Field(..., description="설치 날짜")
    manifest_url: str = Field(..., description="매니페스트 URL")


class PWAInstallPromptRequest(BaseModel):
    """PWA 설치 프롬프트 요청"""
    result: InstallPromptResult = Field(..., description="프롬프트 결과")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    platform: Optional[str] = Field(None, description="플랫폼")


class PWAInstallPromptResponse(BaseModel):
    """PWA 설치 프롬프트 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    show_again: bool = Field(..., description="다시 표시 여부")
    next_prompt_date: Optional[datetime] = Field(None, description="다음 프롬프트 날짜")


class PWAStatusResponse(BaseModel):
    """PWA 상태 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    pwa_enabled: bool = Field(..., description="PWA 활성화 여부")
    is_installed: bool = Field(..., description="PWA 설치 여부")
    install_date: Optional[datetime] = Field(None, description="설치 날짜")
    last_used: Optional[datetime] = Field(None, description="마지막 사용 시간")
    standalone_mode: bool = Field(..., description="독립 실행 모드")
    install_prompt_available: bool = Field(..., description="설치 프롬프트 사용 가능")
    offline_available: bool = Field(..., description="오프라인 기능 사용 가능")
    push_notifications_available: bool = Field(..., description="푸시 알림 사용 가능")


class PWAStatsResponse(BaseModel):
    """PWA 통계 응답"""
    total_users: int = Field(..., description="전체 사용자 수")
    installed_users: int = Field(..., description="PWA 설치 사용자 수")
    installation_rate: float = Field(..., description="설치율 (%)")
    daily_active_users: int = Field(..., description="일일 활성 사용자 수")
    monthly_active_users: int = Field(..., description="월간 활성 사용자 수")
    platform_stats: Dict[str, int] = Field(..., description="플랫폼별 통계")
    install_prompt_stats: Dict[str, int] = Field(..., description="설치 프롬프트 통계")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class ServiceWorkerUpdateRequest(BaseModel):
    """서비스 워커 업데이트 요청"""
    version: str = Field(..., description="버전")
    force_update: bool = Field(default=False, description="강제 업데이트")


class ServiceWorkerUpdateResponse(BaseModel):
    """서비스 워커 업데이트 응답"""
    success: bool = Field(..., description="업데이트 성공 여부")
    version: str = Field(..., description="업데이트된 버전")
    cache_cleared: bool = Field(..., description="캐시 클리어 여부")
    updated_at: datetime = Field(..., description="업데이트 시간")


class PWACapabilitiesResponse(BaseModel):
    """PWA 기능 응답"""
    install_available: bool = Field(..., description="설치 가능 여부")
    standalone_available: bool = Field(..., description="독립 실행 모드 사용 가능")
    offline_available: bool = Field(..., description="오프라인 기능 사용 가능")
    push_notifications_available: bool = Field(..., description="푸시 알림 사용 가능")
    background_sync_available: bool = Field(..., description="백그라운드 동기화 사용 가능")
    file_system_access_available: bool = Field(..., description="파일 시스템 접근 사용 가능")
    share_api_available: bool = Field(..., description="공유 API 사용 가능")
    web_share_target_available: bool = Field(..., description="웹 공유 대상 사용 가능")
    badging_api_available: bool = Field(..., description="배지 API 사용 가능")
    contact_picker_available: bool = Field(..., description="연락처 선택기 사용 가능")


# 검증 함수들

@validator('icons', pre=True)
def validate_icons(cls, v):
    """아이콘 목록 검증"""
    if not v or len(v) == 0:
        raise ValueError("최소 하나의 아이콘이 필요합니다.")
    
    # 필수 크기 확인
    required_sizes = ['192x192', '512x512']
    available_sizes = [icon.sizes for icon in v if hasattr(icon, 'sizes')]
    
    for size in required_sizes:
        if size not in available_sizes:
            raise ValueError(f"필수 아이콘 크기가 누락되었습니다: {size}")
    
    return v


@validator('shortcuts', pre=True)
def validate_shortcuts(cls, v):
    """바로가기 목록 검증"""
    if v and len(v) > 10:
        raise ValueError("바로가기는 최대 10개까지 설정할 수 있습니다.")
    return v


class PWAValidationError(Exception):
    """PWA 검증 오류"""
    pass


class PWANotSupportedError(Exception):
    """PWA 지원하지 않음"""
    pass


class PWAInstallationError(Exception):
    """PWA 설치 오류"""
    pass


class PWAServiceWorkerResponse(BaseModel):
    """PWA 서비스 워커 응답"""
    script_url: str = Field(..., description="서비스 워커 스크립트 URL")
    version: str = Field(..., description="서비스 워커 버전")
    cache_strategy: str = Field(..., description="캐시 전략")
    offline_pages: List[str] = Field(..., description="오프라인 페이지 목록")
    updated_at: datetime = Field(..., description="업데이트 시간")


class PWAOfflinePageRequest(BaseModel):
    """PWA 오프라인 페이지 요청"""
    url: str = Field(..., description="페이지 URL")
    title: str = Field(..., description="페이지 제목")
    content: str = Field(..., description="페이지 내용")
    cache_strategy: str = Field("cache-first", description="캐시 전략")


class PWAUpdateRequest(BaseModel):
    """PWA 업데이트 요청"""
    force_update: bool = Field(False, description="강제 업데이트 여부")
    clear_cache: bool = Field(False, description="캐시 클리어 여부")
    notify_users: bool = Field(True, description="사용자 알림 여부")


class PWAConfigRequest(BaseModel):
    """PWA 설정 요청 모델"""
    app_name: str = Field(..., description="앱 이름")
    app_short_name: str = Field(..., description="앱 짧은 이름")
    description: str = Field(..., description="앱 설명")
    theme_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="테마 색상")
    background_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="배경 색상")
    display: PWADisplayMode = Field(default=PWADisplayMode.STANDALONE, description="디스플레이 모드")
    orientation: PWAOrientation = Field(default=PWAOrientation.PORTRAIT, description="화면 방향")
    start_url: str = Field(default="/", description="시작 URL")
    scope: str = Field(default="/", description="앱 범위")
    icons: List[PWAIcon] = Field(default=[], description="앱 아이콘 목록")
    shortcuts: List[PWAShortcut] = Field(default=[], description="앱 바로가기 목록")
    screenshots: List[PWAScreenshot] = Field(default=[], description="앱 스크린샷 목록")
    enable_offline: bool = Field(default=True, description="오프라인 지원 활성화")
    enable_push_notifications: bool = Field(default=True, description="푸시 알림 활성화")
    cache_strategy: str = Field(default="cache_first", description="캐시 전략")


# 검증 함수들

@validator('icons', pre=True)
def validate_icons(cls, v):
    """아이콘 목록 검증"""
    if not v or len(v) == 0:
        raise ValueError("최소 하나의 아이콘이 필요합니다.")
    
    # 필수 크기 확인
    required_sizes = ['192x192', '512x512']
    available_sizes = [icon.sizes for icon in v if hasattr(icon, 'sizes')]
    
    for size in required_sizes:
        if size not in available_sizes:
            raise ValueError(f"필수 아이콘 크기가 누락되었습니다: {size}")
    
    return v


@validator('shortcuts', pre=True)
def validate_shortcuts(cls, v):
    """바로가기 목록 검증"""
    if v and len(v) > 10:
        raise ValueError("바로가기는 최대 10개까지 설정할 수 있습니다.")
    return v


class PWAValidationError(Exception):
    """PWA 검증 오류"""
    pass


class PWANotSupportedError(Exception):
    """PWA 지원하지 않음"""
    pass


class PWAInstallationError(Exception):
    """PWA 설치 오류"""
    pass


class PWAServiceWorkerResponse(BaseModel):
    """PWA 서비스 워커 응답"""
    script_url: str = Field(..., description="서비스 워커 스크립트 URL")
    version: str = Field(..., description="서비스 워커 버전")
    cache_strategy: str = Field(..., description="캐시 전략")
    offline_pages: List[str] = Field(..., description="오프라인 페이지 목록")
    updated_at: datetime = Field(..., description="업데이트 시간")


class PWAOfflinePageRequest(BaseModel):
    """PWA 오프라인 페이지 요청"""
    url: str = Field(..., description="페이지 URL")
    title: str = Field(..., description="페이지 제목")
    content: str = Field(..., description="페이지 내용")
    cache_strategy: str = Field("cache-first", description="캐시 전략")


class PWAUpdateRequest(BaseModel):
    """PWA 업데이트 요청"""
    force_update: bool = Field(False, description="강제 업데이트 여부")
    clear_cache: bool = Field(False, description="캐시 클리어 여부")
    notify_users: bool = Field(True, description="사용자 알림 여부")


class PWAConfigResponse(BaseModel):
    """PWA 설정 응답 모델"""
    organization_id: int = Field(..., description="조직 ID")
    app_name: str = Field(..., description="앱 이름")
    app_short_name: str = Field(..., description="앱 짧은 이름")
    description: str = Field(..., description="앱 설명")
    theme_color: str = Field(..., description="테마 색상")
    background_color: str = Field(..., description="배경 색상")
    display: PWADisplayMode = Field(..., description="디스플레이 모드")
    orientation: PWAOrientation = Field(..., description="화면 방향")
    start_url: str = Field(..., description="시작 URL")
    scope: str = Field(..., description="앱 범위")
    icons: List[PWAIcon] = Field(..., description="앱 아이콘 목록")
    shortcuts: List[PWAShortcut] = Field(..., description="앱 바로가기 목록")
    screenshots: List[PWAScreenshot] = Field(..., description="앱 스크린샷 목록")
    enable_offline: bool = Field(..., description="오프라인 지원 활성화")
    enable_push_notifications: bool = Field(..., description="푸시 알림 활성화")
    cache_strategy: str = Field(..., description="캐시 전략")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class PWAInstallRequest(BaseModel):
    """PWA 설치 요청"""
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    platform: Optional[str] = Field(None, description="플랫폼")
    referrer: Optional[str] = Field(None, description="리퍼러")


class PWAInstallResponse(BaseModel):
    """PWA 설치 응답"""
    success: bool = Field(..., description="설치 성공 여부")
    message: str = Field(..., description="결과 메시지")
    install_date: datetime = Field(..., description="설치 날짜")
    manifest_url: str = Field(..., description="매니페스트 URL")


class PWAInstallPromptRequest(BaseModel):
    """PWA 설치 프롬프트 요청"""
    result: InstallPromptResult = Field(..., description="프롬프트 결과")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    platform: Optional[str] = Field(None, description="플랫폼")


class PWAInstallPromptResponse(BaseModel):
    """PWA 설치 프롬프트 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    show_again: bool = Field(..., description="다시 표시 여부")
    next_prompt_date: Optional[datetime] = Field(None, description="다음 프롬프트 날짜")


class PWAStatusResponse(BaseModel):
    """PWA 상태 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    pwa_enabled: bool = Field(..., description="PWA 활성화 여부")
    is_installed: bool = Field(..., description="PWA 설치 여부")
    install_date: Optional[datetime] = Field(None, description="설치 날짜")
    last_used: Optional[datetime] = Field(None, description="마지막 사용 시간")
    standalone_mode: bool = Field(..., description="독립 실행 모드")
    install_prompt_available: bool = Field(..., description="설치 프롬프트 사용 가능")
    offline_available: bool = Field(..., description="오프라인 기능 사용 가능")
    push_notifications_available: bool = Field(..., description="푸시 알림 사용 가능")


class PWAStatsResponse(BaseModel):
    """PWA 통계 응답"""
    total_users: int = Field(..., description="전체 사용자 수")
    installed_users: int = Field(..., description="PWA 설치 사용자 수")
    installation_rate: float = Field(..., description="설치율 (%)")
    daily_active_users: int = Field(..., description="일일 활성 사용자 수")
    monthly_active_users: int = Field(..., description="월간 활성 사용자 수")
    platform_stats: Dict[str, int] = Field(..., description="플랫폼별 통계")
    install_prompt_stats: Dict[str, int] = Field(..., description="설치 프롬프트 통계")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class ServiceWorkerUpdateRequest(BaseModel):
    """서비스 워커 업데이트 요청"""
    version: str = Field(..., description="버전")
    force_update: bool = Field(default=False, description="강제 업데이트")


class ServiceWorkerUpdateResponse(BaseModel):
    """서비스 워커 업데이트 응답"""
    success: bool = Field(..., description="업데이트 성공 여부")
    version: str = Field(..., description="업데이트된 버전")
    cache_cleared: bool = Field(..., description="캐시 클리어 여부")
    updated_at: datetime = Field(..., description="업데이트 시간")


class PWACapabilitiesResponse(BaseModel):
    """PWA 기능 응답"""
    install_available: bool = Field(..., description="설치 가능 여부")
    standalone_available: bool = Field(..., description="독립 실행 모드 사용 가능")
    offline_available: bool = Field(..., description="오프라인 기능 사용 가능")
    push_notifications_available: bool = Field(..., description="푸시 알림 사용 가능")
    background_sync_available: bool = Field(..., description="백그라운드 동기화 사용 가능")
    file_system_access_available: bool = Field(..., description="파일 시스템 접근 사용 가능")
    share_api_available: bool = Field(..., description="공유 API 사용 가능")
    web_share_target_available: bool = Field(..., description="웹 공유 대상 사용 가능")
    badging_api_available: bool = Field(..., description="배지 API 사용 가능")
    contact_picker_available: bool = Field(..., description="연락처 선택기 사용 가능")