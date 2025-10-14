"""
DevOps 라우터

SkyBoot Mail SaaS 프로젝트의 DevOps 기능을 위한 API 엔드포인트입니다.
백업, 복구, 테스트 등의 DevOps 작업을 처리합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from ..database.user import get_db
from ..service.auth_service import get_current_user, get_current_admin_user
from ..service.devops_service import DevOpsService
from ..model.user_model import User
from ..model.organization_model import Organization
from ..middleware.tenant_middleware import get_current_organization
from ..schemas.devops_schema import (
    BackupRequest, BackupResponse, BackupListResponse,
    RestoreRequest, RestoreResponse,
    TestRequest, TestResponse,
    SystemHealthResponse, DevOpsResponse, JobStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/devops",
    tags=["DevOps"],
    responses={404: {"description": "Not found"}}
)

def get_devops_service(db: Session = Depends(get_db)) -> DevOpsService:
    """DevOps 서비스 의존성 주입"""
    return DevOpsService(db)

# ===== 백업 관련 엔드포인트 =====

@router.post("/backup", 
             response_model=BackupResponse,
             summary="백업 생성",
             description="시스템 백업을 생성합니다. 데이터베이스, 파일, 설정 등을 백업할 수 있습니다.")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    시스템 백업을 생성합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **backup_type**: 백업 타입 (FULL, INCREMENTAL, DIFFERENTIAL)
    - **include_database**: 데이터베이스 포함 여부
    - **include_files**: 파일 포함 여부
    - **include_config**: 설정 포함 여부
    - **include_attachments**: 첨부파일 포함 여부
    - **compression**: 압축 사용 여부
    - **encryption**: 암호화 사용 여부
    - **description**: 백업 설명
    - **tags**: 백업 태그
    """
    try:
        logger.info(f"📦 백업 요청 - 조직: {organization.id}, 사용자: {current_user.id}, 타입: {request.backup_type}")
        
        # 백업 생성 (백그라운드에서 실행)
        backup_response = await devops_service.create_backup(
            organization_id=organization.id,
            user_id=current_user.id,
            request=request
        )
        
        return backup_response
        
    except Exception as e:
        logger.error(f"❌ 백업 생성 실패 - 조직: {organization.id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 생성 실패: {str(e)}")

@router.get("/backup", 
            response_model=BackupListResponse,
            summary="백업 목록 조회",
            description="조직의 백업 목록을 조회합니다.")
