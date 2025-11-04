"""
오프라인 기능 API 라우터

SkyBoot Mail SaaS 프로젝트의 오프라인 기능을 위한 API 엔드포인트입니다.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas.offline_schema import (
    OfflineActionData, SyncTask, CacheItem, ConflictItem, OfflineSettings,
    OfflineActionRequest, OfflineActionResponse, SyncRequest, SyncResponse,
    SyncStatusResponse, CacheStatusResponse, OfflineSettingsRequest,
    OfflineSettingsResponse, ConflictResolutionRequest, ConflictResolutionResponse,
    OfflineStatsResponse, SyncStatus, SyncDirection, OfflineAction,
    ConflictResolution, CacheStrategy, DataType
)
from app.service.offline_service import OfflineService
from app.service.auth_service import get_current_user
from app.middleware.tenant_middleware import get_current_organization
from app.model.user_model import User
from app.model.organization_model import Organization
from app.database.user import get_db

router = APIRouter()

@router.post("/actions", summary="오프라인 액션 큐에 추가")
async def queue_offline_action(
    action_request: OfflineActionRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> OfflineActionResponse:
    """
    오프라인 상태에서 수행된 액션을 큐에 추가합니다.
    
    - **action**: 수행된 액션 타입 (create, update, delete, send)
    - **data_type**: 데이터 타입 (mail, contact, calendar, note)
    - **data**: 액션 데이터
    - **timestamp**: 액션 수행 시간
    - **device_id**: 디바이스 식별자
    """
    service = OfflineService(db)
    return await service.queue_offline_action(
        organization.id,
        current_user.id,
        action_request
    )


@router.get("/actions", summary="오프라인 액션 목록 조회")
async def get_offline_actions(
    status: Optional[str] = Query(None, description="액션 상태 필터"),
    data_type: Optional[DataType] = Query(None, description="데이터 타입 필터"),
    limit: int = Query(50, ge=1, le=200, description="조회할 액션 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 오프라인 액션 목록을 조회합니다.
    
    - **status**: 액션 상태로 필터링
    - **data_type**: 데이터 타입으로 필터링
    - **limit**: 조회할 액션 수
    - **offset**: 페이지네이션 오프셋
    """
    service = OfflineService(db)
    return await service.get_offline_actions(
        organization.id,
        current_user.id,
        status,
        data_type,
        limit,
        offset
    )


