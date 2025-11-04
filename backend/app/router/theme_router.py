"""
조직별 테마 API 라우터

SkyBoot Mail SaaS 프로젝트의 조직별 테마 및 브랜딩 기능을 위한 API 엔드포인트입니다.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.schemas.theme_schema import (
    ColorPalette, Typography, Layout, Branding, Animation, ThemeSettings,
    OrganizationTheme, UserThemePreference, ThemeCreateRequest, ThemeResponse,
    ThemeListResponse, ThemeUpdateRequest, ThemePreviewRequest, ThemePreviewResponse,
    ThemeImportRequest, ThemeExportRequest, ThemeStatsResponse,
    UserPreferenceRequest, UserPreferenceResponse, ThemeValidationResponse,
    ThemeType, ColorScheme, FontFamily, ComponentSize, BorderRadius
)
from app.service.theme_service import ThemeService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_organization
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import get_db

router = APIRouter()

@router.get("/", summary="조직 테마 목록 조회")
async def get_organization_themes(
    theme_type: Optional[ThemeType] = Query(None, description="테마 타입 필터"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeListResponse:
    """
    조직의 테마 목록을 조회합니다.
    
    - **theme_type**: 테마 타입 (LIGHT, DARK, AUTO, CUSTOM)
    - **is_active**: 활성화된 테마만 조회
    - **page**: 페이지 번호
    - **limit**: 페이지당 항목 수
    """
    service = ThemeService(db)
    return await service.get_organization_themes(
        organization.id,
        theme_type,
        is_active,
        page,
        limit
    )


@router.post("/", summary="새 테마 생성")
async def create_theme(
    theme_request: ThemeCreateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeResponse:
    """
    새로운 테마를 생성합니다.
    
    - **name**: 테마 이름
    - **theme_type**: 테마 타입
    - **color_palette**: 색상 팔레트
    - **typography**: 타이포그래피 설정
    - **layout**: 레이아웃 설정
    - **branding**: 브랜딩 설정
    """
    service = ThemeService(db)
    return await service.create_theme(
        organization.id,
        theme_request,
        current_user.id
    )


@router.get("/{theme_id}", summary="특정 테마 조회")
async def get_theme(
    theme_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeResponse:
    """
    특정 테마의 상세 정보를 조회합니다.
    
    - **theme_id**: 테마 고유 ID
    - **organization_id**: 조직별 테마 접근 권한 확인
    """
    service = ThemeService(db)
    return await service.get_theme(organization.id, theme_id)


@router.put("/{theme_id}", summary="테마 업데이트")
async def update_theme(
    theme_id: str,
    theme_update: ThemeUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeResponse:
    """
    테마를 업데이트합니다.
    
    - **theme_id**: 업데이트할 테마 ID
    - **theme_settings**: 업데이트할 테마 설정
    - **version**: 버전 관리
    """
    service = ThemeService(db)
    return await service.update_theme(
        organization.id,
        theme_id,
        theme_update,
        current_user.id
    )


@router.delete("/{theme_id}", summary="테마 삭제")
async def delete_theme(
    theme_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테마를 삭제합니다.
    
    - **theme_id**: 삭제할 테마 ID
    - **organization_id**: 조직별 삭제 권한 확인
    """
    service = ThemeService(db)
    return await service.delete_theme(organization.id, theme_id, current_user.id)