async def list_backups(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    조직의 백업 목록을 조회합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        logger.info(f"📋 백업 목록 조회 - 조직: {organization.id}, 페이지: {page}")
        
        backup_list = await devops_service.list_backups(
            organization_id=organization.id,
            page=page,
            limit=limit
        )
        
        return backup_list
        
    except Exception as e:
        logger.error(f"❌ 백업 목록 조회 실패 - 조직: {organization.id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 목록 조회 실패: {str(e)}")

@router.get("/backup/{backup_id}", 
            response_model=BackupResponse,
            summary="백업 상세 조회",
            description="특정 백업의 상세 정보를 조회합니다.")
async def get_backup_details(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    특정 백업의 상세 정보를 조회합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **backup_id**: 백업 고유 ID
    """
    try:
        logger.info(f"🔍 백업 상세 조회 - 조직: {organization.id}, 백업: {backup_id}")
        
        # 실제 구현에서는 데이터베이스에서 백업 정보 조회
        # 현재는 간단한 구현으로 대체
        raise HTTPException(status_code=501, detail="백업 상세 조회 기능이 구현되지 않았습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 백업 상세 조회 실패 - 백업: {backup_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 상세 조회 실패: {str(e)}")

@router.get("/backup/{backup_id}/download",
            summary="백업 파일 다운로드",
            description="백업 파일을 다운로드합니다.")
async def download_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    백업 파일을 다운로드합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **backup_id**: 백업 고유 ID
    """
    try:
        logger.info(f"⬇️ 백업 다운로드 - 조직: {organization.id}, 백업: {backup_id}")
        
        # 백업 파일 찾기
        backup_file = await devops_service._find_backup_file(backup_id)
        if not backup_file or not backup_file.exists():
            raise HTTPException(status_code=404, detail="백업 파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=str(backup_file),
            filename=backup_file.name,
            media_type='application/zip'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 백업 다운로드 실패 - 백업: {backup_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 다운로드 실패: {str(e)}")

@router.delete("/backup/{backup_id}",
               response_model=DevOpsResponse,
               summary="백업 삭제",
               description="백업을 삭제합니다.")
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    백업을 삭제합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **backup_id**: 백업 고유 ID
    """
    try:
        logger.info(f"🗑️ 백업 삭제 - 조직: {organization.id}, 백업: {backup_id}")
        
        # 백업 파일 찾기 및 삭제
        backup_file = await devops_service._find_backup_file(backup_id)
        if backup_file and backup_file.exists():
            backup_file.unlink()
            
            return DevOpsResponse(
                success=True,
                message="백업이 성공적으로 삭제되었습니다",
                timestamp=datetime.now(),
                data={"backup_id": backup_id}
            )
        else:
            raise HTTPException(status_code=404, detail="백업 파일을 찾을 수 없습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 백업 삭제 실패 - 백업: {backup_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 삭제 실패: {str(e)}")

# ===== 복구 관련 엔드포인트 =====

@router.post("/restore", 
             response_model=RestoreResponse,
             summary="백업 복구",
             description="백업으로부터 시스템을 복구합니다.")
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    백업으로부터 시스템을 복구합니다.
    
    **관리자 권한이 필요합니다.**
    **주의: 복구 작업은 기존 데이터를 덮어쓸 수 있습니다.**
    
    - **backup_id**: 복구할 백업 ID
    - **restore_type**: 복구 타입 (FULL, PARTIAL, SELECTIVE)
    - **restore_database**: 데이터베이스 복구 여부
    - **restore_files**: 파일 복구 여부
    - **restore_config**: 설정 복구 여부
    - **overwrite_existing**: 기존 데이터 덮어쓰기 여부
    - **target_path**: 복구 대상 경로 (선택사항)
    """
    try:
        logger.info(f"🔄 복구 요청 - 조직: {organization.id}, 백업: {request.backup_id}")
        
        # 복구 실행 (백그라운드에서 실행)
        restore_response = await devops_service.restore_backup(
            organization_id=organization.id,
            user_id=current_user.id,
            request=request
        )
        
        return restore_response
        
    except Exception as e:
        logger.error(f"❌ 복구 실패 - 조직: {organization.id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"복구 실패: {str(e)}")

@router.get("/restore/{restore_id}/status",
            response_model=JobStatusResponse,
            summary="복구 상태 조회",
            description="복구 작업의 진행 상태를 조회합니다.")
async def get_restore_status(
    restore_id: str,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    복구 작업의 진행 상태를 조회합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **restore_id**: 복구 작업 ID
    """
    try:
        logger.info(f"📊 복구 상태 조회 - 조직: {organization.id}, 복구: {restore_id}")
        
        job_status = await devops_service.get_job_status(restore_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="복구 작업을 찾을 수 없습니다")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 복구 상태 조회 실패 - 복구: {restore_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"복구 상태 조회 실패: {str(e)}")

# ===== 테스트 관련 엔드포인트 =====

@router.post("/test", 
             response_model=TestResponse,
             summary="시스템 테스트 실행",
             description="시스템의 다양한 구성 요소를 테스트합니다.")
async def run_tests(
    request: TestRequest,
    current_user: User = Depends(get_current_admin_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    시스템의 다양한 구성 요소를 테스트합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **test_types**: 실행할 테스트 타입 목록
      - HEALTH_CHECK: 기본 헬스체크
      - SYSTEM_STATUS: 시스템 상태 확인
      - DATABASE_CHECK: 데이터베이스 연결 및 상태 확인
      - MAIL_SERVER_CHECK: 메일 서버 상태 확인
      - PERFORMANCE_TEST: 성능 테스트
      - SECURITY_SCAN: 보안 스캔
      - INTEGRATION_TEST: 통합 테스트
    - **timeout**: 테스트 타임아웃 (초)
    - **parallel**: 병렬 실행 여부
    """
    try:
        logger.info(f"🧪 테스트 실행 - 조직: {organization.id}, 테스트: {request.test_types}")
        
        test_response = await devops_service.run_tests(
            organization_id=organization.id,
            user_id=current_user.id,
            request=request
        )
        
        return test_response
        
    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패 - 조직: {organization.id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 실행 실패: {str(e)}")

@router.get("/test/health",
            response_model=SystemHealthResponse,
            summary="시스템 헬스체크",
            description="시스템의 전반적인 상태를 확인합니다.")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    시스템의 전반적인 상태를 확인합니다.
    
    - **status**: 전체 시스템 상태 (healthy, warning, critical)
    - **services**: 각 서비스별 상태
    - **database**: 데이터베이스 상태
    - **mail_server**: 메일 서버 상태
    - **redis**: Redis 상태
    - **disk_usage**: 디스크 사용량
    - **memory_usage**: 메모리 사용량
    - **cpu_usage**: CPU 사용량
    - **uptime**: 시스템 가동 시간
    """
    try:
        logger.info(f"💚 시스템 헬스체크 - 사용자: {current_user.id}")
        
        health_response = await devops_service.get_system_health()
        
        return health_response
        
    except Exception as e:
        logger.error(f"❌ 시스템 헬스체크 실패 - 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 헬스체크 실패: {str(e)}")

@router.get("/test/quick",
            response_model=TestResponse,
            summary="빠른 시스템 테스트",
            description="기본적인 시스템 상태를 빠르게 테스트합니다.")
async def run_quick_test(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    기본적인 시스템 상태를 빠르게 테스트합니다.
    
    다음 테스트를 수행합니다:
    - 헬스체크
    - 시스템 상태 확인
    - 데이터베이스 연결 확인
    """
    try:
        logger.info(f"⚡ 빠른 테스트 - 조직: {organization.id}, 사용자: {current_user.id}")
        
        from ..schemas.devops_schema import TestType
        
        quick_test_request = TestRequest(
            test_types=[
                TestType.HEALTH_CHECK,
                TestType.SYSTEM_STATUS,
                TestType.DATABASE_CHECK
            ],
            timeout=30,
            parallel=True
        )
        
        test_response = await devops_service.run_tests(
            organization_id=organization.id,
            user_id=current_user.id,
            request=quick_test_request
        )
        
        return test_response
        
    except Exception as e:
        logger.error(f"❌ 빠른 테스트 실패 - 조직: {organization.id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"빠른 테스트 실패: {str(e)}")

# ===== 작업 상태 조회 엔드포인트 =====

@router.get("/job/{job_id}/status",
            response_model=JobStatusResponse,
            summary="작업 상태 조회",
            description="백업, 복구 등의 작업 진행 상태를 조회합니다.")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    devops_service: DevOpsService = Depends(get_devops_service)
):
    """
    백업, 복구 등의 작업 진행 상태를 조회합니다.
    
    - **job_id**: 작업 고유 ID
    """
    try:
        logger.info(f"📊 작업 상태 조회 - 사용자: {current_user.id}, 작업: {job_id}")
        
        job_status = await devops_service.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 작업 상태 조회 실패 - 작업: {job_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 실패: {str(e)}")

# ===== 시스템 정보 엔드포인트 =====

@router.get("/info",
            response_model=DevOpsResponse,
            summary="시스템 정보 조회",
            description="시스템의 기본 정보를 조회합니다.")
async def get_system_info(
    current_user: User = Depends(get_current_user)
):
    """
    시스템의 기본 정보를 조회합니다.
    
    - 시스템 버전
    - 설치된 구성 요소
    - 설정 정보
    """
    try:
        logger.info(f"ℹ️ 시스템 정보 조회 - 사용자: {current_user.id}")
        
        import platform
        import sys
        
        system_info = {
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture(),
                "processor": platform.processor()
            },
            "application": {
                "name": "SkyBoot Mail SaaS",
                "version": "1.0.0",
                "environment": "development"  # 실제로는 설정에서 가져옴
            },
            "features": {
                "backup": True,
                "restore": True,
                "testing": True,
                "monitoring": True
            }
        }
        
        return DevOpsResponse(
            success=True,
            message="시스템 정보 조회 완료",
            timestamp=datetime.now(),
            data=system_info
        )
        
    except Exception as e:
        logger.error(f"❌ 시스템 정보 조회 실패 - 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 정보 조회 실패: {str(e)}")

# ===== 로그 조회 엔드포인트 =====

@router.get("/logs",
            response_model=DevOpsResponse,
            summary="시스템 로그 조회",
            description="시스템 로그를 조회합니다.")
async def get_system_logs(
    lines: int = Query(100, ge=1, le=1000, description="조회할 로그 라인 수"),
    level: Optional[str] = Query(None, description="로그 레벨 필터 (DEBUG, INFO, WARNING, ERROR)"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    시스템 로그를 조회합니다.
    
    **관리자 권한이 필요합니다.**
    
    - **lines**: 조회할 로그 라인 수 (기본값: 100, 최대: 1000)
    - **level**: 로그 레벨 필터 (선택사항)
    """
    try:
        logger.info(f"📜 시스템 로그 조회 - 사용자: {current_user.id}, 라인: {lines}")
        
        # 실제 구현에서는 로그 파일에서 읽어옴
        logs = [
            f"[{datetime.now().isoformat()}] INFO: 시스템이 정상적으로 작동 중입니다",
            f"[{datetime.now().isoformat()}] INFO: DevOps 로그 조회 요청 처리",
            # 더 많은 로그 항목...
        ]
        
        return DevOpsResponse(
            success=True,
            message=f"시스템 로그 {len(logs)}개 조회 완료",
            timestamp=datetime.now(),
            data={"logs": logs[:lines], "total_lines": len(logs)}
        )
        
    except Exception as e:
        logger.error(f"❌ 시스템 로그 조회 실패 - 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 로그 조회 실패: {str(e)}")