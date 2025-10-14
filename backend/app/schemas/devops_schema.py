"""
DevOps 스키마

SkyBoot Mail SaaS 프로젝트의 DevOps 기능을 위한 Pydantic 스키마입니다.
백업, 복구, 테스트 등의 DevOps 작업을 위한 요청/응답 모델을 정의합니다.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# ===== Enums =====

class BackupType(str, Enum):
    """백업 타입"""
    FULL = "full"                    # 전체 백업
    INCREMENTAL = "incremental"      # 증분 백업
    DIFFERENTIAL = "differential"    # 차등 백업
    DATABASE_ONLY = "database_only"  # 데이터베이스만
    FILES_ONLY = "files_only"        # 파일만
    CONFIG_ONLY = "config_only"      # 설정만

class BackupStatus(str, Enum):
    """백업 상태"""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패
    CANCELLED = "cancelled"  # 취소됨

class RestoreType(str, Enum):
    """복구 타입"""
    FULL = "full"                    # 전체 복구
    SELECTIVE = "selective"          # 선택적 복구
    DATABASE_ONLY = "database_only"  # 데이터베이스만
    FILES_ONLY = "files_only"        # 파일만
    CONFIG_ONLY = "config_only"      # 설정만

class TestType(str, Enum):
    """테스트 타입"""
    HEALTH_CHECK = "health_check"    # 헬스체크
    SYSTEM_STATUS = "system_status"  # 시스템 상태
    DATABASE_CHECK = "database_check" # 데이터베이스 체크
    MAIL_SERVER_CHECK = "mail_server_check" # 메일 서버 체크
    PERFORMANCE_TEST = "performance_test" # 성능 테스트
    SECURITY_SCAN = "security_scan"  # 보안 스캔
    INTEGRATION_TEST = "integration_test" # 통합 테스트

class TestStatus(str, Enum):
    """테스트 상태"""
    PASS = "pass"        # 통과
    FAIL = "fail"        # 실패
    WARNING = "warning"  # 경고
    SKIP = "skip"        # 건너뜀
    ERROR = "error"      # 오류

# ===== 백업 관련 스키마 =====

class BackupRequest(BaseModel):
    """백업 요청"""
    backup_type: BackupType = Field(..., description="백업 타입")
    include_database: bool = Field(True, description="데이터베이스 포함 여부")
    include_files: bool = Field(True, description="파일 포함 여부")
    include_config: bool = Field(True, description="설정 포함 여부")
    include_attachments: bool = Field(True, description="첨부파일 포함 여부")
    compression: bool = Field(True, description="압축 여부")
    encryption: bool = Field(False, description="암호화 여부")
    password: Optional[str] = Field(None, description="암호화 비밀번호")
    description: Optional[str] = Field(None, description="백업 설명")
    tags: List[str] = Field(default_factory=list, description="백업 태그")

class BackupResponse(BaseModel):
    """백업 응답"""
    backup_id: str = Field(..., description="백업 ID")
    backup_type: BackupType = Field(..., description="백업 타입")
    status: BackupStatus = Field(..., description="백업 상태")
    file_path: Optional[str] = Field(None, description="백업 파일 경로")
    file_size: Optional[int] = Field(None, description="파일 크기 (바이트)")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    organization_id: int = Field(..., description="조직 ID")
    created_by: int = Field(..., description="생성자 ID")
    description: Optional[str] = Field(None, description="백업 설명")
    tags: List[str] = Field(default_factory=list, description="백업 태그")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")

class BackupListResponse(BaseModel):
    """백업 목록 응답"""
    backups: List[BackupResponse] = Field(..., description="백업 목록")
    total: int = Field(..., description="전체 백업 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")

# ===== 복구 관련 스키마 =====

class RestoreRequest(BaseModel):
    """복구 요청"""
    backup_id: str = Field(..., description="복구할 백업 ID")
    restore_type: RestoreType = Field(..., description="복구 타입")
    restore_database: bool = Field(True, description="데이터베이스 복구 여부")
    restore_files: bool = Field(True, description="파일 복구 여부")
    restore_config: bool = Field(True, description="설정 복구 여부")
    overwrite_existing: bool = Field(False, description="기존 데이터 덮어쓰기 여부")
    password: Optional[str] = Field(None, description="암호화된 백업의 비밀번호")
    target_organization_id: Optional[int] = Field(None, description="대상 조직 ID (다른 조직으로 복구시)")

class RestoreResponse(BaseModel):
    """복구 응답"""
    restore_id: str = Field(..., description="복구 작업 ID")
    backup_id: str = Field(..., description="백업 ID")
    restore_type: RestoreType = Field(..., description="복구 타입")
    status: BackupStatus = Field(..., description="복구 상태")
    started_at: datetime = Field(..., description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    organization_id: int = Field(..., description="조직 ID")
    restored_by: int = Field(..., description="복구 실행자 ID")
    progress: int = Field(0, description="진행률 (0-100)")
    log_messages: List[str] = Field(default_factory=list, description="로그 메시지")

# ===== 테스트 관련 스키마 =====

class TestRequest(BaseModel):
    """테스트 요청"""
    test_types: List[TestType] = Field(..., description="실행할 테스트 타입 목록")
    include_performance: bool = Field(False, description="성능 테스트 포함 여부")
    include_security: bool = Field(False, description="보안 스캔 포함 여부")
    detailed_report: bool = Field(True, description="상세 리포트 생성 여부")

class TestResult(BaseModel):
    """개별 테스트 결과"""
    test_type: TestType = Field(..., description="테스트 타입")
    status: TestStatus = Field(..., description="테스트 상태")
    message: str = Field(..., description="테스트 메시지")
    details: Dict[str, Any] = Field(default_factory=dict, description="상세 정보")
    execution_time: float = Field(..., description="실행 시간 (초)")
    timestamp: datetime = Field(..., description="실행 시간")

class TestResponse(BaseModel):
    """테스트 응답"""
    test_id: str = Field(..., description="테스트 실행 ID")
    overall_status: TestStatus = Field(..., description="전체 테스트 상태")
    total_tests: int = Field(..., description="전체 테스트 수")
    passed_tests: int = Field(..., description="통과한 테스트 수")
    failed_tests: int = Field(..., description="실패한 테스트 수")
    warning_tests: int = Field(..., description="경고가 있는 테스트 수")
    results: List[TestResult] = Field(..., description="개별 테스트 결과")
    started_at: datetime = Field(..., description="시작 시간")
    completed_at: datetime = Field(..., description="완료 시간")
    total_execution_time: float = Field(..., description="전체 실행 시간 (초)")
    organization_id: int = Field(..., description="조직 ID")
    executed_by: int = Field(..., description="실행자 ID")

# ===== 시스템 상태 관련 스키마 =====

class SystemHealthResponse(BaseModel):
    """시스템 헬스 응답"""
    status: str = Field(..., description="전체 시스템 상태")
    timestamp: datetime = Field(..., description="체크 시간")
    services: Dict[str, Dict[str, Any]] = Field(..., description="서비스별 상태")
    database: Dict[str, Any] = Field(..., description="데이터베이스 상태")
    mail_server: Dict[str, Any] = Field(..., description="메일 서버 상태")
    redis: Dict[str, Any] = Field(..., description="Redis 상태")
    disk_usage: Dict[str, Any] = Field(..., description="디스크 사용량")
    memory_usage: Dict[str, Any] = Field(..., description="메모리 사용량")
    cpu_usage: float = Field(..., description="CPU 사용률")
    uptime: float = Field(..., description="가동 시간 (초)")

# ===== 공통 응답 스키마 =====

class DevOpsResponse(BaseModel):
    """DevOps 공통 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

class DevOpsErrorResponse(BaseModel):
    """DevOps 오류 응답"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field(..., description="오류 코드")
    error_message: str = Field(..., description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="오류 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="오류 발생 시간")

# ===== 작업 상태 조회 스키마 =====

class JobStatusResponse(BaseModel):
    """작업 상태 응답"""
    job_id: str = Field(..., description="작업 ID")
    job_type: str = Field(..., description="작업 타입")
    status: str = Field(..., description="작업 상태")
    progress: int = Field(..., description="진행률 (0-100)")
    started_at: datetime = Field(..., description="시작 시간")
    updated_at: datetime = Field(..., description="마지막 업데이트 시간")
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료 시간")
    log_messages: List[str] = Field(default_factory=list, description="로그 메시지")
    result: Optional[Dict[str, Any]] = Field(None, description="작업 결과")