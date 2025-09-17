from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Form
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

from ..database.base import get_db
from ..model.base_model import User
from ..model.mail_model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from ..schemas.mail_schema import (
    MailCreate, MailResponse, MailListResponse, MailDetailResponse,
    MailSendRequest, MailSendResponse, MailSearchRequest, MailSearchResponse,
    PaginationResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType
)
from ..service.mail_service import MailService
from ..service.auth_service import get_current_user

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화
router = APIRouter(prefix="/api/mail", tags=["mail"])

# 보안 설정
security = HTTPBearer()

# 메일 서비스 초기화
mail_service = MailService()

# 첨부파일 저장 디렉토리
ATTACHMENT_DIR = "attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)



# 메일 발송 API
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
    """
    메일을 발송합니다.
    
    - **to_emails**: 수신자 이메일 주소들 (쉼표로 구분)
    - **cc_emails**: 참조 수신자 이메일 주소들 (선택사항)
    - **bcc_emails**: 숨은참조 수신자 이메일 주소들 (선택사항)
    - **subject**: 메일 제목
    - **content**: 메일 내용 (HTML 지원)
    - **priority**: 메일 우선순위 (LOW, NORMAL, HIGH)
    - **attachments**: 첨부파일들 (선택사항)
    """
    try:
        logger.info(f"📧 메일 발송 시작 - 발신자: {current_user.email}")
        
        # 첨부파일 처리
        attachment_paths = []
        if attachments:
            for attachment in attachments:
                if attachment.filename:
                    # 고유한 파일명 생성
                    file_id = str(uuid.uuid4())
                    file_extension = os.path.splitext(attachment.filename)[1]
                    unique_filename = f"{file_id}{file_extension}"
                    file_path = os.path.join(ATTACHMENT_DIR, unique_filename)
                    
                    # 파일 저장
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(attachment.file, buffer)
                    
                    attachment_paths.append({
                        "original_name": attachment.filename,
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path),
                        "content_type": attachment.content_type or "application/octet-stream"
                    })
        
        # 메일 발송 요청 생성
        mail_request = MailSendRequest(
            to_emails=to_emails.split(","),
            cc_emails=cc_emails.split(",") if cc_emails else [],
            bcc_emails=bcc_emails.split(",") if bcc_emails else [],
            subject=subject,
            content=content,
            priority=priority,
            sender_email=current_user.email
        )
        
        # 메일 서비스를 통해 발송
        result = await mail_service.send_mail(mail_request, attachment_paths, db)
        
        logger.info(f"✅ 메일 발송 완료 - 메일 ID: {result.mail_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 메일 발송 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")

