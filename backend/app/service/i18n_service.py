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
from fastapi import HTTPException, status

from ..schemas.i18n_schema import (
    SupportedLanguage, TranslationNamespace, TranslationRequest, TranslationResponse,
    BulkTranslationRequest, BulkTranslationResponse, LanguageDetectionRequest,
    LanguageDetectionResponse, TranslationUpdateRequest, TranslationUpdateResponse,
    LanguageStatsResponse, I18nConfigRequest, I18nConfigResponse, LanguageListResponse,
    OrganizationLanguageSettings, UserLanguagePreference,
    TranslationExportRequest, TranslationExportResponse, TranslationImportRequest, TranslationImportResponse,
    LanguageConfigRequest, LanguageConfigResponse, TranslationBulkRequest, TranslationStatsResponse
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

    async def get_supported_languages(self, org_id: Any) -> LanguageListResponse:
        """
        조직에서 지원하는 언어 목록을 조회합니다.

        Args:
            org_id: 조직 ID

        Returns:
            LanguageListResponse: 지원 언어 목록과 카운트 정보
        """
        try:
            org_settings = self._get_organization_language_settings(org_id)

            # 코드 -> 표시 이름 매핑
            language_names = {
                SupportedLanguage.KOREAN.value: "Korean",
                SupportedLanguage.ENGLISH.value: "English",
                SupportedLanguage.JAPANESE.value: "Japanese",
                SupportedLanguage.CHINESE_SIMPLIFIED.value: "Chinese (Simplified)",
                SupportedLanguage.CHINESE_TRADITIONAL.value: "Chinese (Traditional)",
                SupportedLanguage.SPANISH.value: "Spanish",
                SupportedLanguage.FRENCH.value: "French",
                SupportedLanguage.GERMAN.value: "German",
                SupportedLanguage.RUSSIAN.value: "Russian",
                SupportedLanguage.PORTUGUESE.value: "Portuguese",
            }

            languages: List[Dict[str, str]] = []
            for lang in org_settings.supported_languages:
                code = lang.value
                languages.append({
                    "code": code,
                    "name": language_names.get(code, code)
                })

            total_count = len(languages)
            supported_count = len(org_settings.supported_languages)

            logger.info(f"🌐 지원 언어 조회 - 조직: {org_id}, 총 {total_count}개")
            return LanguageListResponse(
                languages=languages,
                total_count=total_count,
                supported_count=supported_count,
            )
        except Exception as e:
            logger.error(f"❌ 지원 언어 조회 오류: {str(e)}")
            return LanguageListResponse(languages=[], total_count=0, supported_count=0)
    
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

    def export_translations(self, org_id: int, request: TranslationExportRequest) -> TranslationExportResponse:
        """
        번역 데이터를 파일로 내보냅니다.

        Args:
            org_id: 조직 ID
            request: 번역 내보내기 요청

        Returns:
            번역 내보내기 응답
        """
        try:
            # 기본 대상 언어/네임스페이스 결정
            org_settings = self._get_organization_language_settings(org_id)
            target_languages = request.languages or org_settings.supported_languages
            target_namespaces = request.namespaces or list(TranslationNamespace)

            # 번역 데이터 수집
            export_payload: Dict[str, Dict[str, Dict[str, str]]] = {}
            for language in target_languages:
                export_payload[language] = {}
                for namespace in target_namespaces:
                    resp = self.get_translations(org_id, TranslationRequest(language=language, namespace=namespace))
                    export_payload[language][namespace] = resp.translations

            # 저장 경로 구성
            from pathlib import Path
            base_dir = Path(os.getcwd()) / "backend" / "backups" / "i18n_exports"
            base_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = "json" if request.format.lower() == "json" else "json"  # 현재 json만 지원
            file_name = f"i18n_export_org{org_id}_{timestamp}.{file_ext}"
            file_path = base_dir / file_name

            # 파일로 저장 (JSON)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "organization_id": org_id,
                    "format": "json",
                    "languages": [lang for lang in target_languages],
                    "namespaces": [ns for ns in target_namespaces],
                    "translations": export_payload,
                    "generated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(file_path)
            expires_at = datetime.now() + timedelta(hours=12)

            logger.info(f"📤 번역 데이터 내보내기 완료 - 조직: {org_id}, 파일: {file_path}")

            return TranslationExportResponse(
                download_url=str(file_path),
                file_size=file_size,
                format="json",
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"❌ 번역 데이터 내보내기 오류 - 조직: {org_id}, 오류: {str(e)}")
            # 실패 시 빈 파일 정보를 반환하거나 예외를 던질 수 있음. 여기서는 예외를 재던짐.
            raise

    def import_translations(self, org_id: int, request: TranslationImportRequest, user_id: int) -> TranslationImportResponse:
        """
        번역 데이터를 파일에서 가져와 적용합니다.

        Args:
            org_id: 조직 ID
            request: 번역 가져오기 요청
            user_id: 수행 사용자 ID

        Returns:
            번역 가져오기 응답
        """
        try:
            imported_count = 0
            skipped_count = 0
            error_count = 0
            errors: List[str] = []

            # 현재는 JSON만 지원
            if request.format.lower() != "json":
                errors.append("현재는 JSON 형식만 지원합니다.")
                error_count += 1
                return TranslationImportResponse(
                    imported_count=imported_count,
                    skipped_count=skipped_count,
                    error_count=error_count,
                    errors=errors,
                    success=False
                )

            # 파일 로드
            try:
                with open(request.file_url, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as read_err:
                logger.error(f"❌ 번역 파일 로드 실패: {str(read_err)}")
                raise

            translations = data.get("translations", {})
            # 예상 구조: translations[language][namespace][key] = value
            for language_str, ns_map in translations.items():
                # 언어/네임스페이스 파싱 안전 처리
                try:
                    language = SupportedLanguage(language_str)
                except Exception:
                    errors.append(f"지원하지 않는 언어: {language_str}")
                    error_count += 1
                    continue

                for namespace_str, kv_map in ns_map.items():
                    try:
                        namespace = TranslationNamespace(namespace_str)
                    except Exception:
                        errors.append(f"지원하지 않는 네임스페이스: {namespace_str}")
                        error_count += 1
                        continue

                    # 기존 번역 조회 (overwrite 판단용)
                    existing = self._get_translations_from_source(org_id, language, namespace)

                    for key, value in kv_map.items():
                        try:
                            if key in existing and not request.overwrite:
                                skipped_count += 1
                                continue

                            if not request.validate_only:
                                self._save_translation(org_id, language, namespace, key, value)
                            imported_count += 1
                        except Exception as e:
                            errors.append(f"키 '{key}' 가져오기 실패: {str(e)}")
                            error_count += 1

                    # 캐시 무효화
                    cache_key = f"i18n:{org_id}:{language}:{namespace}"
                    self._invalidate_cache(cache_key)

            logger.info(f"📥 번역 데이터 가져오기 완료 - 조직: {org_id}, 사용자: {user_id}, 적용: {imported_count}개")

            return TranslationImportResponse(
                imported_count=imported_count,
                skipped_count=skipped_count,
                error_count=error_count,
                errors=errors,
                success=error_count == 0
            )
        except Exception as e:
            logger.error(f"❌ 번역 데이터 가져오기 오류 - 조직: {org_id}, 오류: {str(e)}")
            return TranslationImportResponse(
                imported_count=0,
                skipped_count=0,
                error_count=1,
                errors=[str(e)],
                success=False
            )

    def get_missing_translations(
        self,
        org_id: int,
        language_code: Optional[str] = None,
        namespace: Optional[TranslationNamespace] = None,
    ) -> Dict[str, Any]:
        """
        누락된 번역 키를 조회합니다.

        Args:
            org_id: 조직 ID
            language_code: 특정 언어 코드 (없으면 조직 지원 언어 전체)
            namespace: 네임스페이스 필터 (없으면 전체 네임스페이스)

        Returns:
            누락된 번역 정보 딕셔너리
        """
        try:
            org_settings = self._get_organization_language_settings(org_id)
            target_languages: List[SupportedLanguage]
            if language_code:
                try:
                    target_languages = [SupportedLanguage(language_code)]
                except Exception:
                    logger.warning(f"⚠️ 지원하지 않는 언어 코드 요청: {language_code}")
                    target_languages = []
            else:
                target_languages = org_settings.supported_languages

            target_namespaces = [namespace] if namespace else list(TranslationNamespace)

            results = []
            total_missing = 0
            # 기준: 영어 기본 번역을 베이스로 누락 비교
            for language in target_languages:
                for ns in target_namespaces:
                    base_keys = set(self.default_translations.get(SupportedLanguage.ENGLISH, {}).get(ns, {}).keys())
                    lang_keys = set(self._get_translations_from_source(org_id, language, ns).keys())
                    missing_keys = sorted(list(base_keys - lang_keys))
                    count = len(missing_keys)
                    total_missing += count
                    results.append({
                        "language": language,
                        "namespace": ns,
                        "missing_keys": missing_keys,
                        "total_missing": count,
                    })

            logger.info(f"🔎 누락된 번역 조회 - 조직: {org_id}, 총 누락: {total_missing}")
            return {
                "items": results,
                "total_missing": total_missing,
            }
        except Exception as e:
            logger.error(f"❌ 누락 번역 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            return {"items": [], "total_missing": 0, "error": str(e)}

    def validate_translations(
        self,
        org_id: int,
        language_code: str,
        namespace: Optional[TranslationNamespace] = None,
    ) -> Dict[str, Any]:
        """
        번역 데이터의 유효성을 검증합니다.

        Args:
            org_id: 조직 ID
            language_code: 검증할 언어 코드
            namespace: 네임스페이스 필터 (없으면 전체 네임스페이스)

        Returns:
            검증 결과 딕셔너리
        """
        try:
            try:
                language = SupportedLanguage(language_code)
            except Exception:
                return {"validation_errors": [{"field": "language", "error": f"지원하지 않는 언어: {language_code}"}], "suggestions": []}

            namespaces = [namespace] if namespace else list(TranslationNamespace)
            validation_errors: List[Dict[str, Any]] = []
            suggestions: List[Dict[str, Any]] = []

            for ns in namespaces:
                translations = self._get_translations_from_source(org_id, language, ns)
                for key, value in translations.items():
                    if not key or not key.strip():
                        validation_errors.append({"namespace": ns, "key": key, "error": "빈 키는 허용되지 않습니다."})
                    if not isinstance(value, str):
                        validation_errors.append({"namespace": ns, "key": key, "error": "값은 문자열이어야 합니다."})
                    elif value.strip() == "":
                        suggestions.append({"namespace": ns, "key": key, "suggestion": "빈 문자열 대신 의미 있는 번역을 제공하세요."})

                # 추천: 영어 기준으로 누락된 키에 대한 제안
                base_keys = set(self.default_translations.get(SupportedLanguage.ENGLISH, {}).get(ns, {}).keys())
                lang_keys = set(translations.keys())
                missing = base_keys - lang_keys
                for m in missing:
                    suggestions.append({"namespace": ns, "key": m, "suggestion": "영어 기준으로 누락된 키입니다. 번역을 추가하세요."})

            logger.info(f"✅ 번역 검증 완료 - 조직: {org_id}, 언어: {language}")
            return {
                "validation_errors": validation_errors,
                "suggestions": suggestions,
            }
        except Exception as e:
            logger.error(f"❌ 번역 검증 오류 - 조직: {org_id}, 오류: {str(e)}")
            return {"validation_errors": [{"error": str(e)}], "suggestions": []}

    def detect_browser_language(self, org_id: int, accept_language: str) -> LanguageDetectionResponse:
        """
        브라우저의 Accept-Language 헤더를 기반으로 언어를 감지합니다.

        Args:
            org_id: 조직 ID
            accept_language: 헤더 값

        Returns:
            LanguageDetectionResponse
        """
        try:
            org_settings = self._get_organization_language_settings(org_id)
            # 헤더 파싱: "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
            parts = [p.strip() for p in accept_language.split(',') if p.strip()]
            candidates: List[Dict[str, Any]] = []
            for p in parts:
                if ';q=' in p:
                    code, q = p.split(';q=')
                    try:
                        weight = float(q)
                    except Exception:
                        weight = 0.5
                else:
                    code = p
                    weight = 1.0
                code_norm = code.split('-')[0].lower()
                candidates.append({"code": code_norm, "confidence": weight})

            # 매핑 함수
            def map_code(c: str) -> Optional[SupportedLanguage]:
                mapping = {
                    "ko": SupportedLanguage.KOREAN,
                    "en": SupportedLanguage.ENGLISH,
                    "ja": SupportedLanguage.JAPANESE,
                    "zh": SupportedLanguage.CHINESE_SIMPLIFIED,
                    "es": SupportedLanguage.SPANISH,
                    "fr": SupportedLanguage.FRENCH,
                    "de": SupportedLanguage.GERMAN,
                    "ru": SupportedLanguage.RUSSIAN,
                    "pt": SupportedLanguage.PORTUGUESE,
                }
                return mapping.get(c)

            # 지원 언어와 교집합 찾기
            supported_set = set(org_settings.supported_languages)
            for cand in candidates:
                lang = map_code(cand["code"])
                if lang and lang in supported_set:
                    return LanguageDetectionResponse(
                        detected_language=lang,
                        confidence=min(1.0, max(0.0, cand["confidence"])),
                        alternatives=[{"language": alt, "confidence": 0.5} for alt in org_settings.supported_languages if alt != lang]
                    )

            # 매칭 없으면 폴백
            return LanguageDetectionResponse(
                detected_language=org_settings.fallback_language,
                confidence=0.3,
                alternatives=[{"language": alt, "confidence": 0.5} for alt in org_settings.supported_languages]
            )
        except Exception as e:
            logger.error(f"❌ 브라우저 언어 감지 오류 - 조직: {org_id}, 오류: {str(e)}")
            # 오류 시 폴백 반환
            org_settings = self._get_organization_language_settings(org_id)
            return LanguageDetectionResponse(
                detected_language=org_settings.fallback_language,
                confidence=0.2,
                alternatives=[{"language": alt, "confidence": 0.5} for alt in org_settings.supported_languages]
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

    def get_translation_statistics(self, org_id: int) -> TranslationStatsResponse:
        """번역 통계를 조회합니다.

        Args:
            org_id: 조직 ID

        Returns:
            TranslationStatsResponse: 번역 통계
        """
        try:
            org_settings = self._get_organization_language_settings(org_id)

            # 기준 키 집합: 영어 전체 네임스페이스 합산
            base_keys_by_ns: Dict[TranslationNamespace, int] = {}
            total_base_keys = 0
            for ns in TranslationNamespace:
                count = len(self.default_translations.get(SupportedLanguage.ENGLISH, {}).get(ns, {}))
                base_keys_by_ns[ns] = count
                total_base_keys += count

            languages_stats: Dict[str, Dict[str, Any]] = {}
            namespaces_stats: Dict[str, Dict[str, Any]] = {}

            completed_total = 0
            missing_total = 0

            # 네임스페이스별 통계 초기화
            for ns, base_count in base_keys_by_ns.items():
                namespaces_stats[ns.value] = {
                    "total_keys": base_count,
                    "translated_keys": 0,
                    "missing_keys": 0,
                    "completion_rate": 0.0,
                }

            # 언어별 집계
            for lang in org_settings.supported_languages:
                translated_lang_total = 0
                for ns in TranslationNamespace:
                    translated_ns = len(self._get_translations_from_source(org_id, lang, ns))
                    base_count = base_keys_by_ns.get(ns, 0)
                    translated_lang_total += translated_ns

                    # 네임스페이스 단위 누적(언어 합산 방식)
                    ns_entry = namespaces_stats[ns.value]
                    ns_entry["translated_keys"] += translated_ns
                    ns_entry["missing_keys"] += max(0, base_count - translated_ns)
                # 언어별 통계
                missing_for_lang = max(0, total_base_keys - translated_lang_total)
                completion_rate = (translated_lang_total / total_base_keys * 100.0) if total_base_keys else 0.0
                languages_stats[lang.value] = {
                    "total_keys": total_base_keys,
                    "translated_keys": translated_lang_total,
                    "missing_keys": missing_for_lang,
                    "completion_rate": completion_rate,
                }
                completed_total += translated_lang_total
                missing_total += missing_for_lang

            # 네임스페이스별 완성도 계산 (언어 합산 대비 기준 언어 수로 나누어 평균)
            num_langs = max(1, len(org_settings.supported_languages))
            for ns, base_count in base_keys_by_ns.items():
                ns_entry = namespaces_stats[ns.value]
                # 평균 번역 키 수 계산
                avg_translated = ns_entry["translated_keys"] / num_langs
                ns_entry["completion_rate"] = (avg_translated / base_count * 100.0) if base_count else 0.0

            total_possible = completed_total + missing_total
            overall_rate = (completed_total / total_possible * 100.0) if total_possible else 0.0

            return TranslationStatsResponse(
                total_translations=completed_total,
                completed_translations=completed_total,
                missing_translations=missing_total,
                completion_rate=overall_rate,
                languages=languages_stats,
                namespaces=namespaces_stats,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"❌ 번역 통계 조회 오류: {str(e)}")
            # 안전한 기본값 반환
            return TranslationStatsResponse(
                total_translations=0,
                completed_translations=0,
                missing_translations=0,
                completion_rate=0.0,
                languages={},
                namespaces={},
                last_updated=datetime.now(),
            )
    
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
    
    def _get_organization_language_settings(self, org_id: Any) -> OrganizationLanguageSettings:
        """조직 언어 설정을 조회합니다.
        org_id가 문자열(UUID)인 경우에도 안전하게 처리합니다.
        """
        # organization_id는 스키마에서 int로 정의되어 있으므로 숫자로 변환 시도
        try:
            org_numeric_id = int(org_id) if isinstance(org_id, (str, bytes)) else int(org_id)
        except Exception:
            # 변환 실패 시 0으로 설정 (플레이스홀더)
            org_numeric_id = 0

        # 실제로는 DB에서 조회, 여기서는 기본값 반환
        return OrganizationLanguageSettings(
            organization_id=org_numeric_id,
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

    def clear_translation_cache(self, org_id: int, language_code: Optional[str] = None) -> Dict[str, Any]:
        """번역 캐시를 초기화합니다.

        Args:
            org_id: 조직 ID
            language_code: 특정 언어 코드만 초기화 (선택)

        Returns:
            초기화 결과 딕셔너리
        """
        cleared = 0
        pattern = f"i18n:{org_id}:*" if not language_code else f"i18n:{org_id}:{language_code}:*"
        try:
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        cleared = len(keys)
                except Exception as e:
                    logger.warning(f"⚠️ 캐시 키 삭제 실패: {str(e)}")

            # 메모리 캐시 초기화
            if language_code:
                # 특정 언어 관련 키 제거
                keys_to_delete = [k for k in list(self.translation_cache.keys()) if k.startswith(f"i18n:{org_id}:{language_code}:")]
                for k in keys_to_delete:
                    self.translation_cache.pop(k, None)
            else:
                # 조직 관련 전체 제거
                keys_to_delete = [k for k in list(self.translation_cache.keys()) if k.startswith(f"i18n:{org_id}:")]
                for k in keys_to_delete:
                    self.translation_cache.pop(k, None)

            logger.info(f"🧹 번역 캐시 초기화 - 조직: {org_id}, 패턴: {pattern}, 삭제: {cleared}개")
            return {
                "success": True,
                "cleared_items": cleared,
                "pattern": pattern,
                "cleared_at": datetime.now(),
            }
        except Exception as e:
            logger.error(f"❌ 번역 캐시 초기화 오류 - 조직: {org_id}, 오류: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="번역 캐시 초기화 중 오류가 발생했습니다.")

    def get_organization_language_config(self, org_id: int) -> LanguageConfigResponse:
        """조직 언어 설정을 조회합니다."""
        settings = self._get_organization_language_settings(org_id)
        return LanguageConfigResponse(
            organization_id=settings.organization_id,
            default_language=settings.default_language,
            supported_languages=settings.supported_languages,
            fallback_language=settings.fallback_language,
            auto_detect=settings.auto_detect,
            updated_at=datetime.now(),
        )

    def update_organization_language_config(self, org_id: int, request: LanguageConfigRequest, user_id: int) -> LanguageConfigResponse:
        """조직 언어 설정을 업데이트합니다."""
        try:
            # LanguageConfigRequest를 I18nConfigRequest로 매핑 후 저장
            i18n_req = I18nConfigRequest(
                default_language=request.default_language,
                supported_languages=request.supported_languages,
                fallback_language=request.fallback_language or SupportedLanguage.ENGLISH,
                auto_detect=request.auto_detect,
                cache_enabled=True,
                cache_ttl=self.cache_ttl,
            )
            self._save_organization_language_settings(org_id, i18n_req)
            return self.get_organization_language_config(org_id)
        except Exception as e:
            logger.error(f"❌ 조직 언어 설정 업데이트 오류 - 조직: {org_id}, 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="조직 언어 설정 업데이트 중 오류가 발생했습니다.")

    def get_user_language_preference(self, user_id: int, org_id: int) -> UserLanguagePreference:
        """사용자 언어 선호도를 조회합니다. (단순 Redis/기본값 기반)"""
        try:
            if self.redis_client:
                key = f"i18n:user_pref:{org_id}:{user_id}"
                data = self.redis_client.get(key)
                if data:
                    obj = json.loads(data)
                    return UserLanguagePreference(**obj)

            # 기본값: 조직 기본 언어 사용
            org_settings = self._get_organization_language_settings(org_id)
            return UserLanguagePreference(
                user_id=user_id,
                preferred_language=org_settings.default_language,
                timezone=None,
                date_format=None,
                time_format=None,
            )
        except Exception as e:
            logger.error(f"❌ 사용자 언어 선호도 조회 오류 - 사용자: {user_id}, 조직: {org_id}, 오류: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="사용자 언어 선호도 조회 중 오류가 발생했습니다.")

    def update_user_language_preference(self, user_id: int, org_id: int, preference: UserLanguagePreference) -> UserLanguagePreference:
        """사용자 언어 선호도를 업데이트합니다. (단순 Redis 저장)"""
        try:
            obj = preference.dict()
            obj["user_id"] = user_id  # 보정
            if self.redis_client:
                key = f"i18n:user_pref:{org_id}:{user_id}"
                self.redis_client.setex(key, self.cache_ttl, json.dumps(obj))
            return UserLanguagePreference(**obj)
        except Exception as e:
            logger.error(f"❌ 사용자 언어 선호도 업데이트 오류 - 사용자: {user_id}, 조직: {org_id}, 오류: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="사용자 언어 선호도 업데이트 중 오류가 발생했습니다.")

    def bulk_update_translations(self, org_id: int, bulk_request: TranslationBulkRequest, user_id: int) -> Dict[str, Any]:
        """대량 번역 업데이트를 수행합니다. (단일 언어/네임스페이스 기준)"""
        try:
            update_req = TranslationUpdateRequest(
                language=bulk_request.language,
                namespace=bulk_request.namespace,
                translations=bulk_request.translations,
                overwrite=bulk_request.overwrite,
            )
            result = self.update_translations(org_id, update_req)
            return {
                "success": result.success,
                "updated_count": result.updated_count,
                "skipped_count": result.skipped_count,
                "errors": result.errors,
            }
        except Exception as e:
            logger.error(f"❌ 대량 번역 업데이트 오류 - 조직: {org_id}, 사용자: {user_id}, 오류: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="대량 번역 업데이트 중 오류가 발생했습니다.")