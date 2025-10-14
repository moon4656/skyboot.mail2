"""
오프라인 기능 스키마

SkyBoot Mail SaaS 프로젝트의 오프라인 기능을 위한 Pydantic 스키마입니다.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import json


class SyncStatus(str, Enum):
    """동기화 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncDirection(str, Enum):
    """동기화 방향"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class OfflineAction(str, Enum):
    """오프라인 액션 타입"""
    SEND_MAIL = "send_mail"
    SAVE_DRAFT = "save_draft"
    DELETE_MAIL = "delete_mail"
    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    MOVE_MAIL = "move_mail"
    ADD_LABEL = "add_label"
    REMOVE_LABEL = "remove_label"
    CREATE_FOLDER = "create_folder"
    DELETE_FOLDER = "delete_folder"
    UPDATE_SETTINGS = "update_settings"


class ConflictResolution(str, Enum):
    """충돌 해결 방식"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MERGE = "merge"
    MANUAL = "manual"


class CacheStrategy(str, Enum):
    """캐시 전략"""
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    CACHE_ONLY = "cache_only"
    NETWORK_ONLY = "network_only"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"


class DataType(str, Enum):
    """데이터 타입"""
    MAIL = "mail"
    DRAFT = "draft"
    CONTACT = "contact"
    FOLDER = "folder"
    LABEL = "label"
    SETTINGS = "settings"
    ATTACHMENT = "attachment"


# 오프라인 액션 모델
class OfflineActionData(BaseModel):
    """오프라인 액션 데이터"""
    action_id: str = Field(..., description="액션 고유 ID")
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    action_type: OfflineAction = Field(..., description="액션 타입")
    target_id: Optional[str] = Field(None, description="대상 ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="액션 데이터")
    timestamp: datetime = Field(..., description="액션 발생 시간")
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING, description="동기화 상태")
    retry_count: int = Field(default=0, description="재시도 횟수")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")


# 동기화 작업 모델
class SyncTask(BaseModel):
    """동기화 작업"""
    task_id: str = Field(..., description="작업 고유 ID")
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    data_type: DataType = Field(..., description="데이터 타입")
    direction: SyncDirection = Field(..., description="동기화 방향")
    status: SyncStatus = Field(default=SyncStatus.PENDING, description="동기화 상태")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="진행률 (%)")
    total_items: int = Field(default=0, description="전체 항목 수")
    processed_items: int = Field(default=0, description="처리된 항목 수")
    failed_items: int = Field(default=0, description="실패한 항목 수")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")


# 캐시 항목 모델
class CacheItem(BaseModel):
    """캐시 항목"""
    cache_key: str = Field(..., description="캐시 키")
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    data_type: DataType = Field(..., description="데이터 타입")
    data: Dict[str, Any] = Field(..., description="캐시된 데이터")
    strategy: CacheStrategy = Field(..., description="캐시 전략")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="마지막 접근 시간")
    access_count: int = Field(default=0, description="접근 횟수")
    size_bytes: int = Field(default=0, description="데이터 크기 (바이트)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")


# 충돌 항목 모델
class ConflictItem(BaseModel):
    """충돌 항목"""
    conflict_id: str = Field(..., description="충돌 고유 ID")
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    data_type: DataType = Field(..., description="데이터 타입")
    item_id: str = Field(..., description="항목 ID")
    server_data: Dict[str, Any] = Field(..., description="서버 데이터")
    client_data: Dict[str, Any] = Field(..., description="클라이언트 데이터")
    server_timestamp: datetime = Field(..., description="서버 수정 시간")
    client_timestamp: datetime = Field(..., description="클라이언트 수정 시간")
    resolution: Optional[ConflictResolution] = Field(None, description="해결 방식")
    resolved_data: Optional[Dict[str, Any]] = Field(None, description="해결된 데이터")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")


