"""
국제화(i18n) 서비스

SkyBoot Mail SaaS 프로젝트의 다국어 지원 서비스입니다.
조직별 언어 설정, 번역 관리, 언어 감지 등의 기능을 제공합니다.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..schemas.i18n_schema import (
    SupportedLanguage, TranslationNamespace, TranslationRequest, TranslationResponse,
    BulkTranslationRequest, BulkTranslationResponse, LanguageDetectionRequest,
    LanguageDetectionResponse, TranslationUpdateRequest, TranslationUpdateResponse,
    LanguageStatsResponse, I18nConfigRequest, I18nConfigResponse,
    OrganizationLanguageSettings, UserLanguagePreference
)
from ..model.organization_model import Organization
from ..model.user_model import User
import redis
import logging

logger = logging.getLogger(__name__)


class I18nService:
    """국제화 서비스 클래스"""
    
    def __init__(self, db: Session):
        """
        국제화 서비스를 초기화합니다.
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self.redis_client = self._init_redis()
        self.translation_cache = {}
        self.cache_ttl = 3600  # 1시간
        
        # 기본 번역 데이터 로드
        self._load_default_translations()
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Redis 클라이언트를 초기화합니다."""
        try:
            client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
            client.ping()
            logger.info("✅ Redis 연결 성공 (i18n 캐시)")
            return client
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패 (i18n): {str(e)}")
            return None
    
    def _load_default_translations(self):
        """기본 번역 데이터를 로드합니다."""
        try:
            # 기본 번역 데이터 (실제로는 파일이나 DB에서 로드)
            self.default_translations = {
                SupportedLanguage.KOREAN: {
                    TranslationNamespace.COMMON: {
                        "welcome": "환영합니다",
                        "login": "로그인",
                        "logout": "로그아웃",
                        "email": "이메일",
                        "password": "비밀번호",
                        "submit": "제출",
                        "cancel": "취소",
                        "save": "저장",
                        "delete": "삭제",
                        "edit": "편집",
                        "search": "검색",
                        "loading": "로딩 중...",
                        "error": "오류",
                        "success": "성공"
                    },
                    TranslationNamespace.MAIL: {
                        "inbox": "받은편지함",
                        "sent": "보낸편지함",
                        "draft": "임시보관함",
                        "trash": "휴지통",
                        "compose": "메일 작성",
                        "send": "보내기",
                        "reply": "답장",
                        "forward": "전달",
                        "subject": "제목",
                        "from": "보낸사람",
                        "to": "받는사람",
                        "cc": "참조",
                        "bcc": "숨은참조",
                        "attachment": "첨부파일"
                    }
                },
                SupportedLanguage.ENGLISH: {
                    TranslationNamespace.COMMON: {
                        "welcome": "Welcome",
                        "login": "Login",
                        "logout": "Logout",
                        "email": "Email",
                        "password": "Password",
                        "submit": "Submit",
                        "cancel": "Cancel",
                        "save": "Save",
                        "delete": "Delete",
                        "edit": "Edit",
                        "search": "Search",
                        "loading": "Loading...",
                        "error": "Error",
                        "success": "Success"
                    },
                    TranslationNamespace.MAIL: {
                        "inbox": "Inbox",
                        "sent": "Sent",
                        "draft": "Draft",
                        "trash": "Trash",
                        "compose": "Compose",
                        "send": "Send",
                        "reply": "Reply",
                        "forward": "Forward",
                        "subject": "Subject",
                        "from": "From",
                        "to": "To",
                        "cc": "CC",
                        "bcc": "BCC",
                        "attachment": "Attachment"
                    }
                }
            }
            logger.info("📚 기본 번역 데이터 로드 완료")
        except Exception as e:
            logger.error(f"❌ 기본 번역 데이터 로드 실패: {str(e)}")
            self.default_translations = {}
    
    def get_translations(self, org_id: int, request: TranslationRequest) -> TranslationResponse:
        """
        번역 데이터를 조회합니다.
        
        Args:
            org_id: 조직 ID
            request: 번역 요청
            
        Returns:
            번역 응답
        """
        try:
            # 조직 언어 설정 조회
            org_settings = self._get_organization_language_settings(org_id)
            language = request.language or org_settings.default_language
            namespace = request.namespace or TranslationNamespace.COMMON
            
            # 캐시에서 번역 데이터 조회
            cache_key = f"i18n:{org_id}:{language}:{namespace}"
            cached_translations = self._get_from_cache(cache_key)
            
            if cached_translations:
                translations = cached_translations
                cache_hit = True
            else:
                # 번역 데이터 조회
                translations = self._get_translations_from_source(org_id, language, namespace)
                self._set_cache(cache_key, translations)
                cache_hit = False
            
            # 특정 키만 요청된 경우 필터링
            if request.keys:
                translations = {k: v for k, v in translations.items() if k in request.keys}
            
            # 폴백 언어 처리
            fallback_used = False
            if not translations and language != org_settings.fallback_language:
                fallback_translations = self._get_translations_from_source(
                    org_id, org_settings.fallback_language, namespace
                )
                if fallback_translations:
                    translations = fallback_translations
                    fallback_used = True
                    language = org_settings.fallback_language
            
            logger.info(f"📚 번역 데이터 조회 - 조직: {org_id}, 언어: {language}, 네임스페이스: {namespace}")
            
            return TranslationResponse(
                language=language,
                namespace=namespace,
                translations=translations,
                fallback_used=fallback_used,
                cache_hit=cache_hit
            )
            
        except Exception as e:
            logger.error(f"❌ 번역 데이터 조회 오류: {str(e)}")
            # 기본 번역 반환
            return self._get_default_translation_response(language, namespace)
    
    def get_bulk_translations(self, org_id: int, request: BulkTranslationRequest) -> BulkTranslationResponse:
        """
        대량 번역 데이터를 조회합니다.
        
        Args:
            org_id: 조직 ID
            request: 대량 번역 요청
            
        Returns:
            대량 번역 응답
        """
        try:
            translations = {}
            missing_translations = []
            
            for language in request.languages:
                translations[language] = {}
                
                for namespace in request.namespaces:
                    translation_request = TranslationRequest(
                        language=language,
                        namespace=namespace,
                        keys=request.keys
                    )
                    
                    response = self.get_translations(org_id, translation_request)
                    translations[language][namespace] = response.translations
                    
                    # 누락된 번역 추적
                    if request.keys:
                        for key in request.keys:
                            if key not in response.translations:
                                missing_translations.append({
                                    "language": language,
                                    "namespace": namespace,
                                    "key": key
                                })
            
            logger.info(f"📚 대량 번역 데이터 조회 완료 - 조직: {org_id}")
            
            return BulkTranslationResponse(
                translations=translations,
                missing_translations=missing_translations
            )
            
        except Exception as e:
            logger.error(f"❌ 대량 번역 데이터 조회 오류: {str(e)}")
            raise
    
    def detect_language(self, request: LanguageDetectionRequest) -> LanguageDetectionResponse:
        """
        텍스트의 언어를 감지합니다.
        
        Args:
            request: 언어 감지 요청
            
        Returns:
            언어 감지 응답
        """
        try:
            # 간단한 언어 감지 로직 (실제로는 더 정교한 라이브러리 사용)
            text = request.text.lower()
            
            # 한국어 감지
            korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
            if korean_chars > len(text) * 0.3:
                return LanguageDetectionResponse(
                    detected_language=SupportedLanguage.KOREAN,
                    confidence=0.9,
                    alternatives=[
                        {"language": SupportedLanguage.ENGLISH, "confidence": 0.1}
                    ]
                )
            
            # 일본어 감지
            japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
            if japanese_chars > len(text) * 0.2:
                return LanguageDetectionResponse(
                    detected_language=SupportedLanguage.JAPANESE,
                    confidence=0.8,
                    alternatives=[
                        {"language": SupportedLanguage.ENGLISH, "confidence": 0.2}
                    ]
                )
            
            # 중국어 감지
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            if chinese_chars > len(text) * 0.2:
                return LanguageDetectionResponse(
                    detected_language=SupportedLanguage.CHINESE_SIMPLIFIED,
                    confidence=0.8,
                    alternatives=[
                        {"language": SupportedLanguage.CHINESE_TRADITIONAL, "confidence": 0.1},
                        {"language": SupportedLanguage.ENGLISH, "confidence": 0.1}
                    ]
                )
            
            # 기본값: 영어
            return LanguageDetectionResponse(
                detected_language=SupportedLanguage.ENGLISH,
                confidence=0.7,
                alternatives=[
                    {"language": SupportedLanguage.KOREAN, "confidence": 0.2},
                    {"language": SupportedLanguage.SPANISH, "confidence": 0.1}
                ]
            )
            
        except Exception as e:
            logger.error(f"❌ 언어 감지 오류: {str(e)}")
            return LanguageDetectionResponse(
                detected_language=SupportedLanguage.ENGLISH,
                confidence=0.5,
                alternatives=[]
            )
    
    def update_translations(self, org_id: int, request: TranslationUpdateRequest) -> TranslationUpdateResponse:
        """
        번역 데이터를 업데이트합니다.
        
        Args:
            org_id: 조직 ID
            request: 번역 업데이트 요청
            
        Returns:
            번역 업데이트 응답
        """
        try:
            updated_count = 0
            skipped_count = 0
            errors = []
            
            # 기존 번역 데이터 조회
            existing_translations = self._get_translations_from_source(
                org_id, request.language, request.namespace
            )
            
            for key, value in request.translations.items():
                try:
                    if key in existing_translations and not request.overwrite:
                        skipped_count += 1
                        continue
                    
                    # 번역 데이터 저장 (실제로는 DB에 저장)
                    self._save_translation(org_id, request.language, request.namespace, key, value)
                    updated_count += 1
                    
                except Exception as e:
                    errors.append(f"키 '{key}' 업데이트 실패: {str(e)}")
            
            # 캐시 무효화
            cache_key = f"i18n:{org_id}:{request.language}:{request.namespace}"
            self._invalidate_cache(cache_key)
            
            logger.info(f"📚 번역 데이터 업데이트 완료 - 조직: {org_id}, 업데이트: {updated_count}개")
            
            return TranslationUpdateResponse(
                updated_count=updated_count,
                skipped_count=skipped_count,
                errors=errors,
                success=len(errors) == 0
            )
            
        except Exception as e:
            logger.error(f"❌ 번역 데이터 업데이트 오류: {str(e)}")
            return TranslationUpdateResponse(
                updated_count=0,
                skipped_count=0,
                errors=[str(e)],
                success=False
            )
    
    def get_language_stats(self, org_id: int) -> LanguageStatsResponse:
        """
        언어 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            언어 통계 응답
        """
        try:
            # 조직의 지원 언어 조회
            org_settings = self._get_organization_language_settings(org_id)
            
            total_languages = len(org_settings.supported_languages)
            total_translations = 0
            completion_rates = {}
            
            # 각 언어별 완성도 계산
            base_translation_count = len(self.default_translations.get(SupportedLanguage.ENGLISH, {}).get(TranslationNamespace.COMMON, {}))
            
            for language in org_settings.supported_languages:
                language_translations = self._get_all_translations_for_language(org_id, language)
                total_translations += len(language_translations)
                
                if base_translation_count > 0:
                    completion_rates[language] = (len(language_translations) / base_translation_count) * 100
                else:
                    completion_rates[language] = 0.0
            
            return LanguageStatsResponse(
                total_languages=total_languages,
                total_translations=total_translations,
                completion_rates=completion_rates,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 언어 통계 조회 오류: {str(e)}")
            raise
    
    def get_i18n_config(self, org_id: int) -> I18nConfigResponse:
        """
        국제화 설정을 조회합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            국제화 설정 응답
        """
        try:
            org_settings = self._get_organization_language_settings(org_id)
            
            return I18nConfigResponse(
                organization_id=org_id,
                default_language=org_settings.default_language,
                supported_languages=org_settings.supported_languages,
                fallback_language=org_settings.fallback_language,
                auto_detect=org_settings.auto_detect,
                cache_enabled=True,
                cache_ttl=self.cache_ttl,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 국제화 설정 조회 오류: {str(e)}")
            raise
    
    def update_i18n_config(self, org_id: int, request: I18nConfigRequest) -> I18nConfigResponse:
        """
        국제화 설정을 업데이트합니다.
        
        Args:
            org_id: 조직 ID
            request: 국제화 설정 요청
            
        Returns:
            국제화 설정 응답
        """
        try:
            # 설정 업데이트 (실제로는 DB에 저장)
            self._save_organization_language_settings(org_id, request)
            
            # 캐시 TTL 업데이트
            if request.cache_ttl:
                self.cache_ttl = request.cache_ttl
            
            logger.info(f"📚 국제화 설정 업데이트 완료 - 조직: {org_id}")
            
            return self.get_i18n_config(org_id)
            
        except Exception as e:
            logger.error(f"❌ 국제화 설정 업데이트 오류: {str(e)}")
            raise
    
    # 내부 헬퍼 메서드들
    
    def _get_organization_language_settings(self, org_id: int) -> OrganizationLanguageSettings:
        """조직 언어 설정을 조회합니다."""
        # 실제로는 DB에서 조회, 여기서는 기본값 반환
        return OrganizationLanguageSettings(
            organization_id=org_id,
            default_language=SupportedLanguage.KOREAN,
            supported_languages=[SupportedLanguage.KOREAN, SupportedLanguage.ENGLISH],
            fallback_language=SupportedLanguage.ENGLISH,
            auto_detect=True,
            force_default=False
        )
    
    def _get_translations_from_source(self, org_id: int, language: SupportedLanguage, namespace: TranslationNamespace) -> Dict[str, str]:
        """소스에서 번역 데이터를 조회합니다."""
        # 기본 번역 데이터에서 조회
        return self.default_translations.get(language, {}).get(namespace, {})
    
    def _get_default_translation_response(self, language: SupportedLanguage, namespace: TranslationNamespace) -> TranslationResponse:
        """기본 번역 응답을 반환합니다."""
        translations = self.default_translations.get(SupportedLanguage.ENGLISH, {}).get(namespace, {})
        return TranslationResponse(
            language=SupportedLanguage.ENGLISH,
            namespace=namespace,
            translations=translations,
            fallback_used=True,
            cache_hit=False
        )
    
    def _save_translation(self, org_id: int, language: SupportedLanguage, namespace: TranslationNamespace, key: str, value: str):
        """번역 데이터를 저장합니다."""
        # 실제로는 DB에 저장
        pass
    
    def _save_organization_language_settings(self, org_id: int, request: I18nConfigRequest):
        """조직 언어 설정을 저장합니다."""
        # 실제로는 DB에 저장
        pass
    
    def _get_all_translations_for_language(self, org_id: int, language: SupportedLanguage) -> Dict[str, str]:
        """특정 언어의 모든 번역을 조회합니다."""
        all_translations = {}
        for namespace in TranslationNamespace:
            translations = self._get_translations_from_source(org_id, language, namespace)
            all_translations.update(translations)
        return all_translations
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, str]]:
        """캐시에서 데이터를 조회합니다."""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"⚠️ 캐시 조회 실패: {str(e)}")
        return None
    
    def _set_cache(self, key: str, data: Dict[str, str]):
        """캐시에 데이터를 저장합니다."""
        if self.redis_client:
            try:
                self.redis_client.setex(key, self.cache_ttl, json.dumps(data))
            except Exception as e:
                logger.warning(f"⚠️ 캐시 저장 실패: {str(e)}")
    
    def _invalidate_cache(self, key: str):
        """캐시를 무효화합니다."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"⚠️ 캐시 무효화 실패: {str(e)}")