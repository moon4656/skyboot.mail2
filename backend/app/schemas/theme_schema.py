"""
조직별 테마 스키마

SkyBoot Mail SaaS 프로젝트의 조직별 테마 및 브랜딩 기능을 위한 Pydantic 스키마입니다.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl


class ThemeType(str, Enum):
    """테마 타입"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"


class ColorScheme(str, Enum):
    """색상 스키마"""
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    RED = "red"
    ORANGE = "orange"
    TEAL = "teal"
    PINK = "pink"
    INDIGO = "indigo"
    CUSTOM = "custom"


class FontFamily(str, Enum):
    """폰트 패밀리"""
    SYSTEM = "system"
    ROBOTO = "roboto"
    OPEN_SANS = "open_sans"
    NOTO_SANS = "noto_sans"
    NOTO_SANS_KR = "noto_sans_kr"
    MALGUN_GOTHIC = "malgun_gothic"
    CUSTOM = "custom"


class ComponentSize(str, Enum):
    """컴포넌트 크기"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BorderRadius(str, Enum):
    """테두리 반경"""
    NONE = "none"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FULL = "full"


# 색상 정의 모델
class ColorPalette(BaseModel):
    """색상 팔레트"""
    primary: str = Field(..., description="주 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: str = Field(..., description="보조 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(..., description="강조 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(..., description="배경 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    surface: str = Field(..., description="표면 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    text_primary: str = Field(..., description="주 텍스트 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    text_secondary: str = Field(..., description="보조 텍스트 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    border: str = Field(..., description="테두리 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    success: str = Field(..., description="성공 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    warning: str = Field(..., description="경고 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    error: str = Field(..., description="오류 색상", pattern=r"^#[0-9A-Fa-f]{6}$")
    info: str = Field(..., description="정보 색상", pattern=r"^#[0-9A-Fa-f]{6}$")


# 타이포그래피 설정
class Typography(BaseModel):
    """타이포그래피 설정"""
    font_family: FontFamily = Field(default=FontFamily.SYSTEM, description="폰트 패밀리")
    custom_font_url: Optional[HttpUrl] = Field(None, description="커스텀 폰트 URL")
    font_size_base: int = Field(default=14, ge=10, le=24, description="기본 폰트 크기 (px)")
    font_size_scale: float = Field(default=1.2, ge=1.0, le=2.0, description="폰트 크기 배율")
    line_height: float = Field(default=1.5, ge=1.0, le=3.0, description="줄 간격")
    letter_spacing: float = Field(default=0.0, ge=-2.0, le=2.0, description="자간 (px)")


# 레이아웃 설정
class Layout(BaseModel):
    """레이아웃 설정"""
    sidebar_width: int = Field(default=280, ge=200, le=400, description="사이드바 너비 (px)")
    header_height: int = Field(default=64, ge=48, le=96, description="헤더 높이 (px)")
    content_max_width: int = Field(default=1200, ge=800, le=1920, description="콘텐츠 최대 너비 (px)")
    border_radius: BorderRadius = Field(default=BorderRadius.MEDIUM, description="테두리 반경")
    component_size: ComponentSize = Field(default=ComponentSize.MEDIUM, description="컴포넌트 크기")
    spacing_unit: int = Field(default=8, ge=4, le=16, description="간격 단위 (px)")


# 브랜딩 설정
class Branding(BaseModel):
    """브랜딩 설정"""
    logo_url: Optional[HttpUrl] = Field(None, description="로고 URL")
    logo_dark_url: Optional[HttpUrl] = Field(None, description="다크 모드 로고 URL")
    favicon_url: Optional[HttpUrl] = Field(None, description="파비콘 URL")
    company_name: Optional[str] = Field(None, max_length=100, description="회사명")
    tagline: Optional[str] = Field(None, max_length=200, description="태그라인")
    footer_text: Optional[str] = Field(None, max_length=500, description="푸터 텍스트")
    custom_css: Optional[str] = Field(None, max_length=10000, description="커스텀 CSS")


# 애니메이션 설정
class Animation(BaseModel):
    """애니메이션 설정"""
    enabled: bool = Field(default=True, description="애니메이션 활성화")
    duration: int = Field(default=300, ge=100, le=1000, description="애니메이션 지속 시간 (ms)")
    easing: str = Field(default="ease-in-out", description="이징 함수")
    reduced_motion: bool = Field(default=False, description="모션 감소 모드")


# 테마 설정 모델
class ThemeSettings(BaseModel):
    """테마 설정"""
    theme_type: ThemeType = Field(default=ThemeType.LIGHT, description="테마 타입")
    color_scheme: ColorScheme = Field(default=ColorScheme.BLUE, description="색상 스키마")
    colors: ColorPalette = Field(..., description="색상 팔레트")
    typography: Typography = Field(default_factory=Typography, description="타이포그래피")
    layout: Layout = Field(default_factory=Layout, description="레이아웃")
    branding: Branding = Field(default_factory=Branding, description="브랜딩")
    animation: Animation = Field(default_factory=Animation, description="애니메이션")
    custom_properties: Optional[Dict[str, Any]] = Field(None, description="커스텀 속성")


# 조직 테마 모델
class OrganizationTheme(BaseModel):
    """조직 테마"""
    id: Optional[int] = Field(None, description="테마 ID")
    organization_id: int = Field(..., description="조직 ID")
    name: str = Field(..., min_length=1, max_length=100, description="테마 이름")
    description: Optional[str] = Field(None, max_length=500, description="테마 설명")
    settings: ThemeSettings = Field(..., description="테마 설정")
    is_default: bool = Field(default=False, description="기본 테마 여부")
    is_active: bool = Field(default=True, description="활성화 상태")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    created_by: Optional[int] = Field(None, description="생성자 ID")


# 사용자 테마 선호도
class UserThemePreference(BaseModel):
    """사용자 테마 선호도"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    theme_id: Optional[int] = Field(None, description="선택된 테마 ID")
    custom_settings: Optional[ThemeSettings] = Field(None, description="개인 커스텀 설정")
    auto_switch: bool = Field(default=False, description="자동 테마 전환")
    preferred_theme_type: ThemeType = Field(default=ThemeType.AUTO, description="선호 테마 타입")


