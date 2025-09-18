from fastapi import APIRouter, HTTPException, Depends, Query, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database.base import get_db
from ..model.base_model import User
from ..model.mail_model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from ..schemas.mail_schema import (
    MailSearchRequest, MailSearchResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType
)
from ..service.auth_service import get_current_user

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 편의 기능
router = APIRouter(tags=["mail-convenience"])


@router.post("/search", response_model=MailSearchResponse, summary="메일 검색")
async def search_mails(
    search_request: MailSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 검색"""
    try:
        logger.info(f"User {current_user.email} is searching mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 기본 쿼리 - 사용자와 관련된 메일만
        query = db.query(Mail).filter(
            or_(
                Mail.sender_id == mail_user.id,
                Mail.id.in_(
                    db.query(MailRecipient.mail_id).filter(
                        MailRecipient.recipient_id == mail_user.id
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
            sender_ids = [user.id for user in sender_users]
            if sender_ids:
                query = query.filter(Mail.sender_id.in_(sender_ids))
            else:
                # 발신자가 없으면 빈 결과 반환
                query = query.filter(False)
        
        # 수신자 필터
        if search_request.recipient_email:
            recipient_mail_ids = db.query(MailRecipient.mail_id).filter(
                MailRecipient.email.ilike(f"%{search_request.recipient_email}%")
            ).all()
            mail_ids = [mail_id[0] for mail_id in recipient_mail_ids]
            if mail_ids:
                query = query.filter(Mail.id.in_(mail_ids))
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
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            sender_response = {
                "id": sender.id if sender else 0,
                "email": sender.email if sender else "Unknown",
                "display_name": sender.display_name if sender else "Unknown"
            }
            
            # 수신자 개수
            recipient_count = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).count()
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            # 현재 사용자의 읽음 상태 확인
            current_recipient = db.query(MailRecipient).filter(
                and_(
                    MailRecipient.mail_id == mail.id,
                    MailRecipient.recipient_id == mail_user.id
                )
            ).first()
            is_read = current_recipient.is_read if current_recipient else None
            
            mail_list.append({
                "id": mail.id,
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
        
        return MailSearchResponse(
            mails=mail_list,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error searching mails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 검색 중 오류가 발생했습니다: {str(e)}")


@router.get("/stats", response_model=MailStatsResponse, summary="메일 통계")
async def get_mail_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 통계 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching mail stats")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 보낸 메일 수
        sent_count = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.status == MailStatus.SENT
            )
        ).count()
        
        # 받은 메일 수 계산
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        received_count = 0
        unread_count = 0
        if inbox_folder:
            received_count = db.query(Mail).join(
                MailInFolder, Mail.id == MailInFolder.mail_id
            ).filter(
                MailInFolder.folder_id == inbox_folder.id
            ).count()
            
            # 읽지 않은 메일 수
            unread_count = db.query(Mail).join(
                MailInFolder, Mail.id == MailInFolder.mail_id
            ).join(
                MailRecipient, Mail.id == MailRecipient.mail_id
            ).filter(
                and_(
                    MailInFolder.folder_id == inbox_folder.id,
                    MailRecipient.recipient_id == mail_user.id,
                    MailRecipient.is_read == False
                )
            ).count()
        
        # 임시보관함 메일 수
        draft_count = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.status == MailStatus.DRAFT
            )
        ).count()
        
        # 휴지통 메일 수
        trash_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == FolderType.TRASH
            )
        ).first()
        
        trash_count = 0
        if trash_folder:
            trash_count = db.query(Mail).join(
                MailInFolder, Mail.id == MailInFolder.mail_id
            ).filter(
                MailInFolder.folder_id == trash_folder.id
            ).count()
        
        # 오늘 발송/수신 메일 수 계산
        today = datetime.now().date()
        today_sent = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.status == MailStatus.SENT,
                func.date(Mail.sent_at) == today
            )
        ).count()
        
        today_received = 0
        if inbox_folder:
            today_received = db.query(Mail).join(
                MailInFolder, Mail.id == MailInFolder.mail_id
            ).filter(
                and_(
                    MailInFolder.folder_id == inbox_folder.id,
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
        
        return MailStatsResponse(
            stats=stats,
            success=True,
            message="통계 조회 성공"
        )
        
    except Exception as e:
        logger.error(f"Error fetching mail stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/unread", response_model=APIResponse, summary="읽지 않은 메일만 조회")
async def get_unread_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 메일 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """읽지 않은 메일만 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching unread mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 받은편지함 폴더 조회
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
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
        
        # 읽지 않은 메일 쿼리
        query = db.query(Mail).join(
            MailInFolder, Mail.id == MailInFolder.mail_id
        ).join(
            MailRecipient, Mail.id == MailRecipient.mail_id
        ).filter(
            and_(
                MailInFolder.folder_id == inbox_folder.id,
                MailRecipient.recipient_id == mail_user.id,
                MailRecipient.is_read == False
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
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 현재 사용자의 읽음 상태 확인
            user_recipient = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            ).first()
            is_read = user_recipient.is_read if user_recipient else False
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            mail_list.append({
                "id": mail.id,
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
        
    except Exception as e:
        logger.error(f"Error fetching unread mails: {str(e)}")
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
    db: Session = Depends(get_db)
):
    """중요 표시된 메일 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching starred mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 중요 표시된 메일 쿼리 (우선순위가 HIGH인 메일)
        query = db.query(Mail).filter(
            and_(
                or_(
                    Mail.sender_id == mail_user.id,
                    Mail.id.in_(
                        db.query(MailRecipient.mail_id).filter(
                            MailRecipient.recipient_id == mail_user.id
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
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 현재 사용자의 읽음 상태 확인
            user_recipient = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            ).first()
            is_read = user_recipient.is_read if user_recipient else False
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            mail_list.append({
                "id": mail.id,
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
        
    except Exception as e:
        logger.error(f"Error fetching starred mails: {str(e)}")
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


@router.post("/{mail_id}/read", response_model=APIResponse, summary="메일 읽음 처리")
async def mark_mail_as_read(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 읽음 처리"""
    try:
        logger.info(f"User {current_user.email} is marking mail {mail_id} as read")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_id == mail_user.id
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 수신자의 읽음 상태 확인 및 업데이트
        recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first()
        
        if recipient and not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = datetime.utcnow()
            db.commit()
            
            # 로그 기록
            log_entry = MailLog(
                mail_id=mail.id,
                user_id=mail_user.id,
                action="read",
                status="success",
                message=f"메일 읽음 처리: {mail.subject}"
            )
            db.add(log_entry)
            db.commit()
            
            read_at = recipient.read_at
        elif recipient:
            read_at = recipient.read_at
        else:
            read_at = None
        
        return APIResponse(
            success=True,
            message="메일이 읽음 처리되었습니다.",
            data={
                "mail_id": mail.id,
                "read_at": read_at,
                "is_read": recipient.is_read if recipient else False
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking mail as read: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 읽음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/{mail_id}/unread", response_model=APIResponse, summary="메일 읽지 않음 처리")
async def mark_mail_as_unread(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 읽지 않음 처리"""
    try:
        logger.info(f"User {current_user.email} is marking mail {mail_id} as unread")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_id == mail_user.id
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 읽지 않음 처리
        mail.read_at = None
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_id=mail.id,
            user_id=current_user.id,
            action="unread",
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        
        return APIResponse(
            success=True,
            message="메일이 읽지 않음 처리되었습니다.",
            data={
                "mail_id": mail.id,
                "read_at": mail.read_at
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking mail as unread: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 읽지 않음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/mark-all-read", response_model=APIResponse, summary="모든 메일 읽음 처리")
async def mark_all_mails_as_read(
    folder_type: str = Query("inbox", description="폴더 타입 (inbox, sent, drafts, trash)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모든 메일 읽음 처리"""
    try:
        logger.info(f"User {current_user.email} is marking all mails as read in {folder_type}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더 타입에 따른 처리
        if folder_type == "inbox":
            # 받은편지함 폴더 조회
            folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.user_id == mail_user.id,
                    MailFolder.folder_type == FolderType.INBOX
                )
            ).first()
            
            if folder:
                # 받은편지함의 읽지 않은 메일들
                mails = db.query(Mail).join(
                    MailInFolder, Mail.id == MailInFolder.mail_id
                ).filter(
                    and_(
                        MailInFolder.folder_id == folder.id,
                        Mail.read_at.is_(None)
                    )
                ).all()
        
        elif folder_type == "sent":
            # 보낸 메일함의 읽지 않은 메일들
            mails = db.query(Mail).filter(
                and_(
                    Mail.sender_id == mail_user.id,
                    Mail.status == MailStatus.SENT,
                    Mail.read_at.is_(None)
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
                mail_id=mail.id,
                user_id=current_user.id,
                action="read",
                timestamp=current_time
            )
            db.add(log_entry)
        
        db.commit()
        
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
        logger.error(f"Error marking all mails as read: {str(e)}")
        return APIResponse(
            success=False,
            message=f"모든 메일 읽음 처리 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.post("/{mail_id}/star", response_model=APIResponse, summary="메일 중요 표시")
async def star_mail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 중요 표시"""
    try:
        logger.info(f"User {current_user.email} is starring mail {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_id == mail_user.id
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 중요 표시 (우선순위를 HIGH로 설정)
        mail.priority = MailPriority.HIGH
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_id=mail.id,
            user_id=current_user.id,
            action="star",
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        
        return APIResponse(
            success=True,
            message="메일이 중요 표시되었습니다.",
            data={
                "mail_id": mail.id,
                "priority": mail.priority
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error starring mail: {str(e)}")
        return APIResponse(
            success=False,
            message=f"메일 중요 표시 중 오류가 발생했습니다: {str(e)}",
            data={}
        )


@router.delete("/{mail_id}/star", response_model=APIResponse, summary="메일 중요 표시 해제")
async def unstar_mail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 중요 표시 해제"""
    try:
        logger.info(f"User {current_user.email} is unstarring mail {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        is_sender = mail.sender_id == mail_user.id
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.email == mail_user.email
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 중요 표시 해제 (우선순위를 NORMAL로 설정)
        mail.priority = MailPriority.NORMAL
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_id=mail.id,
            user_id=current_user.id,
            action="unstar",
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        
        return APIResponse(
            success=True,
            message="메일 중요 표시가 해제되었습니다.",
            data={
                "mail_id": mail.id,
                "priority": mail.priority
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error unstarring mail: {str(e)}")
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
    db: Session = Depends(get_db)
):
    """검색 자동완성"""
    try:
        logger.info(f"User {current_user.email} is getting search suggestions for: {query}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        suggestions = []
        
        # 제목 기반 제안
        subject_suggestions = db.query(Mail.subject).filter(
            and_(
                or_(
                    Mail.sender_id == mail_user.id,
                    Mail.id.in_(
                        db.query(MailRecipient.mail_id).filter(
                            MailRecipient.recipient_id == mail_user.id
                        )
                    )
                ),
                Mail.subject.ilike(f"%{query}%"),
                Mail.subject.is_not(None)
            )
        ).distinct().limit(limit // 2).all()
        
        for subject in subject_suggestions:
            if subject[0] and subject[0] not in suggestions:
                suggestions.append({
                    "type": "subject",
                    "text": subject[0],
                    "category": "제목"
                })
        
        # 발신자 기반 제안
        sender_suggestions = db.query(MailUser.email).join(
            Mail, Mail.sender_id == MailUser.id
        ).filter(
            and_(
                MailUser.email.ilike(f"%{query}%"),
                or_(
                    Mail.sender_id == mail_user.id,
                    Mail.id.in_(
                        db.query(MailRecipient.mail_id).filter(
                            MailRecipient.email == mail_user.email
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
        
        # 수신자 기반 제안
        recipient_suggestions = db.query(MailRecipient.email).join(
            Mail, Mail.id == MailRecipient.mail_id
        ).filter(
            and_(
                MailRecipient.email.ilike(f"%{query}%"),
                Mail.sender_id == mail_user.id
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
        
        return APIResponse(
            success=True,
            message="검색 제안 조회 성공",
            data={
                "suggestions": suggestions,
                "query": query,
                "total": len(suggestions)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        return APIResponse(
            success=False,
            message=f"검색 제안 조회 중 오류가 발생했습니다: {str(e)}",
            data={
                "suggestions": [],
                "query": query,
                "total": 0
            }
        )