# 받은 메일 목록 조회
@router.get("/inbox", response_model=MailListResponse, summary="받은 메일 목록")
async def get_inbox_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 발신자)"),
    status: Optional[MailStatus] = Query(None, description="메일 상태 필터"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    받은 메일 목록을 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 메일 수 (최대 100개)
    - **search**: 제목이나 발신자로 검색
    - **status**: 메일 상태로 필터링 (UNREAD, READ, ARCHIVED)
    """
    try:
        logger.info(f"📥 받은 메일 목록 조회 - 사용자: {current_user.email}")
        
        # 받은편지함 폴더 조회
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user.email,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        if not inbox_folder:
            return MailListResponse(
                mails=[],
                pagination=PaginationResponse(page=page, limit=limit, total=0, total_pages=0)
            )
        
        # 기본 쿼리
        query = db.query(Mail).join(MailInFolder).filter(
            MailInFolder.folder_id == inbox_folder.folder_id
        )
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.sender_email.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Mail.status == status)
        
        # 총 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_responses = []
        for mail in mails:
            # 수신자 정보 조회
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.mail_id
            ).all()
            
            # 첨부파일 정보 조회
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail.mail_id
            ).all()
            
            mail_responses.append(MailResponse(
                mail_id=mail.mail_id,
                subject=mail.subject,
                sender_email=mail.sender_email,
                sender_name=mail.sender_name,
                content=mail.content[:200] + "..." if len(mail.content) > 200 else mail.content,
                status=mail.status,
                priority=mail.priority,
                created_at=mail.created_at,
                updated_at=mail.updated_at,
                recipients=[{
                    "email": r.recipient_email,
                    "name": r.recipient_name,
                    "type": r.recipient_type
                } for r in recipients],
                attachments=[{
                    "filename": a.original_filename,
                    "file_size": a.file_size,
                    "content_type": a.content_type
                } for a in attachments],
                has_attachments=len(attachments) > 0
            ))
        
        total_pages = (total + limit - 1) // limit
        
        logger.info(f"✅ 받은 메일 목록 조회 완료 - 총 {total}개")
        return MailListResponse(
            mails=mail_responses,
            pagination=PaginationResponse(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages
            )
        )
        
    except Exception as e:
        logger.error(f"❌ 받은 메일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"받은 메일 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 받은 메일 상세 조회
@router.get("/inbox/{mail_id}", response_model=MailDetailResponse, summary="받은 메일 상세")
async def get_inbox_mail_detail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    받은 메일의 상세 정보를 조회합니다.
    
    - **mail_id**: 조회할 메일의 고유 ID
    """
    try:
        logger.info(f"📧 받은 메일 상세 조회 - 메일 ID: {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.mail_id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 사용자 권한 확인 (받은편지함에 있는지 확인)
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user.email,
                MailFolder.folder_type == FolderType.INBOX
            )
        ).first()
        
        if inbox_folder:
            mail_in_folder = db.query(MailInFolder).filter(
                and_(
                    MailInFolder.mail_id == mail_id,
                    MailInFolder.folder_id == inbox_folder.folder_id
                )
            ).first()
            
            if not mail_in_folder:
                raise HTTPException(status_code=403, detail="해당 메일에 접근할 권한이 없습니다")
        
        # 수신자 정보 조회
        recipients = db.query(MailRecipient).filter(
            MailRecipient.mail_id == mail_id
        ).all()
        
        # 첨부파일 정보 조회
        attachments = db.query(MailAttachment).filter(
            MailAttachment.mail_id == mail_id
        ).all()
        
        # 읽음 상태로 업데이트
        if mail.status == MailStatus.UNREAD:
            mail.status = MailStatus.READ
            mail.updated_at = datetime.utcnow()
            db.commit()
        
        response = MailDetailResponse(
            mail_id=mail.mail_id,
            subject=mail.subject,
            sender_email=mail.sender_email,
            sender_name=mail.sender_name,
            content=mail.content,
            status=mail.status,
            priority=mail.priority,
            created_at=mail.created_at,
            updated_at=mail.updated_at,
            recipients=[{
                "email": r.recipient_email,
                "name": r.recipient_name,
                "type": r.recipient_type
            } for r in recipients],
            attachments=[{
                "attachment_id": a.attachment_id,
                "filename": a.original_filename,
                "file_size": a.file_size,
                "content_type": a.content_type
            } for a in attachments]
        )
        
        logger.info(f"✅ 받은 메일 상세 조회 완료 - 메일 ID: {mail_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 받은 메일 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"받은 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")

# 보낸 메일 목록 조회
@router.get("/sent", response_model=MailListResponse, summary="보낸 메일 목록")
async def get_sent_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    보낸 메일 목록을 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 메일 수 (최대 100개)
    - **search**: 제목이나 수신자로 검색
    """
    try:
        logger.info(f"📤 보낸 메일 목록 조회 - 사용자: {current_user.email}")
        
        # 보낸편지함 폴더 조회
        sent_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user.email,
                MailFolder.folder_type == FolderType.SENT
            )
        ).first()
        
        if not sent_folder:
            return MailListResponse(
                mails=[],
                pagination=PaginationResponse(page=page, limit=limit, total=0, total_pages=0)
            )
        
        # 기본 쿼리
        query = db.query(Mail).join(MailInFolder).filter(
            MailInFolder.folder_id == sent_folder.folder_id
        )
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.mail_id.in_(
                        db.query(MailRecipient.mail_id).filter(
                            MailRecipient.recipient_email.ilike(f"%{search}%")
                        )
                    )
                )
            )
        
        # 총 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_responses = []
        for mail in mails:
            # 수신자 정보 조회
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.mail_id
            ).all()
            
            # 첨부파일 정보 조회
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail.mail_id
            ).all()
            
            mail_responses.append(MailResponse(
                mail_id=mail.mail_id,
                subject=mail.subject,
                sender_email=mail.sender_email,
                sender_name=mail.sender_name,
                content=mail.content[:200] + "..." if len(mail.content) > 200 else mail.content,
                status=mail.status,
                priority=mail.priority,
                created_at=mail.created_at,
                updated_at=mail.updated_at,
                recipients=[{
                    "email": r.recipient_email,
                    "name": r.recipient_name,
                    "type": r.recipient_type
                } for r in recipients],
                attachments=[{
                    "filename": a.original_filename,
                    "file_size": a.file_size,
                    "content_type": a.content_type
                } for a in attachments],
                has_attachments=len(attachments) > 0
            ))
        
        total_pages = (total + limit - 1) // limit
        
        logger.info(f"✅ 보낸 메일 목록 조회 완료 - 총 {total}개")
        return MailListResponse(
            mails=mail_responses,
            pagination=PaginationResponse(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages
            )
        )
        
    except Exception as e:
        logger.error(f"❌ 보낸 메일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 보낸 메일 상세 조회
@router.get("/sent/{mail_id}", response_model=MailDetailResponse, summary="보낸 메일 상세")
async def get_sent_mail_detail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    보낸 메일의 상세 정보를 조회합니다.
    
    - **mail_id**: 조회할 메일의 고유 ID
    """
    try:
        logger.info(f"📧 보낸 메일 상세 조회 - 메일 ID: {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(
            and_(
                Mail.mail_id == mail_id,
                Mail.sender_email == current_user.email
            )
        ).first()
        
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 수신자 정보 조회
        recipients = db.query(MailRecipient).filter(
            MailRecipient.mail_id == mail_id
        ).all()
        
        # 첨부파일 정보 조회
        attachments = db.query(MailAttachment).filter(
            MailAttachment.mail_id == mail_id
        ).all()
        
        response = MailDetailResponse(
            mail_id=mail.mail_id,
            subject=mail.subject,
            sender_email=mail.sender_email,
            sender_name=mail.sender_name,
            content=mail.content,
            status=mail.status,
            priority=mail.priority,
            created_at=mail.created_at,
            updated_at=mail.updated_at,
            recipients=[{
                "email": r.recipient_email,
                "name": r.recipient_name,
                "type": r.recipient_type
            } for r in recipients],
            attachments=[{
                "attachment_id": a.attachment_id,
                "filename": a.original_filename,
                "file_size": a.file_size,
                "content_type": a.content_type
            } for a in attachments]
        )
        
        logger.info(f"✅ 보낸 메일 상세 조회 완료 - 메일 ID: {mail_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 보낸 메일 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보낸 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")

# 임시보관함 메일 목록 조회
@router.get("/drafts", response_model=MailListResponse, summary="임시보관함 메일 목록")
async def get_draft_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    임시보관함 메일 목록을 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 메일 수 (최대 100개)
    - **search**: 제목이나 수신자로 검색
    """
    try:
        logger.info(f"📝 임시보관함 메일 목록 조회 - 사용자: {current_user.email}")
        
        # 임시보관함 폴더 조회
        draft_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user.email,
                MailFolder.folder_type == FolderType.DRAFT
            )
        ).first()
        
        if not draft_folder:
            return MailListResponse(
                mails=[],
                pagination=PaginationResponse(page=page, limit=limit, total=0, total_pages=0)
            )
        
        # 기본 쿼리
        query = db.query(Mail).join(MailInFolder).filter(
            MailInFolder.folder_id == draft_folder.folder_id
        )
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search}%"),
                    Mail.mail_id.in_(
                        db.query(MailRecipient.mail_id).filter(
                            MailRecipient.recipient_email.ilike(f"%{search}%")
                        )
                    )
                )
            )
        
        # 총 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        mails = query.order_by(desc(Mail.updated_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        mail_responses = []
        for mail in mails:
            # 수신자 정보 조회
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.mail_id
            ).all()
            
            # 첨부파일 정보 조회
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail.mail_id
            ).all()
            
            mail_responses.append(MailResponse(
                mail_id=mail.mail_id,
                subject=mail.subject,
                sender_email=mail.sender_email,
                sender_name=mail.sender_name,
                content=mail.content[:200] + "..." if len(mail.content) > 200 else mail.content,
                status=mail.status,
                priority=mail.priority,
                created_at=mail.created_at,
                updated_at=mail.updated_at,
                recipients=[{
                    "email": r.recipient_email,
                    "name": r.recipient_name,
                    "type": r.recipient_type
                } for r in recipients],
                attachments=[{
                    "filename": a.original_filename,
                    "file_size": a.file_size,
                    "content_type": a.content_type
                } for a in attachments],
                has_attachments=len(attachments) > 0
            ))
        
        total_pages = (total + limit - 1) // limit
        
        logger.info(f"✅ 임시보관함 메일 목록 조회 완료 - 총 {total}개")
        return MailListResponse(
            mails=mail_responses,
            pagination=PaginationResponse(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages
            )
        )
        
    except Exception as e:
        logger.error(f"❌ 임시보관함 메일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임시보관함 메일 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 메일 검색
@router.post("/search", response_model=MailSearchResponse, summary="메일 검색")
async def search_mails(
    search_request: MailSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메일을 검색합니다.
    
    - **keyword**: 검색 키워드
    - **folder_type**: 검색할 폴더 타입 (선택사항)
    - **date_from**: 검색 시작 날짜 (선택사항)
    - **date_to**: 검색 종료 날짜 (선택사항)
    - **sender_email**: 발신자 이메일 필터 (선택사항)
    - **has_attachments**: 첨부파일 유무 필터 (선택사항)
    """
    try:
        logger.info(f"🔍 메일 검색 - 사용자: {current_user.email}, 키워드: {search_request.keyword}")
        
        # 사용자 폴더들 조회
        folders_query = db.query(MailFolder).filter(
            MailFolder.user_email == current_user.email
        )
        
        # 폴더 타입 필터
        if search_request.folder_type:
            folders_query = folders_query.filter(
                MailFolder.folder_type == search_request.folder_type
            )
        
        folders = folders_query.all()
        folder_ids = [f.folder_id for f in folders]
        
        if not folder_ids:
            return MailSearchResponse(
                mails=[],
                total=0,
                search_keyword=search_request.keyword
            )
        
        # 기본 쿼리
        query = db.query(Mail).join(MailInFolder).filter(
            MailInFolder.folder_id.in_(folder_ids)
        )
        
        # 키워드 검색
        if search_request.keyword:
            query = query.filter(
                or_(
                    Mail.subject.ilike(f"%{search_request.keyword}%"),
                    Mail.content.ilike(f"%{search_request.keyword}%"),
                    Mail.sender_email.ilike(f"%{search_request.keyword}%")
                )
            )
        
        # 날짜 필터
        if search_request.date_from:
            query = query.filter(Mail.created_at >= search_request.date_from)
        
        if search_request.date_to:
            query = query.filter(Mail.created_at <= search_request.date_to)
        
        # 발신자 필터
        if search_request.sender_email:
            query = query.filter(Mail.sender_email.ilike(f"%{search_request.sender_email}%"))
        
        # 첨부파일 필터
        if search_request.has_attachments is not None:
            if search_request.has_attachments:
                query = query.filter(
                    Mail.mail_id.in_(
                        db.query(MailAttachment.mail_id).distinct()
                    )
                )
            else:
                query = query.filter(
                    ~Mail.mail_id.in_(
                        db.query(MailAttachment.mail_id).distinct()
                    )
                )
        
        # 총 개수 조회
        total = query.count()
        
        # 결과 조회 (최대 100개)
        mails = query.order_by(desc(Mail.created_at)).limit(100).all()
        
        # 응답 데이터 구성
        mail_responses = []
        for mail in mails:
            # 수신자 정보 조회
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.mail_id
            ).all()
            
            # 첨부파일 정보 조회
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail.mail_id
            ).all()
            
            mail_responses.append(MailResponse(
                mail_id=mail.mail_id,
                subject=mail.subject,
                sender_email=mail.sender_email,
                sender_name=mail.sender_name,
                content=mail.content[:200] + "..." if len(mail.content) > 200 else mail.content,
                status=mail.status,
                priority=mail.priority,
                created_at=mail.created_at,
                updated_at=mail.updated_at,
                recipients=[{
                    "email": r.recipient_email,
                    "name": r.recipient_name,
                    "type": r.recipient_type
                } for r in recipients],
                attachments=[{
                    "filename": a.original_filename,
                    "file_size": a.file_size,
                    "content_type": a.content_type
                } for a in attachments],
                has_attachments=len(attachments) > 0
            ))
        
        logger.info(f"✅ 메일 검색 완료 - 총 {total}개 발견")
        return MailSearchResponse(
            mails=mail_responses,
            total=total,
            search_keyword=search_request.keyword
        )
        
    except Exception as e:
        logger.error(f"❌ 메일 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 검색 중 오류가 발생했습니다: {str(e)}")

