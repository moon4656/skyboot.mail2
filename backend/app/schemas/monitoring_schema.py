"""
모니터링 관련 스키마 정의
"""
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic import field_validator


class AuditActionType(str, Enum):
    """감사 로그 액션 타입"""
    LOGIN = "login"
    LOGOUT = "logout"
    SEND_EMAIL = "send_email"
    READ_EMAIL = "read_email"
    DELETE_EMAIL = "delete_email"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    UPDATE_SETTINGS = "update_settings"


class UsageMetrics(BaseModel):
    """사용량 메트릭"""
    current_users: int
    max_users: int
    emails_sent_today: int
    emails_received_today: int
    storage_used_gb: float
    storage_limit_gb: float


class DailyUsageStats(BaseModel):
    """일별 사용량 통계"""
    date: date
    emails_sent: int
    emails_received: int
    active_users: int
    storage_used_gb: float


class WeeklyUsageStats(BaseModel):
    """주별 사용량 통계"""
    week_start: date
    week_end: date
    total_emails_sent: int
    total_emails_received: int
    avg_daily_active_users: float
    peak_storage_used_gb: float


class MonthlyUsageStats(BaseModel):
    """월별 사용량 통계"""
    year: int
    month: int
    total_emails_sent: int
    total_emails_received: int
    avg_daily_active_users: float
    peak_storage_used_gb: float


class UsageResponse(BaseModel):
    """사용량 통계 응답"""
    current_metrics: UsageMetrics
    daily_stats: List[DailyUsageStats] = []
    weekly_stats: List[WeeklyUsageStats] = []
    monthly_stats: List[MonthlyUsageStats] = []


class AuditLogEntry(BaseModel):
    """감사 로그 항목"""
    id: int
    action: AuditActionType
    user_email: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class AuditResponse(BaseModel):
    """감사 로그 응답"""
    logs: List[AuditLogEntry]
    total_count: int
    page: int
    page_size: int


class SystemHealthMetrics(BaseModel):
    """시스템 건강 상태 메트릭"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    email_queue_size: int


class OrganizationSummary(BaseModel):
    """조직 요약 정보"""
    total_users: int
    active_users_today: int
    emails_sent_today: int
    storage_usage_percent: float
    user_usage_percent: float


class DashboardData(BaseModel):
    """대시보드 데이터"""
    organization_summary: OrganizationSummary
    system_health: SystemHealthMetrics
    recent_activities: List[Dict[str, Any]] = []
    alerts: List[str] = []
    performance_metrics: Dict[str, float] = {}


class DashboardResponse(BaseModel):
    """대시보드 응답"""
    success: bool
    data: DashboardData
    last_updated: datetime


# 요청 스키마들
class UsageRequest(BaseModel):
    """사용량 통계 요청"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period: Optional[str] = "daily"
    include_trends: bool = True

    @field_validator("start_date", "end_date", mode="before")
    def _parse_date(cls, v):
        """
        날짜 입력을 유연하게 파싱합니다.
        - 지원 형식: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD, ISO datetime 문자열
        - datetime 입력은 date로 변환합니다.
        """
        if v is None:
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                # YYYYMMDD
                if len(s) == 8 and s.isdigit():
                    return datetime.strptime(s, "%Y%m%d").date()
                # YYYY-MM-DD
                if len(s) == 10 and s[4] == "-" and s[7] == "-":
                    return datetime.strptime(s, "%Y-%m-%d").date()
                # YYYY/MM/DD
                if len(s) == 10 and s[4] == "/" and s[7] == "/":
                    return datetime.strptime(s, "%Y/%m/%d").date()
                # ISO datetime 문자열 처리 (예: 2025-10-25T12:34:56Z)
                iso = s.replace("Z", "+00:00")
                return datetime.fromisoformat(iso).date()
            except Exception:
                raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 또는 YYYYMMDD 형식을 사용하세요.")
        # 그 외 타입은 그대로 반환 (pydantic에 위임)
        return v


class AuditRequest(BaseModel):
    """감사 로그 요청"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    action_type: Optional[AuditActionType] = Field(
        None,
        description="필터링할 액션 타입",
        json_schema_extra={
            "examples": [
                "login",
                "logout",
                "send_email",
                "read_email",
                "delete_email",
                "create_user",
                "update_user",
                "delete_user",
                "update_settings"
            ]
        }
    )
    user_email: Optional[str] = None
    page: int = 1
    page_size: int = 20


class DashboardRequest(BaseModel):
    """대시보드 요청"""
    refresh: bool = False
    refresh_cache: bool = False
    include_performance: bool = True
    include_alerts: bool = True