# 오프라인 설정 모델
class OfflineSettings(BaseModel):
    """오프라인 설정"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    enabled: bool = Field(default=True, description="오프라인 기능 활성화")
    auto_sync: bool = Field(default=True, description="자동 동기화")
    sync_interval: int = Field(default=300, ge=60, le=3600, description="동기화 간격 (초)")
    max_cache_size: int = Field(default=100, ge=10, le=1000, description="최대 캐시 크기 (MB)")
    cache_duration: int = Field(default=86400, ge=3600, le=604800, description="캐시 유지 시간 (초)")
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.SERVER_WINS, description="기본 충돌 해결 방식")
    sync_on_startup: bool = Field(default=True, description="시작 시 동기화")
    sync_on_network_change: bool = Field(default=True, description="네트워크 변경 시 동기화")
    background_sync: bool = Field(default=True, description="백그라운드 동기화")
    compress_data: bool = Field(default=True, description="데이터 압축")
    encrypt_cache: bool = Field(default=True, description="캐시 암호화")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")


# 요청/응답 모델들

class OfflineActionRequest(BaseModel):
    """오프라인 액션 요청"""
    action_type: OfflineAction = Field(..., description="액션 타입")
    target_id: Optional[str] = Field(None, description="대상 ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="액션 데이터")
    timestamp: Optional[datetime] = Field(None, description="액션 발생 시간")


class OfflineActionResponse(BaseModel):
    """오프라인 액션 응답"""
    action_id: str = Field(..., description="액션 고유 ID")
    success: bool = Field(..., description="처리 성공 여부")
    message: str = Field(..., description="결과 메시지")
    sync_status: SyncStatus = Field(..., description="동기화 상태")
    created_at: datetime = Field(..., description="생성 시간")


class SyncRequest(BaseModel):
    """동기화 요청"""
    data_types: List[DataType] = Field(..., description="동기화할 데이터 타입 목록")
    direction: SyncDirection = Field(default=SyncDirection.BIDIRECTIONAL, description="동기화 방향")
    force_sync: bool = Field(default=False, description="강제 동기화")
    last_sync_time: Optional[datetime] = Field(None, description="마지막 동기화 시간")


class SyncResponse(BaseModel):
    """동기화 응답"""
    task_id: str = Field(..., description="동기화 작업 ID")
    status: SyncStatus = Field(..., description="동기화 상태")
    message: str = Field(..., description="결과 메시지")
    estimated_duration: Optional[int] = Field(None, description="예상 소요 시간 (초)")
    started_at: datetime = Field(..., description="시작 시간")


class SyncStatusResponse(BaseModel):
    """동기화 상태 응답"""
    task_id: str = Field(..., description="작업 ID")
    status: SyncStatus = Field(..., description="동기화 상태")
    progress: float = Field(..., description="진행률 (%)")
    total_items: int = Field(..., description="전체 항목 수")
    processed_items: int = Field(..., description="처리된 항목 수")
    failed_items: int = Field(..., description="실패한 항목 수")
    current_item: Optional[str] = Field(None, description="현재 처리 중인 항목")
    estimated_remaining: Optional[int] = Field(None, description="예상 남은 시간 (초)")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")


class CacheStatusResponse(BaseModel):
    """캐시 상태 응답"""
    total_items: int = Field(..., description="전체 캐시 항목 수")
    total_size_mb: float = Field(..., description="전체 캐시 크기 (MB)")
    used_size_mb: float = Field(..., description="사용된 캐시 크기 (MB)")
    available_size_mb: float = Field(..., description="사용 가능한 캐시 크기 (MB)")
    cache_hit_rate: float = Field(..., description="캐시 적중률 (%)")
    oldest_item_date: Optional[datetime] = Field(None, description="가장 오래된 항목 날짜")
    newest_item_date: Optional[datetime] = Field(None, description="가장 최신 항목 날짜")
    data_type_breakdown: Dict[str, int] = Field(..., description="데이터 타입별 항목 수")
    last_cleanup: Optional[datetime] = Field(None, description="마지막 정리 시간")


class OfflineSettingsRequest(BaseModel):
    """오프라인 설정 요청"""
    enabled: bool = Field(default=True, description="오프라인 기능 활성화")
    auto_sync: bool = Field(default=True, description="자동 동기화")
    sync_interval: int = Field(default=300, ge=60, le=3600, description="동기화 간격 (초)")
    max_cache_size: int = Field(default=100, ge=10, le=1000, description="최대 캐시 크기 (MB)")
    cache_duration: int = Field(default=86400, ge=3600, le=604800, description="캐시 유지 시간 (초)")
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.SERVER_WINS, description="기본 충돌 해결 방식")
    sync_on_startup: bool = Field(default=True, description="시작 시 동기화")
    sync_on_network_change: bool = Field(default=True, description="네트워크 변경 시 동기화")
    background_sync: bool = Field(default=True, description="백그라운드 동기화")
    compress_data: bool = Field(default=True, description="데이터 압축")
    encrypt_cache: bool = Field(default=True, description="캐시 암호화")


class OfflineSettingsResponse(BaseModel):
    """오프라인 설정 응답"""
    user_id: int = Field(..., description="사용자 ID")
    organization_id: int = Field(..., description="조직 ID")
    enabled: bool = Field(..., description="오프라인 기능 활성화")
    auto_sync: bool = Field(..., description="자동 동기화")
    sync_interval: int = Field(..., description="동기화 간격 (초)")
    max_cache_size: int = Field(..., description="최대 캐시 크기 (MB)")
    cache_duration: int = Field(..., description="캐시 유지 시간 (초)")
    conflict_resolution: ConflictResolution = Field(..., description="기본 충돌 해결 방식")
    sync_on_startup: bool = Field(..., description="시작 시 동기화")
    sync_on_network_change: bool = Field(..., description="네트워크 변경 시 동기화")
    background_sync: bool = Field(..., description="백그라운드 동기화")
    compress_data: bool = Field(..., description="데이터 압축")
    encrypt_cache: bool = Field(..., description="캐시 암호화")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class ConflictListResponse(BaseModel):
    """충돌 목록 응답"""
    conflicts: List[ConflictItem] = Field(..., description="충돌 항목 목록")
    total_count: int = Field(..., description="전체 충돌 수")
    unresolved_count: int = Field(..., description="미해결 충돌 수")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class ConflictResolutionRequest(BaseModel):
    """충돌 해결 요청"""
    conflict_id: str = Field(..., description="충돌 ID")
    resolution: ConflictResolution = Field(..., description="해결 방식")
    resolved_data: Optional[Dict[str, Any]] = Field(None, description="해결된 데이터 (수동 해결 시)")


class ConflictResolutionResponse(BaseModel):
    """충돌 해결 응답"""
    conflict_id: str = Field(..., description="충돌 ID")
    success: bool = Field(..., description="해결 성공 여부")
    resolution: ConflictResolution = Field(..., description="적용된 해결 방식")
    resolved_data: Dict[str, Any] = Field(..., description="해결된 데이터")
    resolved_at: datetime = Field(..., description="해결 시간")


class OfflineStatsResponse(BaseModel):
    """오프라인 통계 응답"""
    total_offline_actions: int = Field(..., description="전체 오프라인 액션 수")
    pending_actions: int = Field(..., description="대기 중인 액션 수")
    completed_actions: int = Field(..., description="완료된 액션 수")
    failed_actions: int = Field(..., description="실패한 액션 수")
    sync_success_rate: float = Field(..., description="동기화 성공률 (%)")
    average_sync_time: float = Field(..., description="평균 동기화 시간 (초)")
    cache_efficiency: float = Field(..., description="캐시 효율성 (%)")
    data_usage_mb: float = Field(..., description="데이터 사용량 (MB)")
    last_sync_time: Optional[datetime] = Field(None, description="마지막 동기화 시간")
    next_sync_time: Optional[datetime] = Field(None, description="다음 동기화 시간")
    conflicts_count: int = Field(..., description="충돌 수")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")


class NetworkStatusResponse(BaseModel):
    """네트워크 상태 응답"""
    is_online: bool = Field(..., description="온라인 상태")
    connection_type: Optional[str] = Field(None, description="연결 타입")
    effective_type: Optional[str] = Field(None, description="유효 연결 타입")
    downlink: Optional[float] = Field(None, description="다운링크 속도 (Mbps)")
    rtt: Optional[int] = Field(None, description="왕복 시간 (ms)")
    save_data: bool = Field(default=False, description="데이터 절약 모드")
    last_checked: datetime = Field(..., description="마지막 확인 시간")


# 검증 함수들

@validator('data', pre=True)
def validate_action_data(cls, v, values):
    """액션 데이터 검증"""
    action_type = values.get('action_type')
    
    if action_type == OfflineAction.SEND_MAIL:
        required_fields = ['recipient', 'subject', 'content']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"메일 발송 액션에는 {field} 필드가 필요합니다.")
    
    return v


@validator('sync_interval')
def validate_sync_interval(cls, v):
    """동기화 간격 검증"""
    if v < 60:
        raise ValueError("동기화 간격은 최소 60초 이상이어야 합니다.")
    if v > 3600:
        raise ValueError("동기화 간격은 최대 3600초 이하여야 합니다.")
    return v


@validator('max_cache_size')
def validate_cache_size(cls, v):
    """캐시 크기 검증"""
    if v < 10:
        raise ValueError("최대 캐시 크기는 최소 10MB 이상이어야 합니다.")
    if v > 1000:
        raise ValueError("최대 캐시 크기는 최대 1000MB 이하여야 합니다.")
    return v


class OfflineError(Exception):
    """오프라인 기능 오류"""
    pass


class SyncError(Exception):
    """동기화 오류"""
    pass


class CacheError(Exception):
    """캐시 오류"""
    pass


class ConflictError(Exception):
    """충돌 해결 오류"""
    pass