@router.delete("/actions/{action_id}", summary="오프라인 액션 삭제")
async def delete_offline_action(
    action_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 오프라인 액션을 삭제합니다.
    
    - **action_id**: 삭제할 액션 ID
    """
    service = OfflineService(db)
    return await service.delete_offline_action(
        organization.id,
        current_user.id,
        action_id
    )


@router.post("/sync", summary="동기화 시작")
async def start_sync(
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> SyncResponse:
    """
    오프라인 데이터 동기화를 시작합니다.
    
    - **direction**: 동기화 방향 (upload, download, bidirectional)
    - **data_types**: 동기화할 데이터 타입 목록
    - **force_sync**: 강제 동기화 여부
    - **conflict_resolution**: 충돌 해결 방법
    """
    service = OfflineService(db)
    return await service.start_sync(
        organization.id,
        current_user.id,
        sync_request
    )


@router.get("/sync/status", summary="동기화 상태 조회")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> SyncStatusResponse:
    """
    현재 동기화 상태를 조회합니다.
    
    - **status**: 동기화 상태 (idle, running, completed, failed)
    - **progress**: 진행률 (0-100)
    - **current_task**: 현재 작업
    - **total_tasks**: 전체 작업 수
    - **completed_tasks**: 완료된 작업 수
    - **failed_tasks**: 실패한 작업 수
    """
    service = OfflineService(db)
    return await service.get_sync_status(
        organization.id,
        current_user.id
    )


@router.post("/sync/cancel", summary="동기화 취소")
async def cancel_sync(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    진행 중인 동기화를 취소합니다.
    
    - **cancelled**: 취소 성공 여부
    - **message**: 취소 결과 메시지
    """
    service = OfflineService(db)
    return await service.cancel_sync(
        organization.id,
        current_user.id
    )


@router.get("/sync/history", summary="동기화 히스토리")
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100, description="조회할 히스토리 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    동기화 히스토리를 조회합니다.
    
    - **sync_tasks**: 동기화 작업 목록
    - **total_count**: 전체 작업 수
    - **success_rate**: 성공률
    - **average_duration**: 평균 소요 시간
    """
    service = OfflineService(db)
    return await service.get_sync_history(
        organization.id,
        current_user.id,
        limit,
        offset
    )


@router.get("/cache/status", summary="캐시 상태 조회")
async def get_cache_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> CacheStatusResponse:
    """
    오프라인 캐시 상태를 조회합니다.
    
    - **total_size**: 전체 캐시 크기
    - **used_size**: 사용된 캐시 크기
    - **available_size**: 사용 가능한 캐시 크기
    - **cache_items**: 캐시된 항목 수
    - **last_updated**: 마지막 업데이트 시간
    """
    service = OfflineService(db)
    return await service.get_cache_status(
        organization.id,
        current_user.id
    )


@router.get("/cache/items", summary="캐시 항목 목록")
async def get_cache_items(
    data_type: Optional[DataType] = Query(None, description="데이터 타입 필터"),
    limit: int = Query(50, ge=1, le=200, description="조회할 항목 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    캐시된 항목 목록을 조회합니다.
    
    - **data_type**: 데이터 타입으로 필터링
    - **limit**: 조회할 항목 수
    - **offset**: 페이지네이션 오프셋
    """
    service = OfflineService(db)
    return await service.get_cache_items(
        organization.id,
        current_user.id,
        data_type,
        limit,
        offset
    )


@router.delete("/cache/items/{item_id}", summary="캐시 항목 삭제")
async def delete_cache_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 캐시 항목을 삭제합니다.
    
    - **item_id**: 삭제할 캐시 항목 ID
    """
    service = OfflineService(db)
    return await service.delete_cache_item(
        organization.id,
        current_user.id,
        item_id
    )


@router.post("/cache/clear", summary="캐시 초기화")
async def clear_cache(
    data_type: Optional[DataType] = Query(None, description="초기화할 데이터 타입"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 캐시를 초기화합니다.
    
    - **data_type**: 특정 데이터 타입만 초기화 (선택사항)
    - **cleared_items**: 초기화된 항목 수
    - **freed_space**: 확보된 공간 크기
    """
    service = OfflineService(db)
    return await service.clear_cache(
        organization.id,
        current_user.id,
        data_type
    )


@router.get("/settings", summary="오프라인 설정 조회")
async def get_offline_settings(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> OfflineSettingsResponse:
    """
    사용자의 오프라인 설정을 조회합니다.
    
    - **auto_sync**: 자동 동기화 활성화 여부
    - **sync_interval**: 동기화 간격 (분)
    - **cache_strategy**: 캐시 전략
    - **max_cache_size**: 최대 캐시 크기 (MB)
    - **sync_on_wifi_only**: WiFi에서만 동기화 여부
    """
    service = OfflineService(db)
    return await service.get_offline_settings(
        organization.id,
        current_user.id
    )


@router.put("/settings", summary="오프라인 설정 업데이트")
async def update_offline_settings(
    settings_request: OfflineSettingsRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> OfflineSettingsResponse:
    """
    사용자의 오프라인 설정을 업데이트합니다.
    
    - **auto_sync**: 자동 동기화 활성화/비활성화
    - **sync_interval**: 동기화 간격 변경
    - **cache_strategy**: 캐시 전략 변경
    - **max_cache_size**: 최대 캐시 크기 변경
    - **sync_on_wifi_only**: WiFi 전용 동기화 설정
    """
    service = OfflineService(db)
    return await service.update_offline_settings(
        organization.id,
        current_user.id,
        settings_request
    )


@router.get("/conflicts", summary="동기화 충돌 목록")
async def get_sync_conflicts(
    resolved: Optional[bool] = Query(None, description="해결 상태 필터"),
    limit: int = Query(20, ge=1, le=100, description="조회할 충돌 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    동기화 충돌 목록을 조회합니다.
    
    - **resolved**: 해결 상태로 필터링
    - **limit**: 조회할 충돌 수
    - **offset**: 페이지네이션 오프셋
    """
    service = OfflineService(db)
    return await service.get_sync_conflicts(
        organization.id,
        current_user.id,
        resolved,
        limit,
        offset
    )


@router.post("/conflicts/{conflict_id}/resolve", summary="동기화 충돌 해결")
async def resolve_sync_conflict(
    conflict_id: str,
    resolution_request: ConflictResolutionRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> ConflictResolutionResponse:
    """
    동기화 충돌을 해결합니다.
    
    - **conflict_id**: 해결할 충돌 ID
    - **resolution**: 해결 방법 (local_wins, remote_wins, merge, manual)
    - **merged_data**: 병합된 데이터 (merge 선택 시)
    """
    service = OfflineService(db)
    return await service.resolve_sync_conflict(
        organization.id,
        current_user.id,
        conflict_id,
        resolution_request
    )


@router.get("/stats", summary="오프라인 통계")
async def get_offline_statistics(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> OfflineStatsResponse:
    """
    오프라인 사용 통계를 조회합니다.
    
    - **total_offline_actions**: 총 오프라인 액션 수
    - **successful_syncs**: 성공한 동기화 수
    - **failed_syncs**: 실패한 동기화 수
    - **cache_hit_rate**: 캐시 적중률
    - **average_sync_time**: 평균 동기화 시간
    """
    service = OfflineService(db)
    return await service.get_offline_statistics(
        organization.id,
        current_user.id
    )


@router.get("/network/status", summary="네트워크 상태 확인")
async def check_network_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    현재 네트워크 상태를 확인합니다.
    
    - **online**: 온라인 상태 여부
    - **connection_type**: 연결 타입 (wifi, cellular, ethernet)
    - **bandwidth**: 대역폭 정보
    - **latency**: 지연 시간
    """
    service = OfflineService(db)
    return await service.check_network_status()


@router.post("/preload", summary="데이터 사전 로드")
async def preload_data(
    data_types: List[DataType],
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 사용을 위해 데이터를 사전 로드합니다.
    
    - **data_types**: 사전 로드할 데이터 타입 목록
    - **preloaded_items**: 사전 로드된 항목 수
    - **cache_size**: 사용된 캐시 크기
    """
    service = OfflineService(db)
    return await service.preload_data(
        organization.id,
        current_user.id,
        data_types
    )


@router.get("/queue/status", summary="오프라인 큐 상태")
async def get_queue_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 액션 큐 상태를 조회합니다.
    
    - **pending_actions**: 대기 중인 액션 수
    - **processing_actions**: 처리 중인 액션 수
    - **failed_actions**: 실패한 액션 수
    - **queue_size**: 큐 크기
    """
    service = OfflineService(db)
    return await service.get_queue_status(
        organization.id,
        current_user.id
    )


@router.post("/queue/retry", summary="실패한 액션 재시도")
async def retry_failed_actions(
    action_ids: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    실패한 오프라인 액션을 재시도합니다.
    
    - **action_ids**: 재시도할 액션 ID 목록 (선택사항, 전체 재시도 시 생략)
    - **retried_actions**: 재시도된 액션 수
    - **success_count**: 성공한 액션 수
    """
    service = OfflineService(db)
    return await service.retry_failed_actions(
        organization.id,
        current_user.id,
        action_ids
    )


@router.get("/backup/status", summary="오프라인 백업 상태")
async def get_backup_status(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 데이터 백업 상태를 조회합니다.
    
    - **last_backup**: 마지막 백업 시간
    - **backup_size**: 백업 크기
    - **backup_items**: 백업된 항목 수
    - **auto_backup**: 자동 백업 활성화 여부
    """
    service = OfflineService(db)
    return await service.get_backup_status(
        organization.id,
        current_user.id
    )


@router.post("/backup/create", summary="오프라인 백업 생성")
async def create_backup(
    data_types: Optional[List[DataType]] = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 데이터 백업을 생성합니다.
    
    - **data_types**: 백업할 데이터 타입 목록 (선택사항, 전체 백업 시 생략)
    - **backup_id**: 생성된 백업 ID
    - **backup_size**: 백업 크기
    """
    service = OfflineService(db)
    return await service.create_backup(
        organization.id,
        current_user.id,
        data_types
    )


@router.post("/backup/restore", summary="오프라인 백업 복원")
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    오프라인 데이터 백업을 복원합니다.
    
    - **backup_id**: 복원할 백업 ID
    - **restored_items**: 복원된 항목 수
    - **conflicts**: 복원 중 발생한 충돌 수
    """
    service = OfflineService(db)
    return await service.restore_backup(
        organization.id,
        current_user.id,
        backup_id
    )