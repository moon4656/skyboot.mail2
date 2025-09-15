from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query, Form
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

from mail_database import get_db, init_database
from mail_models import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from mail_schemas import (
    MailCreate, MailResponse, MailListResponse, MailDetailResponse,
    MailSendRequest, MailSendResponse, MailSearchRequest, MailSearchResponse,
    PaginationResponse, MailStatsResponse, APIResponse,
    RecipientType, MailStatus, MailPriority, FolderType
)
from mail_service import MailService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="SkyBoot Mail API",
    description="메일 발송, 수신, 관리를 위한 FastAPI 서비스",
    version="1.0.0"
)

# 보안 설정
security = HTTPBearer()

# 메일 서비스 초기화
mail_service = MailService()

# 첨부파일 저장 디렉토리
ATTACHMENT_DIR = "attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)

# 인증 의존성
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    JWT 토큰을 통한 사용자 인증
    """
    # 실제 구현에서는 JWT 토큰 검증 로직 필요
    # 현재는 간단한 예시로 구현
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
    
    # 토큰에서 사용자 정보 추출 (실제로는 JWT 디코딩)
    # 예시: user_email = decode_jwt_token(token)
    user_email = "user@test.com"  # 임시 사용자
    
    return {"email": user_email, "user_uuid": str(uuid.uuid4())}

@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 데이터베이스 초기화
    """
    logger.info("🚀 SkyBoot Mail API 시작")
    init_database()
    logger.info("✅ 데이터베이스 초기화 완료")

# 메일 발송 API
@app.post("/api/mail/send", response_model=MailSendResponse, summary="메일 발송")
async def send_mail(
    to_emails: str = Form(..., description="수신자 이메일 (쉼표로 구분)"),
    cc_emails: Optional[str] = Form(None, description="참조 이메일 (쉼표로 구분)"),
    bcc_emails: Optional[str] = Form(None, description="숨은참조 이메일 (쉼표로 구분)"),
    subject: str = Form(..., description="메일 제목"),
    content: str = Form(..., description="메일 내용"),
    priority: MailPriority = Form(MailPriority.NORMAL, description="메일 우선순위"),
    attachments: List[UploadFile] = File(None, description="첨부파일"),
    current_user: dict = Depends(get_current_user),
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
        logger.info(f"📧 메일 발송 시작 - 발신자: {current_user['email']}")
        
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
            sender_email=current_user["email"]
        )
        
        # 메일 서비스를 통해 발송
        result = await mail_service.send_mail(mail_request, attachment_paths, db)
        
        logger.info(f"✅ 메일 발송 완료 - 메일 ID: {result.mail_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 메일 발송 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")

