"""
모니터링 서비스
- 사용량 통계 수집 및 분석
- 감사 로그 관리
- 대시보드 데이터 생성
"""

import logging
import psutil
import redis
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_

from ..model.user_model import User
from ..model.organization_model import Organization, OrganizationUsage
from ..model.mail_model import Mail, MailUser, MailLog
from ..schemas.monitoring_schema import (
    UsageResponse, UsageMetrics, DailyUsageStats, WeeklyUsageStats, MonthlyUsageStats,
    AuditResponse, AuditLogEntry, AuditActionType,
    DashboardResponse, DashboardData, SystemHealthMetrics, OrganizationSummary,
    UsageRequest, AuditRequest, DashboardRequest
)
from ..config import settings

logger = logging.getLogger(__name__)


class MonitoringService:
    """모니터링 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Redis 연결 테스트
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패: {str(e)}")
            self.redis_client = None

    def get_usage_statistics(self, org_id: str, request: UsageRequest) -> UsageResponse:
        """
        조직별 사용량 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            request: 사용량 통계 요청
            
        Returns:
            UsageResponse: 사용량 통계 응답
        """
        try:
            logger.info(f"📊 사용량 통계 조회 시작 - 조직: {org_id}")
            
            # 조직 정보 조회
            organization = self.db.query(Organization).filter(
                Organization.org_id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"조직을 찾을 수 없습니다: {org_id}")
            
            # 현재 사용량 조회
            current_usage = self._get_current_usage(org_id)
            
            # 제한 정보
            limits = {
                "max_users": organization.max_users,
                "max_storage_gb": organization.max_storage_gb,
                "max_emails_per_day": organization.max_emails_per_day
            }
            
            # 사용률 계산
            usage_percentages = self._calculate_usage_percentages(current_usage, limits)
            
            # 기간별 통계
            daily_stats = self._get_daily_stats(org_id, request.start_date, request.end_date)
            weekly_stats = self._get_weekly_stats(org_id, request.start_date, request.end_date)
            monthly_stats = self._get_monthly_stats(org_id, request.start_date, request.end_date)
            
            logger.info(f"✅ 사용량 통계 조회 완료 - 조직: {org_id}")
            
            return UsageResponse(
                org_id=org_id,
                current_usage=current_usage,
                limits=limits,
                usage_percentages=usage_percentages,
                daily_stats=daily_stats,
                weekly_stats=weekly_stats,
                monthly_stats=monthly_stats
            )
            
        except Exception as e:
            logger.error(f"❌ 사용량 통계 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            raise

    def get_audit_logs(self, org_id: str, request: AuditRequest) -> AuditResponse:
        """
        조직별 감사 로그를 조회합니다.
        
        Args:
            org_id: 조직 ID
            request: 감사 로그 요청
            
        Returns:
            AuditResponse: 감사 로그 응답
        """
        try:
            logger.info(f"📋 감사 로그 조회 시작 - 조직: {org_id}")
            
            # 기본 쿼리 구성
            query = self.db.query(MailLog).filter(MailLog.org_id == org_id)
            
            # 필터 적용
            filters = {}
            
            if request.start_date:
                query = query.filter(MailLog.created_at >= request.start_date)
                filters["start_date"] = request.start_date.isoformat()
                
            if request.end_date:
                query = query.filter(MailLog.created_at <= request.end_date)
                filters["end_date"] = request.end_date.isoformat()
                
            if request.action:
                query = query.filter(MailLog.action == request.action.value)
                filters["action"] = request.action.value
                
            if request.user_id:
                query = query.filter(MailLog.user_id == request.user_id)
                filters["user_id"] = request.user_id
                
            if request.resource_type:
                query = query.filter(MailLog.resource_type == request.resource_type)
                filters["resource_type"] = request.resource_type
            
            # 총 개수 조회
            total = query.count()
            
            # 페이징 적용
            offset = (request.page - 1) * request.limit
            logs_data = query.order_by(MailLog.created_at.desc()).offset(offset).limit(request.limit).all()
            
            # AuditLogEntry로 변환
            logs = []
            for log in logs_data:
                user = self.db.query(User).filter(User.user_uuid == log.user_id).first()
                
                audit_entry = AuditLogEntry(
                    id=log.id,
                    org_id=log.org_id,
                    user_id=log.user_id,
                    user_email=user.email if user else None,
                    action=AuditActionType(log.action) if log.action else AuditActionType.API_ACCESS,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    details=log.details if hasattr(log, 'details') else {},
                    ip_address=log.ip_address if hasattr(log, 'ip_address') else None,
                    user_agent=log.user_agent if hasattr(log, 'user_agent') else None,
                    timestamp=log.created_at
                )
                logs.append(audit_entry)
            
            logger.info(f"✅ 감사 로그 조회 완료 - 조직: {org_id}, 총 {total}개")
            
            return AuditResponse(
                org_id=org_id,
                logs=logs,
                total=total,
                page=request.page,
                limit=request.limit,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"❌ 감사 로그 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            raise

    def get_dashboard_data(self, org_id: str, request: DashboardRequest) -> DashboardResponse:
        """
        조직별 대시보드 데이터를 조회합니다.
        
        Args:
            org_id: 조직 ID
            request: 대시보드 요청
            
        Returns:
            DashboardResponse: 대시보드 응답
        """
        try:
            logger.info(f"📊 대시보드 데이터 조회 시작 - 조직: {org_id}")
            
            # 시스템 건강 상태
            system_health = self._get_system_health()
            
            # 조직 요약
            organization_summary = self._get_organization_summary(org_id)
            
            # 최근 활동 (최근 10개)
            recent_activities = self._get_recent_activities(org_id, limit=10)
            
            # 실시간 통계
            realtime_stats = self._get_current_usage(org_id)
            
            # 알림 및 경고
            alerts, warnings = self._get_alerts_and_warnings(org_id)
            
            # 성능 메트릭 (최근 24시간)
            performance_metrics = []
            if request.include_performance:
                performance_metrics = self._get_performance_metrics(org_id)
            
            dashboard_data = DashboardData(
                system_health=system_health,
                organization_summary=organization_summary,
                recent_activities=recent_activities,
                realtime_stats=realtime_stats,
                alerts=alerts,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
            logger.info(f"✅ 대시보드 데이터 조회 완료 - 조직: {org_id}")
            
            return DashboardResponse(
                org_id=org_id,
                dashboard=dashboard_data,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ 대시보드 데이터 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            raise

    def _get_current_usage(self, org_id: str) -> UsageMetrics:
        """현재 사용량을 조회합니다."""
        try:
            # 오늘 날짜
            today = date.today()
            
            # 오늘 발송된 메일 수
            emails_sent = self.db.query(func.count(Mail.mail_id)).filter(
                and_(
                    Mail.org_id == org_id,
                    func.date(Mail.sent_at) == today
                )
            ).scalar() or 0
            
            # 오늘 수신된 메일 수 (받은편지함 기준)
            emails_received = self.db.query(func.count(Mail.mail_id)).filter(
                and_(
                    Mail.org_id == org_id,
                    func.date(Mail.received_at) == today
                )
            ).scalar() or 0
            
            # 사용된 저장 공간
            storage_used = self.db.query(func.sum(MailUser.storage_used_mb)).filter(
                MailUser.org_id == org_id
            ).scalar() or 0
            
            # 활성 사용자 수 (최근 24시간 내 활동)
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_users = self.db.query(func.count(func.distinct(User.user_uuid))).filter(
                and_(
                    User.org_id == org_id,
                    User.last_login_at >= yesterday
                )
            ).scalar() or 0
            
            # API 요청 수 (Redis에서 조회, 없으면 0)
            api_requests = 0
            if self.redis_client:
                try:
                    api_key = f"api_requests:{org_id}:{today.strftime('%Y-%m-%d')}"
                    api_requests = int(self.redis_client.get(api_key) or 0)
                except Exception:
                    pass
            
            return UsageMetrics(
                emails_sent=emails_sent,
                emails_received=emails_received,
                storage_used_mb=int(storage_used),
                active_users=active_users,
                api_requests=api_requests
            )
            
        except Exception as e:
            logger.error(f"❌ 현재 사용량 조회 오류: {str(e)}")
            return UsageMetrics()

    def _calculate_usage_percentages(self, usage: UsageMetrics, limits: Dict[str, Any]) -> Dict[str, float]:
        """사용률을 계산합니다."""
        percentages = {}
        
        # 저장 공간 사용률
        if limits.get("max_storage_gb", 0) > 0:
            max_storage_mb = limits["max_storage_gb"] * 1024
            percentages["storage"] = round((usage.storage_used_mb / max_storage_mb) * 100, 2)
        else:
            percentages["storage"] = 0
        
        # 일일 메일 발송 사용률
        if limits.get("max_emails_per_day", 0) > 0:
            percentages["daily_emails"] = round((usage.emails_sent / limits["max_emails_per_day"]) * 100, 2)
        else:
            percentages["daily_emails"] = 0
        
        # 사용자 수 사용률
        if limits.get("max_users", 0) > 0:
            percentages["users"] = round((usage.active_users / limits["max_users"]) * 100, 2)
        else:
            percentages["users"] = 0
        
        return percentages

    def _get_daily_stats(self, org_id: str, start_date: Optional[date], end_date: Optional[date]) -> List[DailyUsageStats]:
        """일일 통계를 조회합니다."""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # OrganizationUsage 테이블에서 조회
            usage_data = self.db.query(OrganizationUsage).filter(
                and_(
                    OrganizationUsage.org_id == org_id,
                    func.date(OrganizationUsage.usage_date) >= start_date,
                    func.date(OrganizationUsage.usage_date) <= end_date
                )
            ).order_by(OrganizationUsage.usage_date).all()
            
            daily_stats = []
            for usage in usage_data:
                daily_stat = DailyUsageStats(
                    date=usage.usage_date.date(),
                    emails_sent=usage.emails_sent_today,
                    emails_received=usage.emails_received_today,
                    storage_used_mb=usage.current_storage_gb * 1024,
                    active_users=usage.current_users,
                    api_requests=0,  # 추후 구현
                    peak_concurrent_users=0  # 추후 구현
                )
                daily_stats.append(daily_stat)
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"❌ 일일 통계 조회 오류: {str(e)}")
            return []

    def _get_weekly_stats(self, org_id: str, start_date: Optional[date], end_date: Optional[date]) -> List[WeeklyUsageStats]:
        """주간 통계를 조회합니다."""
        # 간단한 구현 - 실제로는 더 복잡한 집계 로직 필요
        return []

    def _get_monthly_stats(self, org_id: str, start_date: Optional[date], end_date: Optional[date]) -> List[MonthlyUsageStats]:
        """월간 통계를 조회합니다."""
        # 간단한 구현 - 실제로는 더 복잡한 집계 로직 필요
        return []

    def _get_system_health(self) -> SystemHealthMetrics:
        """시스템 건강 상태를 조회합니다."""
        try:
            # CPU 사용률
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 데이터베이스 연결 수 (추정)
            database_connections = 10  # 실제 구현 필요
            
            # Redis 연결 수
            redis_connections = 0
            if self.redis_client:
                try:
                    info = self.redis_client.info()
                    redis_connections = info.get('connected_clients', 0)
                except Exception:
                    pass
            
            # 메일 큐 크기 (추정)
            mail_queue_size = 0  # 실제 구현 필요
            
            return SystemHealthMetrics(
                cpu_usage=round(cpu_usage, 2),
                memory_usage=round(memory_usage, 2),
                disk_usage=round(disk_usage, 2),
                database_connections=database_connections,
                redis_connections=redis_connections,
                mail_queue_size=mail_queue_size
            )
            
        except Exception as e:
            logger.error(f"❌ 시스템 건강 상태 조회 오류: {str(e)}")
            return SystemHealthMetrics()

    def _get_organization_summary(self, org_id: str) -> OrganizationSummary:
        """조직 요약 정보를 조회합니다."""
        try:
            # 조직 정보
            org = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not org:
                raise ValueError(f"조직을 찾을 수 없습니다: {org_id}")
            
            # 총 사용자 수
            total_users = self.db.query(func.count(User.user_uuid)).filter(User.org_id == org_id).scalar() or 0
            
            # 활성 사용자 수 (최근 7일)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users = self.db.query(func.count(User.user_uuid)).filter(
                and_(
                    User.org_id == org_id,
                    User.last_login_at >= week_ago
                )
            ).scalar() or 0
            
            # 오늘 메일 수
            today = date.today()
            emails_today = self.db.query(func.count(Mail.mail_id)).filter(
                and_(
                    Mail.org_id == org_id,
                    func.date(Mail.sent_at) == today
                )
            ).scalar() or 0
            
            # 사용된 저장 공간
            storage_used = self.db.query(func.sum(MailUser.storage_used_mb)).filter(
                MailUser.org_id == org_id
            ).scalar() or 0
            
            # 마지막 활동 시간
            last_activity = self.db.query(func.max(User.last_login_at)).filter(
                User.org_id == org_id
            ).scalar()
            
            return OrganizationSummary(
                org_id=org_id,
                name=org.name,
                total_users=total_users,
                active_users=active_users,
                emails_today=emails_today,
                storage_used_mb=int(storage_used),
                last_activity=last_activity
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 요약 정보 조회 오류: {str(e)}")
            return OrganizationSummary(org_id=org_id, name="Unknown")

    def _get_recent_activities(self, org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 활동을 조회합니다."""
        try:
            logs = self.db.query(MailLog).filter(
                MailLog.org_id == org_id
            ).order_by(MailLog.created_at.desc()).limit(limit).all()
            
            activities = []
            for log in logs:
                user = self.db.query(User).filter(User.user_uuid == log.user_id).first()
                
                activity = {
                    "id": log.id,
                    "org_id": log.org_id,
                    "user_id": log.user_id,
                    "user_email": user.email if user else None,
                    "action": log.action if log.action else "api_access",
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": {},
                    "ip_address": None,
                    "user_agent": None,
                    "timestamp": log.created_at.isoformat() if log.created_at else None
                }
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"❌ 최근 활동 조회 오류: {str(e)}")
            return []

    def _get_alerts_and_warnings(self, org_id: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """알림과 경고를 조회합니다."""
        alerts = []
        warnings = []
        
        try:
            # 조직 정보 조회
            org = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not org:
                return alerts, warnings
            
            # 현재 사용량 조회
            current_usage = self._get_current_usage(org_id)
            
            # 저장 공간 경고 (80% 이상)
            if org.max_storage_gb > 0:
                storage_percent = (current_usage.storage_used_mb / (org.max_storage_gb * 1024)) * 100
                if storage_percent >= 90:
                    alerts.append({
                        "type": "storage",
                        "level": "critical",
                        "message": f"저장 공간 사용률이 {storage_percent:.1f}%입니다.",
                        "timestamp": datetime.utcnow()
                    })
                elif storage_percent >= 80:
                    warnings.append({
                        "type": "storage",
                        "level": "warning",
                        "message": f"저장 공간 사용률이 {storage_percent:.1f}%입니다.",
                        "timestamp": datetime.utcnow()
                    })
            
            # 일일 메일 발송 제한 경고 (80% 이상)
            if org.max_emails_per_day > 0:
                email_percent = (current_usage.emails_sent / org.max_emails_per_day) * 100
                if email_percent >= 90:
                    alerts.append({
                        "type": "email_limit",
                        "level": "critical",
                        "message": f"일일 메일 발송 제한의 {email_percent:.1f}%를 사용했습니다.",
                        "timestamp": datetime.utcnow()
                    })
                elif email_percent >= 80:
                    warnings.append({
                        "type": "email_limit",
                        "level": "warning",
                        "message": f"일일 메일 발송 제한의 {email_percent:.1f}%를 사용했습니다.",
                        "timestamp": datetime.utcnow()
                    })
            
        except Exception as e:
            logger.error(f"❌ 알림 및 경고 조회 오류: {str(e)}")
        
        return alerts, warnings

    def _get_performance_metrics(self, org_id: str) -> List[Dict[str, Any]]:
        """성능 메트릭을 조회합니다."""
        # 간단한 구현 - 실제로는 더 복잡한 메트릭 수집 필요
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "response_time_ms": 150,
                "throughput": 100,
                "error_rate": 0.1
            }
        ]