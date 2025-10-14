"""
모니터링 라우터
- 조직별 사용량 통계 API
- 조직별 감사 로그 API  
- 조직별 대시보드 API
"""

import logging
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database.user import get_db
from ..model.user_model import User
from ..model.organization_model import Organization
from ..service.monitoring_service import MonitoringService
from ..service.auth_service import get_current_user, get_current_admin_user
from ..schemas.monitoring_schema import (
    UsageRequest, UsageResponse,
    AuditRequest, AuditResponse, AuditActionType,
    DashboardRequest, DashboardResponse
)
from ..schemas.user_schema import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}}
)


@router.get("/usage", response_model=UsageResponse, summary="사용량 통계 조회")
async def get_usage_statistics(
    request: UsageRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    조직별 사용량 통계를 조회합니다.
    
    **주요 기능:**
    - 현재 사용량 (메일 발송량, 저장 공간, 활성 사용자 수)
    - 제한 대비 사용률 계산
    - 일일/주간/월간 사용량 트렌드
    - API 요청 통계
    
    **권한:**
    - 조직 관리자 또는 사용자 (자신의 조직 데이터만 조회 가능)
    
    **응답 데이터:**
    - current_usage: 현재 사용량
    - limits: 조직 제한 설정
    - usage_percentages: 사용률 (%)
    - daily_stats: 일일 통계 (선택적)
    - weekly_stats: 주간 통계 (선택적)
    - monthly_stats: 월간 통계 (선택적)
    """
    try:
        logger.info(f"📊 사용량 통계 API 호출 - 조직: {current_user.org_id}, 사용자: {current_user.email}")
        
        # 모니터링 서비스 초기화
        monitoring_service = MonitoringService(db)
        
        # 사용량 통계 조회
        usage_stats = monitoring_service.get_usage_statistics(
            org_id=current_user.org_id,
            request=request
        )
        
        logger.info(f"✅ 사용량 통계 조회 완료 - 조직: {current_user.org_id}")
        return usage_stats
        
    except ValueError as e:
        logger.error(f"❌ 사용량 통계 조회 실패 - 조직: {current_user.org_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 요청입니다: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ 사용량 통계 조회 오류 - 조직: {current_user.org_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용량 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/audit",
           response_model=AuditResponse,
           summary="조직별 감사 로그 조회",
           description="조직의 사용자 활동, 메일 처리, 시스템 접근 등의 감사 로그를 조회합니다.")
async def get_audit_logs(
    start_date: Optional[datetime] = Query(None, description="시작 날짜시간"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜시간"),
    action: Optional[AuditActionType] = Query(None, description="필터링할 액션 타입"),
    user_id: Optional[str] = Query(None, description="필터링할 사용자 ID"),
    resource_type: Optional[str] = Query(None, description="필터링할 리소스 타입"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=1000, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    조직별 감사 로그를 조회합니다.
    
    **주요 기능:**
    - 사용자 활동 로그 (로그인, 로그아웃, 설정 변경)
    - 메일 처리 로그 (발송, 수신, 삭제, 이동)
    - 시스템 접근 로그 (API 호출, 파일 접근)
    - 보안 이벤트 로그 (실패한 로그인, 권한 오류)
    
    **필터링 옵션:**
    - 날짜 범위
    - 액션 타입 (LOGIN, LOGOUT, SEND_EMAIL, DELETE_EMAIL 등)
    - 특정 사용자
    - 리소스 타입
    
    **권한:**
    - 조직 관리자만 조회 가능
    
    **응답 데이터:**
    - logs: 감사 로그 목록
    - total: 전체 로그 수
    - page, limit: 페이징 정보
    - filters: 적용된 필터
    """
    try:
        logger.info(f"📋 감사 로그 API 호출 - 조직: {current_user.org_id}, 사용자: {current_user.email}")
        
        # 관리자 권한 확인 (조직 관리자 또는 시스템 관리자)
        if current_user.role not in ["admin", "org_admin"]:
            logger.warning(f"⚠️ 감사 로그 접근 권한 없음 - 사용자: {current_user.email}, 역할: {current_user.role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="감사 로그 조회 권한이 없습니다. 관리자만 접근 가능합니다."
            )
        
        # 요청 객체 생성
        audit_request = AuditRequest(
            start_date=start_date,
            end_date=end_date,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            page=page,
            limit=limit
        )
        
        # 모니터링 서비스 초기화
        monitoring_service = MonitoringService(db)
        
        # 감사 로그 조회
        audit_logs = monitoring_service.get_audit_logs(
            org_id=current_user.org_id,
            request=audit_request
        )
        
        logger.info(f"✅ 감사 로그 조회 완료 - 조직: {current_user.org_id}, 총 {audit_logs.total}개")
        return audit_logs
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"❌ 감사 로그 조회 실패 - 조직: {current_user.org_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 요청입니다: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ 감사 로그 조회 오류 - 조직: {current_user.org_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="감사 로그 조회 중 오류가 발생했습니다."
        )


@router.get("/dashboard", response_model=DashboardResponse, summary="대시보드 데이터 조회")
async def get_dashboard_data(
    request: DashboardRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    조직의 대시보드 데이터를 조회합니다.
    
    - **refresh_cache**: 캐시 새로고침 여부
    - **include_alerts**: 알림 포함 여부
    """
    logger.info(f"📊 대시보드 데이터 조회 - 조직: {current_user.org_id}, 사용자: {current_user.email}")
    
    try:
        monitoring_service = MonitoringService(db)
        dashboard_data = monitoring_service.get_dashboard_data(current_user.org_id, request)
        
        logger.info(f"✅ 대시보드 데이터 조회 성공 - 조직: {current_user.org_id}")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ 대시보드 데이터 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대시보드 데이터 조회 중 오류가 발생했습니다."
        )


@router.get("/health",
           response_model=MessageResponse,
           summary="모니터링 시스템 상태 확인",
           description="모니터링 시스템의 기본 상태를 확인합니다.")
async def health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    모니터링 시스템의 상태를 확인합니다.
    
    **확인 항목:**
    - 데이터베이스 연결 상태
    - Redis 연결 상태 (선택적)
    - 기본 쿼리 실행 가능 여부
    - 서비스 초기화 상태
    
    **권한:**
    - 모든 인증된 사용자
    
    **응답:**
    - 성공 시: "모니터링 시스템이 정상 작동 중입니다."
    - 실패 시: 구체적인 오류 메시지
    """
    try:
        logger.info(f"🔍 모니터링 시스템 상태 확인 - 조직: {current_user.org_id}, 사용자: {current_user.email}")
        
        # 모니터링 서비스 초기화 테스트
        monitoring_service = MonitoringService(db)
        
        # 기본 데이터베이스 쿼리 테스트
        org_count = db.query(Organization).filter(Organization.org_id == current_user.org_id).count()
        if org_count == 0:
            raise ValueError("조직 정보를 찾을 수 없습니다.")
        
        # Redis 연결 테스트 (선택적)
        redis_status = "연결됨" if monitoring_service.redis_client else "연결 안됨"
        
        logger.info(f"✅ 모니터링 시스템 상태 확인 완료 - 조직: {current_user.org_id}, Redis: {redis_status}")
        
        return MessageResponse(
            message=f"모니터링 시스템이 정상 작동 중입니다. (Redis: {redis_status})"
        )
        
    except Exception as e:
        logger.error(f"❌ 모니터링 시스템 상태 확인 오류 - 조직: {current_user.org_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모니터링 시스템 상태 확인 중 오류가 발생했습니다: {str(e)}"
        )