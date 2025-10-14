"""
국제화(i18n) 관련 스키마 정의

SkyBoot Mail SaaS 프로젝트의 다국어 지원을 위한 Pydantic 모델들을 정의합니다.
조직별로 다른 언어 설정과 번역 데이터를 관리할 수 있습니다.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SupportedLanguage(str, Enum):
    """지원하는 언어 목록"""
    KOREAN = "ko"
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    RUSSIAN = "ru"
    PORTUGUESE = "pt"


class TranslationNamespace(str, Enum):
    """번역 네임스페이스"""
    COMMON = "common"
    AUTH = "auth"
    MAIL = "mail"
    ORGANIZATION = "organization"
    USER = "user"
    MONITORING = "monitoring"
    SETTINGS = "settings"
    ERRORS = "errors"


class TranslationEntry(BaseModel):
    """번역 항목"""
    key: str
    value: str
    namespace: TranslationNamespace
    description: Optional[str] = None


class LanguagePackage(BaseModel):
    """언어 패키지"""
    language: SupportedLanguage
    translations: Dict[str, str]
    namespace: TranslationNamespace
    version: str = "1.0.0"
    last_updated: datetime


class OrganizationLanguageSettings(BaseModel):
    """조직 언어 설정"""
    organization_id: int
    default_language: SupportedLanguage
    supported_languages: List[SupportedLanguage]
    fallback_language: SupportedLanguage = SupportedLanguage.ENGLISH
    auto_detect: bool = True
    force_default: bool = False


class UserLanguagePreference(BaseModel):
    """사용자 언어 선호도"""
    user_id: int
    preferred_language: SupportedLanguage
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None


class TranslationRequest(BaseModel):
    """번역 요청"""
    language: Optional[SupportedLanguage] = None
    namespace: Optional[TranslationNamespace] = None
    keys: Optional[List[str]] = None


class TranslationResponse(BaseModel):
    """번역 응답"""
    language: SupportedLanguage
    namespace: TranslationNamespace
    translations: Dict[str, str]
    fallback_used: bool = False
    cache_hit: bool = False


class BulkTranslationRequest(BaseModel):
    """대량 번역 요청"""
    languages: List[SupportedLanguage]
    namespaces: List[TranslationNamespace]
    keys: Optional[List[str]] = None


class BulkTranslationResponse(BaseModel):
    """대량 번역 응답"""
    translations: Dict[str, Dict[str, Dict[str, str]]]  # language -> namespace -> key -> value
    missing_translations: List[Dict[str, Any]]


class LanguageDetectionRequest(BaseModel):
    """언어 감지 요청"""
    text: str
    hint_languages: Optional[List[SupportedLanguage]] = None


class LanguageDetectionResponse(BaseModel):
    """언어 감지 응답"""
    detected_language: SupportedLanguage
    confidence: float
    alternatives: List[Dict[str, Any]]


class TranslationUpdateRequest(BaseModel):
    """번역 업데이트 요청"""
    language: SupportedLanguage
    namespace: TranslationNamespace
    translations: Dict[str, str]
    overwrite: bool = False


class TranslationUpdateResponse(BaseModel):
    """번역 업데이트 응답"""
    updated_count: int
    skipped_count: int
    errors: List[str]
    success: bool


class LanguageStatsResponse(BaseModel):
    """언어 통계 응답"""
    total_languages: int
    total_translations: int
    completion_rates: Dict[str, float]  # language -> completion percentage
    last_updated: datetime


class I18nConfigRequest(BaseModel):
    """국제화 설정 요청"""
    default_language: SupportedLanguage
    supported_languages: List[SupportedLanguage]
    fallback_language: SupportedLanguage
    auto_detect: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600


class I18nConfigResponse(BaseModel):
    """국제화 설정 응답"""
    organization_id: int
    default_language: SupportedLanguage
    supported_languages: List[SupportedLanguage]
    fallback_language: SupportedLanguage
    auto_detect: bool
    cache_enabled: bool
    cache_ttl: int
    created_at: datetime
    updated_at: datetime


class LanguageConfigRequest(BaseModel):
    """언어 설정 요청"""
    default_language: SupportedLanguage
    supported_languages: List[SupportedLanguage]
    fallback_language: Optional[SupportedLanguage] = SupportedLanguage.ENGLISH
    auto_detect: bool = True


class LanguageConfigResponse(BaseModel):
    """언어 설정 응답"""
    organization_id: int
    default_language: SupportedLanguage
    supported_languages: List[SupportedLanguage]
    fallback_language: SupportedLanguage
    auto_detect: bool
    updated_at: datetime


class UserLanguageRequest(BaseModel):
    """사용자 언어 요청"""
    preferred_language: SupportedLanguage
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None


class UserLanguageResponse(BaseModel):
    """사용자 언어 응답"""
    user_id: int
    preferred_language: SupportedLanguage
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    updated_at: datetime


class TranslationExportRequest(BaseModel):
    """번역 내보내기 요청"""
    languages: Optional[List[SupportedLanguage]] = None
    namespaces: Optional[List[TranslationNamespace]] = None
    format: str = "json"  # json, csv, xlsx


class TranslationExportResponse(BaseModel):
    """번역 내보내기 응답"""
    download_url: str
    file_size: int
    format: str
    expires_at: datetime


class TranslationImportRequest(BaseModel):
    """번역 가져오기 요청"""
    file_url: str
    format: str = "json"
    overwrite: bool = False
    validate_only: bool = False


class TranslationImportResponse(BaseModel):
    """번역 가져오기 응답"""
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    success: bool


class MissingTranslationResponse(BaseModel):
    """누락된 번역 응답"""
    language: SupportedLanguage
    namespace: TranslationNamespace
    missing_keys: List[str]
    total_missing: int


class TranslationValidationRequest(BaseModel):
    """번역 검증 요청"""
    language: SupportedLanguage
    namespace: TranslationNamespace
    translations: Dict[str, str]


class TranslationValidationResponse(BaseModel):
    """번역 검증 응답"""
    valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]


class LanguageListResponse(BaseModel):
    """언어 목록 응답"""
    languages: List[Dict[str, str]]
    total_count: int
    supported_count: int


class TranslationBulkRequest(BaseModel):
    """대량 번역 요청"""
    language: SupportedLanguage
    namespace: TranslationNamespace
    translations: Dict[str, str]
    overwrite: bool = False


class TranslationStatsResponse(BaseModel):
    """번역 통계 응답"""
    total_translations: int
    completed_translations: int
    missing_translations: int
    completion_rate: float
    languages: Dict[str, Dict[str, Any]]
    namespaces: Dict[str, Dict[str, Any]]
    last_updated: datetime