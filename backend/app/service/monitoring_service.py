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

from ..model.user_model import User, LoginLog
from ..model.organization_model import Organization, OrganizationUsage
from ..model.mail_model import (
    Mail,
    MailUser,
    MailLog,
    MailFolder,
    MailInFolder,
    FolderType,
)
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
        조직별 사용량 통계를 조회하여 스키마(UsageResponse)에 맞춰 반환합니다.
        """
        try:
            logger.info(f"📊 사용량 통계 조회 시작 - 조직: {org_id}")

            # 조직 확인 (제한값 포함)
            organization = self.db.query(Organization).filter(
                Organization.org_id == org_id
            ).first()
            if not organization:
                raise ValueError(f"조직을 찾을 수 없습니다: {org_id}")

            # 현재 메트릭 계산 (스키마 호환)
            current_metrics = self._get_current_metrics(org_id, organization)

            # 기간별 통계
            daily_stats = self._get_daily_stats(org_id, request.start_date, request.end_date)
            weekly_stats = self._get_weekly_stats(org_id, request.start_date, request.end_date)
            monthly_stats = self._get_monthly_stats(org_id, request.start_date, request.end_date)

            logger.info(f"✅ 사용량 통계 조회 완료 - 조직: {org_id}")

            return UsageResponse(
                current_metrics=current_metrics,
                daily_stats=daily_stats,
                weekly_stats=weekly_stats,
                monthly_stats=monthly_stats,
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

            # MailLog 액션 문자열 ↔ 스키마 Enum 매핑
            enum_to_maillog = {
                AuditActionType.SEND_EMAIL: "send",
                AuditActionType.READ_EMAIL: "read",
                AuditActionType.DELETE_EMAIL: "delete",
            }
            maillog_to_enum = {
                "send": AuditActionType.SEND_EMAIL,
                "read": AuditActionType.READ_EMAIL,
                "delete": AuditActionType.DELETE_EMAIL,
            }

            # 날짜 범위 계산
            start_dt: Optional[datetime] = None
            end_dt: Optional[datetime] = None
            if request.start_date:
                start_dt = datetime.combine(request.start_date, datetime.min.time())
            if request.end_date:
                end_dt = datetime.combine(request.end_date, datetime.min.time()) + timedelta(days=1)

            logs: List[AuditLogEntry] = []
            total: int = 0

            # 1) LOGIN/LOGOUT 요청은 LoginLog에서 조회 (조직 필터 포함)
            if request.action_type in {AuditActionType.LOGIN, AuditActionType.LOGOUT}:
                # 로그인 로그에는 org_id가 없으므로 사용자 조인을 통해 조직 필터 적용
                # 실패 로그의 경우 user_uuid가 없을 수 있으므로 user_id/email 매핑도 포함
                login_query = self.db.query(LoginLog).join(
                    User,
                    or_(
                        LoginLog.user_uuid == User.user_uuid,
                        LoginLog.user_id == User.user_id,
                        LoginLog.user_id == User.email,
                    )
                ).filter(User.org_id == org_id)

                if start_dt:
                    login_query = login_query.filter(LoginLog.created_at >= start_dt)
                if end_dt:
                    login_query = login_query.filter(LoginLog.created_at < end_dt)
                if request.user_email:
                    login_query = login_query.filter(User.email == request.user_email)

                total = login_query.count()
                offset = (request.page - 1) * request.page_size
                login_logs = (
                    login_query.order_by(LoginLog.created_at.desc())
                    .offset(offset)
                    .limit(request.page_size)
                    .all()
                )

                for log in login_logs:
                    # 조인된 User로 이메일 추출
                    user = self.db.query(User).filter(User.user_uuid == log.user_uuid).first()
                    details: Dict[str, Any] = {
                        "status": getattr(log, "login_status", None),
                        "failure_reason": getattr(log, "failure_reason", None),
                    }
                    logs.append(
                        AuditLogEntry(
                            id=log.id,
                            action=AuditActionType.LOGIN if request.action_type == AuditActionType.LOGIN else AuditActionType.LOGOUT,
                            user_email=user.email if user else "",
                            ip_address=getattr(log, "ip_address", None),
                            user_agent=getattr(log, "user_agent", None),
                            details=details,
                            timestamp=log.created_at,
                        )
                    )

            else:
                # 2) 메일 관련 액션은 MailLog에서 조회
                mail_query = self.db.query(MailLog).filter(MailLog.org_id == org_id)
                if start_dt:
                    mail_query = mail_query.filter(MailLog.created_at >= start_dt)
                if end_dt:
                    mail_query = mail_query.filter(MailLog.created_at < end_dt)

                # 액션 타입 필터를 DB 저장 문자열로 변환하여 적용
                if request.action_type and request.action_type in enum_to_maillog:
                    mail_query = mail_query.filter(MailLog.action == enum_to_maillog[request.action_type])

                # 사용자 이메일 필터
                if request.user_email:
                    user = self.db.query(User).filter(User.email == request.user_email).first()
                    if user:
                        mail_query = mail_query.filter(MailLog.user_uuid == user.user_uuid)

                total = mail_query.count()
                offset = (request.page - 1) * request.page_size
                logs_data = (
                    mail_query.order_by(MailLog.created_at.desc())
                    .offset(offset)
                    .limit(request.page_size)
                    .all()
                )

                for log in logs_data:
                    user = self.db.query(User).filter(User.user_uuid == log.user_uuid).first()
                    # DB 문자열을 AuditActionType으로 매핑 (알 수 없는 값은 UPDATE_SETTINGS)
                    action_type = maillog_to_enum.get(getattr(log, "action", None), AuditActionType.UPDATE_SETTINGS)
                    details_obj = getattr(log, "details", {})
                    details = details_obj if isinstance(details_obj, dict) else {}
                    logs.append(
                        AuditLogEntry(
                            id=log.id,
                            action=action_type,
                            user_email=user.email if user else "",
                            ip_address=getattr(log, "ip_address", None),
                            user_agent=getattr(log, "user_agent", None),
                            details=details,
                            timestamp=log.created_at,
                        )
                    )

            logger.info(f"✅ 감사 로그 조회 완료 - 조직: {org_id}, 총 {total}개")

            return AuditResponse(
                logs=logs,
                total_count=total,
                page=request.page,
                page_size=request.page_size,
            )
            
        except Exception as e:
            logger.error(f"❌ 감사 로그 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            raise

    def get_dashboard_data(self, org_id: str, request: DashboardRequest) -> DashboardResponse:
        """
        조직별 대시보드 데이터를 조회합니다.
        스키마(monitoring_schema)와 필드명이 정확히 일치하도록 응답을 구성합니다.
        """
        try:
            logger.info(f"📊 대시보드 데이터 조회 시작 - 조직: {org_id}")

            # 시스템 건강 상태 (스키마 필드와 일치)
            system_health = self._get_system_health()

            # 조직 요약 (스키마 필드와 일치)
            organization_summary = self._get_organization_summary(org_id)

            # 최근 활동 (최근 10개)
            recent_activities = self._get_recent_activities(org_id, limit=10)

            # 알림 (문자열 메세지 리스트로 반환)
            alerts = self._get_alerts(org_id)

            # 성능 메트릭 (키-값 형태의 단일 딕셔너리)
            performance_metrics: Dict[str, float] = {}
            if request.include_performance:
                performance_metrics = self._get_performance_metrics(org_id)

            dashboard_data = DashboardData(
                organization_summary=organization_summary,
                system_health=system_health,
                recent_activities=recent_activities,
                alerts=alerts,
                performance_metrics=performance_metrics,
            )

            logger.info(f"✅ 대시보드 데이터 조회 완료 - 조직: {org_id}")

            return DashboardResponse(
                success=True,
                data=dashboard_data,
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"❌ 대시보드 데이터 조회 오류 - 조직: {org_id}, 오류: {str(e)}")
            # 실패 시 최소한의 기본 구조로 반환 (success=False)
            return DashboardResponse(
                success=False,
                data=DashboardData(
                    organization_summary=OrganizationSummary(
                        total_users=0,
                        active_users_today=0,
                        emails_sent_today=0,
                        storage_usage_percent=0.0,
                        user_usage_percent=0.0,
                    ),
                    system_health=SystemHealthMetrics(
                        cpu_usage_percent=0.0,
                        memory_usage_percent=0.0,
                        disk_usage_percent=0.0,
                        active_connections=0,
                        email_queue_size=0,
                    ),
                    recent_activities=[],
                    alerts=[],
                    performance_metrics={},
                ),
                last_updated=datetime.utcnow(),
            )

    def _get_current_metrics(self, org_id: str, organization: Organization) -> UsageMetrics:
        """스키마에 맞춘 현재 사용량 메트릭을 계산합니다."""
        try:
            today = date.today()

            # 오늘 발송 메일 수 (status=SENT, sent_at 날짜 기준)
            emails_sent_today = (
                self.db.query(func.count(Mail.mail_uuid))
                .filter(
                    and_(
                        Mail.org_id == org_id,
                        func.date(Mail.sent_at) == today,
                        Mail.status == 'sent',
                    )
                )
                .scalar()
                or 0
            )

            # 오늘 수신 메일 수 (조직 내 INBOX 폴더에 할당된 메일, created_at 날짜 기준)
            emails_received_today = (
                self.db.query(func.count(func.distinct(Mail.mail_uuid)))
                .join(MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid)
                .join(MailFolder, MailInFolder.folder_uuid == MailFolder.folder_uuid)
                .filter(
                    and_(
                        Mail.org_id == org_id,
                        MailFolder.org_id == org_id,
                        MailFolder.folder_type == FolderType.INBOX,
                        func.date(Mail.created_at) == today,
                    )
                )
                .scalar()
                or 0
            )

            # 저장 공간(GB)
            storage_used_mb = (
                self.db.query(func.sum(MailUser.storage_used_mb))
                .filter(MailUser.org_id == org_id)
                .scalar()
                or 0
            )
            storage_used_gb = float(storage_used_mb) / 1024.0

            # 활성 사용자 수(최근 24시간)
            yesterday = datetime.utcnow() - timedelta(days=1)
            current_users = (
                self.db.query(func.count(func.distinct(User.user_uuid)))
                .filter(and_(User.org_id == org_id, User.last_login_at >= yesterday))
                .scalar()
                or 0
            )

            # 제한값
            max_users = organization.max_users or 0
            storage_limit_gb = float(organization.max_storage_gb or 0)

            return UsageMetrics(
                current_users=current_users,
                max_users=max_users,
                emails_sent_today=emails_sent_today,
                emails_received_today=emails_received_today,
                storage_used_gb=round(storage_used_gb, 2),
                storage_limit_gb=storage_limit_gb,
            )

        except Exception as e:
            logger.error(f"❌ 현재 메트릭 계산 오류: {str(e)}")
            # 실패 시 기본값 반환
            return UsageMetrics(
                current_users=0,
                max_users=organization.max_users or 0,
                emails_sent_today=0,
                emails_received_today=0,
                storage_used_gb=0.0,
                storage_limit_gb=float(organization.max_storage_gb or 0),
            )

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
        """일일 통계를 조회합니다 (스키마 필드에 맞춰 반환)."""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            usage_data = (
                self.db.query(OrganizationUsage)
                .filter(
                    and_(
                        OrganizationUsage.org_id == org_id,
                        func.date(OrganizationUsage.usage_date) >= start_date,
                        func.date(OrganizationUsage.usage_date) <= end_date,
                    )
                )
                .order_by(OrganizationUsage.usage_date)
                .all()
            )

            daily_stats: List[DailyUsageStats] = []
            for usage in usage_data:
                daily_stats.append(
                    DailyUsageStats(
                        date=usage.usage_date.date(),
                        emails_sent=usage.emails_sent_today or 0,
                        emails_received=usage.emails_received_today or 0,
                        active_users=usage.current_users or 0,
                        storage_used_gb=float(usage.current_storage_gb or 0),
                    )
                )

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
        """시스템 건강 상태를 조회합니다 (스키마 필드에 정확히 맞춤)."""
        try:
            # CPU 사용률 (%)
            cpu_usage = psutil.cpu_percent(interval=1)

            # 메모리 사용률 (%)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # 디스크 사용률 (%)
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100

            # 활성 연결 수 (DB + Redis 등 합산, 실제 구현 시 교체)
            database_connections = 10  # TODO: 실제 연결 수로 교체
            redis_connections = 0
            if self.redis_client:
                try:
                    info = self.redis_client.info()
                    redis_connections = int(info.get('connected_clients', 0))
                except Exception:
                    pass
            active_connections = int(database_connections) + int(redis_connections)

            # 메일 큐 크기 (실제 구현 시 큐 시스템 조회)
            mail_queue_size = 0

            return SystemHealthMetrics(
                cpu_usage_percent=round(cpu_usage, 2),
                memory_usage_percent=round(memory_usage, 2),
                disk_usage_percent=round(disk_usage, 2),
                active_connections=active_connections,
                email_queue_size=mail_queue_size,
            )
        except Exception as e:
            logger.error(f"❌ 시스템 건강 상태 조회 오류: {str(e)}")
            return SystemHealthMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                email_queue_size=0,
            )

    def _get_organization_summary(self, org_id: str) -> OrganizationSummary:
        """조직 요약 정보를 조회합니다 (스키마 필드에 맞춤)."""
        try:
            org = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not org:
                raise ValueError(f"조직을 찾을 수 없습니다: {org_id}")

            # 총 사용자 수
            total_users = self.db.query(func.count(User.user_uuid)).filter(User.org_id == org_id).scalar() or 0

            # 오늘 활성 사용자 수 (오늘 날짜 기준 로그인 기록 보유)
            today_start = datetime.combine(date.today(), datetime.min.time())
            active_users_today = (
                self.db.query(func.count(User.user_uuid))
                .filter(and_(User.org_id == org_id, User.last_login_at >= today_start))
                .scalar()
                or 0
            )

            # 오늘 발송 메일 수
            emails_sent_today = (
                self.db.query(func.count(Mail.mail_id))
                .filter(and_(Mail.org_id == org_id, func.date(Mail.sent_at) == date.today()))
                .scalar()
                or 0
            )

            # 저장 공간 사용률 (%)
            storage_used_mb = (
                self.db.query(func.sum(MailUser.storage_used_mb)).filter(MailUser.org_id == org_id).scalar() or 0
            )
            max_storage_gb = float(getattr(org, "max_storage_gb", 0) or 0)
            storage_usage_percent = 0.0
            if max_storage_gb > 0:
                storage_usage_percent = round((float(storage_used_mb) / (max_storage_gb * 1024.0)) * 100.0, 2)

            # 사용자 수 사용률 (%)
            max_users = int(getattr(org, "max_users", 0) or 0)
            user_usage_percent = 0.0
            if max_users > 0:
                user_usage_percent = round((float(total_users) / float(max_users)) * 100.0, 2)

            return OrganizationSummary(
                total_users=total_users,
                active_users_today=active_users_today,
                emails_sent_today=emails_sent_today,
                storage_usage_percent=storage_usage_percent,
                user_usage_percent=user_usage_percent,
            )
        except Exception as e:
            logger.error(f"❌ 조직 요약 정보 조회 오류: {str(e)}")
            return OrganizationSummary(
                total_users=0,
                active_users_today=0,
                emails_sent_today=0,
                storage_usage_percent=0.0,
                user_usage_percent=0.0,
            )

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

    def _get_alerts(self, org_id: str) -> List[str]:
        """알림 메시지를 문자열 리스트로 반환합니다."""
        alerts: List[str] = []
        try:
            org = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not org:
                return alerts

            # 현재 사용량 조회
            current_usage = self._get_current_usage(org_id)

            # 저장 공간 경고 (80% 이상)
            if getattr(org, "max_storage_gb", 0) > 0:
                storage_percent = (current_usage.storage_used_mb / (org.max_storage_gb * 1024)) * 100
                if storage_percent >= 90:
                    alerts.append(f"[CRITICAL] 저장 공간 사용률 {storage_percent:.1f}%")
                elif storage_percent >= 80:
                    alerts.append(f"[WARNING] 저장 공간 사용률 {storage_percent:.1f}%")

            # 일일 메일 발송 제한 경고 (80% 이상)
            if getattr(org, "max_emails_per_day", 0) > 0:
                email_percent = (current_usage.emails_sent / org.max_emails_per_day) * 100
                if email_percent >= 90:
                    alerts.append(f"[CRITICAL] 일일 메일 발송 제한 {email_percent:.1f}% 사용")
                elif email_percent >= 80:
                    alerts.append(f"[WARNING] 일일 메일 발송 제한 {email_percent:.1f}% 사용")
        except Exception as e:
            logger.error(f"❌ 알림 조회 오류: {str(e)}")
        return alerts

    def _get_performance_metrics(self, org_id: str) -> Dict[str, float]:
        """성능 메트릭을 조회합니다 (키-값 딕셔너리)."""
        # 간단한 구현 - 실제로는 더 복잡한 메트릭 수집 필요
        return {
            "response_time_ms": 150.0,
            "throughput": 100.0,
            "error_rate": 0.1,
        }