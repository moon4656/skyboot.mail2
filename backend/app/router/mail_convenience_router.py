from fastapi import APIRouter, HTTPException, Depends, Query, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database.user import get_db
from ..model.user_model import User
from ..model.mail_model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from ..model.organization_model import Organization, OrganizationUsage, OrganizationSettings
from ..schemas.mail_schema import (
    MailSearchRequest, MailSearchResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType, MailUserResponse,
    OrgUsageTodayResponse, OrgUsageHistoryResponse, OrgDailyUsage,
    OrgTemplatesResponse, TemplateItem,
    SignatureResponse, SignatureUpdateRequest,
    LabelsResponse, LabelItem,
    OrgRulesResponse, RuleItem,
    ScheduleRequest, RescheduleRequest, ScheduleResponse, ScheduleDispatchResponse,
    FiltersResponse, SavedSearchItem, SavedSearchesResponse, DateRange,
    AttachmentItem, AttachmentsResponse, VirusScanRequest, VirusScanResponse, VirusScanResultItem, AttachmentPreviewResponse
)
from ..service.auth_service import get_current_user
from ..middleware.tenant_middleware import get_current_org_id
from ..service.mail_service import MailService
from ..service.virus_scan_service import get_virus_scanner
from ..config import settings
import json
import os
import base64
import hashlib
import mimetypes

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 편의 기능
router = APIRouter()


@router.post("/search", response_model=MailSearchResponse, summary="메일 검색")
async def search_mails(
    search_request: MailSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> MailSearchResponse:
    """메일 검색"""
    try:
        logger.info(f"📧 search_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 기본 쿼리 - 조직별 필터링 및 사용자와 관련된 메일만
        query = db.query(Mail).filter(
            Mail.org_id == current_org_id,
            or_(
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.mail_uuid.in_(
                db.query(MailRecipient.mail_uuid).filter(
                    MailRecipient.recipient_uuid == mail_user.user_uuid
                )
                )
            )
        )
        
        # 검색 조건 적용 (FTS + 부분일치 병행)
        if search_request.query:
            search_term = f"%{search_request.query}%"
            # PostgreSQL FTS: subject + body_text 결합하여 검색
            try:
                fts_vector = func.to_tsvector(
                    'simple',
                    func.concat(
                        func.coalesce(Mail.subject, ''),
                        ' ',
                        func.coalesce(Mail.body_text, '')
                    )
                )
                fts_query = func.plainto_tsquery('simple', search_request.query)
                query = query.filter(
                    or_(
                        fts_vector.op('@@')(fts_query),
                        Mail.subject.ilike(search_term),
                        Mail.body_text.ilike(search_term)
                    )
                )
            except Exception:
                # FTS 사용 불가 시 부분일치만 수행
                query = query.filter(
                    or_(
                        Mail.subject.ilike(search_term),
                        Mail.body_text.ilike(search_term)
                    )
                )
        
        # 발신자 필터
        if search_request.sender_email:
            sender_users = db.query(MailUser).filter(
                MailUser.email.ilike(f"%{search_request.sender_email}%")
            ).all()
            sender_uuids = [user.user_uuid for user in sender_users]
            if sender_uuids:
                query = query.filter(Mail.sender_uuid.in_(sender_uuids))
            else:
                # 발신자가 없으면 빈 결과 반환
                query = query.filter(False)
        
        # 수신자 필터
        if search_request.recipient_email:
            # 이메일로 MailUser를 찾고, 해당 user_uuid로 MailRecipient 검색
            recipient_users = db.query(MailUser).filter(
                MailUser.email.ilike(f"%{search_request.recipient_email}%")
            ).all()
            recipient_uuids = [user.user_uuid for user in recipient_users]
            
            if recipient_uuids:
                recipient_mail_uuids = db.query(MailRecipient.mail_uuid).filter(
                    MailRecipient.recipient_uuid.in_(recipient_uuids)
                ).all()
                mail_uuids = [mail_uuid[0] for mail_uuid in recipient_mail_uuids]
                if mail_uuids:
                    query = query.filter(Mail.mail_uuid.in_(mail_uuids))
                else:
                    # 수신자가 없으면 빈 결과 반환
                    query = query.filter(False)
            else:
                # 수신자가 없으면 빈 결과 반환
                query = query.filter(False)
        
        # 제목 필터
        if search_request.subject:
            query = query.filter(Mail.subject.ilike(f"%{search_request.subject}%"))
        
        # 날짜 범위 필터
        if search_request.date_from:
            query = query.filter(Mail.created_at >= search_request.date_from)

        if search_request.date_to:
            # 날짜 끝까지 포함하기 위해 하루 더함
            end_date = search_request.date_to + timedelta(days=1)
            query = query.filter(Mail.created_at < end_date)

        # 상태 필터
        if search_request.status:
            query = query.filter(Mail.status == search_request.status)

        # 폴더 타입 필터
        if search_request.folder_type:
            # 사용자의 해당 폴더 타입 폴더 조회
            user_folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.folder_type == search_request.folder_type
                )
            ).first()

            if user_folder:
                # 해당 폴더에 있는 메일들만 필터링
                folder_mail_uuids = db.query(MailInFolder.mail_uuid).filter(
                    MailInFolder.folder_uuid == user_folder.folder_uuid
                ).all()
                mail_uuids = [mail_uuid[0] for mail_uuid in folder_mail_uuids]
                if mail_uuids:
                    query = query.filter(Mail.mail_uuid.in_(mail_uuids))
                else:
                    # 폴더에 메일이 없으면 빈 결과 반환
                    query = query.filter(False)
            else:
                # 폴더가 없으면 빈 결과 반환
                query = query.filter(False)

        # 우선순위 필터
        if search_request.priority:
            query = query.filter(Mail.priority == search_request.priority)

        # 전체 개수
        total_count = query.count()

        # 기본 정렬: 최신순
        query = query.order_by(desc(Mail.created_at))

        # 페이지네이션
        page = search_request.page or 1
        limit = search_request.limit or 20
        offset = (page - 1) * limit
        mails = query.offset(offset).limit(limit).all()
        
        # 결과 구성
        mail_list = []
        for mail in mails:
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            if sender:
                sender_response = MailUserResponse(
                    user_uuid=sender.user_uuid,
                    email=sender.email,
                    display_name=sender.display_name,
                    is_active=sender.is_active,
                    created_at=sender.created_at,
                    updated_at=sender.updated_at
                )
            else:
                # 발신자가 없는 경우 None으로 설정
                sender_response = None
            
            # 수신자 개수
            recipient_count = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).count()
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            # 현재 사용자의 읽음 상태 확인 (MailRecipient 모델에 is_read 필드가 없으므로 기본값 사용)
            current_recipient = db.query(MailRecipient).filter(
                and_(
                    MailRecipient.mail_uuid == mail.mail_uuid,
                    MailRecipient.recipient_uuid == mail_user.user_uuid
                )
            ).first()
            is_read = False  # 기본값으로 설정 (추후 읽음 상태 추적 기능 구현 필요)
            
            mail_list.append({
                "id": mail.mail_uuid,
                "mail_uuid": mail.mail_uuid,
                "subject": mail.subject,
                "status": mail.status,
                "is_draft": mail.is_draft,
                "priority": mail.priority,
                "sent_at": mail.sent_at,
                "created_at": mail.created_at,
                "sender": sender_response,
                "recipient_count": recipient_count,
                "attachment_count": attachment_count,
                "is_read": is_read
            })
        
        # 총 페이지 수 계산
        total_pages = (total_count + limit - 1) // limit
        
        logger.info(f"✅ search_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 검색 결과: {len(mail_list)}개")
        
        return MailSearchResponse(
            mails=mail_list,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ search_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 검색 중 오류가 발생했습니다: {str(e)}")


@router.get("/stats", response_model=MailStatsResponse, summary="메일 통계")
async def get_mail_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> MailStatsResponse:
    """메일 통계 조회"""
    try:
        logger.info(f"📊 get_mail_stats 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 보낸 메일 수 (조직별 필터링 추가)
        sent_count = db.query(Mail).filter(
            and_(
                Mail.org_id == current_org_id,
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.SENT
            )
        ).count()
        
        # 받은 메일 수 계산
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        received_count = 0
        unread_count = 0
        if inbox_folder:
            received_count = db.query(Mail).join(
                MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
            ).filter(
                and_(
                    Mail.org_id == current_org_id,
                    MailInFolder.folder_uuid == inbox_folder.folder_uuid
                )
            ).count()
            
            # 읽지 않은 메일 수 (현재는 모든 받은 메일을 읽지 않음으로 처리)
            # TODO: 읽음 상태 추적을 위한 별도 테이블 필요
            unread_count = received_count
        
        # 임시보관함 메일 수 (조직별 필터링 추가)
        draft_count = db.query(Mail).filter(
            and_(
                Mail.org_id == current_org_id,
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.DRAFT
            )
        ).count()
        
        # 휴지통 메일 수
        trash_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.folder_type == FolderType.TRASH
            )
        ).first()
        
        trash_count = 0
        if trash_folder:
            trash_count = db.query(Mail).join(
                MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
            ).filter(
                and_(
                    Mail.org_id == current_org_id,
                    MailInFolder.folder_uuid == trash_folder.folder_uuid
                )
            ).count()
        
        # 오늘 발송/수신 메일 수 계산
        today = datetime.now().date()
        today_sent = db.query(Mail).filter(
            and_(
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.SENT,
                func.date(Mail.sent_at) == today
            )
        ).count()
        
        today_received = 0
        if inbox_folder:
            today_received = db.query(Mail).join(
                MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
            ).filter(
                and_(
                    MailInFolder.folder_uuid == inbox_folder.folder_uuid,
                    func.date(Mail.created_at) == today
                )
            ).count()
        
        from ..schemas.mail_schema import MailStats
        
        stats = MailStats(
            total_sent=sent_count,
            total_received=received_count,
            total_drafts=draft_count,
            unread_count=unread_count,
            today_sent=today_sent,
            today_received=today_received
        )
        
        logger.info(f"✅ get_mail_stats 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 보낸메일: {sent_count}, 받은메일: {received_count}")
        
        return MailStatsResponse(
            stats=stats,
            success=True,
            message="통계 조회 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_mail_stats 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 통계 조회 중 오류가 발생했습니다: {str(e)}")