@router.post("/{theme_id}/activate", summary="테마 활성화")
async def activate_theme(
    theme_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테마를 활성화합니다.
    
    - **theme_id**: 활성화할 테마 ID
    - **organization_id**: 조직의 기본 테마로 설정
    """
    service = ThemeService(db)
    return await service.activate_theme(organization.id, theme_id, current_user.id)


@router.post("/{theme_id}/duplicate", summary="테마 복제")
async def duplicate_theme(
    theme_id: str,
    new_name: str = Query(..., description="새 테마 이름"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeResponse:
    """
    기존 테마를 복제하여 새 테마를 생성합니다.
    
    - **theme_id**: 복제할 테마 ID
    - **new_name**: 새 테마 이름
    """
    service = ThemeService(db)
    return await service.duplicate_theme(
        organization.id,
        theme_id,
        new_name,
        current_user.id
    )


@router.get("/{theme_id}/css", summary="테마 CSS 생성")
async def get_theme_css(
    theme_id: str,
    minified: bool = Query(False, description="CSS 압축 여부"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Response:
    """
    테마의 CSS 파일을 생성합니다.
    
    - **theme_id**: 테마 ID
    - **minified**: CSS 압축 여부
    - **Content-Type**: text/css
    """
    service = ThemeService(db)
    css_content = await service.generate_theme_css(
        organization.id,
        theme_id,
        minified
    )
    
    return Response(
        content=css_content,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename=theme-{theme_id}.css"
        }
    )


@router.post("/preview", summary="테마 미리보기")
async def preview_theme(
    preview_request: ThemePreviewRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemePreviewResponse:
    """
    테마 설정을 미리보기합니다.
    
    - **theme_settings**: 미리보기할 테마 설정
    - **components**: 미리보기할 컴포넌트 목록
    - **preview_url**: 미리보기 URL
    """
    service = ThemeService(db)
    return await service.preview_theme(
        organization.id,
        preview_request,
        current_user.id
    )


@router.post("/import", summary="테마 가져오기")
async def import_theme(
    import_request: ThemeImportRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeResponse:
    """
    외부 테마를 가져옵니다.
    
    - **source_url**: 테마 파일 URL
    - **theme_data**: 테마 데이터 (JSON)
    - **import_mode**: 가져오기 모드 (create, update, merge)
    """
    service = ThemeService(db)
    return await service.import_theme(
        organization.id,
        import_request,
        current_user.id
    )


@router.post("/{theme_id}/export", summary="테마 내보내기")
async def export_theme(
    theme_id: str,
    export_request: ThemeExportRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테마를 내보냅니다.
    
    - **theme_id**: 내보낼 테마 ID
    - **format**: 내보내기 형식 (json, css, scss)
    - **include_assets**: 에셋 포함 여부
    """
    service = ThemeService(db)
    return await service.export_theme(
        organization.id,
        theme_id,
        export_request
    )


@router.post("/upload-asset", summary="테마 에셋 업로드")
async def upload_theme_asset(
    file: UploadFile = File(...),
    asset_type: str = Query(..., description="에셋 타입 (logo, icon, background)"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테마에 사용할 에셋을 업로드합니다.
    
    - **file**: 업로드할 파일
    - **asset_type**: 에셋 타입 (logo, icon, background, font)
    - **max_size**: 최대 파일 크기 제한
    """
    service = ThemeService(db)
    return await service.upload_theme_asset(
        organization.id,
        file,
        asset_type,
        current_user.id
    )


@router.get("/user/preference", summary="사용자 테마 설정 조회")
async def get_user_theme_preference(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserPreferenceResponse:
    """
    사용자의 테마 설정을 조회합니다.
    
    - **preferred_theme_id**: 선호 테마 ID
    - **color_scheme**: 색상 스키마 (light, dark, auto)
    - **font_size**: 글꼴 크기
    - **custom_settings**: 사용자 커스텀 설정
    """
    service = ThemeService(db)
    return await service.get_user_theme_preference(
        current_user.id,
        organization.id
    )


@router.put("/user/preference", summary="사용자 테마 설정 업데이트")
async def update_user_theme_preference(
    preference_request: UserPreferenceRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserPreferenceResponse:
    """
    사용자의 테마 설정을 업데이트합니다.
    
    - **preferred_theme_id**: 선호 테마 변경
    - **color_scheme**: 색상 스키마 변경
    - **font_size**: 글꼴 크기 변경
    - **custom_settings**: 커스텀 설정 변경
    """
    service = ThemeService(db)
    return await service.update_user_theme_preference(
        current_user.id,
        organization.id,
        preference_request
    )


@router.get("/stats", summary="테마 사용 통계")
async def get_theme_statistics(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeStatsResponse:
    """
    테마 사용 통계를 조회합니다.
    
    - **total_themes**: 전체 테마 수
    - **active_themes**: 활성 테마 수
    - **popular_themes**: 인기 테마 목록
    - **usage_stats**: 사용량 통계
    """
    service = ThemeService(db)
    return await service.get_theme_statistics(organization.id)


@router.post("/{theme_id}/validate", summary="테마 유효성 검증")
async def validate_theme(
    theme_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeValidationResponse:
    """
    테마의 유효성을 검증합니다.
    
    - **theme_id**: 검증할 테마 ID
    - **validation_errors**: 검증 오류 목록
    - **warnings**: 경고 목록
    - **suggestions**: 개선 제안
    """
    service = ThemeService(db)
    return await service.validate_theme(organization.id, theme_id)


@router.get("/defaults", summary="기본 테마 목록")
async def get_default_themes(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ThemeListResponse:
    """
    시스템 기본 테마 목록을 조회합니다.
    
    - **system_themes**: 시스템 제공 기본 테마
    - **template_themes**: 템플릿 테마
    - **industry_themes**: 업종별 테마
    """
    service = ThemeService(db)
    return await service.get_default_themes()


@router.post("/reset", summary="테마 설정 초기화")
async def reset_organization_themes(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    조직의 테마 설정을 초기화합니다.
    
    - **reset_to_default**: 기본 테마로 초기화
    - **preserve_custom**: 커스텀 테마 보존 여부
    """
    service = ThemeService(db)
    return await service.reset_organization_themes(
        organization.id,
        current_user.id
    )


@router.get("/cache/clear", summary="테마 캐시 초기화")
async def clear_theme_cache(
    theme_id: Optional[str] = Query(None, description="특정 테마 캐시만 초기화"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테마 캐시를 초기화합니다.
    
    - **theme_id**: 특정 테마 캐시만 초기화 (선택사항)
    - **organization_id**: 조직별 캐시 초기화
    """
    service = ThemeService(db)
    return await service.clear_theme_cache(organization.id, theme_id)


@router.get("/color-palettes", summary="색상 팔레트 목록")
async def get_color_palettes(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용 가능한 색상 팔레트 목록을 조회합니다.
    
    - **predefined_palettes**: 미리 정의된 팔레트
    - **custom_palettes**: 조직 커스텀 팔레트
    - **trending_palettes**: 인기 팔레트
    """
    service = ThemeService(db)
    return await service.get_color_palettes(organization.id)


@router.get("/fonts", summary="사용 가능한 폰트 목록")
async def get_available_fonts(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용 가능한 폰트 목록을 조회합니다.
    
    - **system_fonts**: 시스템 폰트
    - **web_fonts**: 웹 폰트
    - **custom_fonts**: 조직 커스텀 폰트
    """
    service = ThemeService(db)
    return await service.get_available_fonts(organization.id)