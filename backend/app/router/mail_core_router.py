from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Form, status, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any, Union
import os
import uuid
import shutil
from datetime import datetime, timedelta
import mimetypes
import logging
import json

from ..database.user import get_db
from ..model.user_model import User
from ..model.mail_model import FolderType, Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog, generate_mail_uuid
from ..schemas.mail_schema import (
    APIResponse,
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
router = APIRouter()

# 보안 설정
security = HTTPBearer()

# 첨부파일 저장 디렉토리
ATTACHMENT_DIR = "attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)

# 안전한 첨부파일 처리를 위한 커스텀 dependency
async def safe_attachments_handler(
    request: Request
) -> Optional[List[UploadFile]]:
    """
    첨부파일을 안전하게 처리하는 dependency 함수
    클라이언트가 잘못된 형태의 데이터를 보내더라도 안전하게 처리합니다.
    """
    try:
        # multipart/form-data에서 첨부파일 필드 추출
        form = await request.form()
        logger.info(f"📎 Form 필드들: {list(form.keys())}")
        
        # 모든 필드 내용 확인
        for key, value in form.items():
            if isinstance(value, str):
                logger.info(f"📎 필드 '{key}': 타입={type(value)}, 값={value}")
            else:
                filename = getattr(value, "filename", "unknown")
                logger.info(f"📎 필드 '{key}': 타입={type(value)}, 값=파일객체({filename})")
        
        # 다양한 필드명으로 첨부파일 찾기
        attachments = form.getlist("attachments")
        if not attachments:
            attachments = form.getlist("files")  # 'files' 필드도 확인
        if not attachments:
            attachments = form.getlist("attachment")  # 단수형도 확인
        
        logger.info(f"📎 찾은 첨부파일: {len(attachments) if attachments else 0}개")
        
        if not attachments:
            logger.info("📎 첨부파일 없음")
            return None
            
        valid_files = []
        for i, attachment in enumerate(attachments):
            # UploadFile인지 확인
            if isinstance(attachment, UploadFile) and attachment.filename:
                valid_files.append(attachment)
                logger.debug(f"📎 유효한 첨부파일: {attachment.filename}")
            elif isinstance(attachment, str):
                logger.warning(f"⚠️ 문자열 형태의 첨부파일 무시: {attachment}")
            else:
                logger.warning(f"⚠️ 유효하지 않은 첨부파일 건너뜀 - 인덱스: {i}, 타입: {type(attachment)}")
        
        logger.debug(f"📎 처리된 첨부파일 개수: {len(valid_files)}")
        return valid_files if valid_files else None
        
    except Exception as e:
        logger.error(f"❌ 첨부파일 처리 중 오류: {str(e)}")
        return None


@router.post("/send", response_model=MailSendResponse, summary="메일 발송")
async def send_mail(
    to_emails: str = Form(..., description="수신자 이메일 (쉼표로 구분)"),
    cc_emails: Optional[str] = Form(None, description="참조 이메일 (쉼표로 구분)"),
    bcc_emails: Optional[str] = Form(None, description="숨은참조 이메일 (쉼표로 구분)"),
    subject: str = Form(..., description="메일 제목"),
    content: str = Form(..., description="메일 내용"),
    priority: MailPriority = Form(MailPriority.NORMAL, description="메일 우선순위"),
    is_draft: Optional[str] = Form("false", description="임시보관함 여부 (true/false)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
    attachments: Optional[List[UploadFile]] = File(None, description="첨부파일 목록")
) -> MailSendResponse:
    """
    메일 발송 API
    조직 내에서 메일을 발송합니다.
    """
    try:
        logger.info(f"📤 메일 발송 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 수신자: {to_emails}")
        logger.debug(f"🔍 첨부파일 정보 - 타입: {type(attachments)}, 값: {attachments}")
        
        # 조직 내에서 메일 사용자 조회
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found in this organization")
        
        # is_draft 파라미터 처리
        is_draft_bool = is_draft.lower() == "true" if is_draft else False
        
        # 메일 생성 (조직 ID 포함) - 년월일_시분초_uuid[12] 형식
        from ..model.mail_model import generate_mail_uuid
        mail_uuid = generate_mail_uuid()
        mail = Mail(
            mail_uuid=mail_uuid,
            sender_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            subject=subject,
            body_text=content,
            priority=priority,
            status=MailStatus.DRAFT if is_draft_bool else MailStatus.SENT,
            is_draft=is_draft_bool,
            created_at=datetime.utcnow(),
            sent_at=None if is_draft_bool else datetime.utcnow(),
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
                            user_id=f"external_{external_user_uuid[:8]}",  # user_id 필드 추가
                            user_uuid=external_user_uuid,
                            email=email,
                            password_hash="external_user",  # 외부 사용자 표시
                            is_active=False,
                            org_id=current_org_id  # 현재 조직에 속하도록 설정
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    recipient_type_value = RecipientType.TO.value
                    logger.info(f"🔍 DEBUG: RecipientType.TO.value = {recipient_type_value}")
                    logger.info(f"🔍 DEBUG: type(recipient_type_value) = {type(recipient_type_value)}")
                    
                    recipient = MailRecipient(
                        mail_uuid=mail.mail_uuid,
                        recipient_uuid=recipient_user.user_uuid,
                        recipient_email=email,  # 누락된 recipient_email 필드 추가
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
                            user_id=f"external_{external_user_uuid[:8]}",  # user_id 필드 추가
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
                        recipient_uuid=recipient_user.user_uuid,
                        recipient_email=email,  # 누락된 recipient_email 필드 추가
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
                            user_id=f"external_{external_user_uuid[:8]}",  # user_id 필드 추가
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
                        recipient_uuid=recipient_user.user_uuid,
                        recipient_email=email,  # 누락된 recipient_email 필드 추가
                        recipient_type=RecipientType.BCC.value
                    )
                    recipients.append(recipient)
                    db.add(recipient)
        
        # 첨부파일 처리
        attachment_list = []
        try:
            if attachments is not None and len(attachments) > 0:
                logger.info(f"📎 첨부파일 처리 시작 - 개수: {len(attachments)}")
                for i, attachment in enumerate(attachments):
                    if attachment and attachment.filename:
                        logger.info(f"📎 첨부파일 처리 중 - 파일명: {attachment.filename}, 타입: {attachment.content_type}")
                        
                        # 파일 저장
                        file_id = str(uuid.uuid4())
                        file_extension = os.path.splitext(attachment.filename)[1]
                        saved_filename = f"{file_id}{file_extension}"
                        file_path = os.path.join(ATTACHMENT_DIR, saved_filename)
                        
                        # 파일 내용 저장
                        with open(file_path, "wb") as buffer:
                            content = await attachment.read()
                            buffer.write(content)
                        
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
                        logger.info(f"✅ 첨부파일 저장 완료 - 파일명: {attachment.filename}, 크기: {mail_attachment.file_size}바이트")
                    else:
                        logger.warning(f"⚠️ 유효하지 않은 첨부파일 건너뜀 - 인덱스: {i}, 파일명: {getattr(attachment, 'filename', 'None')}")
            else:
                logger.info(f"📎 첨부파일 없음 - attachments: {attachments}")
        except Exception as attachment_error:
            logger.error(f"❌ 첨부파일 처리 중 오류 발생: {str(attachment_error)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # 첨부파일 오류가 있어도 메일 발송은 계속 진행
            attachment_list = []
        
        # 메일 로그 생성
        mail_log = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=mail_user.user_uuid,
            action="SEND",
            details=f"메일 발송 - 수신자: {len(recipients)}명"
        )
        db.add(mail_log)
        
        # 먼저 메일과 수신자 정보를 커밋 (외래키 제약 조건 해결)
        try:
            db.commit()
            logger.info(f"💾 메일 및 수신자 정보 저장 완료 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
        except Exception as commit_error:
            db.rollback()
            logger.error(f"❌ 메일 저장 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(commit_error)}")
            raise HTTPException(status_code=500, detail=f"메일 저장에 실패했습니다: {str(commit_error)}")
        
        # 실제 메일 발송 (SMTP) - 임시보관함이 아닌 경우에만
        smtp_result = {'success': True, 'error': None}  # 임시보관함의 경우 기본값
        if not is_draft_bool:
            try:
                mail_service = MailService(db)
                
                # 첨부파일 정보를 메일 서비스 형식으로 변환
                attachment_data = []
                if attachment_list:
                    for attachment in attachment_list:
                        attachment_data.append({
                            "filename": attachment.filename,
                            "file_path": attachment.file_path,
                            "file_size": attachment.file_size,
                            "content_type": attachment.content_type
                        })
                
                smtp_result = await mail_service.send_email_smtp(
                    sender_email=mail_user.email,
                    recipient_emails=[r.recipient_email for r in recipients],
                    subject=subject,
                    body_text=content,
                    body_html=None,  # Form 데이터에서는 HTML 본문이 없음
                    org_id=current_org_id,
                    attachments=attachment_data if attachment_data else None
                )
            
                # SMTP 발송 결과 디버깅
                logger.info(f"🔍 SMTP 발송 결과 디버깅 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                logger.info(f"🔍 SMTP 결과 타입: {type(smtp_result)}")
                logger.info(f"🔍 SMTP 결과 전체: {smtp_result}")
                logger.info(f"🔍 SMTP success 값: {smtp_result.get('success')}")
                logger.info(f"🔍 SMTP success 타입: {type(smtp_result.get('success'))}")
                logger.info(f"🔍 SMTP success 조건 결과: {smtp_result.get('success', False)}")
                logger.info(f"🔍 NOT 조건 결과: {not smtp_result.get('success', False)}")
                
                if not smtp_result.get('success', False):
                    logger.error(f"❌ SMTP 발송 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {smtp_result.get('error')}")
                    mail.status = MailStatus.FAILED
                    
                    # 실패 로그 추가
                    fail_log = MailLog(
                        mail_uuid=mail.mail_uuid,
                        user_uuid=mail_user.user_uuid,
                        action="SEND_FAILED",
                        details=f"SMTP 발송 실패: {smtp_result.get('error')}"
                    )
                    db.add(fail_log)
                else:
                    logger.info(f"✅ SMTP 발송 성공 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                    
            except Exception as smtp_error:
                logger.error(f"❌ SMTP 발송 예외 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(smtp_error)}")
                mail.status = MailStatus.FAILED
                
                # 실패 로그 추가
                fail_log = MailLog(
                    mail_uuid=mail.mail_uuid,
                    user_uuid=mail_user.user_uuid,
                    action="SEND_FAILED",
                    details=f"SMTP 발송 예외: {str(smtp_error)}"
                )
                db.add(fail_log)
                smtp_result = {'success': False, 'error': str(smtp_error)}
        else:
            logger.info(f"📝 임시보관함 메일 생성 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
        
        # 메일 폴더 할당 처리 (임시보관함 또는 보낸편지함)
        try:
            if is_draft_bool:
                # 임시보관함 폴더 조회
                draft_folder = db.query(MailFolder).filter(
                    and_(
                        MailFolder.user_uuid == mail_user.user_uuid,
                        MailFolder.org_id == current_org_id,
                        MailFolder.folder_type == FolderType.DRAFT
                    )
                ).first()
                
                if draft_folder:
                    # 이미 할당되어 있는지 확인
                    existing_relation = db.query(MailInFolder).filter(
                        and_(
                            MailInFolder.mail_uuid == mail.mail_uuid,
                            MailInFolder.folder_uuid == draft_folder.folder_uuid
                        )
                    ).first()
                    
                    if not existing_relation:
                        # 발신자의 임시보관함에 메일 할당
                        mail_in_folder = MailInFolder(
                            mail_uuid=mail.mail_uuid,
                            folder_uuid=draft_folder.folder_uuid,
                            user_uuid=mail_user.user_uuid
                        )
                        db.add(mail_in_folder)
                        logger.info(f"📁 메일을 발신자 임시보관함에 할당 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                    else:
                        logger.debug(f"📁 메일이 이미 임시보관함에 할당됨 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                else:
                    logger.warning(f"⚠️ 발신자 임시보관함을 찾을 수 없음 - 조직: {current_org_id}, 사용자: {mail_user.user_uuid}")
            else:
                # 발신자의 보낸편지함 조회
                sent_folder = db.query(MailFolder).filter(
                    and_(
                        MailFolder.user_uuid == mail_user.user_uuid,
                        MailFolder.org_id == current_org_id,
                        MailFolder.folder_type == FolderType.SENT
                    )
                ).first()
                
                if sent_folder:
                    # 이미 할당되어 있는지 확인
                    existing_relation = db.query(MailInFolder).filter(
                        and_(
                            MailInFolder.mail_uuid == mail.mail_uuid,
                            MailInFolder.folder_uuid == sent_folder.folder_uuid
                        )
                    ).first()
                    
                    if not existing_relation:
                        # 발신자의 보낸편지함에 메일 할당
                        mail_in_folder = MailInFolder(
                            mail_uuid=mail.mail_uuid,
                            folder_uuid=sent_folder.folder_uuid,
                            user_uuid=mail_user.user_uuid
                        )
                        db.add(mail_in_folder)
                        logger.info(f"📁 메일을 발신자 보낸편지함에 할당 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                    else:
                        logger.debug(f"📁 메일이 이미 보낸편지함에 할당됨 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                else:
                    logger.warning(f"⚠️ 발신자 보낸편지함을 찾을 수 없음 - 조직: {current_org_id}, 사용자: {mail_user.user_uuid}")
                
        except Exception as folder_error:
            logger.error(f"❌ 폴더 할당 중 오류 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(folder_error)}")
            # 폴더 할당 실패는 메일 발송 실패로 처리하지 않음
        
        # 폴더 할당 정보 커밋
        try:
            db.commit()
            logger.info(f"📁 폴더 할당 완료 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
        except Exception as folder_commit_error:
            logger.error(f"❌ 폴더 할당 커밋 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(folder_commit_error)}")
            # 폴더 할당 실패는 메일 발송 실패로 처리하지 않음
        
        # SMTP 발송 결과에 따라 응답 결정
        if smtp_result.get('success', False):
            logger.info(f"✅ 메일 발송 완료 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 수신자 수: {len(recipients)}, 첨부파일 수: {len(attachment_list)}")
            return MailSendResponse(
                success=True,
                message="메일이 성공적으로 발송되었습니다.",
                mail_uuid=mail.mail_uuid,
                sent_at=mail.sent_at
            )
        else:
            logger.error(f"❌ 메일 발송 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {smtp_result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"메일 발송에 실패했습니다: {smtp_result.get('error', '알 수 없는 오류')}"
            )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 메일 발송 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")


@router.post("/send-json", response_model=MailSendResponse, summary="메일 발송 (JSON)")
async def send_mail_json(
    mail_data: MailSendRequest,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailSendResponse:
    """
    JSON 요청으로 메일 발송 API
    조직 내에서 메일을 발송합니다.
    """
    try:
        logger.info(f"📤 메일 발송 시작 (JSON) - 조직: {current_org_id}, 사용자: {current_user.email}, 수신자: {mail_data.to}")
        
        # 조직 내에서 메일 사용자 조회
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found in this organization")
        
        # 메일 생성 (조직 ID 포함) - 년월일_시분초_uuid[12] 형식
        mail_uuid = generate_mail_uuid()
        mail = Mail(
            mail_uuid=mail_uuid,
            sender_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            subject=mail_data.subject,
            body_text=mail_data.body_text,
            body_html=mail_data.body_html,
            sent_at=datetime.utcnow(),
            status=MailStatus.SENT,
            priority=mail_data.priority
        )
        db.add(mail)
        db.flush()
        
        # 수신자 처리
        recipients = []
        
        # TO 수신자 처리 (조직별 격리)
        if mail_data.to:
            for email in mail_data.to:
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
                    recipient_uuid=recipient_user.user_uuid,  # 누락된 recipient_uuid 필드 추가
                    recipient_email=email,
                    recipient_type=RecipientType.TO.value
                )
                recipients.append(recipient)
                db.add(recipient)
        
        # CC 수신자 처리 (조직별 격리)
        if mail_data.cc:
            for email in mail_data.cc:
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
                    recipient_uuid=recipient_user.user_uuid,  # 누락된 recipient_uuid 필드 추가
                    recipient_email=email,
                    recipient_type=RecipientType.CC.value
                )
                recipients.append(recipient)
                db.add(recipient)
        
        # BCC 수신자 처리 (조직별 격리)
        if mail_data.bcc:
            for email in mail_data.bcc:
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
                    recipient_uuid=recipient_user.user_uuid,  # 누락된 recipient_uuid 필드 추가
                    recipient_email=email,
                    recipient_type=RecipientType.BCC.value
                )
                recipients.append(recipient)
                db.add(recipient)
        
        # 메일 로그 생성
        mail_log = MailLog(
            mail_uuid=mail.mail_uuid,
            user_uuid=mail_user.user_uuid,
            action="SEND",
            details=f"메일 발송 - 수신자: {len(recipients)}명"
        )
        db.add(mail_log)
        
        # 먼저 메일과 수신자 정보를 커밋
        try:
            db.commit()
            logger.info(f"💾 메일 및 수신자 정보 저장 완료 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
        except Exception as commit_error:
            db.rollback()
            logger.error(f"❌ 메일 저장 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(commit_error)}")
            raise HTTPException(status_code=500, detail=f"메일 저장에 실패했습니다: {str(commit_error)}")

        # 실제 메일 발송 (SMTP)
        try:
            mail_service = MailService(db)
            smtp_result = await mail_service.send_email_smtp(
                sender_email=mail_user.email,
                recipient_emails=[r.recipient_email for r in recipients],
                subject=mail_data.subject,
                body_text=mail_data.body_text,
                body_html=mail_data.body_html,
                org_id=current_org_id
            )
            
            if not smtp_result.get('success', False):
                logger.error(f"❌ SMTP 발송 실패 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {smtp_result.get('error')}")
                # 메일 상태를 실패로 업데이트
                mail.status = MailStatus.FAILED
                
                # 실패 로그 추가
                fail_log = MailLog(
                    mail_uuid=mail.mail_uuid,
                    user_uuid=mail_user.user_uuid,
                    action="SEND_FAILED",
                    details=f"SMTP 발송 실패: {smtp_result.get('error')}"
                )
                db.add(fail_log)
                db.commit()
            else:
                logger.info(f"✅ SMTP 발송 성공 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                
        except Exception as smtp_error:
            logger.error(f"❌ SMTP 발송 예외 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(smtp_error)}")
            # 메일 상태를 실패로 업데이트
            mail.status = MailStatus.FAILED
            
            # 실패 로그 추가
            fail_log = MailLog(
                mail_uuid=mail.mail_uuid,
                user_uuid=mail_user.user_uuid,
                action="SEND_FAILED",
                details=f"SMTP 발송 예외: {str(smtp_error)}"
            )
            db.add(fail_log)
            db.commit()
            smtp_result = {'success': False, 'error': str(smtp_error)}
        
        # SMTP 발송 결과에 따라 처리 분기
        logger.info(f"🔍 SMTP 발송 결과 디버깅 - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
        logger.info(f"🔍 SMTP 결과 타입: {type(smtp_result)}")
        logger.info(f"🔍 SMTP 결과 전체: {smtp_result}")
        logger.info(f"🔍 SMTP success 값: {smtp_result.get('success')}")
        logger.info(f"🔍 SMTP success 타입: {type(smtp_result.get('success'))}")
        logger.info(f"🔍 SMTP success 조건 결과: {smtp_result.get('success', False)}")
        
        if smtp_result.get('success', False):
            # SMTP 발송 성공 시 폴더 할당 처리
            try:
                # 발신자의 보낸편지함 조회
                sent_folder = db.query(MailFolder).filter(
                    and_(
                        MailFolder.user_uuid == mail_user.user_uuid,
                        MailFolder.org_id == current_org_id,
                        MailFolder.folder_type == FolderType.SENT
                    )
                ).first()
                
                if sent_folder:
                    # 이미 할당되어 있는지 확인
                    existing_relation = db.query(MailInFolder).filter(
                        and_(
                            MailInFolder.mail_uuid == mail.mail_uuid,
                            MailInFolder.folder_uuid == sent_folder.folder_uuid
                        )
                    ).first()
                    
                    if not existing_relation:
                        # 발신자의 보낸편지함에 메일 할당
                        mail_in_folder = MailInFolder(
                            mail_uuid=mail.mail_uuid,
                            folder_uuid=sent_folder.folder_uuid,
                            user_uuid=mail_user.user_uuid
                        )
                        db.add(mail_in_folder)
                        db.commit()
                        logger.info(f"📁 메일을 발신자 보낸편지함에 할당 (JSON) - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                    else:
                        logger.debug(f"📁 메일이 이미 보낸편지함에 할당됨 (JSON) - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}")
                else:
                    logger.warning(f"⚠️ 발신자 보낸편지함을 찾을 수 없음 (JSON) - 조직: {current_org_id}, 사용자: {mail_user.user_uuid}")
                    
            except Exception as folder_error:
                logger.error(f"❌ 폴더 할당 중 오류 (JSON) - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {str(folder_error)}")
                # 폴더 할당 실패는 메일 발송 실패로 처리하지 않음
            
            logger.info(f"✅ 메일 발송 완료 (JSON) - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 수신자 수: {len(recipients)}")
            return MailSendResponse(
                success=True,
                message="메일이 성공적으로 발송되었습니다.",
                mail_uuid=mail.mail_uuid,
                sent_at=mail.sent_at
            )
        else:
            logger.error(f"❌ 메일 발송 실패 (JSON) - 조직: {current_org_id}, 메일 ID: {mail.mail_uuid}, 오류: {smtp_result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"메일 발송에 실패했습니다: {smtp_result.get('error', '알 수 없는 오류')}"
            )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 메일 발송 실패 (JSON) - 조직: {current_org_id}, 사용자: {current_user.email}, 오류: {str(e)}")
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
            
            # 현재 사용자의 읽음 상태 조회 (MailInFolder에서)
            mail_in_folder = db.query(MailInFolder).filter(
                and_(
                    MailInFolder.mail_uuid == mail.mail_uuid,
                    MailInFolder.user_uuid == mail_user.user_uuid
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
                is_read=mail_in_folder.is_read if mail_in_folder else False
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
            MailRecipient.recipient_uuid == mail_user.user_uuid
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
            message="메일 상세 조회 성공",
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
            message="보낸 메일 상세 조회 성공",
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
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> MailDetailResponse:
    """임시보관함 메일 상세 조회"""
    try:
        logger.info(f"📧 get_draft_mail_detail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링)
        mail_user = db.query(MailUser).filter(
            and_(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            )
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="해당 조직에서 메일 사용자를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 필터링 및 발신자 확인)
        mail = db.query(Mail).filter(
            and_(
                Mail.mail_uuid == mail_uuid,
                Mail.org_id == current_org_id,
                Mail.sender_uuid == mail_user.user_uuid
            )
        ).first()
        if not mail:
            raise HTTPException(status_code=404, detail="임시보관함 메일을 찾을 수 없거나 접근 권한이 없습니다")
        
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
        
        logger.info(f"✅ get_draft_mail_detail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return MailDetailResponse(
            success=True,
            message="임시보관함 메일 상세 조회 성공",
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_draft_mail_detail 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
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
            sender_response = None
            if sender:
                sender_response = MailUserResponse(
                    user_uuid=sender.user_uuid,
                    email=sender.email,
                    display_name=sender.display_name,
                    is_active=sender.is_active,
                    created_at=sender.created_at,
                    updated_at=sender.updated_at
                )
            
            # 수신자 개수
            recipient_count = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).count()
            
            # 첨부파일 개수
            attachment_count = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).count()
            
            # 읽음 상태 확인 (수신자인 경우)
            is_read = None
            if mail.sender_uuid != mail_user.user_uuid:
                recipient_record = db.query(MailRecipient).filter(
                    MailRecipient.mail_uuid == mail.mail_uuid,
                    MailRecipient.recipient_uuid == mail_user.user_uuid
                ).first()
                is_read = recipient_record.is_read if recipient_record else None
            
            mail_response = MailListResponse(
                mail_uuid=mail.mail_uuid,
                subject=mail.subject,
                status=MailStatus(mail.status),
                is_draft=mail.status == MailStatus.DRAFT.value,
                priority=MailPriority(mail.priority),
                sent_at=mail.sent_at,
                created_at=mail.created_at,
                sender=sender_response,
                recipient_count=recipient_count,
                attachment_count=attachment_count,
                is_read=is_read
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
        
        logger.info(f"✅ get_trash_mail_detail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
        
        return MailDetailResponse(
            success=True,
            message="휴지통 메일 상세 조회 성공",
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
        
        # 첨부파일 다운로드 로그 생성
        mail_log = MailLog(
            action="download_attachment",
            details=f"첨부파일 다운로드 - 파일명: {attachment.filename}, 크기: {attachment.file_size}바이트",
            mail_uuid=attachment.mail_uuid,
            user_uuid=current_user.user_uuid,
            ip_address=None,  # TODO: 실제 IP 주소 추가
            user_agent=None   # TODO: 실제 User-Agent 추가
        )
        db.add(mail_log)
        db.commit()
        
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


@router.delete("/{mail_uuid}", response_model=Dict[str, Any], summary="메일 삭제")
async def delete_mail(
    mail_uuid: str,
    permanent: bool = Query(False, description="영구 삭제 여부"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    메일을 삭제합니다.
    
    - **mail_uuid**: 삭제할 메일의 UUID
    - **permanent**: True면 영구 삭제, False면 휴지통으로 이동 (기본값: False)
    """
    try:
        logger.info(f"🗑️ delete_mail 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 영구삭제: {permanent}")
        
        # 메일 서비스 인스턴스 생성
        mail_service = MailService(db)
        
        # 메일 삭제 실행
        success = await mail_service.delete_mail(
            org_id=current_org_id,
            user_uuid=current_user.user_uuid,
            mail_uuid=mail_uuid,
            permanent=permanent
        )
        
        if success:
            action_type = "영구 삭제" if permanent else "휴지통으로 이동"
            logger.info(f"✅ delete_mail 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 작업: {action_type}")
            
            return {
                "success": True,
                "message": f"메일이 성공적으로 {action_type}되었습니다.",
                "data": {"mail_uuid": mail_uuid, "permanent": permanent}
            }
        else:
            logger.warning(f"⚠️ delete_mail 실패 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}")
            return {
                "success": False,
                "message": "메일 삭제에 실패했습니다.",
                "data": {}
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ delete_mail 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일UUID: {mail_uuid}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 삭제 중 오류가 발생했습니다: {str(e)}")