# ------------------------------
# 조직 메일 사용량 관련 엔드포인트
# ------------------------------

@router.get("/usage", response_model=OrgUsageTodayResponse, summary="조직 오늘 발송 사용량")
async def get_org_usage_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> OrgUsageTodayResponse:
    """조직별로 오늘까지의 발송 통계를 제공합니다."""
    try:
        logger.info(f"📈 조직 오늘 사용량 조회 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")

        # 오늘 날짜 (UTC 기준)
        today = datetime.now().date()

        # 오늘 사용량 행들 조회 (동일 날짜의 중복 행이 있을 수 있어 합산/최대 사용)
        usage_rows = db.query(OrganizationUsage).filter(
            OrganizationUsage.org_id == current_org_id,
            func.date(OrganizationUsage.usage_date) == today
        ).all()

        emails_sent_today = sum(row.emails_sent_today or 0 for row in usage_rows) if usage_rows else 0
        emails_received_today = sum(row.emails_received_today or 0 for row in usage_rows) if usage_rows else 0
        total_emails_sent = max([row.total_emails_sent or 0 for row in usage_rows] or [0])
        total_emails_received = max([row.total_emails_received or 0 for row in usage_rows] or [0])
        current_users = max([row.current_users or 0 for row in usage_rows] or [0])
        current_storage_gb = max([row.current_storage_gb or 0 for row in usage_rows] or [0])

        # 조직의 일일 발송 제한 조회
        org = db.query(Organization).filter(Organization.org_id == current_org_id).first()
        daily_limit = org.max_emails_per_day if org else None

        usage_percent = None
        remaining_until_limit = None
        if daily_limit is not None and daily_limit > 0:
            try:
                usage_percent = round((emails_sent_today / daily_limit) * 100, 2)
            except Exception:
                usage_percent = 0.0
            remaining_until_limit = max(daily_limit - emails_sent_today, 0)

        usage = OrgDailyUsage(
            usage_date=datetime.now(),
            emails_sent_today=emails_sent_today,
            emails_received_today=emails_received_today,
            total_emails_sent=total_emails_sent,
            total_emails_received=total_emails_received,
            current_users=current_users,
            current_storage_gb=current_storage_gb
        )

        return OrgUsageTodayResponse(
            success=True,
            message="오늘 사용량 조회 성공",
            usage=usage,
            daily_limit=daily_limit,
            usage_percent=usage_percent,
            remaining_until_limit=remaining_until_limit
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 오늘 사용량 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"오늘 사용량 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/usage/history", response_model=OrgUsageHistoryResponse, summary="조직 발송 이력 통계")
async def get_org_usage_history(
    days: int = Query(30, ge=1, le=365, description="조회 일수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> OrgUsageHistoryResponse:
    """조직별 발송 이력 통계를 일별로 제공합니다."""
    try:
        logger.info(f"📈 조직 사용량 히스토리 조회 시작 - 조직: {current_org_id}, 일수: {days}")

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        usage_day = func.date(OrganizationUsage.usage_date)
        rows = db.query(
            usage_day.label('usage_day'),
            func.sum(OrganizationUsage.emails_sent_today).label('emails_sent_today'),
            func.sum(OrganizationUsage.emails_received_today).label('emails_received_today'),
            func.max(OrganizationUsage.total_emails_sent).label('total_emails_sent'),
            func.max(OrganizationUsage.total_emails_received).label('total_emails_received'),
            func.max(OrganizationUsage.current_users).label('current_users'),
            func.max(OrganizationUsage.current_storage_gb).label('current_storage_gb')
        ).filter(
            OrganizationUsage.org_id == current_org_id,
            usage_day >= start_date,
            usage_day <= today
        ).group_by(usage_day).order_by(usage_day.desc()).all()

        items: List[OrgDailyUsage] = []
        for r in rows:
            # usage_day는 date 객체이므로 해당 날짜의 00:00으로 변환
            usage_dt = datetime.combine(r.usage_day, datetime.min.time())
            items.append(OrgDailyUsage(
                usage_date=usage_dt,
                emails_sent_today=int(r.emails_sent_today or 0),
                emails_received_today=int(r.emails_received_today or 0),
                total_emails_sent=int(r.total_emails_sent or 0),
                total_emails_received=int(r.total_emails_received or 0),
                current_users=int(r.current_users or 0),
                current_storage_gb=int(r.current_storage_gb or 0)
            ))

        return OrgUsageHistoryResponse(
            success=True,
            message="사용량 히스토리 조회 성공",
            items=items,
            total=len(items)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용량 히스토리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용량 히스토리 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/unread", response_model=APIResponse, summary="읽지 않은 메일만 조회")
async def get_unread_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 메일 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> APIResponse:
    """읽지 않은 메일만 조회"""
    try:
        logger.info(f"📧 get_unread_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 받은편지함 폴더 조회 (조직별 필터링 추가)
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        if not inbox_folder:
            return APIResponse(
                success=True,
                message="받은편지함이 없습니다.",
                data={
                    "mails": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "pages": 0
                }
            )
        
        # 읽지 않은 메일 쿼리 (조직별 필터링 및 읽지 않은 상태 필터링 추가)
        # MailRecipient 조인 제거 - 받은편지함 API와 동일한 방식 사용
        query = db.query(Mail).join(
            MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
        ).filter(
            and_(
                Mail.org_id == current_org_id,
                MailInFolder.folder_uuid == inbox_folder.folder_uuid,
                MailInFolder.is_read == False  # 읽지 않은 메일만 필터링
            )
        )
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 결과 구성
        mail_list = []
        for mail in mails:
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 현재 사용자의 읽음 상태 확인 (MailInFolder에서)
            mail_in_folder = db.query(MailInFolder).filter(
                MailInFolder.mail_uuid == mail.mail_uuid,
                MailInFolder.user_uuid == mail_user.user_uuid
            ).first()
            is_read = mail_in_folder.is_read if mail_in_folder else False
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            mail_list.append({
                "id": mail.mail_uuid,
                "subject": mail.subject,
                "sender_email": sender_email,
                "to_emails": to_emails,
                "status": mail.status,
                "priority": mail.priority,
                "has_attachments": attachment_count > 0,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "is_read": is_read
            })
        
        logger.info(f"✅ get_unread_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 읽지않은메일: {len(mail_list)}개")
        
        return APIResponse(
            success=True,
            message="읽지 않은 메일 조회 성공",
            data={
                "mails": mail_list,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": (total_count + limit - 1) // limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_unread_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"읽지 않은 메일 조회 중 오류가 발생했습니다: {str(e)}",
            data={
                "mails": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
        )


@router.get("/starred", response_model=APIResponse, summary="중요 표시된 메일 조회")
async def get_starred_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 메일 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> APIResponse:
    """중요 표시된 메일 조회"""
    try:
        logger.info(f"⭐ get_starred_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 중요 표시된 메일 쿼리 (조직별 필터링 및 우선순위가 HIGH인 메일)
        query = db.query(Mail).filter(
            and_(
                Mail.org_id == current_org_id,
                or_(
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.mail_uuid.in_(
                        db.query(MailRecipient.mail_uuid).filter(
                            MailRecipient.recipient_uuid == mail_user.user_uuid
                        )
                    )
                ),
                Mail.priority == MailPriority.HIGH
            )
        )
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 결과 구성
        mail_list = []
        for mail in mails:
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 현재 사용자의 읽음 상태 확인
            user_recipient = db.query(MailRecipient).filter(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            ).first()
            # TODO: is_read 필드가 MailRecipient 모델에 없음 - 임시로 False 설정
            is_read = False  # user_recipient.is_read if user_recipient else False
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            mail_list.append({
                "id": mail.mail_uuid, 
                "subject": mail.subject,
                "sender_email": sender_email,
                "to_emails": to_emails,
                "status": mail.status,
                "priority": mail.priority,
                "has_attachments": attachment_count > 0,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "is_read": is_read
            })
        
        logger.info(f"✅ get_starred_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 중요메일: {len(mail_list)}개")
        
        return APIResponse(
            success=True,
            message="중요 표시된 메일 조회 성공",
            data={
                "mails": mail_list,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": (total_count + limit - 1) // limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_starred_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"중요 표시된 메일 조회 중 오류가 발생했습니다: {str(e)}",
            data={
                "mails": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
        )


@router.post("/{mail_uuid}/read", response_model=APIResponse, summary="메일 읽음 처리")
async def mark_mail_as_read(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> APIResponse:
    """메일 읽음 처리"""
    try:
        logger.info(f"📧 mark_mail_as_read 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 필터링 추가)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        
        if not mail:
            logger.warning(f"⚠️ 메일을 찾을 수 없음 - 조직: {current_org_id}, 메일UUID: {mail_uuid}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일을 찾을 수 없습니다")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_uuid == mail_user.user_uuid
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # MailInFolder 테이블에서 읽음 상태 업데이트
        mail_in_folder = db.query(MailInFolder).filter(
            and_(
                MailInFolder.mail_uuid == mail.mail_uuid,
                MailInFolder.user_uuid == mail_user.user_uuid
            )
        ).first()
        
        if not mail_in_folder:
            logger.warning(f"⚠️ MailInFolder 레코드를 찾을 수 없음 - 메일UUID: {mail_uuid}, 사용자UUID: {mail_user.user_uuid}")
            raise HTTPException(status_code=404, detail="메일 폴더 정보를 찾을 수 없습니다")
        
        # 읽음 상태 업데이트
        read_at = datetime.utcnow()
        mail_in_folder.is_read = True
        mail_in_folder.read_at = read_at
        
        # 수신자 정보 확인 (응답용)
        recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first()
        
        # 로그 기록
        log_entry = MailLog(
            action="read",
            details=f"메일 읽음 처리: {mail.subject}",
            mail_uuid=mail.mail_uuid,
            user_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            ip_address=None,  # TODO: 실제 IP 주소 추가
            user_agent=None   # TODO: 실제 User-Agent 추가
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"✅ mark_mail_as_read 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return APIResponse(
            success=True,
            message="메일이 읽음 처리되었습니다.",
            data={
                "mail_uuid": mail.mail_uuid,
                "read_at": read_at,
                "is_read": mail_in_folder.is_read
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ mark_mail_as_read 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 읽음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/{mail_uuid}/unread", response_model=APIResponse, summary="메일 읽지 않음 처리")
async def mark_mail_as_unread(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> APIResponse:
    """메일 읽지 않음 처리"""
    try:
        logger.info(f"📧 mark_mail_as_unread 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 격리)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_uuid == mail_user.user_uuid
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # MailInFolder 테이블에서 읽지 않음 상태 업데이트
        mail_in_folder = db.query(MailInFolder).filter(
            and_(
                MailInFolder.mail_uuid == mail.mail_uuid,
                MailInFolder.user_uuid == mail_user.user_uuid
            )
        ).first()
        
        if not mail_in_folder:
            logger.warning(f"⚠️ MailInFolder 레코드를 찾을 수 없음 - 메일UUID: {mail_uuid}, 사용자UUID: {mail_user.user_uuid}")
            raise HTTPException(status_code=404, detail="메일 폴더 정보를 찾을 수 없습니다")
        
        # 읽지 않음 상태 업데이트
        mail_in_folder.is_read = False
        mail_in_folder.read_at = None
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=current_user.user_uuid,
            org_id=current_org_id,
            action="unread",
            details=f"메일 읽지 않음 처리: {mail.subject}",
            ip_address=None,  # TODO: 실제 IP 주소 추가
            user_agent=None   # TODO: 실제 User-Agent 추가
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"✅ mark_mail_as_unread 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return APIResponse(
            success=True,
            message="메일이 읽지 않음 처리되었습니다.",
            data={
                "mail_uuid": mail.mail_uuid,
                "read_at": mail_in_folder.read_at,
                "is_read": mail_in_folder.is_read
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ mark_mail_as_unread 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 읽지 않음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/mark-all-read", response_model=APIResponse, summary="모든 메일 읽음 처리")
async def mark_all_mails_as_read(
    folder_type: str = Query("inbox", description="폴더 타입 (inbox, sent, drafts, trash)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> APIResponse:
    """모든 메일 읽음 처리"""
    try:
        logger.info(f"📧 mark_all_mails_as_read 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더: {folder_type}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더 타입에 따른 처리
        if folder_type == "inbox":
            # 받은편지함 폴더 조회
            folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.folder_type == FolderType.INBOX
                )
            ).first()
            
            if folder:
                # 받은편지함의 읽지 않은 메일들 (조직별 격리)
                mails = db.query(Mail).join(
                    MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
                ).filter(
                    and_(
                        MailInFolder.folder_uuid == folder.folder_uuid,
                        Mail.read_at.is_(None),
                        Mail.org_id == current_org_id
                    )
                ).all()
        
        elif folder_type == "sent":
            # 보낸 메일함의 읽지 않은 메일들 (조직별 격리)
            mails = db.query(Mail).filter(
                and_(
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.status == MailStatus.SENT,
                    Mail.read_at.is_(None),
                    Mail.org_id == current_org_id
                )
            ).all()
        
        else:
            return APIResponse(
                success=False,
                message="지원하지 않는 폴더 타입입니다.",
                data={}
            )
        
        # 모든 메일 읽음 처리
        updated_count = 0
        current_time = datetime.utcnow()
        
        for mail in mails:
            mail.read_at = current_time
            updated_count += 1
            
            # 로그 기록
            log_entry = MailLog(
                mail_uuid=mail.mail_uuid,
                user_uuid=current_user.user_uuid,
                org_id=current_org_id,
                action="read"
            )
            db.add(log_entry)
        
        db.commit()
        
        logger.info(f"✅ mark_all_mails_as_read 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더: {folder_type}, 처리된 메일 수: {updated_count}")
        
        return APIResponse(
            success=True,
            message=f"{updated_count}개의 메일이 읽음 처리되었습니다.",
            data={
                "updated_count": updated_count,
                "folder_type": folder_type
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ mark_all_mails_as_read 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더: {folder_type}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"모든 메일 읽음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/{mail_uuid}/star", response_model=APIResponse, summary="메일 중요 표시")
async def star_mail(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> APIResponse:
    """메일 중요 표시"""
    try:
        logger.info(f"📧 star_mail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 격리)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_uuid == mail_user.user_uuid
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 중요 표시 (우선순위를 HIGH로 설정)
        mail.priority = MailPriority.HIGH
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=current_user.user_uuid,
            action="star",
            details=f"메일 중요 표시 - 제목: {mail.subject}"
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"✅ star_mail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return APIResponse(
            success=True,
            message="메일이 중요 표시되었습니다.",
            data={
                "mail_uuid": mail.mail_uuid,
                "priority": mail.priority
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ star_mail 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 중요 표시 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.delete("/{mail_uuid}/star", response_model=APIResponse, summary="메일 중요 표시 해제")
async def unstar_mail(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> APIResponse:
    """메일 중요 표시 해제"""
    try:
        logger.info(f"📧 unstar_mail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 격리)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_uuid == mail_user.user_uuid
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 중요 표시 해제 (우선순위를 NORMAL로 설정)
        mail.priority = MailPriority.NORMAL
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=current_user.user_uuid,
            action="unstar",
            details=f"메일 중요 표시 해제 - 제목: {mail.subject}"
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"✅ unstar_mail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return APIResponse(
            success=True,
            message="메일 중요 표시가 해제되었습니다.",
            data={
                "mail_uuid": mail.mail_uuid,
                "priority": mail.priority
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ unstar_mail 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 중요 표시 해제 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.get("/search/suggestions", response_model=APIResponse, summary="검색 자동완성")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(10, ge=1, le=20, description="제안 개수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> APIResponse:
    """검색 자동완성"""
    try:
        logger.info(f"🔍 get_search_suggestions 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 검색어: {query}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        suggestions = []
        
        # 제목에서 검색 (조직별 필터링 추가)
        subject_suggestions = db.query(Mail.subject).filter(
            and_(
                Mail.org_id == current_org_id,
                or_(
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.mail_uuid.in_(
                        db.query(MailRecipient.mail_uuid).filter(
                            MailRecipient.recipient_uuid == mail_user.user_uuid
                        )
                    )
                ),
                Mail.subject.ilike(f"%{query}%")
            )
        ).distinct().limit(limit // 2).all()
        
        for subject in subject_suggestions:
            if subject[0] and subject[0] not in suggestions:
                suggestions.append({
                    "type": "subject",
                    "text": subject[0],
                    "category": "제목"
                })
        
        # 발신자 기반 제안 (조직별 필터링 추가)
        sender_suggestions = db.query(MailUser.email).join(
            Mail, Mail.sender_uuid == MailUser.user_uuid
        ).filter(
            and_(
                Mail.org_id == current_org_id,
                MailUser.email.ilike(f"%{query}%"),
                or_(
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.mail_uuid.in_(
                        db.query(MailRecipient.mail_uuid).filter(
                            MailRecipient.recipient_uuid == mail_user.user_uuid
                        )
                    )
                )
            )
        ).distinct().limit(limit // 2).all()
        
        for sender in sender_suggestions:
            if sender[0] and sender[0] not in [s["text"] for s in suggestions]:
                suggestions.append({
                    "type": "sender",
                    "text": sender[0],
                    "category": "발신자"
                })
        
        # 수신자 기반 제안 (조직별 필터링 추가)
        recipient_suggestions = db.query(MailRecipient.recipient_email).join(
            Mail, Mail.mail_uuid == MailRecipient.mail_uuid
        ).filter(
            and_(
                Mail.org_id == current_org_id,
                MailRecipient.recipient_email.ilike(f"%{query}%"),
                Mail.sender_uuid == mail_user.user_uuid
            )
        ).distinct().limit(limit // 2).all()
        
        for recipient in recipient_suggestions:
            if recipient[0] and recipient[0] not in [s["text"] for s in suggestions]:
                suggestions.append({
                    "type": "recipient",
                    "text": recipient[0],
                    "category": "수신자"
                })
        
        # 제한된 개수만 반환
        suggestions = suggestions[:limit]
        
        logger.info(f"✅ get_search_suggestions 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 검색어: {query}, 제안 수: {len(suggestions)}")
        
        return APIResponse(
            success=True,
            message="검색 제안 조회 성공",
            data={
                "suggestions": suggestions,
                "query": query,
                "total": len(suggestions)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_search_suggestions 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 검색어: {query}, 에러: {str(e)}")
        return APIResponse(
            success=False,
            message=f"검색 제안 조회 중 오류가 발생했습니다: {str(e)}",
            data={
                "suggestions": [],
                "query": query,
                "total": 0
            }
        )

# =========================
# 템플릿 / 서명 / 라벨 / 규칙
# =========================

@router.get("/templates", response_model=OrgTemplatesResponse, summary="조직 템플릿 조회")
async def get_org_templates(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> OrgTemplatesResponse:
    try:
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.org_id == current_org_id,
            OrganizationSettings.setting_key == "mail_templates"
        ).first()

        templates: List[TemplateItem] = []
        if setting and setting.setting_value:
            try:
                data = json.loads(setting.setting_value)
                for t in data or []:
                    templates.append(TemplateItem(**t))
            except Exception:
                logger.warning("⚠️ 템플릿 JSON 파싱 실패, 빈 목록 반환")

        return OrgTemplatesResponse(success=True, message="템플릿 조회 성공", templates=templates)
    except Exception as e:
        logger.error(f"❌ 템플릿 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return OrgTemplatesResponse(success=False, message=f"템플릿 조회 실패: {str(e)}", templates=[])


@router.get("/signatures", response_model=SignatureResponse, summary="조직/사용자 서명 조회")
async def get_signatures(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> SignatureResponse:
    try:
        # 사용자 메일 설정
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()

        # 조직 기본 서명
        org_sign_setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.org_id == current_org_id,
            OrganizationSettings.setting_key == "mail_default_signature"
        ).first()

        org_default = None
        if org_sign_setting and org_sign_setting.setting_value:
            org_default = org_sign_setting.setting_value

        return SignatureResponse(
            success=True,
            message="서명 조회 성공",
            org_default_signature=org_default,
            user_signature=mail_user.signature if mail_user else None
        )
    except Exception as e:
        logger.error(f"❌ 서명 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return SignatureResponse(success=False, message=f"서명 조회 실패: {str(e)}")


@router.get("/labels", response_model=LabelsResponse, summary="라벨 목록 조회")
async def get_labels(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> LabelsResponse:
    try:
        # 사용자 라벨(커스텀 폴더)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")

        folders = db.query(MailFolder).filter(
            MailFolder.org_id == current_org_id,
            MailFolder.user_uuid == mail_user.user_uuid,
            MailFolder.folder_type == FolderType.CUSTOM
        ).all()

        labels = [LabelItem(folder_uuid=f.folder_uuid, name=f.name) for f in folders]
        return LabelsResponse(success=True, message="라벨 조회 성공", labels=labels)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 라벨 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return LabelsResponse(success=False, message=f"라벨 조회 실패: {str(e)}", labels=[])


@router.get("/rules", response_model=OrgRulesResponse, summary="조직 규칙 조회")
async def get_org_rules(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> OrgRulesResponse:
    try:
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.org_id == current_org_id,
            OrganizationSettings.setting_key == "mail_rules"
        ).first()

        rules: List[RuleItem] = []
        if setting and setting.setting_value:
            try:
                data = json.loads(setting.setting_value)
                for r in data or []:
                    rules.append(RuleItem(**r))
            except Exception:
                logger.warning("⚠️ 규칙 JSON 파싱 실패, 빈 목록 반환")

        return OrgRulesResponse(success=True, message="규칙 조회 성공", rules=rules)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 규칙 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return OrgRulesResponse(success=False, message=f"규칙 조회 실패: {str(e)}", rules=[])

@router.get("/filters", response_model=FiltersResponse, summary="조직별 필터 제공")
async def get_org_filters(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> FiltersResponse:
    """조직 전체 메일 데이터 기반 필터 옵션 제공"""
    try:
        logger.info(f"🔍 get_org_filters 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")

        # 상태 목록
        status_rows = db.query(Mail.status).filter(Mail.org_id == current_org_id).distinct().all()
        statuses = []
        for (status,) in status_rows:
            # MailStatus Enum 호환 처리
            try:
                statuses.append(MailStatus(status))
            except Exception:
                # 알 수 없는 상태는 문자열로 무시
                pass

        # 우선순위 목록
        priority_rows = db.query(Mail.priority).filter(Mail.org_id == current_org_id).distinct().all()
        priorities = []
        for (priority,) in priority_rows:
            try:
                priorities.append(MailPriority(priority))
            except Exception:
                pass

        # 발신자 도메인 목록 (최대 50개)
        sender_emails = db.query(MailUser.email).join(Mail, Mail.sender_uuid == MailUser.user_uuid).\
            filter(Mail.org_id == current_org_id).distinct().all()
        domains = set()
        for (email,) in sender_emails:
            if email and '@' in email:
                domains.add(email.split('@')[-1].lower())
        sender_domains = sorted(list(domains))[:50]

        # 날짜 범위
        min_date = db.query(func.min(Mail.created_at)).filter(Mail.org_id == current_org_id).scalar()
        max_date = db.query(func.max(Mail.created_at)).filter(Mail.org_id == current_org_id).scalar()
        date_range = DateRange(min_date=min_date, max_date=max_date)

        return FiltersResponse(
            success=True,
            message="필터 조회 성공",
            statuses=statuses,
            priorities=priorities,
            sender_domains=sender_domains,
            date_range=date_range,
            has_attachments_options=[True, False]
        )
    except Exception as e:
        logger.error(f"❌ 필터 조회 실패 - 조직: {current_org_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"필터 조회 실패: {str(e)}")

@router.get("/saved-searches", response_model=SavedSearchesResponse, summary="조직 저장된 검색 조회")
async def get_saved_searches(
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> SavedSearchesResponse:
    """조직 설정에 저장된 검색 목록 제공"""
    try:
        logger.info(f"💾 get_saved_searches 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")

        settings = db.query(OrganizationSettings).filter(
            and_(
                OrganizationSettings.org_id == current_org_id,
                OrganizationSettings.setting_key == 'mail_saved_searches'
            )
        ).first()

        searches: List[SavedSearchItem] = []
        if settings and settings.setting_value:
            try:
                raw = json.loads(settings.setting_value)
                if isinstance(raw, list):
                    for item in raw:
                        try:
                            searches.append(SavedSearchItem(
                                search_id=item.get('search_id') or item.get('id') or '',
                                name=item.get('name') or '검색',
                                query=item.get('query'),
                                filters=item.get('filters') or {},
                                created_at=item.get('created_at')
                            ))
                        except Exception:
                            # 항목 파싱 실패 시 무시
                            continue
            except Exception:
                logger.warning("저장된 검색 설정 JSON 파싱 실패")

        return SavedSearchesResponse(success=True, message="저장된 검색 조회 성공", searches=searches)
    except Exception as e:
        logger.error(f"❌ 저장된 검색 조회 실패 - 조직: {current_org_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장된 검색 조회 실패: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 규칙 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return OrgRulesResponse(success=False, message=f"규칙 조회 실패: {str(e)}", rules=[])


# =========================
# 첨부파일 관리 (조직 단위)
# =========================

@router.get("/attachments", response_model=AttachmentsResponse, summary="조직 첨부파일 목록 조회")
async def list_attachments(
    filename: Optional[str] = Query(None, description="파일명 부분 일치"),
    content_type: Optional[str] = Query(None, description="MIME 타입 부분 일치"),
    mail_uuid: Optional[str] = Query(None, description="특정 메일 UUID로 필터"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> AttachmentsResponse:
    try:
        # 조직 단위로 첨부파일 조회 (Mail과 조인하여 org_id 기준으로 필터링)
        q = db.query(MailAttachment).join(Mail, Mail.mail_uuid == MailAttachment.mail_uuid).filter(
            Mail.org_id == current_org_id
        )

        if filename:
            q = q.filter(MailAttachment.filename.ilike(f"%{filename}%"))
        if content_type:
            q = q.filter(MailAttachment.content_type.ilike(f"%{content_type}%"))
        if mail_uuid:
            q = q.filter(MailAttachment.mail_uuid == mail_uuid)
        if date_from:
            q = q.filter(MailAttachment.created_at >= date_from)
        if date_to:
            q = q.filter(MailAttachment.created_at <= date_to)

        total = q.count()
        items = q.order_by(desc(MailAttachment.created_at)).offset((page - 1) * limit).limit(limit).all()

        attachments: List[AttachmentItem] = []
        for a in items:
            attachments.append(AttachmentItem(
                attachment_uuid=a.attachment_uuid,
                mail_uuid=a.mail_uuid,
                filename=a.filename,
                file_size=a.file_size,
                content_type=a.content_type,
                created_at=a.created_at
            ))

        total_pages = (total + limit - 1) // limit
        logger.info(f"✅ 첨부파일 목록 조회 - 조직: {current_org_id}, 사용자: {current_user.email}, 총 {total}건")
        return AttachmentsResponse(
            success=True,
            message="첨부파일 조회 성공",
            attachments=attachments,
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"❌ 첨부파일 목록 조회 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"첨부파일 목록 조회 실패: {str(e)}")


@router.post("/attachments/virus-scan", response_model=VirusScanResponse, summary="첨부파일 바이러스 검사")
async def virus_scan_attachments(
    req: VirusScanRequest,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> VirusScanResponse:
    """
    ClamAV를 사용하여 첨부파일 바이러스 검사를 수행합니다.
    
    - **attachment_uuids**: 검사할 첨부파일 UUID 목록
    - **engine**: ClamAV 또는 휴리스틱 검사 엔진 사용
    - **조직별 격리**: 조직 소속 첨부파일만 검사 가능
    - **자동 격리**: 감염된 파일 자동 격리 (설정 시)
    """
    try:
        if not settings.VIRUS_SCAN_ENABLED:
            raise HTTPException(status_code=503, detail="바이러스 검사 기능이 비활성화되어 있습니다")
        
        results: List[VirusScanResultItem] = []
        infected_count = 0
        
        # 바이러스 스캐너 인스턴스 가져오기
        virus_scanner = get_virus_scanner()
        
        logger.info(f"🦠 바이러스 검사 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 첨부파일 수: {len(req.attachment_uuids)}")

        for att_uuid in req.attachment_uuids:
            try:
                # 첨부파일 및 조직 소속 확인
                attachment = db.query(MailAttachment).filter(MailAttachment.attachment_uuid == att_uuid).first()
                if not attachment:
                    results.append(VirusScanResultItem(
                        attachment_uuid=att_uuid,
                        status="error",
                        engine="validation",
                        message="첨부파일을 찾을 수 없습니다",
                        sha256=None
                    ))
                    continue

                mail = db.query(Mail).filter(Mail.mail_uuid == attachment.mail_uuid).first()
                if not mail or mail.org_id != current_org_id:
                    results.append(VirusScanResultItem(
                        attachment_uuid=att_uuid,
                        status="error",
                        engine="validation",
                        message="권한이 없거나 다른 조직 소속 첨부파일입니다",
                        sha256=None
                    ))
                    continue

                if not attachment.file_path or not os.path.exists(attachment.file_path):
                    results.append(VirusScanResultItem(
                        attachment_uuid=att_uuid,
                        status="error",
                        engine="validation",
                        message="첨부파일이 서버에 존재하지 않습니다",
                        sha256=None
                    ))
                    continue

                # 파일 크기 확인
                file_size_mb = os.path.getsize(attachment.file_path) / (1024 * 1024)
                if file_size_mb > settings.VIRUS_SCAN_MAX_FILE_SIZE_MB:
                    results.append(VirusScanResultItem(
                        attachment_uuid=att_uuid,
                        status="error",
                        engine="validation",
                        message=f"파일 크기가 너무 큽니다 ({file_size_mb:.1f}MB > {settings.VIRUS_SCAN_MAX_FILE_SIZE_MB}MB)",
                        sha256=None
                    ))
                    continue

                # ClamAV 바이러스 검사 수행
                logger.info(f"🔍 바이러스 검사 수행 - 파일: {attachment.filename}, 크기: {file_size_mb:.1f}MB")
                scan_result = virus_scanner.scan_file(attachment.file_path)
                
                # 결과 변환
                if scan_result.error_message:
                    status = "error"
                    message = scan_result.error_message
                elif scan_result.is_infected:
                    status = "infected"
                    message = f"바이러스 발견: {scan_result.virus_name}"
                    infected_count += 1
                    
                    # 감염된 파일 로깅
                    logger.warning(f"🦠 바이러스 발견 - 조직: {current_org_id}, 파일: {attachment.filename}, 바이러스: {scan_result.virus_name}")
                else:
                    status = "clean"
                    message = None

                results.append(VirusScanResultItem(
                    attachment_uuid=att_uuid,
                    status=status,
                    engine=scan_result.engine,
                    message=message,
                    sha256=scan_result.file_hash
                ))
                
            except Exception as inner_e:
                logger.error(f"❌ 첨부파일 바이러스 검사 중 오류 - 첨부UUID: {att_uuid}, 에러: {str(inner_e)}")
                results.append(VirusScanResultItem(
                    attachment_uuid=att_uuid,
                    status="error",
                    engine="system_error",
                    message=f"검사 중 오류 발생: {str(inner_e)}",
                    sha256=None
                ))

        # 검사 완료 로깅
        logger.info(f"✅ 바이러스 검사 완료 - 조직: {current_org_id}, 총 파일: {len(req.attachment_uuids)}, 감염: {infected_count}")
        
        return VirusScanResponse(
            success=True,
            message=f"바이러스 검사 완료 - 총 {len(req.attachment_uuids)}개 파일 중 {infected_count}개 감염",
            results=results,
            infected_count=infected_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 바이러스 검사 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"바이러스 검사 실패: {str(e)}")


@router.get("/attachments/preview", response_model=AttachmentPreviewResponse, summary="첨부파일 미리보기")
async def preview_attachment(
    attachment_uuid: str = Query(..., description="첨부파일 UUID"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> AttachmentPreviewResponse:
    try:
        attachment = db.query(MailAttachment).filter(MailAttachment.attachment_uuid == attachment_uuid).first()
        if not attachment:
            raise HTTPException(status_code=404, detail="첨부파일을 찾을 수 없습니다")

        mail = db.query(Mail).filter(Mail.mail_uuid == attachment.mail_uuid).first()
        if not mail or mail.org_id != current_org_id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

        if not attachment.file_path or not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="첨부파일이 서버에 존재하지 않습니다")

        # 콘텐츠 타입 확인 및 보완
        content_type = attachment.content_type or mimetypes.guess_type(attachment.filename)[0]

        preview_type = "unsupported"
        preview_text = None
        preview_data_url = None

        try:
            if content_type and content_type.startswith("text/"):
                # 텍스트 파일은 앞부분만 읽어 미리보기 제공 (최대 32KB)
                with open(attachment.file_path, "rb") as f:
                    blob = f.read(32 * 1024)
                # 인코딩 추정 없이 UTF-8 우선, 실패 시 cp949/latin-1 시도
                for enc in ["utf-8", "cp949", "latin-1"]:
                    try:
                        preview_text = blob.decode(enc)
                        preview_type = "text"
                        break
                    except Exception:
                        continue
            elif content_type and content_type.startswith("image/"):
                with open(attachment.file_path, "rb") as f:
                    blob = f.read()
                b64 = base64.b64encode(blob).decode("ascii")
                preview_data_url = f"data:{content_type};base64,{b64}"
                preview_type = "image"
            else:
                preview_type = "unsupported"
        except Exception as p_err:
            logger.warning(f"⚠️ 미리보기 처리 중 오류 - 첨부UUID: {attachment_uuid}, 에러: {str(p_err)}")
            preview_type = "unsupported"

        download_url = f"/api/v1/mail/attachments/{attachment.attachment_uuid}"
        return AttachmentPreviewResponse(
            success=True,
            message="미리보기 제공",
            attachment_uuid=attachment.attachment_uuid,
            filename=attachment.filename,
            content_type=content_type,
            preview_type=preview_type,
            preview_text=preview_text,
            preview_data_url=preview_data_url,
            download_url=download_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 첨부파일 미리보기 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"첨부파일 미리보기 실패: {str(e)}")


# =========================
# 예약 설정 / 예약 발송 처리
# =========================

@router.post("/reschedule", response_model=ScheduleResponse, summary="예약 메일 재설정")
async def reschedule_mail(
    req: RescheduleRequest,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> ScheduleResponse:
    try:
        # 메일 존재 확인 (조직 격리)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == req.mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")

        # 스케줄 설정 읽기
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.org_id == current_org_id,
            OrganizationSettings.setting_key == "mail_schedules"
        ).first()

        schedules: List[Dict[str, Any]] = []
        if setting and setting.setting_value:
            try:
                schedules = json.loads(setting.setting_value) or []
            except Exception:
                schedules = []

        # 기존 항목 업데이트 또는 추가
        updated = False
        for s in schedules:
            if s.get("mail_uuid") == req.mail_uuid:
                s["scheduled_at"] = req.scheduled_at.isoformat()
                updated = True
                break
        if not updated:
            schedules.append({"mail_uuid": req.mail_uuid, "scheduled_at": req.scheduled_at.isoformat()})

        # 저장
        if not setting:
            setting = OrganizationSettings(
                org_id=current_org_id,
                setting_key="mail_schedules",
                setting_type="json",
                setting_value=json.dumps(schedules, ensure_ascii=False)
            )
            db.add(setting)
        else:
            setting.setting_value = json.dumps(schedules, ensure_ascii=False)
        db.commit()

        return ScheduleResponse(success=True, message="예약 재설정 성공", mail_uuid=req.mail_uuid, scheduled_at=req.scheduled_at)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 예약 재설정 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return ScheduleResponse(success=False, message=f"예약 재설정 실패: {str(e)}", mail_uuid=req.mail_uuid, scheduled_at=req.scheduled_at)


@router.post("/schedule", response_model=ScheduleDispatchResponse, summary="예약 메일 발송 처리")
async def process_scheduled_mails(
    limit: int = Query(50, description="최대 처리 메일 수"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> ScheduleDispatchResponse:
    try:
        now = datetime.utcnow()
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.org_id == current_org_id,
            OrganizationSettings.setting_key == "mail_schedules"
        ).first()

        schedules: List[Dict[str, Any]] = []
        if setting and setting.setting_value:
            try:
                schedules = json.loads(setting.setting_value) or []
            except Exception:
                schedules = []

        # 처리 대상 선정
        ready: List[Dict[str, Any]] = []
        pending: List[Dict[str, Any]] = []
        for s in schedules:
            try:
                ts = datetime.fromisoformat(s.get("scheduled_at"))
            except Exception:
                ts = None
            if ts and ts <= now and len(ready) < limit:
                ready.append(s)
            else:
                pending.append(s)

        processed = 0
        mail_service = MailService(db=db)

        for s in ready:
            mail_uuid = s.get("mail_uuid")
            if not mail_uuid:
                continue

            mail = db.query(Mail).filter(
                Mail.mail_uuid == mail_uuid,
                Mail.org_id == current_org_id
            ).first()
            if not mail:
                logger.warning(f"⚠️ 예약 메일을 찾을 수 없음: {mail_uuid}")
                continue

            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            if not sender:
                logger.warning(f"⚠️ 발신자 정보를 찾을 수 없음: {mail_uuid}")
                continue

            recips = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            recipient_emails = [r.recipient_email for r in recips]

            atts = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
            attachments = [
                {"file_path": a.file_path, "filename": a.filename}
                for a in atts if a.file_path
            ]

            result = await mail_service.send_email_smtp(
                sender_email=sender.email,
                recipient_emails=recipient_emails,
                subject=mail.subject or "(제목 없음)",
                body_text=mail.body_text or "",
                body_html=mail.body_html,
                org_id=current_org_id,
                attachments=attachments
            )

            if result.get("success"):
                # 상태 갱신
                mail.status = MailStatus.SENT
                mail.sent_at = datetime.utcnow()
                db.add(mail)
                processed += 1
            else:
                logger.error(f"❌ 예약 메일 발송 실패 - {mail_uuid}: {result}")

        # 스케줄 목록 갱신 (처리된 항목 제거)
        remaining = [s for s in pending]
        setting_value = json.dumps(remaining, ensure_ascii=False)
        if not setting:
            setting = OrganizationSettings(
                org_id=current_org_id,
                setting_key="mail_schedules",
                setting_type="json",
                setting_value=setting_value
            )
            db.add(setting)
        else:
            setting.setting_value = setting_value

        db.commit()

        return ScheduleDispatchResponse(success=True, message="예약 메일 발송 완료", processed_count=processed)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 예약 메일 발송 처리 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return ScheduleDispatchResponse(success=False, message=f"예약 메일 발송 처리 실패: {str(e)}", processed_count=0)


@router.get("/logs", summary="메일 로그 조회")
async def get_mail_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
):
    """
    사용자의 메일 로그를 조회합니다.
    
    Args:
        page: 페이지 번호 (기본값: 1)
        limit: 페이지당 항목 수 (기본값: 20, 최대: 100)
        current_user: 현재 사용자
        db: 데이터베이스 세션
        current_org_id: 현재 조직 ID
    
    Returns:
        메일 로그 목록과 페이지네이션 정보
    """
    try:
        logger.info(f"📊 메일 로그 조회 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 페이지: {page}")
        
        # 오프셋 계산
        offset = (page - 1) * limit
        
        # 메일 로그 조회 (조직별 필터링)
        logs_query = db.query(MailLog).filter(
            MailLog.org_id == current_org_id,
            MailLog.user_uuid == current_user.user_uuid
        ).order_by(desc(MailLog.created_at))
        
        # 전체 개수 조회
        total_count = logs_query.count()
        
        # 페이지네이션 적용
        logs = logs_query.offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        log_items = []
        for log in logs:
            log_items.append({
                "id": log.id,
                "mail_id": log.mail_uuid,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        
        response_data = {
            "success": True,
            "data": {
                "logs": log_items,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "page_size": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            },
            "message": "메일 로그 조회 성공"
        }
        
        logger.info(f"✅ 메일 로그 조회 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 로그 수: {len(log_items)}")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ 메일 로그 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"메일 로그 조회 실패: {str(e)}"
        )


@router.get("/logs/{mail_id}", summary="특정 메일 로그 조회")
async def get_mail_log(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
):
    """
    특정 메일의 로그를 조회합니다.
    
    Args:
        mail_id: 메일 ID
        current_user: 현재 사용자
        db: 데이터베이스 세션
        current_org_id: 현재 조직 ID
    
    Returns:
        특정 메일의 로그 정보
    """
    try:
        logger.info(f"📊 특정 메일 로그 조회 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일ID: {mail_id}")
        
        # 메일 로그 조회 (조직별 필터링)
        logs = db.query(MailLog).filter(
            MailLog.org_id == current_org_id,
            MailLog.user_uuid == current_user.user_uuid,
            MailLog.mail_uuid == mail_id
        ).order_by(desc(MailLog.created_at)).all()
        
        if not logs:
            raise HTTPException(
                status_code=404,
                detail="해당 메일의 로그를 찾을 수 없습니다."
            )
        
        # 응답 데이터 구성
        log_items = []
        for log in logs:
            log_items.append({
                "id": log.id,
                "mail_id": log.mail_uuid,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        response_data = {
            "success": True,
            "data": {
                "mail_id": mail_id,
                "logs": log_items
            },
            "message": "메일 로그 조회 성공"
        }
        
        logger.info(f"✅ 특정 메일 로그 조회 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일ID: {mail_id}, 로그 수: {len(log_items)}")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 특정 메일 로그 조회 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일ID: {mail_id}, 에러: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"메일 로그 조회 실패: {str(e)}"
        )