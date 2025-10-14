"""
모니터링 관련 스키마 정의
"""
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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


class AuditRequest(BaseModel):
    """감사 로그 요청"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    action_type: Optional[AuditActionType] = None
    user_email: Optional[str] = None
    page: int = 1
    page_size: int = 20


class DashboardRequest(BaseModel):
    """대시보드 요청"""
    refresh: bool = False
    refresh_cache: bool = False
    include_performance: bool = True
    include_alerts: bool = True