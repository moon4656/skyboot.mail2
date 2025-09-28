"""
디버그 라우터 (임시)

조직 컨텍스트 디버깅을 위한 임시 엔드포인트
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..service.auth_service import get_current_user
from ..model import User
from ..middleware.tenant_middleware import (
    get_current_org, 
    get_current_org_id_from_context, 
    current_org_context,
    current_user_context
)

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "디버그 정보를 찾을 수 없습니다"}}
)


@router.get(
    "/context",
    summary="컨텍스트 디버그 정보",
    description="현재 요청의 컨텍스트 정보를 디버깅합니다."
)
async def get_context_debug_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    컨텍스트 디버그 정보 조회
    
    현재 요청의 조직 및 사용자 컨텍스트 정보를 반환합니다.
    """
    try:
        logger.info(f"🔍 컨텍스트 디버그 정보 조회 - 사용자: {current_user.email}")
        
        # 1. ContextVar에서 조직 정보 가져오기
        org_context = current_org_context.get()
        user_context = current_user_context.get()
        
        # 2. 헬퍼 함수들로 정보 가져오기
        current_org = get_current_org()
        current_org_id = get_current_org_id_from_context()
        
        # 3. request.state에서 정보 가져오기
        request_state_info = {}
        if hasattr(request.state, 'org_id'):
            request_state_info['org_id'] = request.state.org_id
        if hasattr(request.state, 'org_code'):
            request_state_info['org_code'] = request.state.org_code
        if hasattr(request.state, 'org_info'):
            request_state_info['org_info'] = request.state.org_info
        if hasattr(request.state, 'user_info'):
            request_state_info['user_info'] = request.state.user_info
        
        # 4. 헤더 정보
        headers_info = {
            'host': request.headers.get('host'),
            'x-org-id': request.headers.get('x-org-id'),
            'x-org-code': request.headers.get('x-org-code'),
            'authorization': 'Bearer ***' if request.headers.get('authorization') else None
        }
        
        # 5. 쿼리 파라미터
        query_params = dict(request.query_params)
        
        debug_info = {
            "timestamp": str(logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="debug", level=logging.INFO, pathname="", lineno=0,
                msg="", args=(), exc_info=None
            )) if logger.handlers else "N/A"),
            "current_user": {
                "email": current_user.email,
                "user_uuid": current_user.user_uuid,
                "org_id": current_user.org_id,
                "role": current_user.role,
                "is_active": current_user.is_active
            },
            "context_vars": {
                "org_context": org_context,
                "user_context": user_context,
                "current_org_from_helper": current_org,
                "current_org_id_from_helper": current_org_id
            },
            "request_state": request_state_info,
            "headers": headers_info,
            "query_params": query_params,
            "url": {
                "path": request.url.path,
                "query": request.url.query,
                "scheme": request.url.scheme,
                "hostname": request.url.hostname,
                "port": request.url.port
            }
        }
        
        logger.info(f"✅ 컨텍스트 디버그 정보 조회 완료")
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ 컨텍스트 디버그 정보 조회 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"컨텍스트 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )