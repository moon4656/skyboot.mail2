from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Form, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
from datetime import datetime, timedelta
import mimetypes
import logging
import json

from ..database.base import get_db
from ..model.base_model import User
from ..model.mail_model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from ..schemas.mail_schema import (
    MailCreate, MailResponse, MailListResponse, MailDetailResponse,
    MailSendRequest, MailSendResponse, MailSearchRequest, MailSearchResponse,
    MailListWithPaginationResponse, MailUserResponse,
    PaginationResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType
)
from ..service.mail_service import MailService
from ..service.auth_service import get_current_user

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 필수 기능
router = APIRouter(tags=["mail-core"])

# 보안 설정
security = HTTPBearer()

# 메일 서비스 초기화
mail_service = MailService()

# 첨부파일 저장 디렉토리
ATTACHMENT_DIR = "attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


@router.post("/send", response_model=MailSendResponse, summary="메일 발송")
async def send_mail(
    to_emails: str = Form(..., description="수신자 이메일 (쉼표로 구분)"),
    cc_emails: Optional[str] = Form(None, description="참조 이메일 (쉼표로 구분)"),
    bcc_emails: Optional[str] = Form(None, description="숨은참조 이메일 (쉼표로 구분)"),
    subject: str = Form(..., description="메일 제목"),
    content: str = Form(..., description="메일 내용"),
    priority: MailPriority = Form(MailPriority.NORMAL, description="메일 우선순위"),
    attachments: List[UploadFile] = File(None, description="첨부파일"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 발송 API"""
    try:
        logger.info(f"User {current_user.email} is sending mail to {to_emails}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 메일 생성
        mail = Mail(
            sender_id=mail_user.id,
            subject=subject,
            body_text=content,
            priority=priority,
            status=MailStatus.SENT,
            is_draft=False,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow()
        )
        
        db.add(mail)
        db.flush()
        
        # 수신자 처리
        recipients = []
        
        # TO 수신자
        if to_emails:
            for email in to_emails.split(','):
                email = email.strip()
                if email:
                    # 수신자 사용자 찾기 또는 생성
                    recipient_user = db.query(MailUser).filter(MailUser.email == email).first()
                    if not recipient_user:
                        # 외부 사용자인 경우 임시 사용자 생성
                        recipient_user = MailUser(
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient = MailRecipient(
                        mail_id=mail.id,
                        recipient_id=recipient_user.id,
                        recipient_type=RecipientType.TO
                    )
                    recipients.append(recipient)
                    db.add(recipient)
        
        # CC 수신자
        if cc_emails:
            for email in cc_emails.split(','):
                email = email.strip()
                if email:
                    # 수신자 사용자 찾기 또는 생성
                    recipient_user = db.query(MailUser).filter(MailUser.email == email).first()
                    if not recipient_user:
                        # 외부 사용자인 경우 임시 사용자 생성
                        recipient_user = MailUser(
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient = MailRecipient(
                        mail_id=mail.id,
                        recipient_id=recipient_user.id,
                        recipient_type=RecipientType.CC
                    )
                    recipients.append(recipient)
                    db.add(recipient)
        
        # BCC 수신자
        if bcc_emails:
            for email in bcc_emails.split(','):
                email = email.strip()
                if email:
                    # 수신자 사용자 찾기 또는 생성
                    recipient_user = db.query(MailUser).filter(MailUser.email == email).first()
                    if not recipient_user:
                        # 외부 사용자인 경우 임시 사용자 생성
                        recipient_user = MailUser(
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient = MailRecipient(
                        mail_id=mail.id,
                        recipient_id=recipient_user.id,
                        recipient_type=RecipientType.BCC
                    )
                    recipients.append(recipient)
                    db.add(recipient)
        
        # 첨부파일 처리
        attachment_list = []
        if attachments:
            for attachment in attachments:
                if attachment.filename:
                    # 파일 저장
                    file_id = str(uuid.uuid4())
                    file_extension = os.path.splitext(attachment.filename)[1]
                    saved_filename = f"{file_id}{file_extension}"
                    file_path = os.path.join(ATTACHMENT_DIR, saved_filename)
                    
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(attachment.file, buffer)
                    
                    # 첨부파일 정보 저장
                    mail_attachment = MailAttachment(
                        id=file_id,
                        mail_id=mail.id,
                        filename=attachment.filename,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        content_type=attachment.content_type or mimetypes.guess_type(attachment.filename)[0]
                    )
                    attachment_list.append(mail_attachment)
                    db.add(mail_attachment)
        
        db.commit()
        
        return MailSendResponse(
            success=True,
            message="메일이 성공적으로 발송되었습니다.",
            mail_uuid=mail.mail_uuid,
            sent_at=mail.sent_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending mail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")


@router.get("/inbox", response_model=MailListWithPaginationResponse, summary="받은 메일함")
async def get_inbox_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 발신자)"),
    status: Optional[MailStatus] = Query(None, description="메일 상태 필터"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """받은 메일함 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching inbox mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 받은 메일함 폴더 조회
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        if not inbox_folder:
            raise HTTPException(status_code=404, detail="Inbox folder not found")
        
        # 기본 쿼리
        query = db.query(Mail).join(
            MailInFolder, Mail.id == MailInFolder.mail_id
        ).filter(
            MailInFolder.folder_id == inbox_folder.id
        )
        
        # 검색 조건 추가
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.body_text.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Mail.status == status)
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_list = []
        for mail in mails:
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 현재 사용자의 read_at 정보 조회
            current_recipient = db.query(MailRecipient).filter(
                and_(
                    MailRecipient.mail_id == mail.id,
                    MailRecipient.recipient_id == mail_user.id
                )
            ).first()
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            # 발송자 정보 구성
            sender_info = MailUserResponse(
                id=str(sender.id),
                user_uuid=sender.user_uuid,
                email=sender.email,
                display_name=sender.display_name,
                is_active=sender.is_active,
                created_at=sender.created_at,
                updated_at=sender.updated_at
            ) if sender else None
            
            mail_response = MailListResponse(
                id=mail.id,
                mail_uuid=mail.mail_uuid,
                subject=mail.subject,
                status=mail.status,
                is_draft=mail.is_draft,
                priority=mail.priority,
                sent_at=mail.sent_at,
                created_at=mail.created_at,
                sender=sender_info,
                recipient_count=len(recipients),
                attachment_count=attachment_count,
                is_read=current_recipient.read_at is not None if current_recipient else None
            )
            mail_list.append(mail_response)
        
        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        pagination = PaginationResponse(
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error fetching inbox mails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"받은 메일함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/inbox/{mail_id}", response_model=MailDetailResponse, summary="받은 메일 상세")
async def get_inbox_mail_detail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """받은 메일 상세 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching mail detail: {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 발신자 정보
        sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
        sender_email = sender.email if sender else "Unknown"
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
        to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        # 현재 사용자의 수신자 레코드 찾기
        mail_user = db.query(MailUser).filter(MailUser.email == current_user.email).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        current_recipient = db.query(MailRecipient).filter(
            MailRecipient.mail_id == mail.id,
            MailRecipient.recipient_id == mail_user.id
        ).first()
        
        read_at = None
        if current_recipient:
            # 읽음 처리
            if not current_recipient.read_at:
                current_recipient.read_at = datetime.utcnow()
                db.commit()
            read_at = current_recipient.read_at
        
        return MailDetailResponse(
            success=True,
            data={
                "id": mail.id,
                "subject": mail.subject,
                "content": mail.body_text,
                "sender_email": sender_email,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "bcc_emails": bcc_emails,
                "status": mail.status,
                "priority": mail.priority,
                "attachments": attachment_list,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "read_at": read_at
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching mail detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/sent", response_model=MailListWithPaginationResponse, summary="보낸 메일함")
async def get_sent_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """보낸 메일함 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching sent mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 기본 쿼리 - 발신자가 현재 사용자인 메일
        query = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.status == MailStatus.SENT
            )
        )
        
        # 검색 조건 추가
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.body_text.ilike(f"%{search}%")
                )
            )
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.sent_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_list = []
        for mail in mails:
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            # 발송자 정보 구성
            sender_info = MailUserResponse(
                id=str(mail_user.id),
                user_uuid=mail_user.user_uuid,
                email=mail_user.email,
                display_name=mail_user.display_name,
                is_active=mail_user.is_active,
                created_at=mail_user.created_at,
                updated_at=mail_user.updated_at
            )
            
            mail_response = MailListResponse(
                id=mail.id,
                mail_uuid=mail.mail_uuid,
                subject=mail.subject,
                status=mail.status,
                is_draft=mail.is_draft,
                priority=mail.priority,
                sent_at=mail.sent_at,
                created_at=mail.created_at,
                sender=sender_info,
                recipient_count=len(recipients),
                attachment_count=attachment_count,
                is_read=None  # 보낸 메일함에서는 읽음 상태가 없음
            )
            mail_list.append(mail_response)
        
        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        pagination = PaginationResponse(
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error fetching sent mails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/sent/{mail_id}", response_model=MailDetailResponse, summary="보낸 메일 상세")
async def get_sent_mail_detail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """보낸 메일 상세 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching sent mail detail: {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user or mail.sender_id != mail_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
        to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        return MailDetailResponse(
            success=True,
            data={
                "id": mail.id,
                "subject": mail.subject,
                "content": mail.body_text,
                "sender_email": mail_user.email,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "bcc_emails": bcc_emails,
                "status": mail.status,
                "priority": mail.priority,
                "attachments": attachment_list,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "read_at": None  # 보낸 메일에서는 read_at 정보가 없음
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching sent mail detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/drafts", response_model=MailListWithPaginationResponse, summary="임시보관함")
async def get_draft_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """임시보관함 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching draft mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 기본 쿼리 - 임시보관 상태인 메일
        query = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.status == MailStatus.DRAFT
            )
        )
        
        # 검색 조건 추가
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.body_text.ilike(f"%{search}%")
                )
            )
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_list = []
        for mail in mails:
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            mail_response = MailResponse(
                id=mail.id,
                subject=mail.subject or "(제목 없음)",
                sender_email=mail_user.email,
                to_emails=to_emails,
                status=mail.status,
                priority=mail.priority,
                has_attachments=attachment_count > 0,
                created_at=mail.created_at,
                sent_at=mail.sent_at,
                read_at=None  # Mail 모델에는 read_at 필드가 없음
            )
            mail_list.append(mail_response)
        
        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        pagination = PaginationResponse(
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error fetching draft mails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임시보관함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/drafts/{mail_id}", response_model=MailDetailResponse, summary="임시보관함 메일 상세 조회")
async def get_draft_mail_detail(
    mail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """임시보관함 메일 상세 조회"""
    try:
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == str(mail_id)).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user or mail.sender_id != mail_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
        to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        return MailDetailResponse(
            success=True,
            data={
                "id": mail.id,
                "subject": mail.subject,
                "content": mail.body_text,
                "sender_email": mail_user.email,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "bcc_emails": bcc_emails,
                "status": mail.status,
                "priority": mail.priority,
                "attachments": attachment_list,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "read_at": None  # 임시보관함 메일에서는 read_at 정보가 없음
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching draft mail detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임시보관함 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/trash", response_model=MailListWithPaginationResponse, summary="휴지통")
async def get_deleted_mails(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"), 
    search: Optional[str] = Query(None, description="Search keyword"),
    status: Optional[MailStatus] = Query(None, description="Mail status filter")
):
    """휴지통 메일 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching deleted mails")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 휴지통 폴더 조회
        trash_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == FolderType.TRASH
            )
        ).first()
        
        if not trash_folder:
            raise HTTPException(status_code=404, detail="Trash folder not found")
        
        # 기본 쿼리
        query = db.query(Mail).join(
            MailInFolder, Mail.id == MailInFolder.mail_id
        ).filter(
            MailInFolder.folder_id == trash_folder.id
        )
        
        # 검색 조건 추가
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.body_text.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Mail.status == status)
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_list = []
        for mail in mails:
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).count()
            
            mail_response = MailResponse(
                id=mail.id,
                subject=mail.subject,
                sender_email=sender_email,
                to_emails=to_emails,
                status=mail.status,
                priority=mail.priority,
                has_attachments=attachment_count > 0,
                created_at=mail.created_at,
                sent_at=mail.sent_at,
                read_at=None  # Mail 모델에는 read_at 필드가 없음
            )
            mail_list.append(mail_response)
        
        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        pagination = PaginationResponse(
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Error fetching deleted mails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"휴지통 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/trash/{mail_id}", response_model=MailDetailResponse, summary="휴지통 메일 상세 조회")
async def get_trash_mail_detail(
    mail_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """휴지통 메일 상세 조회"""
    try:
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 발신자 정보
        sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
        sender_email = sender.email if sender else "Unknown"
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
        to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        return MailDetailResponse(
            success=True,
            data={
                "id": mail.id,
                "subject": mail.subject,
                "content": mail.body_text,
                "sender_email": sender_email,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "bcc_emails": bcc_emails,
                "status": mail.status,
                "priority": mail.priority,
                "attachments": attachment_list,
                "created_at": mail.created_at,
                "sent_at": mail.sent_at,
                "read_at": None  # 휴지통 메일에서는 read_at 정보가 없음
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching trash mail detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"휴지통 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/attachments/{attachment_id}", summary="첨부파일 다운로드")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """첨부파일 다운로드"""
    try:
        # 첨부파일 조회
        attachment = db.query(MailAttachment).filter(MailAttachment.id == attachment_id).first()
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == attachment.mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 권한 확인 (발신자이거나 수신자인지 확인)
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 발신자 확인
        is_sender = mail.sender_id == mail_user.id
        
        # 수신자 확인
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 파일 존재 확인
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=attachment.file_path,
            filename=attachment.filename,
            media_type=attachment.content_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading attachment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"첨부파일 다운로드 중 오류가 발생했습니다: {str(e)}")