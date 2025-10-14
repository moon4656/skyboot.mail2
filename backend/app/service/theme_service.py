"""
조직별 테마 서비스

SkyBoot Mail SaaS 프로젝트의 조직별 테마 및 브랜딩 서비스입니다.
테마 관리, CSS 생성, 사용자 선호도 등의 기능을 제공합니다.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..schemas.theme_schema import (
    ThemeType, ColorScheme, FontFamily, ComponentSize, BorderRadius,
    ColorPalette, Typography, Layout, Branding, Animation, ThemeSettings,
    OrganizationTheme, UserThemePreference,
    ThemeCreateRequest, ThemeUpdateRequest, ThemeResponse, ThemeListResponse,
    ThemePreviewRequest, ThemePreviewResponse, ThemeExportRequest, ThemeExportResponse,
    ThemeImportRequest, ThemeImportResponse, UserThemePreferenceRequest,
    UserThemePreferenceResponse, ThemeStatsResponse,
    ThemeValidationError, ThemeNotFoundError, ThemePermissionError
)
from ..model.organization_model import Organization
from ..model.user_model import User
import redis
import logging

logger = logging.getLogger(__name__)


class ThemeService:
    """조직별 테마 서비스 클래스"""
    
    def __init__(self, db: Session):
        """
        테마 서비스를 초기화합니다.
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self.redis_client = self._init_redis()
        self.cache_ttl = 3600  # 1시간
        
        # 기본 테마 설정 로드
        self._load_default_themes()
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Redis 클라이언트를 초기화합니다."""
        try:
            client = redis.Redis(host='localhost', port=6379, db=3, decode_responses=True)
            client.ping()
            logger.info("✅ Redis 연결 성공 (테마 캐시)")
            return client
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패 (테마): {str(e)}")
            return None
    
    def _load_default_themes(self):
        """기본 테마 설정을 로드합니다."""
        try:
            # 기본 색상 팔레트들
            self.default_color_palettes = {
                ColorScheme.BLUE: ColorPalette(
                    primary="#1976d2",
                    secondary="#424242",
                    accent="#ff4081",
                    background="#ffffff",
                    surface="#f5f5f5",
                    text_primary="#212121",
                    text_secondary="#757575",
                    border="#e0e0e0",
                    success="#4caf50",
                    warning="#ff9800",
                    error="#f44336",
                    info="#2196f3"
                ),
                ColorScheme.GREEN: ColorPalette(
                    primary="#388e3c",
                    secondary="#424242",
                    accent="#ff4081",
                    background="#ffffff",
                    surface="#f5f5f5",
                    text_primary="#212121",
                    text_secondary="#757575",
                    border="#e0e0e0",
                    success="#4caf50",
                    warning="#ff9800",
                    error="#f44336",
                    info="#2196f3"
                ),
                ColorScheme.PURPLE: ColorPalette(
                    primary="#7b1fa2",
                    secondary="#424242",
                    accent="#ff4081",
                    background="#ffffff",
                    surface="#f5f5f5",
                    text_primary="#212121",
                    text_secondary="#757575",
                    border="#e0e0e0",
                    success="#4caf50",
                    warning="#ff9800",
                    error="#f44336",
                    info="#2196f3"
                )
            }
            
            # 다크 모드 색상 팔레트들
            self.dark_color_palettes = {
                ColorScheme.BLUE: ColorPalette(
                    primary="#2196f3",
                    secondary="#616161",
                    accent="#ff4081",
                    background="#121212",
                    surface="#1e1e1e",
                    text_primary="#ffffff",
                    text_secondary="#b0b0b0",
                    border="#333333",
                    success="#4caf50",
                    warning="#ff9800",
                    error="#f44336",
                    info="#2196f3"
                )
            }
            
            logger.info("🎨 기본 테마 설정 로드 완료")
        except Exception as e:
            logger.error(f"❌ 기본 테마 설정 로드 실패: {str(e)}")
            self.default_color_palettes = {}
            self.dark_color_palettes = {}
    
    def create_theme(self, org_id: int, user_id: int, request: ThemeCreateRequest) -> ThemeResponse:
        """
        새로운 테마를 생성합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            request: 테마 생성 요청
            
        Returns:
            생성된 테마 응답
        """
        try:
            # 테마 설정 검증
            self._validate_theme_settings(request.settings)
            
            # 기본 테마 설정 시 기존 기본 테마 해제
            if request.is_default:
                self._unset_default_themes(org_id)
            
            # 테마 생성 (실제로는 DB에 저장)
            theme_id = self._save_theme(org_id, user_id, request)
            
            # 캐시 무효화
            self._invalidate_theme_cache(org_id)
            
            logger.info(f"🎨 테마 생성 완료 - 조직: {org_id}, 테마: {request.name}")
            
            return self.get_theme(org_id, theme_id)
            
        except Exception as e:
            logger.error(f"❌ 테마 생성 오류: {str(e)}")
            raise
    
    def get_theme(self, org_id: int, theme_id: int) -> ThemeResponse:
        """
        테마를 조회합니다.
        
        Args:
            org_id: 조직 ID
            theme_id: 테마 ID
            
        Returns:
            테마 응답
        """
        try:
            # 캐시에서 조회
            cache_key = f"theme:{org_id}:{theme_id}"
            cached_theme = self._get_from_cache(cache_key)
            
            if cached_theme:
                return ThemeResponse(**cached_theme)
            
            # DB에서 조회 (실제로는 DB 쿼리)
            theme_data = self._get_theme_from_db(org_id, theme_id)
            
            if not theme_data:
                raise ThemeNotFoundError(f"테마를 찾을 수 없습니다: {theme_id}")
            
            # 캐시에 저장
            self._set_cache(cache_key, theme_data)
            
            return ThemeResponse(**theme_data)
            
        except Exception as e:
            logger.error(f"❌ 테마 조회 오류: {str(e)}")
            raise
    
    def get_themes(self, org_id: int, page: int = 1, limit: int = 20, active_only: bool = True) -> ThemeListResponse:
        """
        조직의 테마 목록을 조회합니다.
        
        Args:
            org_id: 조직 ID
            page: 페이지 번호
            limit: 페이지당 항목 수
            active_only: 활성 테마만 조회
            
        Returns:
            테마 목록 응답
        """
        try:
            # 캐시에서 조회
            cache_key = f"themes:{org_id}:{page}:{limit}:{active_only}"
            cached_themes = self._get_from_cache(cache_key)
            
            if cached_themes:
                return ThemeListResponse(**cached_themes)
            
            # DB에서 조회 (실제로는 DB 쿼리)
            themes_data, total = self._get_themes_from_db(org_id, page, limit, active_only)
            
            themes = [ThemeResponse(**theme) for theme in themes_data]
            
            result = ThemeListResponse(
                themes=themes,
                total=total,
                page=page,
                limit=limit
            )
            
            # 캐시에 저장
            self._set_cache(cache_key, result.dict())
            
            logger.info(f"🎨 테마 목록 조회 완료 - 조직: {org_id}, 총 {total}개")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 테마 목록 조회 오류: {str(e)}")
            raise
    
    def update_theme(self, org_id: int, theme_id: int, user_id: int, request: ThemeUpdateRequest) -> ThemeResponse:
        """
        테마를 업데이트합니다.
        
        Args:
            org_id: 조직 ID
            theme_id: 테마 ID
            user_id: 사용자 ID
            request: 테마 업데이트 요청
            
        Returns:
            업데이트된 테마 응답
        """
        try:
            # 기존 테마 조회
            existing_theme = self.get_theme(org_id, theme_id)
            
            # 권한 확인 (실제로는 더 정교한 권한 체크)
            if not self._check_theme_permission(org_id, theme_id, user_id):
                raise ThemePermissionError("테마 수정 권한이 없습니다.")
            
            # 테마 설정 검증
            if request.settings:
                self._validate_theme_settings(request.settings)
            
            # 기본 테마 설정 시 기존 기본 테마 해제
            if request.is_default:
                self._unset_default_themes(org_id, exclude_theme_id=theme_id)
            
            # 테마 업데이트 (실제로는 DB 업데이트)
            self._update_theme_in_db(org_id, theme_id, request)
            
            # 캐시 무효화
            self._invalidate_theme_cache(org_id)
            self._invalidate_cache(f"theme:{org_id}:{theme_id}")
            
            logger.info(f"🎨 테마 업데이트 완료 - 조직: {org_id}, 테마: {theme_id}")
            
            return self.get_theme(org_id, theme_id)
            
        except Exception as e:
            logger.error(f"❌ 테마 업데이트 오류: {str(e)}")
            raise
    
    def delete_theme(self, org_id: int, theme_id: int, user_id: int) -> bool:
        """
        테마를 삭제합니다.
        
        Args:
            org_id: 조직 ID
            theme_id: 테마 ID
            user_id: 사용자 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 권한 확인
            if not self._check_theme_permission(org_id, theme_id, user_id):
                raise ThemePermissionError("테마 삭제 권한이 없습니다.")
            
            # 기본 테마인지 확인
            theme = self.get_theme(org_id, theme_id)
            if theme.is_default:
                raise ThemeValidationError("기본 테마는 삭제할 수 없습니다.")
            
            # 테마 삭제 (실제로는 DB에서 삭제)
            self._delete_theme_from_db(org_id, theme_id)
            
            # 캐시 무효화
            self._invalidate_theme_cache(org_id)
            self._invalidate_cache(f"theme:{org_id}:{theme_id}")
            
            logger.info(f"🎨 테마 삭제 완료 - 조직: {org_id}, 테마: {theme_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 테마 삭제 오류: {str(e)}")
            raise
    
    def preview_theme(self, org_id: int, request: ThemePreviewRequest) -> ThemePreviewResponse:
        """
        테마를 미리보기합니다.
        
        Args:
            org_id: 조직 ID
            request: 테마 미리보기 요청
            
        Returns:
            테마 미리보기 응답
        """
        try:
            # CSS 생성
            css = self._generate_css(request.settings)
            variables = self._extract_css_variables(request.settings)
            
            # 미리보기 URL 생성 (실제로는 임시 파일 생성)
            preview_url = self._generate_preview_url(org_id, css)
            
            logger.info(f"🎨 테마 미리보기 생성 완료 - 조직: {org_id}")
            
            return ThemePreviewResponse(
                css=css,
                variables=variables,
                preview_url=preview_url
            )
            
        except Exception as e:
            logger.error(f"❌ 테마 미리보기 오류: {str(e)}")
            raise
    
    def export_theme(self, org_id: int, request: ThemeExportRequest) -> ThemeExportResponse:
        """
        테마를 내보냅니다.
        
        Args:
            org_id: 조직 ID
            request: 테마 내보내기 요청
            
        Returns:
            테마 내보내기 응답
        """
        try:
            theme = self.get_theme(org_id, request.theme_id)
            
            if request.format == "json":
                data = json.dumps(theme.dict(), indent=2, ensure_ascii=False)
                filename = f"theme_{theme.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                content_type = "application/json"
            elif request.format == "css":
                data = self._generate_css(theme.settings)
                filename = f"theme_{theme.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.css"
                content_type = "text/css"
            else:
                raise ThemeValidationError(f"지원하지 않는 내보내기 형식: {request.format}")
            
            logger.info(f"🎨 테마 내보내기 완료 - 조직: {org_id}, 테마: {request.theme_id}")
            
            return ThemeExportResponse(
                data=data,
                filename=filename,
                content_type=content_type
            )
            
        except Exception as e:
            logger.error(f"❌ 테마 내보내기 오류: {str(e)}")
            raise
    
    def import_theme(self, org_id: int, user_id: int, request: ThemeImportRequest) -> ThemeImportResponse:
        """
        테마를 가져옵니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            request: 테마 가져오기 요청
            
        Returns:
            테마 가져오기 응답
        """
        try:
            # 데이터 파싱
            try:
                theme_data = json.loads(request.data)
            except json.JSONDecodeError:
                raise ThemeValidationError("잘못된 JSON 형식입니다.")
            
            # 테마 설정 검증
            if "settings" not in theme_data:
                raise ThemeValidationError("테마 설정이 없습니다.")
            
            settings = ThemeSettings(**theme_data["settings"])
            self._validate_theme_settings(settings)
            
            # 테마 생성 요청 구성
            create_request = ThemeCreateRequest(
                name=request.name,
                description=theme_data.get("description"),
                settings=settings,
                is_default=False
            )
            
            # 기존 테마 확인 및 덮어쓰기 처리
            if not request.overwrite:
                existing_themes = self.get_themes(org_id, limit=1000)
                if any(theme.name == request.name for theme in existing_themes.themes):
                    raise ThemeValidationError(f"이미 존재하는 테마 이름입니다: {request.name}")
            
            # 테마 생성
            created_theme = self.create_theme(org_id, user_id, create_request)
            
            logger.info(f"🎨 테마 가져오기 완료 - 조직: {org_id}, 테마: {created_theme.id}")
            
            return ThemeImportResponse(
                theme_id=created_theme.id,
                success=True,
                message="테마를 성공적으로 가져왔습니다."
            )
            
        except Exception as e:
            logger.error(f"❌ 테마 가져오기 오류: {str(e)}")
            return ThemeImportResponse(
                theme_id=0,
                success=False,
                message=f"테마 가져오기 실패: {str(e)}"
            )
    
    def get_user_theme_preference(self, org_id: int, user_id: int) -> UserThemePreferenceResponse:
        """
        사용자 테마 선호도를 조회합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            
        Returns:
            사용자 테마 선호도 응답
        """
        try:
            # 사용자 선호도 조회 (실제로는 DB에서 조회)
            preference_data = self._get_user_preference_from_db(org_id, user_id)
            
            # 선택된 테마 조회
            theme = None
            if preference_data.get("theme_id"):
                try:
                    theme = self.get_theme(org_id, preference_data["theme_id"])
                except ThemeNotFoundError:
                    # 테마가 삭제된 경우 기본 테마로 설정
                    theme = self._get_default_theme(org_id)
            else:
                theme = self._get_default_theme(org_id)
            
            # 최종 적용 설정 계산
            effective_settings = self._calculate_effective_settings(
                theme.settings if theme else None,
                preference_data.get("custom_settings"),
                preference_data.get("preferred_theme_type", ThemeType.AUTO)
            )
            
            return UserThemePreferenceResponse(
                user_id=user_id,
                organization_id=org_id,
                theme=theme,
                custom_settings=preference_data.get("custom_settings"),
                auto_switch=preference_data.get("auto_switch", False),
                preferred_theme_type=preference_data.get("preferred_theme_type", ThemeType.AUTO),
                effective_settings=effective_settings
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 테마 선호도 조회 오류: {str(e)}")
            raise
    
    def update_user_theme_preference(self, org_id: int, user_id: int, request: UserThemePreferenceRequest) -> UserThemePreferenceResponse:
        """
        사용자 테마 선호도를 업데이트합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            request: 사용자 테마 선호도 요청
            
        Returns:
            사용자 테마 선호도 응답
        """
        try:
            # 선택된 테마 검증
            if request.theme_id:
                try:
                    self.get_theme(org_id, request.theme_id)
                except ThemeNotFoundError:
                    raise ThemeValidationError(f"존재하지 않는 테마입니다: {request.theme_id}")
            
            # 커스텀 설정 검증
            if request.custom_settings:
                self._validate_theme_settings(request.custom_settings)
            
            # 사용자 선호도 저장 (실제로는 DB에 저장)
            self._save_user_preference(org_id, user_id, request)
            
            # 캐시 무효화
            self._invalidate_cache(f"user_preference:{org_id}:{user_id}")
            
            logger.info(f"🎨 사용자 테마 선호도 업데이트 완료 - 조직: {org_id}, 사용자: {user_id}")
            
            return self.get_user_theme_preference(org_id, user_id)
            
        except Exception as e:
            logger.error(f"❌ 사용자 테마 선호도 업데이트 오류: {str(e)}")
            raise
    
    def get_theme_stats(self, org_id: int) -> ThemeStatsResponse:
        """
        테마 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            테마 통계 응답
        """
        try:
            # 테마 통계 계산 (실제로는 DB 쿼리)
            stats_data = self._calculate_theme_stats(org_id)
            
            return ThemeStatsResponse(
                total_themes=stats_data["total_themes"],
                active_themes=stats_data["active_themes"],
                custom_themes=stats_data["custom_themes"],
                usage_stats=stats_data["usage_stats"],
                popular_colors=stats_data["popular_colors"],
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 테마 통계 조회 오류: {str(e)}")
            raise
    
    # 내부 헬퍼 메서드들
    
    def _validate_theme_settings(self, settings: ThemeSettings):
        """테마 설정을 검증합니다."""
        try:
            # 색상 형식 검증
            colors = settings.colors
            color_fields = [
                colors.primary, colors.secondary, colors.accent,
                colors.background, colors.surface, colors.text_primary,
                colors.text_secondary, colors.border, colors.success,
                colors.warning, colors.error, colors.info
            ]
            
            for color in color_fields:
                if not color.startswith('#') or len(color) != 7:
                    raise ThemeValidationError(f"잘못된 색상 형식: {color}")
            
            # 폰트 크기 검증
            typography = settings.typography
            if typography.font_size_base < 10 or typography.font_size_base > 24:
                raise ThemeValidationError("폰트 크기는 10px~24px 사이여야 합니다.")
            
            # 레이아웃 검증
            layout = settings.layout
            if layout.sidebar_width < 200 or layout.sidebar_width > 400:
                raise ThemeValidationError("사이드바 너비는 200px~400px 사이여야 합니다.")
            
        except Exception as e:
            logger.error(f"❌ 테마 설정 검증 오류: {str(e)}")
            raise ThemeValidationError(str(e))
    
    def _generate_css(self, settings: ThemeSettings) -> str:
        """테마 설정으로부터 CSS를 생성합니다."""
        try:
            css_parts = []
            
            # CSS 변수 정의
            css_parts.append(":root {")
            
            # 색상 변수
            colors = settings.colors
            css_parts.extend([
                f"  --color-primary: {colors.primary};",
                f"  --color-secondary: {colors.secondary};",
                f"  --color-accent: {colors.accent};",
                f"  --color-background: {colors.background};",
                f"  --color-surface: {colors.surface};",
                f"  --color-text-primary: {colors.text_primary};",
                f"  --color-text-secondary: {colors.text_secondary};",
                f"  --color-border: {colors.border};",
                f"  --color-success: {colors.success};",
                f"  --color-warning: {colors.warning};",
                f"  --color-error: {colors.error};",
                f"  --color-info: {colors.info};"
            ])
            
            # 타이포그래피 변수
            typography = settings.typography
            css_parts.extend([
                f"  --font-family: {self._get_font_family_css(typography.font_family)};",
                f"  --font-size-base: {typography.font_size_base}px;",
                f"  --font-size-scale: {typography.font_size_scale};",
                f"  --line-height: {typography.line_height};",
                f"  --letter-spacing: {typography.letter_spacing}px;"
            ])
            
            # 레이아웃 변수
            layout = settings.layout
            css_parts.extend([
                f"  --sidebar-width: {layout.sidebar_width}px;",
                f"  --header-height: {layout.header_height}px;",
                f"  --content-max-width: {layout.content_max_width}px;",
                f"  --border-radius: {self._get_border_radius_css(layout.border_radius)};",
                f"  --spacing-unit: {layout.spacing_unit}px;"
            ])
            
            # 애니메이션 변수
            animation = settings.animation
            css_parts.extend([
                f"  --animation-duration: {animation.duration}ms;",
                f"  --animation-easing: {animation.easing};"
            ])
            
            css_parts.append("}")
            
            # 기본 스타일
            css_parts.extend([
                "",
                "body {",
                "  font-family: var(--font-family);",
                "  font-size: var(--font-size-base);",
                "  line-height: var(--line-height);",
                "  letter-spacing: var(--letter-spacing);",
                "  color: var(--color-text-primary);",
                "  background-color: var(--color-background);",
                "}",
                "",
                ".theme-surface {",
                "  background-color: var(--color-surface);",
                "  border: 1px solid var(--color-border);",
                "  border-radius: var(--border-radius);",
                "}",
                "",
                ".theme-primary {",
                "  background-color: var(--color-primary);",
                "  color: white;",
                "}",
                "",
                ".theme-secondary {",
                "  background-color: var(--color-secondary);",
                "  color: white;",
                "}"
            ])
            
            # 커스텀 CSS 추가
            if settings.branding.custom_css:
                css_parts.extend(["", "/* Custom CSS */", settings.branding.custom_css])
            
            return "\n".join(css_parts)
            
        except Exception as e:
            logger.error(f"❌ CSS 생성 오류: {str(e)}")
            raise
    
    def _extract_css_variables(self, settings: ThemeSettings) -> Dict[str, str]:
        """테마 설정에서 CSS 변수를 추출합니다."""
        variables = {}
        
        # 색상 변수
        colors = settings.colors
        variables.update({
            "--color-primary": colors.primary,
            "--color-secondary": colors.secondary,
            "--color-accent": colors.accent,
            "--color-background": colors.background,
            "--color-surface": colors.surface,
            "--color-text-primary": colors.text_primary,
            "--color-text-secondary": colors.text_secondary,
            "--color-border": colors.border,
            "--color-success": colors.success,
            "--color-warning": colors.warning,
            "--color-error": colors.error,
            "--color-info": colors.info
        })
        
        # 타이포그래피 변수
        typography = settings.typography
        variables.update({
            "--font-family": self._get_font_family_css(typography.font_family),
            "--font-size-base": f"{typography.font_size_base}px",
            "--font-size-scale": str(typography.font_size_scale),
            "--line-height": str(typography.line_height),
            "--letter-spacing": f"{typography.letter_spacing}px"
        })
        
        return variables
    
    def _get_font_family_css(self, font_family: FontFamily) -> str:
        """폰트 패밀리를 CSS 값으로 변환합니다."""
        font_map = {
            FontFamily.SYSTEM: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            FontFamily.ROBOTO: "'Roboto', sans-serif",
            FontFamily.OPEN_SANS: "'Open Sans', sans-serif",
            FontFamily.NOTO_SANS: "'Noto Sans', sans-serif",
            FontFamily.NOTO_SANS_KR: "'Noto Sans KR', sans-serif",
            FontFamily.MALGUN_GOTHIC: "'Malgun Gothic', sans-serif"
        }
        return font_map.get(font_family, font_map[FontFamily.SYSTEM])
    
    def _get_border_radius_css(self, border_radius: BorderRadius) -> str:
        """테두리 반경을 CSS 값으로 변환합니다."""
        radius_map = {
            BorderRadius.NONE: "0",
            BorderRadius.SMALL: "4px",
            BorderRadius.MEDIUM: "8px",
            BorderRadius.LARGE: "12px",
            BorderRadius.FULL: "50%"
        }
        return radius_map.get(border_radius, radius_map[BorderRadius.MEDIUM])
    
    # 데이터베이스 관련 메서드들 (실제로는 SQLAlchemy 모델 사용)
    
    def _save_theme(self, org_id: int, user_id: int, request: ThemeCreateRequest) -> int:
        """테마를 저장합니다."""
        # 실제로는 DB에 저장하고 ID 반환
        return 1
    
    def _get_theme_from_db(self, org_id: int, theme_id: int) -> Optional[Dict[str, Any]]:
        """DB에서 테마를 조회합니다."""
        # 실제로는 DB 쿼리
        return {
            "id": theme_id,
            "organization_id": org_id,
            "name": "기본 테마",
            "description": "기본 테마입니다.",
            "settings": self._get_default_theme_settings().dict(),
            "is_default": True,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": 1
        }
    
    def _get_default_theme_settings(self) -> ThemeSettings:
        """기본 테마 설정을 반환합니다."""
        return ThemeSettings(
            theme_type=ThemeType.LIGHT,
            color_scheme=ColorScheme.BLUE,
            colors=self.default_color_palettes.get(ColorScheme.BLUE, ColorPalette(
                primary="#1976d2", secondary="#424242", accent="#ff4081",
                background="#ffffff", surface="#f5f5f5", text_primary="#212121",
                text_secondary="#757575", border="#e0e0e0", success="#4caf50",
                warning="#ff9800", error="#f44336", info="#2196f3"
            ))
        )
    
    # 캐시 관련 메서드들
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터를 조회합니다."""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"⚠️ 캐시 조회 실패: {str(e)}")
        return None
    
    def _set_cache(self, key: str, data: Dict[str, Any]):
        """캐시에 데이터를 저장합니다."""
        if self.redis_client:
            try:
                self.redis_client.setex(key, self.cache_ttl, json.dumps(data, default=str))
            except Exception as e:
                logger.warning(f"⚠️ 캐시 저장 실패: {str(e)}")
    
    def _invalidate_cache(self, key: str):
        """캐시를 무효화합니다."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"⚠️ 캐시 무효화 실패: {str(e)}")
    
    def _invalidate_theme_cache(self, org_id: int):
        """조직의 테마 관련 캐시를 모두 무효화합니다."""
        if self.redis_client:
            try:
                pattern = f"theme*:{org_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"⚠️ 테마 캐시 무효화 실패: {str(e)}")
    
    # 기타 헬퍼 메서드들
    
    def _unset_default_themes(self, org_id: int, exclude_theme_id: Optional[int] = None):
        """기존 기본 테마를 해제합니다."""
        # 실제로는 DB 업데이트
        pass
    
    def _check_theme_permission(self, org_id: int, theme_id: int, user_id: int) -> bool:
        """테마 권한을 확인합니다."""
        # 실제로는 더 정교한 권한 체크
        return True
    
    def _update_theme_in_db(self, org_id: int, theme_id: int, request: ThemeUpdateRequest):
        """DB에서 테마를 업데이트합니다."""
        # 실제로는 DB 업데이트
        pass
    
    def _delete_theme_from_db(self, org_id: int, theme_id: int):
        """DB에서 테마를 삭제합니다."""
        # 실제로는 DB 삭제
        pass
    
    def _generate_preview_url(self, org_id: int, css: str) -> Optional[str]:
        """미리보기 URL을 생성합니다."""
        # 실제로는 임시 파일 생성 후 URL 반환
        return f"/api/v1/themes/preview/{org_id}/{datetime.now().timestamp()}"
    
    def _get_default_theme(self, org_id: int) -> Optional[ThemeResponse]:
        """기본 테마를 조회합니다."""
        # 실제로는 DB에서 기본 테마 조회
        try:
            return self.get_theme(org_id, 1)  # 기본 테마 ID
        except:
            return None
    
    def _calculate_effective_settings(self, theme_settings: Optional[ThemeSettings], 
                                    custom_settings: Optional[ThemeSettings], 
                                    preferred_type: ThemeType) -> ThemeSettings:
        """최종 적용 설정을 계산합니다."""
        # 기본 설정부터 시작
        effective = theme_settings or self._get_default_theme_settings()
        
        # 커스텀 설정 적용
        if custom_settings:
            # 실제로는 더 정교한 병합 로직
            effective = custom_settings
        
        # 선호 테마 타입 적용
        if preferred_type == ThemeType.DARK:
            # 다크 모드 색상으로 변경
            if effective.color_scheme in self.dark_color_palettes:
                effective.colors = self.dark_color_palettes[effective.color_scheme]
        
        return effective
    
    def _get_user_preference_from_db(self, org_id: int, user_id: int) -> Dict[str, Any]:
        """DB에서 사용자 선호도를 조회합니다."""
        # 실제로는 DB 쿼리
        return {
            "theme_id": None,
            "custom_settings": None,
            "auto_switch": False,
            "preferred_theme_type": ThemeType.AUTO
        }
    
    def _save_user_preference(self, org_id: int, user_id: int, request: UserThemePreferenceRequest):
        """사용자 선호도를 저장합니다."""
        # 실제로는 DB에 저장
        pass
    
    def _get_themes_from_db(self, org_id: int, page: int, limit: int, active_only: bool) -> Tuple[List[Dict[str, Any]], int]:
        """DB에서 테마 목록을 조회합니다."""
        # 실제로는 DB 쿼리
        themes = [self._get_theme_from_db(org_id, 1)]
        return themes, 1
    
    def _calculate_theme_stats(self, org_id: int) -> Dict[str, Any]:
        """테마 통계를 계산합니다."""
        # 실제로는 DB 쿼리
        return {
            "total_themes": 1,
            "active_themes": 1,
            "custom_themes": 0,
            "usage_stats": {"기본 테마": 1},
            "popular_colors": ["#1976d2", "#4caf50", "#ff9800"]
        }