# 요청/응답 모델들

class ThemeCreateRequest(BaseModel):
    """테마 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100, description="테마 이름")
    description: Optional[str] = Field(None, max_length=500, description="테마 설명")
    settings: ThemeSettings = Field(..., description="테마 설정")
    is_default: bool = Field(default=False, description="기본 테마 여부")


class ThemeUpdateRequest(BaseModel):
    """테마 업데이트 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="테마 이름")
    description: Optional[str] = Field(None, max_length=500, description="테마 설명")
    settings: Optional[ThemeSettings] = Field(None, description="테마 설정")
    is_default: Optional[bool] = Field(None, description="기본 테마 여부")
    is_active: Optional[bool] = Field(None, description="활성화 상태")


class ThemeResponse(BaseModel):
    """테마 응답"""
    id: int = Field(..., description="테마 ID")
    organization_id: int = Field(..., description="조직 ID")
    name: str = Field(..., description="테마 이름")
    description: Optional[str] = Field(None, description="테마 설명")
    settings: ThemeSettings = Field(..., description="테마 설정")
    is_default: bool = Field(..., description="기본 테마 여부")
    is_active: bool = Field(..., description="활성화 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    created_by: Optional[int] = Field(None, description="생성자 ID")


class ThemeListResponse(BaseModel):
    """테마 목록 응답"""
    themes: List[ThemeResponse] = Field(..., description="테마 목록")
    total: int = Field(..., description="전체 테마 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


class ThemePreviewRequest(BaseModel):
    """테마 미리보기 요청"""
    settings: ThemeSettings = Field(..., description="미리보기할 테마 설정")
    component: Optional[str] = Field(None, description="미리보기할 컴포넌트")


class ThemePreviewResponse(BaseModel):
    """테마 미리보기 응답"""
    css: str = Field(..., description="생성된 CSS")
    variables: Dict[str, str] = Field(..., description="CSS 변수")
    preview_url: Optional[str] = Field(None, description="미리보기 URL")


class ThemeExportRequest(BaseModel):
    """테마 내보내기 요청"""
    theme_id: int = Field(..., description="내보낼 테마 ID")
    format: str = Field(default="json", description="내보내기 형식 (json, css)")
    include_assets: bool = Field(default=False, description="에셋 포함 여부")


class ThemeExportResponse(BaseModel):
    """테마 내보내기 응답"""
    data: str = Field(..., description="내보낸 데이터")
    filename: str = Field(..., description="파일명")
    content_type: str = Field(..., description="콘텐츠 타입")


class ThemeImportRequest(BaseModel):
    """테마 가져오기 요청"""
    data: str = Field(..., description="가져올 테마 데이터")
    name: str = Field(..., min_length=1, max_length=100, description="테마 이름")
    overwrite: bool = Field(default=False, description="기존 테마 덮어쓰기")


class ThemeImportResponse(BaseModel):
    """테마 가져오기 응답"""
    theme_id: int = Field(..., description="생성된 테마 ID")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="결과 메시지")


class UserThemePreferenceRequest(BaseModel):
    """사용자 테마 선호도 요청"""
    theme_id: Optional[int] = Field(None, description="선택된 테마 ID")
    custom_settings: Optional[ThemeSettings] = Field(None, description="개인 커스텀 설정")
    auto_switch: bool = Field(default=False, description="자동 테마 전환")
    preferred_theme_type: ThemeType = Field(default=ThemeType.AUTO, description="선호 테마 타입")


class UserThemePreferenceResponse(BaseModel):
    """사용자 테마 선호도 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    theme: Optional[ThemeResponse] = Field(None, description="선택된 테마")
    custom_settings: Optional[ThemeSettings] = Field(None, description="개인 커스텀 설정")
    auto_switch: bool = Field(..., description="자동 테마 전환")
    preferred_theme_type: ThemeType = Field(..., description="선호 테마 타입")
    effective_settings: ThemeSettings = Field(..., description="적용된 최종 설정")


class ThemeStatsResponse(BaseModel):
    """테마 통계 응답"""
    total_themes: int = Field(..., description="전체 테마 수")
    active_themes: int = Field(..., description="활성 테마 수")
    custom_themes: int = Field(..., description="커스텀 테마 수")
    usage_stats: Dict[str, int] = Field(..., description="테마별 사용 통계")
    popular_colors: List[str] = Field(..., description="인기 색상")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


# 검증 함수들

@validator('colors', pre=True)
def validate_color_palette(cls, v):
    """색상 팔레트 검증"""
    if isinstance(v, dict):
        # 필수 색상이 모두 있는지 확인
        required_colors = ['primary', 'secondary', 'background', 'text_primary']
        for color in required_colors:
            if color not in v:
                raise ValueError(f"필수 색상 '{color}'가 누락되었습니다.")
    return v


class ThemeValidationError(Exception):
    """테마 검증 오류"""
    pass


class ThemeNotFoundError(Exception):
    """테마를 찾을 수 없음"""
    pass


class ThemePermissionError(Exception):
    """테마 권한 오류"""
    pass


class ThemeValidationResponse(BaseModel):
    """테마 검증 응답"""
    valid: bool = Field(..., description="검증 결과")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    suggestions: List[str] = Field(default_factory=list, description="개선 제안")


class UserPreferenceRequest(BaseModel):
    """사용자 선호도 요청"""
    theme_id: Optional[int] = Field(None, description="테마 ID")
    custom_settings: Optional[ThemeSettings] = Field(None, description="커스텀 설정")
    auto_switch: bool = Field(True, description="자동 테마 전환")
    preferred_theme_type: ThemeType = Field(ThemeType.LIGHT, description="선호 테마 타입")


class UserPreferenceResponse(BaseModel):
    """사용자 선호도 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    theme_id: Optional[int] = Field(None, description="테마 ID")
    custom_settings: Optional[ThemeSettings] = Field(None, description="커스텀 설정")
    auto_switch: bool = Field(..., description="자동 테마 전환")
    preferred_theme_type: ThemeType = Field(..., description="선호 테마 타입")
    updated_at: datetime = Field(..., description="업데이트 시간")