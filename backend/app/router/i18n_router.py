"""
국제화(i18n) API 라우터

SkyBoot Mail SaaS 프로젝트의 다국어 지원 기능을 위한 API 엔드포인트입니다.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas.i18n_schema import (
    TranslationEntry, LanguagePackage, OrganizationLanguageSettings,
    UserLanguagePreference, TranslationRequest, TranslationResponse,
    LanguageDetectionResponse, LanguageConfigRequest, LanguageConfigResponse,
    LanguageListResponse, TranslationUpdateRequest, TranslationBulkRequest,
    TranslationExportRequest, TranslationImportRequest, TranslationStatsResponse,
    SupportedLanguage, TranslationNamespace
)
from app.service.i18n_service import I18nService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_organization
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import get_db

router = APIRouter(prefix="/i18n", tags=["국제화"])


@router.get("/languages", summary="지원 언어 목록 조회")
async def get_supported_languages(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguageListResponse:
    """
    지원하는 언어 목록을 조회합니다.
    
    - **organization_id**: 조직별 지원 언어 목록
    - **enabled_only**: 활성화된 언어만 조회 여부
    """
    service = I18nService(db)
    return await service.get_supported_languages(organization.id)


@router.get("/detect", summary="언어 자동 감지")
async def detect_language(
    text: str = Query(..., description="언어를 감지할 텍스트"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguageDetectionResponse:
    """
    텍스트의 언어를 자동으로 감지합니다.
    
    - **text**: 언어를 감지할 텍스트
    - **confidence**: 감지 정확도
    - **alternatives**: 대안 언어 목록
    """
    service = I18nService(db)
    return await service.detect_language(text, organization.id)


@router.post("/translate", summary="텍스트 번역")
async def translate_text(
    translation_request: TranslationRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> TranslationResponse:
    """
    텍스트를 번역합니다.
    
    - **text**: 번역할 텍스트
    - **source_language**: 원본 언어 (자동 감지 가능)
    - **target_language**: 대상 언어
    - **namespace**: 번역 네임스페이스 (UI, EMAIL, SYSTEM 등)
    - **context**: 번역 컨텍스트 정보
    """
    service = I18nService(db)
    return await service.translate_text(
        organization.id,
        translation_request,
        current_user.id
    )


@router.get("/translations/{language_code}", summary="언어별 번역 데이터 조회")
async def get_translations(
    language_code: str,
    namespace: Optional[TranslationNamespace] = Query(None, description="번역 네임스페이스"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguagePackage:
    """
    특정 언어의 번역 데이터를 조회합니다.
    
    - **language_code**: 언어 코드 (예: ko, en, ja)
    - **namespace**: 번역 네임스페이스 필터
    - **organization_id**: 조직별 커스텀 번역 포함
    """
    service = I18nService(db)
    return await service.get_language_package(
        organization.id,
        language_code,
        namespace
    )


@router.put("/translations/{language_code}", summary="번역 데이터 업데이트")
async def update_translations(
    language_code: str,
    update_request: TranslationUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    번역 데이터를 업데이트합니다.
    
    - **language_code**: 언어 코드
    - **translations**: 업데이트할 번역 항목들
    - **merge_mode**: 병합 모드 (replace, merge, append)
    """
    service = I18nService(db)
    return await service.update_translations(
        organization.id,
        language_code,
        update_request,
        current_user.id
    )


@router.post("/translations/bulk", summary="대량 번역 업데이트")
async def bulk_update_translations(
    bulk_request: TranslationBulkRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    여러 언어의 번역을 대량으로 업데이트합니다.
    
    - **languages**: 언어별 번역 데이터
    - **namespace**: 대상 네임스페이스
    - **overwrite**: 기존 번역 덮어쓰기 여부
    """
    service = I18nService(db)
    return await service.bulk_update_translations(
        organization.id,
        bulk_request,
        current_user.id
    )


@router.post("/export", summary="번역 데이터 내보내기")
async def export_translations(
    export_request: TranslationExportRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    번역 데이터를 내보냅니다.
    
    - **languages**: 내보낼 언어 목록
    - **namespaces**: 내보낼 네임스페이스 목록
    - **format**: 내보내기 형식 (json, csv, xlsx)
    - **include_metadata**: 메타데이터 포함 여부
    """
    service = I18nService(db)
    return await service.export_translations(
        organization.id,
        export_request
    )


@router.post("/import", summary="번역 데이터 가져오기")
async def import_translations(
    import_request: TranslationImportRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    번역 데이터를 가져옵니다.
    
    - **file_url**: 가져올 파일 URL
    - **format**: 파일 형식 (json, csv, xlsx)
    - **merge_mode**: 병합 모드
    - **validate_only**: 검증만 수행 여부
    """
    service = I18nService(db)
    return await service.import_translations(
        organization.id,
        import_request,
        current_user.id
    )


@router.get("/config", summary="조직 언어 설정 조회")
async def get_language_config(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguageConfigResponse:
    """
    조직의 언어 설정을 조회합니다.
    
    - **default_language**: 기본 언어
    - **enabled_languages**: 활성화된 언어 목록
    - **fallback_language**: 대체 언어
    - **auto_detection**: 자동 언어 감지 설정
    """
    service = I18nService(db)
    return await service.get_organization_language_config(organization.id)


@router.put("/config", summary="조직 언어 설정 업데이트")
async def update_language_config(
    config_request: LanguageConfigRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguageConfigResponse:
    """
    조직의 언어 설정을 업데이트합니다.
    
    - **default_language**: 기본 언어 설정
    - **enabled_languages**: 활성화할 언어 목록
    - **fallback_language**: 대체 언어 설정
    - **auto_detection_enabled**: 자동 언어 감지 활성화
    """
    service = I18nService(db)
    return await service.update_organization_language_config(
        organization.id,
        config_request,
        current_user.id
    )


@router.get("/user/preference", summary="사용자 언어 설정 조회")
async def get_user_language_preference(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserLanguagePreference:
    """
    사용자의 언어 설정을 조회합니다.
    
    - **preferred_language**: 선호 언어
    - **timezone**: 시간대 설정
    - **date_format**: 날짜 형식
    - **number_format**: 숫자 형식
    """
    service = I18nService(db)
    return await service.get_user_language_preference(
        current_user.id,
        organization.id
    )


@router.put("/user/preference", summary="사용자 언어 설정 업데이트")
async def update_user_language_preference(
    preference: UserLanguagePreference,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> UserLanguagePreference:
    """
    사용자의 언어 설정을 업데이트합니다.
    
    - **preferred_language**: 선호 언어 변경
    - **timezone**: 시간대 변경
    - **date_format**: 날짜 형식 변경
    - **number_format**: 숫자 형식 변경
    """
    service = I18nService(db)
    return await service.update_user_language_preference(
        current_user.id,
        organization.id,
        preference
    )


@router.get("/stats", summary="번역 통계 조회")
async def get_translation_statistics(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> TranslationStatsResponse:
    """
    번역 통계를 조회합니다.
    
    - **total_keys**: 전체 번역 키 수
    - **translated_keys**: 번역된 키 수
    - **completion_rate**: 번역 완성도
    - **language_stats**: 언어별 통계
    """
    service = I18nService(db)
    return await service.get_translation_statistics(organization.id)


@router.get("/missing", summary="누락된 번역 조회")
async def get_missing_translations(
    language_code: Optional[str] = Query(None, description="특정 언어의 누락 번역"),
    namespace: Optional[TranslationNamespace] = Query(None, description="네임스페이스 필터"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    누락된 번역을 조회합니다.
    
    - **language_code**: 특정 언어 필터
    - **namespace**: 네임스페이스 필터
    - **missing_keys**: 누락된 번역 키 목록
    """
    service = I18nService(db)
    return await service.get_missing_translations(
        organization.id,
        language_code,
        namespace
    )


@router.post("/validate", summary="번역 데이터 검증")
async def validate_translations(
    language_code: str,
    namespace: Optional[TranslationNamespace] = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    번역 데이터의 유효성을 검증합니다.
    
    - **language_code**: 검증할 언어
    - **namespace**: 검증할 네임스페이스
    - **validation_errors**: 검증 오류 목록
    - **suggestions**: 개선 제안
    """
    service = I18nService(db)
    return await service.validate_translations(
        organization.id,
        language_code,
        namespace
    )


@router.get("/browser-language", summary="브라우저 언어 감지")
async def detect_browser_language(
    request: Request,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> LanguageDetectionResponse:
    """
    브라우저의 Accept-Language 헤더를 기반으로 언어를 감지합니다.
    
    - **detected_language**: 감지된 언어
    - **supported**: 조직에서 지원하는 언어인지 여부
    - **fallback**: 대체 언어
    """
    service = I18nService(db)
    accept_language = request.headers.get("Accept-Language", "")
    return await service.detect_browser_language(
        organization.id,
        accept_language
    )


@router.get("/cache/clear", summary="번역 캐시 초기화")
async def clear_translation_cache(
    language_code: Optional[str] = Query(None, description="특정 언어 캐시만 초기화"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    번역 캐시를 초기화합니다.
    
    - **language_code**: 특정 언어 캐시만 초기화 (선택사항)
    - **organization_id**: 조직별 캐시 초기화
    """
    service = I18nService(db)
    return await service.clear_translation_cache(
        organization.id,
        language_code
    )