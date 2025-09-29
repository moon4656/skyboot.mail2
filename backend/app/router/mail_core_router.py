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

from ..database.user import get_db
from ..model.user_model import User
from ..model.mail_model import FolderType, Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from ..schemas.mail_schema import (
    MailSendRequest,
    MailResponse,
    MailListResponse,
    MailSendResponse,
    MailDetailResponse,
    MailListWithPaginationResponse,
    MailUserResponse,
    PaginationResponse,
    RecipientType,
    MailStatus,
    MailPriority,
)
from ..service.mail_service import MailService
from ..service.auth_service import get_current_user
from ..middleware.tenant_middleware import get_current_org_id, get_current_organization

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 필수 기능
router = APIRouter(tags=["메일 핵심 기능"])

# 보안 설정
security = HTTPBearer()

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
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailSendResponse:
    """
    메일 발송 API
    조직 내에서 메일을 발송합니다.
    """
    try:
        logger.info(f"📤 메일 발송 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 수신자: {to_emails}")
        
        # 조직 내에서 메일 사용자 조회
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found in this organization")
        
        # 메일 생성 (조직 ID 포함)
        mail_uuid = str(uuid.uuid4())
        mail = Mail(
            mail_uuid=mail_uuid,
            sender_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            subject=subject,
            body_text=content,
            priority=priority,
            status=MailStatus.SENT,
            is_draft=False,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow(),
            message_id=str(uuid.uuid4())
        )
        
        db.add(mail)
        db.flush()
        
        # 수신자 처리
        recipients = []
        
        # TO 수신자 처리 (조직별 격리)
        if to_emails:
            for email in to_emails.split(','):
                email = email.strip()
                if email:
                    # 같은 조직 내에서 수신자 사용자 찾기
                    recipient_user = db.query(MailUser).filter(
                        MailUser.email == email,
                        MailUser.org_id == current_org_id
                    ).first()
                    
                    if not recipient_user:
                        # 조직 내에 없는 경우 외부 사용자로 임시 생성
                        external_user_uuid = str(uuid.uuid4())
                        recipient_user = MailUser(
                            user_id=external_user_uuid,  # user_id 추가
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False,
                            org_id=current_org_id,  # 현재 조직에 속하도록 설정
                            user_uuid=external_user_uuid
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient_type_value = RecipientType.TO.value
                    logger.info(f"🔍 DEBUG: RecipientType.TO.value = {recipient_type_value}")
                    logger.info(f"🔍 DEBUG: type(recipient_type_value) = {type(recipient_type_value)}")
                    
                    recipient = MailRecipient(
                        mail_uuid=mail.mail_uuid,
                        recipient_email=email,
                        recipient_type=recipient_type_value
                    )
                    logger.info(f"🔍 DEBUG: recipient.recipient_type = {recipient.recipient_type}")
                    logger.info(f"🔍 DEBUG: type(recipient.recipient_type) = {type(recipient.recipient_type)}")
                    recipients.append(recipient)
                    db.add(recipient)
        
        # CC 수신자 처리 (조직별 격리)
        if cc_emails:
            for email in cc_emails.split(','):
                email = email.strip()
                if email:
                    # 같은 조직 내에서 수신자 사용자 찾기
                    recipient_user = db.query(MailUser).filter(
                        MailUser.email == email,
                        MailUser.org_id == current_org_id
                    ).first()
                    
                    if not recipient_user:
                        # 조직 내에 없는 경우 외부 사용자로 임시 생성
                        external_user_uuid = str(uuid.uuid4())
                        recipient_user = MailUser(
                            user_uuid=external_user_uuid,
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False,
                            org_id=current_org_id  # 현재 조직에 속하도록 설정
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient = MailRecipient(
                        mail_uuid=mail.mail_uuid,
                        recipient_email=email,
                        recipient_type=RecipientType.CC.value
                    )
                    recipients.append(recipient)
                    db.add(recipient)
        
        # BCC 수신자 처리 (조직별 격리)
        if bcc_emails:
            for email in bcc_emails.split(','):
                email = email.strip()
                if email:
                    # 같은 조직 내에서 수신자 사용자 찾기
                    recipient_user = db.query(MailUser).filter(
                        MailUser.email == email,
                        MailUser.org_id == current_org_id
                    ).first()
                    
                    if not recipient_user:
                        # 조직 내에 없는 경우 외부 사용자로 임시 생성
                        external_user_uuid = str(uuid.uuid4())
                        recipient_user = MailUser(
                            user_id=external_user_uuid,  # user_id 추가
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False,
                            org_id=current_org_id,  # 현재 조직에 속하도록 설정
                            user_uuid=external_user_uuid
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient = MailRecipient(
                        mail_uuid=mail.mail_uuid,
                        recipient_email=email,
                        recipient_type=RecipientType.BCC.value
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
                        attachment_uuid=file_id,
                        mail_uuid=mail.mail_uuid,
                        filename=attachment.filename,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        content_type=attachment.content_type or mimetypes.guess_type(attachment.filename)[0]
                    )
                    attachment_list.append(mail_attachment)
                    db.add(mail_attachment)
        
        db.commit()
        
        logger.info(f"✅ 메일 발송 완료 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 수신자 수: {len(recipients)}, 첨부파일 수: {len(attachment_list)}")
        
        return MailSendResponse(
            success=True,
            message="메일이 성공적으로 발송되었습니다.",
            mail_uuid=mail.mail_uuid,
            sent_at=mail.sent_at
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 메일 발송 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")


@router.get("/inbox", response_model=MailListWithPaginationResponse, summary="받은 메일함")
async def get_inbox_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 발신자)"),
    status: Optional[MailStatus] = Query(None, description="메일 상태 필터"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailListWithPaginationResponse:
    """받은 메일함 조회"""
    try:
        logger.info(f"📥 받은 메일함 조회 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링)
        mail_user = db.query(MailUser).filter(
            and_(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            )
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="해당 조직에서 메일 사용자를 찾을 수 없습니다")
        
        # 받은 메일함 폴더 조회
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        if not inbox_folder:
            raise HTTPException(status_code=404, detail="Inbox folder not found")
        
        # 기본 쿼리 (조직별 필터링 포함)
        query = db.query(Mail).join(
            MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
        ).filter(
            and_(
                MailInFolder.folder_uuid == inbox_folder.folder_uuid,
                Mail.org_id == current_org_id
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
            # 발신자 정보 (조직별 필터링)
            sender = db.query(MailUser).filter(
                and_(
                    MailUser.user_uuid == mail.sender_uuid,
                    MailUser.org_id == current_org_id
                )
            ).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            cc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.CC]
            bcc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.BCC]
            
            # 현재 사용자의 read_at 정보 조회
            current_recipient = db.query(MailRecipient).filter(
                and_(
                    MailRecipient.mail_uuid == mail.mail_uuid,
                    MailRecipient.recipient_email == mail_user.email
                )
            ).first()
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            # 발송자 정보 구성
            sender_info = MailUserResponse(
                user_uuid=sender.user_uuid,
                email=sender.email,
                display_name=sender.display_name,
                is_active=sender.is_active,
                created_at=sender.created_at,
                updated_at=sender.updated_at
            ) if sender else None
            
            mail_response = MailListResponse(
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
        
        logger.info(f"✅ 받은 메일함 조회 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 수: {len(mail_list)}")
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 받은 메일함 조회 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"받은 메일함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/inbox/{mail_uuid}", response_model=MailDetailResponse, summary="받은 메일 상세 조회")
async def get_inbox_mail_detail(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailDetailResponse:
    """받은 메일 상세 조회"""
    try:
        logger.info(f"📧 get_inbox_mail_detail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 조회 (조직별 격리)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,    
            Mail.org_id == current_org_id
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 발신자 정보 (조직별 격리)
        sender = db.query(MailUser).filter(
            MailUser.user_uuid == mail.sender_uuid,
            MailUser.org_id == current_org_id
        ).first()
        sender_email = sender.email if sender else "Unknown"
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
        to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        # 현재 사용자의 수신자 레코드 찾기 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.email == current_user.email,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        current_recipient = db.query(MailRecipient).filter(
            MailRecipient.mail_uuid == mail.mail_uuid,  
            MailRecipient.recipient_email == mail_user.email
        ).first()
        
        read_at = None
        if current_recipient:
            # 읽음 처리
            if not current_recipient.read_at:
                current_recipient.read_at = datetime.utcnow()
                db.commit()
            read_at = current_recipient.read_at
        
        logger.info(f"✅ get_inbox_mail_detail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return MailDetailResponse(
            success=True,
            data={
                "mail_uuid": mail.mail_uuid,       
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
        logger.error(f"❌ get_inbox_mail_detail 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/sent", response_model=MailListWithPaginationResponse, summary="보낸 메일함")
async def get_sent_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailListWithPaginationResponse:
    """보낸 메일함 조회"""
    try:
        logger.info(f"📤 보낸 메일함 조회 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링)
        mail_user = db.query(MailUser).filter(
            and_(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            )
        ).first()
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="해당 조직에서 메일 사용자를 찾을 수 없습니다")
        
        # 기본 쿼리 - 발신자가 현재 사용자인 메일 (조직별 필터링 포함)
        query = db.query(Mail).filter(
            and_(
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.SENT,
                Mail.org_id == current_org_id
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
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            # 발송자 정보 구성
            sender_info = MailUserResponse(
                user_uuid=mail_user.user_uuid,
                email=mail_user.email,
                display_name=mail_user.display_name,
                is_active=mail_user.is_active,
                created_at=mail_user.created_at,
                updated_at=mail_user.updated_at
            )
            
            mail_response = MailListResponse(
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
        
        logger.info(f"✅ 보낸 메일함 조회 완료 - org_id: {current_org_id}, user: {current_user.email}, 메일 수: {len(mail_list)}")
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 보낸 메일함 조회 중 오류 발생 - org_id: {current_org_id}, user: {current_user.email}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/sent/{mail_uuid}", response_model=MailDetailResponse, summary="보낸 메일 상세")
async def get_sent_mail_detail(
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailDetailResponse:
    """보낸 메일 상세 조회"""
    try:
        logger.info(f"📧 보낸 메일 상세 조회 시작 - org_id: {current_org_id}, user: {current_user.email}, mail_uuid: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링)
        mail_user = db.query(MailUser).filter(
            and_(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            )
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="해당 조직에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 필터링)
        mail = db.query(Mail).filter(
            and_(
                Mail.mail_uuid == mail_uuid,
                Mail.org_id == current_org_id,
                Mail.sender_uuid == mail_user.user_uuid
            )
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없거나 접근 권한이 없습니다")
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
        to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        logger.info(f"✅ 보낸 메일 상세 조회 완료 - org_id: {current_org_id}, user: {current_user.email}, mail_uuid: {mail_uuid}")
        
        return MailDetailResponse(
            success=True,
            data={
                "mail_uuid": mail.mail_uuid,
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 보낸 메일 상세 조회 중 오류 발생 - org_id: {current_org_id}, user: {current_user.email}, mail_uuid: {mail_uuid}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/drafts", response_model=MailListWithPaginationResponse, summary="임시보관함")
async def get_draft_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailListWithPaginationResponse:
    """임시보관함 조회"""
    try:
        logger.info(f"📧 임시보관함 조회 시작 - org_id: {current_org_id}, user: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링)
        mail_user = db.query(MailUser).filter(
            and_(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            )
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="해당 조직에서 메일 사용자를 찾을 수 없습니다")
        
        # 기본 쿼리 - 임시보관 상태인 메일 (조직별 필터링)
        query = db.query(Mail).filter(
            and_(
                Mail.sender_uuid == mail_user.user_uuid,    
                Mail.status == MailStatus.DRAFT,
                Mail.org_id == current_org_id
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
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            mail_response = MailResponse(
                mail_uuid=mail.mail_uuid,
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
        
        logger.info(f"✅ 임시보관함 조회 완료 - org_id: {current_org_id}, user: {current_user.email}, 메일 수: {len(mail_list)}")
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 임시보관함 조회 중 오류 발생 - org_id: {current_org_id}, user: {current_user.email}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임시보관함 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/drafts/{mail_uuid}", response_model=MailDetailResponse, summary="임시보관함 메일 상세 조회")
async def get_draft_mail_detail(
    mail_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MailDetailResponse:
    """임시보관함 메일 상세 조회"""
    try:
        # 메일 조회
        mail = db.query(Mail).filter(Mail.mail_uuid == mail_uuid).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_uuid == current_user.user_uuid).first()
        if not mail_user or mail.sender_uuid != mail_user.user_uuid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()    
        to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
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
                "mail_uuid": mail.mail_uuid,
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
    current_org_id: str = Depends(get_current_org_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"), 
    search: Optional[str] = Query(None, description="Search keyword"),
    status: Optional[MailStatus] = Query(None, description="Mail status filter")
) -> MailListWithPaginationResponse:
    """휴지통 메일 조회"""
    try:
        logger.info(f"📧 get_deleted_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 페이지: {page}, 제한: {limit}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 휴지통 폴더 조회
        trash_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id,
                MailFolder.folder_type == FolderType.TRASH
            )
        ).first()
        
        if not trash_folder:
            logger.warning(f"⚠️ 휴지통 폴더를 찾을 수 없음 - 사용자: {mail_user.user_uuid}")
            raise HTTPException(status_code=404, detail="휴지통 폴더를 찾을 수 없습니다")
        
        # 기본 쿼리 (조직별 필터링 추가)
        query = db.query(Mail).join(
            MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid
        ).filter(
            Mail.org_id == current_org_id,
            MailInFolder.folder_uuid == trash_folder.folder_uuid
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
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            sender_email = sender.email if sender else "Unknown"
            
            # 수신자 정보
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()    
            to_emails = [r.recipient_email for r in recipients if r.recipient_type == RecipientType.TO]
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            mail_response = MailResponse(
                mail_uuid=mail.mail_uuid,
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
        
        logger.info(f"✅ get_deleted_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 수: {len(mail_list)}")
        
        return MailListWithPaginationResponse(
            mails=mail_list,
            pagination=pagination
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_deleted_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"휴지통 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/trash/{mail_uuid}", response_model=MailDetailResponse, summary="휴지통 메일 상세 조회")
async def get_trash_mail_detail(
    mail_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id)
) -> MailDetailResponse:
    """휴지통 메일 상세 조회"""
    try:
        logger.info(f"📧 get_trash_mail_detail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
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
        
        # 발신자 정보
        sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
        sender_email = sender.email if sender else "Unknown"
        
        # 수신자 정보
        recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
        to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO]
        cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC]
        bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC]
        
        # 첨부파일 정보
        attachments = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type
            })
        
        logger.info(f"✅ get_trash_mail_detail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return MailDetailResponse(
            success=True,
            data={
                "id": mail.mail_uuid,
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_trash_mail_detail 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"휴지통 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/attachments/{attachment_id}", response_model=None, summary="첨부파일 다운로드")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> FileResponse:
    """첨부파일 다운로드"""
    try:
        logger.info(f"📧 download_attachment 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 첨부파일ID: {attachment_id}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 첨부파일 조회 (attachment_uuid 사용)
        attachment = db.query(MailAttachment).filter(MailAttachment.attachment_uuid == attachment_id).first()
        if not attachment:
            logger.warning(f"⚠️ 첨부파일을 찾을 수 없음 - 첨부파일ID: {attachment_id}")
            raise HTTPException(status_code=404, detail="첨부파일을 찾을 수 없습니다")
        
        # 메일 조회 (조직별 필터링 추가)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == attachment.mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        
        if not mail:
            logger.warning(f"⚠️ 메일을 찾을 수 없음 - 조직: {current_org_id}, 메일UUID: {attachment.mail_uuid}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일을 찾을 수 없습니다")
        
        # 발신자 확인
        is_sender = mail.sender_uuid == mail_user.user_uuid 
        
        # 수신자 확인
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_email == mail_user.email
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            logger.warning(f"⚠️ 첨부파일 접근 권한 없음 - 조직: {current_org_id}, 사용자: {current_user.email}, 첨부파일ID: {attachment_id}")
            raise HTTPException(status_code=403, detail="첨부파일에 대한 접근 권한이 없습니다")
        
        # 파일 존재 확인
        if not os.path.exists(attachment.file_path):
            logger.warning(f"⚠️ 첨부파일이 존재하지 않음 - 경로: {attachment.file_path}")
            raise HTTPException(status_code=404, detail="첨부파일이 존재하지 않습니다")
        
        logger.info(f"✅ download_attachment 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 첨부파일: {attachment.filename}")
        
        return FileResponse(
            path=attachment.file_path,
            filename=attachment.filename,
            media_type=attachment.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ download_attachment 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 첨부파일ID: {attachment_id}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"첨부파일 다운로드 중 오류가 발생했습니다: {str(e)}")