# 메일 통계
@router.get("/stats", response_model=MailStatsResponse, summary="메일 통계")
async def get_mail_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 메일 통계를 조회합니다.
    
    - 받은 메일 수 (읽음/안읽음)
    - 보낸 메일 수
    - 임시보관함 메일 수
    - 휴지통 메일 수
    """
    try:
        logger.info(f"📊 메일 통계 조회 - 사용자: {current_user.email}")
        
        # 사용자 폴더들 조회
        folders = db.query(MailFolder).filter(
            MailFolder.user_email == current_user.email
        ).all()
        
        stats = {
            "inbox_total": 0,
            "inbox_unread": 0,
            "sent_total": 0,
            "draft_total": 0,
            "trash_total": 0
        }
        
        for folder in folders:
            # 폴더별 메일 수 조회
            mail_count = db.query(Mail).join(MailInFolder).filter(
                MailInFolder.folder_id == folder.folder_id
            ).count()
            
            if folder.folder_type == FolderType.INBOX:
                stats["inbox_total"] = mail_count
                # 읽지 않은 메일 수
                stats["inbox_unread"] = db.query(Mail).join(MailInFolder).filter(
                    and_(
                        MailInFolder.folder_id == folder.folder_id,
                        Mail.status == MailStatus.UNREAD
                    )
                ).count()
            elif folder.folder_type == FolderType.SENT:
                stats["sent_total"] = mail_count
            elif folder.folder_type == FolderType.DRAFT:
                stats["draft_total"] = mail_count
            elif folder.folder_type == FolderType.TRASH:
                stats["trash_total"] = mail_count
        
        logger.info(f"✅ 메일 통계 조회 완료")
        return MailStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ 메일 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 통계 조회 중 오류가 발생했습니다: {str(e)}")

# 첨부파일 다운로드
@router.get("/attachments/{attachment_id}", summary="첨부파일 다운로드")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    첨부파일을 다운로드합니다.
    
    - **attachment_id**: 다운로드할 첨부파일의 고유 ID
    """
    try:
        logger.info(f"📎 첨부파일 다운로드 - 첨부파일 ID: {attachment_id}")
        
        # 첨부파일 조회
        attachment = db.query(MailAttachment).filter(
            MailAttachment.attachment_id == attachment_id
        ).first()
        
        if not attachment:
            raise HTTPException(status_code=404, detail="첨부파일을 찾을 수 없습니다")
        
        # 메일 권한 확인
        mail = db.query(Mail).filter(Mail.mail_id == attachment.mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 사용자 권한 확인 (발신자이거나 수신자인지)
        has_permission = False
        
        # 발신자 확인
        if mail.sender_email == current_user.email:
            has_permission = True
        else:
            # 수신자 확인
            user_folders = db.query(MailFolder).filter(
                MailFolder.user_email == current_user.email
            ).all()
            
            for folder in user_folders:
                mail_in_folder = db.query(MailInFolder).filter(
                    and_(
                        MailInFolder.mail_id == mail.mail_id,
                        MailInFolder.folder_id == folder.folder_id
                    )
                ).first()
                
                if mail_in_folder:
                    has_permission = True
                    break
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="첨부파일에 접근할 권한이 없습니다")
        
        # 파일 존재 확인
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="첨부파일이 서버에서 찾을 수 없습니다")
        
        logger.info(f"✅ 첨부파일 다운로드 시작 - {attachment.original_filename}")
        return FileResponse(
            path=attachment.file_path,
            filename=attachment.original_filename,
            media_type=attachment.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 첨부파일 다운로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"첨부파일 다운로드 중 오류가 발생했습니다: {str(e)}")