# 받은 메일 목록 조회
@app.get("/api/mail/inbox", response_model=MailListResponse, summary="받은 메일 목록")
async def get_inbox_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 발신자)"),
    status: Optional[MailStatus] = Query(None, description="메일 상태 필터"),
    current_user: dict = Depends(get_current_user),
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
        logger.info(f"📥 받은 메일 목록 조회 - 사용자: {current_user['email']}")
        
        # 받은편지함 폴더 조회
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user["email"],
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
@app.get("/api/mail/inbox/{mail_id}", response_model=MailDetailResponse, summary="받은 메일 상세")
async def get_inbox_mail_detail(
    mail_id: str,
    current_user: dict = Depends(get_current_user),
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
                MailFolder.user_email == current_user["email"],
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
@app.get("/api/mail/sent", response_model=MailListResponse, summary="보낸 메일 목록")
async def get_sent_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    보낸 메일 목록을 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 메일 수 (최대 100개)
    - **search**: 제목이나 수신자로 검색
    """
    try:
        logger.info(f"📤 보낸 메일 목록 조회 - 사용자: {current_user['email']}")
        
        # 보낸편지함 폴더 조회
        sent_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user["email"],
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
@app.get("/api/mail/sent/{mail_id}", response_model=MailDetailResponse, summary="보낸 메일 상세")
async def get_sent_mail_detail(
    mail_id: str,
    current_user: dict = Depends(get_current_user),
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
                Mail.sender_email == current_user["email"]
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
@app.get("/api/mail/drafts", response_model=MailListResponse, summary="임시보관함 메일 목록")
async def get_draft_mails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 수신자)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    임시보관함 메일 목록을 조회합니다.
    
    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 표시할 메일 수 (최대 100개)
    - **search**: 제목이나 수신자로 검색
    """
    try:
        logger.info(f"📝 임시보관함 메일 목록 조회 - 사용자: {current_user['email']}")
        
        # 임시보관함 폴더 조회
        draft_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user["email"],
                MailFolder.folder_type == FolderType.DRAFTS
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
                subject=mail.subject or "(제목 없음)",
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

# 임시보관함 메일 상세 조회
@app.get("/api/mail/drafts/{mail_id}", response_model=MailDetailResponse, summary="임시보관함 메일 상세")
async def get_draft_mail_detail(
    mail_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    임시보관함 메일의 상세 정보를 조회합니다.
    
    - **mail_id**: 조회할 메일의 고유 ID
    """
    try:
        logger.info(f"📝 임시보관함 메일 상세 조회 - 메일 ID: {mail_id}")
        
        # 메일 조회 (임시보관함에 있는 메일만)
        draft_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_email == current_user["email"],
                MailFolder.folder_type == FolderType.DRAFTS
            )
        ).first()
        
        if not draft_folder:
            raise HTTPException(status_code=404, detail="임시보관함을 찾을 수 없습니다")
        
        mail_in_folder = db.query(MailInFolder).filter(
            and_(
                MailInFolder.mail_id == mail_id,
                MailInFolder.folder_id == draft_folder.folder_id
            )
        ).first()
        
        if not mail_in_folder:
            raise HTTPException(status_code=404, detail="임시보관함에서 메일을 찾을 수 없습니다")
        
        mail = db.query(Mail).filter(Mail.mail_id == mail_id).first()
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
            subject=mail.subject or "(제목 없음)",
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
        
        logger.info(f"✅ 임시보관함 메일 상세 조회 완료 - 메일 ID: {mail_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 임시보관함 메일 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임시보관함 메일 상세 조회 중 오류가 발생했습니다: {str(e)}")

# 첨부파일 다운로드
@app.get("/api/mail/attachments/{attachment_id}", summary="첨부파일 다운로드")
async def download_attachment(
    attachment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    첨부파일을 다운로드합니다.
    
    - **attachment_id**: 다운로드할 첨부파일의 고유 ID
    """
    try:
        logger.info(f"📎 첨부파일 다운로드 - 첨부파일 ID: {attachment_id}")
        
        # 첨부파일 정보 조회
        attachment = db.query(MailAttachment).filter(
            MailAttachment.attachment_id == attachment_id
        ).first()
        
        if not attachment:
            raise HTTPException(status_code=404, detail="첨부파일을 찾을 수 없습니다")
        
        # 메일 권한 확인 (사용자가 접근 가능한 메일의 첨부파일인지)
        mail = db.query(Mail).filter(Mail.mail_id == attachment.mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 파일 존재 확인
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="첨부파일이 서버에서 삭제되었습니다")
        
        logger.info(f"✅ 첨부파일 다운로드 완료 - 파일명: {attachment.original_filename}")
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

# 메일 삭제
@app.delete("/api/mail/{mail_id}", response_model=APIResponse, summary="메일 삭제")
async def delete_mail(
    mail_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메일을 삭제합니다.
    
    - **mail_id**: 삭제할 메일의 고유 ID
    """
    try:
        logger.info(f"🗑️ 메일 삭제 - 메일 ID: {mail_id}")
        
        # 메일 조회 및 권한 확인
        mail = db.query(Mail).filter(Mail.mail_id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 사용자 폴더에서 메일 제거
        user_folders = db.query(MailFolder).filter(
            MailFolder.user_email == current_user["email"]
        ).all()
        
        folder_ids = [folder.folder_id for folder in user_folders]
        
        mail_in_folders = db.query(MailInFolder).filter(
            and_(
                MailInFolder.mail_id == mail_id,
                MailInFolder.folder_id.in_(folder_ids)
            )
        ).all()
        
        if not mail_in_folders:
            raise HTTPException(status_code=403, detail="해당 메일을 삭제할 권한이 없습니다")
        
        # 폴더에서 메일 제거
        for mail_in_folder in mail_in_folders:
            db.delete(mail_in_folder)
        
        # 다른 사용자의 폴더에도 없다면 메일 완전 삭제
        remaining_folders = db.query(MailInFolder).filter(
            MailInFolder.mail_id == mail_id
        ).count()
        
        if remaining_folders == 0:
            # 첨부파일 삭제
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail_id
            ).all()
            
            for attachment in attachments:
                if os.path.exists(attachment.file_path):
                    os.remove(attachment.file_path)
                db.delete(attachment)
            
            # 수신자 정보 삭제
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail_id
            ).all()
            
            for recipient in recipients:
                db.delete(recipient)
            
            # 메일 삭제
            db.delete(mail)
        
        db.commit()
        
        logger.info(f"✅ 메일 삭제 완료 - 메일 ID: {mail_id}")
        return APIResponse(
            success=True,
            message="메일이 성공적으로 삭제되었습니다",
            data={"mail_id": mail_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 메일 삭제 실패: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"메일 삭제 중 오류가 발생했습니다: {str(e)}")

# 메일 통계
@app.get("/api/mail/stats", response_model=MailStatsResponse, summary="메일 통계")
async def get_mail_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 메일 통계를 조회합니다.
    """
    try:
        logger.info(f"📊 메일 통계 조회 - 사용자: {current_user['email']}")
        
        # 사용자 폴더 조회
        folders = db.query(MailFolder).filter(
            MailFolder.user_email == current_user["email"]
        ).all()
        
        folder_map = {folder.folder_type: folder.folder_id for folder in folders}
        
        stats = {
            "total_mails": 0,
            "unread_mails": 0,
            "inbox_count": 0,
            "sent_count": 0,
            "draft_count": 0,
            "trash_count": 0
        }
        
        # 받은편지함 통계
        if FolderType.INBOX in folder_map:
            inbox_query = db.query(Mail).join(MailInFolder).filter(
                MailInFolder.folder_id == folder_map[FolderType.INBOX]
            )
            stats["inbox_count"] = inbox_query.count()
            stats["unread_mails"] = inbox_query.filter(
                Mail.status == MailStatus.UNREAD
            ).count()
        
        # 보낸편지함 통계
        if FolderType.SENT in folder_map:
            stats["sent_count"] = db.query(Mail).join(MailInFolder).filter(
                MailInFolder.folder_id == folder_map[FolderType.SENT]
            ).count()
        
        # 임시보관함 통계
        if FolderType.DRAFTS in folder_map:
            stats["draft_count"] = db.query(Mail).join(MailInFolder).filter(
                MailInFolder.folder_id == folder_map[FolderType.DRAFTS]
            ).count()
        
        # 휴지통 통계
        if FolderType.TRASH in folder_map:
            stats["trash_count"] = db.query(Mail).join(MailInFolder).filter(
                MailInFolder.folder_id == folder_map[FolderType.TRASH]
            ).count()
        
        stats["total_mails"] = stats["inbox_count"] + stats["sent_count"] + stats["draft_count"]
        
        logger.info(f"✅ 메일 통계 조회 완료")
        return MailStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ 메일 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 통계 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)