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
from ..schemas.mail_schema import (
    MailSearchRequest, MailSearchResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType, MailUserResponse
)
from ..service.auth_service import get_current_user
from ..middleware.tenant_middleware import get_current_org_id

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
        
        # 검색 조건 적용
        if search_request.query:
            search_term = f"%{search_request.query}%"
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
        
        # 읽지 않은 메일 쿼리 (조직별 필터링 추가)
        # 현재 MailRecipient 모델에 is_read 필드가 없으므로 모든 받은 메일을 반환
        query = db.query(Mail).join(
            MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
        ).join(
            MailRecipient, Mail.mail_uuid == MailRecipient.mail_uuid
        ).filter(
            and_(
                Mail.org_id == current_org_id,
                MailInFolder.folder_uuid == inbox_folder.folder_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
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
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
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
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
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
        
        # 수신자의 읽음 상태 확인 및 업데이트 (MailRecipient 모델에 is_read 필드가 없으므로 기본 처리)
        recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first()
        
        # 읽음 처리 로직은 추후 구현 필요 (현재는 기본값 반환)
        read_at = datetime.utcnow()  # 임시로 현재 시간 설정
        
        # 로그 기록
        log_entry = MailLog(
            action="read",
            details=f"메일 읽음 처리: {mail.subject}",
            mail_uuid=mail.mail_uuid,
            user_uuid=mail_user.user_uuid,
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
                "is_read": recipient.is_read if recipient else False
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
        
        # 읽지 않음 처리
        mail.read_at = None
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=current_user.user_uuid,
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
                "read_at": mail.read_at
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
                action="read",
                timestamp=current_time
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
            timestamp=datetime.utcnow()
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
            timestamp=datetime.utcnow()
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
        recipient_suggestions = db.query(MailRecipient.email).join(
            Mail, Mail.mail_uuid == MailRecipient.mail_uuid
        ).filter(
            and_(
                Mail.org_id == current_org_id,
                MailRecipient.email.ilike(f"%{query}%"),
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