"""
호환(Compatibility) 라우터

기존 클라이언트가 사용하는 경로를 보존하기 위한 호환용 엔드포인트를 제공합니다.
현재는 사용자 언어 설정(i18n) 경로의 하위 호환을 제공합니다.
"""

from fastapi import APIRouter, Depends
import zlib
from sqlalchemy.orm import Session

from app.service.i18n_service import I18nService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_org_id
from app.schemas.i18n_schema import UserLanguagePreference, UserLanguageRequest
from app.model.user_model import User
from app.database.user import get_db

router = APIRouter()


def _to_numeric_user_id(user_id: str) -> int:
    """문자형 사용자 ID를 안정적인 정수로 매핑합니다."""
    try:
        return int(user_id)
    except Exception:
        return zlib.crc32(user_id.encode("utf-8")) & 0xFFFFFFFF


@router.get("/user/preference", summary="사용자 언어 설정 조회 (호환)")
async def get_user_language_preference_compat(
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> UserLanguagePreference:
    """사용자의 언어 설정을 조회합니다. (하위 호환용 경로)

    - 기존 경로: `/api/v1/user/preference`
    - 신규 권장 경로: `/api/v1/i18n/user/preference`
    """
    service = I18nService(db)
    numeric_user_id = _to_numeric_user_id(current_user.user_id)
    return service.get_user_language_preference(numeric_user_id, org_id)


@router.put("/user/preference", summary="사용자 언어 설정 업데이트 (호환)")
async def update_user_language_preference_compat(
    request: UserLanguageRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> UserLanguagePreference:
    """사용자의 언어 설정을 업데이트합니다. (하위 호환용 경로)

    - 기존 경로: `/api/v1/user/preference`
    - 신규 권장 경로: `/api/v1/i18n/user/preference`
    """
    service = I18nService(db)
    numeric_user_id = _to_numeric_user_id(current_user.user_id)
    preference = UserLanguagePreference(
        user_id=numeric_user_id,
        preferred_language=request.preferred_language,
        timezone=request.timezone,
        date_format=request.date_format,
        time_format=request.time_format,
    )
    return service.update_user_language_preference(numeric_user_id, org_id, preference)