# 메일 상태 업데이트
@router.patch("/status/{mail_id}", response_model=APIResponse, summary="메일 상태 업데이트")
async def update_mail_status(
    mail_id: str,
    status: MailStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메일의 상태를 업데이트합니다.
    
    - **mail_id**: 업데이트할 메일의 고유 ID
    - **status**: 새로운 메일 상태 (UNREAD, READ, ARCHIVED)
    """
    try:
        logger.info(f"🔄 메일 상태 업데이트 - 메일 ID: {mail_id}, 상태: {status}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.mail_id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 사용자 권한 확인
        user_folders = db.query(MailFolder).filter(
            MailFolder.user_email == current_user.email
        ).all()
        
        has_permission = False
        for folder in user_folders:
            mail_in_folder = db.query(MailInFolder).filter(
                and_(
                    MailInFolder.mail_id == mail_id,
                    MailInFolder.folder_id == folder.folder_id
                )
            ).first()
            
            if mail_in_folder:
                has_permission = True
                break
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="해당 메일에 접근할 권한이 없습니다")
        
        # 상태 업데이트
        mail.status = status
        mail.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ 메일 상태 업데이트 완료 - 메일 ID: {mail_id}")
        return APIResponse(
            success=True,
            message="메일 상태가 성공적으로 업데이트되었습니다",
            data={"mail_id": mail_id, "status": status}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 메일 상태 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 상태 업데이트 중 오류가 발생했습니다: {str(e)}")

# 메일 삭제 (휴지통으로 이동)
@router.delete("/{mail_id}", response_model=APIResponse, summary="메일 삭제")
async def delete_mail(
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메일을 휴지통으로 이동합니다.
    
    - **mail_id**: 삭제할 메일의 고유 ID
    """
    try:
        logger.info(f"🗑️ 메일 삭제 - 메일 ID: {mail_id}")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.mail_id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 사용자 권한 확인
        user_folders = db.query(MailFolder).filter(
            MailFolder.user_email == current_user.email
        ).all()
        
        current_folder = None
        for folder in user_folders:
            mail_in_folder = db.query(MailInFolder).filter(
                and_(
                    MailInFolder.mail_id == mail_id,
                    MailInFolder.folder_id == folder.folder_id
                )
            ).first()
            
            if mail_in_folder:
                current_folder = folder
                break
        
        if not current_folder:
            raise HTTPException(status_code=403, detail="해당 메일에 접근할 권한이 없습니다")
        
        # 휴지통 폴더 조회
        trash_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user.email,
                MailFolder.folder_type == FolderType.TRASH
            )
        ).first()
        
        if not trash_folder:
            # 휴지통 폴더가 없으면 생성
            trash_folder = MailFolder(
                folder_id=str(uuid.uuid4()),
                user_email=current_user.email,
                folder_name="휴지통",
                folder_type=FolderType.TRASH
            )
            db.add(trash_folder)
            db.commit()
        
        # 현재 폴더에서 제거
        db.query(MailInFolder).filter(
            and_(
                MailInFolder.mail_id == mail_id,
                MailInFolder.folder_id == current_folder.folder_id
            )
        ).delete()
        
        # 휴지통으로 이동
        mail_in_trash = MailInFolder(
            mail_id=mail_id,
            folder_id=trash_folder.folder_id
        )
        db.add(mail_in_trash)
        db.commit()
        
        logger.info(f"✅ 메일 삭제 완료 - 메일 ID: {mail_id}")
        return APIResponse(
            success=True,
            message="메일이 휴지통으로 이동되었습니다",
            data={"mail_id": mail_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 메일 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 삭제 중 오류가 발생했습니다: {str(e)}")

# 메일 로그 조회
@router.get("/logs", response_model=List[Dict[str, Any]], summary="메일 로그 조회")
async def get_mail_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메일 발송/수신 로그를 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 로그 수 (최대 100개)
    """
    try:
        logger.info(f"📋 메일 로그 조회 - 사용자: {current_user.email}")
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        
        # 사용자 관련 메일 로그 조회
        logs = db.query(MailLog).filter(
            or_(
                MailLog.sender_email == current_user.email,
                MailLog.recipient_email == current_user.email
            )
        ).order_by(desc(MailLog.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        log_responses = []
        for log in logs:
            log_responses.append({
                "log_id": log.log_id,
                "mail_id": log.mail_id,
                "action": log.action,
                "sender_email": log.sender_email,
                "recipient_email": log.recipient_email,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at
            })
        
        logger.info(f"✅ 메일 로그 조회 완료 - {len(log_responses)}개")
        return log_responses
        
    except Exception as e:
        logger.error(f"❌ 메일 로그 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 로그 조회 중 오류가 발생했습니다: {str(e)}")
