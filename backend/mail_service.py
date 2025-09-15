import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import os
import uuid
import logging
import mimetypes
from pathlib import Path

from mail_models import (
    Mail, MailUser, MailRecipient, MailAttachment, 
    MailFolder, MailInFolder, MailLog
)
from mail_schemas import (
    MailCreate, MailUpdate, RecipientBase, MailStatus,
    MailPriority, RecipientType, PaginationParams,
    MailSearchParams, SendMailResult
)

# 로깅 설정
logger = logging.getLogger(__name__)

class MailService:
    """
    메일 서비스 클래스 - 메일 발송, 수신, 관리 기능을 제공합니다.
    """
    
    def __init__(self):
        # SMTP 설정
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        
        # IMAP 설정
        self.imap_server = os.getenv("IMAP_SERVER", "localhost")
        self.imap_port = int(os.getenv("IMAP_PORT", "143"))
        self.imap_use_ssl = os.getenv("IMAP_USE_SSL", "false").lower() == "true"
        
        # 첨부파일 저장 경로
        self.attachment_path = Path(os.getenv("ATTACHMENT_PATH", "./attachments"))
        self.attachment_path.mkdir(exist_ok=True)
    
    def create_mail(self, db: Session, mail_data: MailCreate, sender_id: int) -> Mail:
        """
        새 메일을 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            mail_data: 메일 생성 데이터
            sender_id: 발신자 ID
            
        Returns:
            Mail: 생성된 메일 객체
        """
        try:
            # 메일 객체 생성
            mail = Mail(
                sender_id=sender_id,
                subject=mail_data.subject,
                body_text=mail_data.body_text,
                body_html=mail_data.body_html,
                priority=mail_data.priority,
                is_draft=mail_data.is_draft,
                status=MailStatus.DRAFT if mail_data.is_draft else MailStatus.SENT
            )
            
            db.add(mail)
            db.flush()  # ID 생성을 위해 flush
            
            # 수신자 추가
            for recipient_data in mail_data.recipients:
                # 수신자 사용자 찾기 또는 생성
                recipient_user = db.query(MailUser).filter(
                    MailUser.email == recipient_data.email
                ).first()
                
                if not recipient_user:
                    # 외부 사용자인 경우 임시 사용자 생성
                    recipient_user = MailUser(
                        email=recipient_data.email,
                        password_hash="external_user",
                        display_name=recipient_data.email.split('@')[0],
                        is_active=False
                    )
                    db.add(recipient_user)
                    db.flush()
                
                # 수신자 관계 생성
                mail_recipient = MailRecipient(
                    mail_id=mail.id,
                    recipient_id=recipient_user.id,
                    recipient_type=recipient_data.recipient_type
                )
                db.add(mail_recipient)
            
            # 즉시 발송이 요청된 경우
            if mail_data.send_immediately and not mail_data.is_draft:
                mail.sent_at = datetime.utcnow()
                self._send_mail_smtp(mail, db)
            
            db.commit()
            
            # 로그 기록
            self._log_mail_action(db, mail.id, "create", "success", "메일이 생성되었습니다.")
            
            logger.info(f"✅ 메일 생성 완료 - ID: {mail.id}, 제목: {mail.subject}")
            return mail
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 메일 생성 실패: {e}")
            raise
    
    def send_mail(self, db: Session, mail_id: int) -> SendMailResult:
        """
        메일을 발송합니다.
        
        Args:
            db: 데이터베이스 세션
            mail_id: 메일 ID
            
        Returns:
            SendMailResult: 발송 결과
        """
        try:
            mail = db.query(Mail).filter(Mail.id == mail_id).first()
            if not mail:
                raise ValueError(f"메일을 찾을 수 없습니다: {mail_id}")
            
            if mail.status == MailStatus.SENT:
                return SendMailResult(
                    mail_uuid=mail.mail_uuid,
                    status=MailStatus.SENT,
                    sent_at=mail.sent_at,
                    message="이미 발송된 메일입니다.",
                    failed_recipients=[]
                )
            
            # SMTP로 메일 발송
            failed_recipients = self._send_mail_smtp(mail, db)
            
            # 상태 업데이트
            if not failed_recipients:
                mail.status = MailStatus.SENT
                mail.sent_at = datetime.utcnow()
                mail.is_draft = False
                message = "메일이 성공적으로 발송되었습니다."
            else:
                mail.status = MailStatus.FAILED
                message = f"일부 수신자에게 발송 실패: {', '.join(failed_recipients)}"
            
            db.commit()
            
            # 로그 기록
            self._log_mail_action(db, mail.id, "send", 
                                "success" if not failed_recipients else "failed", 
                                message)
            
            return SendMailResult(
                mail_uuid=mail.mail_uuid,
                status=mail.status,
                sent_at=mail.sent_at,
                message=message,
                failed_recipients=failed_recipients
            )
            
        except Exception as e:
            logger.error(f"❌ 메일 발송 실패: {e}")
            self._log_mail_action(db, mail_id, "send", "failed", str(e))
            raise
    
    def _send_mail_smtp(self, mail: Mail, db: Session) -> List[str]:
        """
        SMTP를 통해 실제 메일을 발송합니다.
        
        Args:
            mail: 메일 객체
            db: 데이터베이스 세션
            
        Returns:
            List[str]: 발송 실패한 수신자 이메일 목록
        """
        failed_recipients = []
        
        try:
            # SMTP 서버 연결
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            # 인증 (필요한 경우)
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # 발신자 정보
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            from_email = sender.email
            
            # 수신자 목록 구성
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.id
            ).all()
            
            to_emails = []
            cc_emails = []
            bcc_emails = []
            
            for recipient in recipients:
                recipient_user = db.query(MailUser).filter(
                    MailUser.id == recipient.recipient_id
                ).first()
                
                if recipient.recipient_type == RecipientType.TO:
                    to_emails.append(recipient_user.email)
                elif recipient.recipient_type == RecipientType.CC:
                    cc_emails.append(recipient_user.email)
                elif recipient.recipient_type == RecipientType.BCC:
                    bcc_emails.append(recipient_user.email)
            
            # 메일 메시지 구성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = mail.subject
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 우선순위 설정
            if mail.priority == MailPriority.HIGH:
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif mail.priority == MailPriority.LOW:
                msg['X-Priority'] = '5'
                msg['X-MSMail-Priority'] = 'Low'
            
            # 본문 추가
            if mail.body_text:
                text_part = MIMEText(mail.body_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if mail.body_html:
                html_part = MIMEText(mail.body_html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 첨부파일 추가
            attachments = db.query(MailAttachment).filter(
                MailAttachment.mail_id == mail.id
            ).all()
            
            for attachment in attachments:
                try:
                    with open(attachment.file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment.original_filename}'
                        )
                        msg.attach(part)
                except Exception as e:
                    logger.warning(f"첨부파일 추가 실패: {attachment.filename} - {e}")
            
            # 모든 수신자 목록
            all_recipients = to_emails + cc_emails + bcc_emails
            
            # 메일 발송
            try:
                server.send_message(msg, from_email, all_recipients)
                logger.info(f"✅ 메일 발송 성공 - 수신자: {len(all_recipients)}명")
            except Exception as e:
                logger.error(f"❌ 메일 발송 실패: {e}")
                failed_recipients = all_recipients
            
            server.quit()
            
        except Exception as e:
            logger.error(f"❌ SMTP 연결 실패: {e}")
            # 모든 수신자를 실패로 처리
            recipients = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail.id
            ).all()
            failed_recipients = [r.recipient.email for r in recipients]
        
        return failed_recipients
    
    def get_sent_mails(self, db: Session, user_id: int, 
                      pagination: PaginationParams,
                      search: Optional[MailSearchParams] = None) -> Tuple[List[Mail], int]:
        """
        보낸 메일 목록을 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            pagination: 페이지네이션 매개변수
            search: 검색 매개변수
            
        Returns:
            Tuple[List[Mail], int]: (메일 목록, 전체 개수)
        """
        query = db.query(Mail).filter(
            Mail.sender_id == user_id,
            Mail.is_draft == False,
            Mail.status == MailStatus.SENT
        )
        
        # 검색 조건 적용
        if search:
            query = self._apply_search_filters(query, search)
        
        # 전체 개수
        total = query.count()
        
        # 정렬
        if pagination.sort_order == "desc":
            query = query.order_by(desc(getattr(Mail, pagination.sort_by)))
        else:
            query = query.order_by(asc(getattr(Mail, pagination.sort_by)))
        
        # 페이지네이션
        offset = (pagination.page - 1) * pagination.size
        mails = query.offset(offset).limit(pagination.size).all()
        
        return mails, total
    
    def get_received_mails(self, db: Session, user_id: int,
                          pagination: PaginationParams,
                          search: Optional[MailSearchParams] = None) -> Tuple[List[Mail], int]:
        """
        받은 메일 목록을 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            pagination: 페이지네이션 매개변수
            search: 검색 매개변수
            
        Returns:
            Tuple[List[Mail], int]: (메일 목록, 전체 개수)
        """
        query = db.query(Mail).join(MailRecipient).filter(
            MailRecipient.recipient_id == user_id,
            Mail.status == MailStatus.SENT,
            MailRecipient.is_deleted == False
        )
        
        # 검색 조건 적용
        if search:
            query = self._apply_search_filters(query, search)
        
        # 전체 개수
        total = query.count()
        
        # 정렬
        if pagination.sort_order == "desc":
            query = query.order_by(desc(getattr(Mail, pagination.sort_by)))
        else:
            query = query.order_by(asc(getattr(Mail, pagination.sort_by)))
        
        # 페이지네이션
        offset = (pagination.page - 1) * pagination.size
        mails = query.offset(offset).limit(pagination.size).all()
        
        return mails, total
    
    def get_draft_mails(self, db: Session, user_id: int,
                       pagination: PaginationParams) -> Tuple[List[Mail], int]:
        """
        임시보관함 메일 목록을 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            pagination: 페이지네이션 매개변수
            
        Returns:
            Tuple[List[Mail], int]: (메일 목록, 전체 개수)
        """
        query = db.query(Mail).filter(
            Mail.sender_id == user_id,
            Mail.is_draft == True
        )
        
        # 전체 개수
        total = query.count()
        
        # 정렬
        if pagination.sort_order == "desc":
            query = query.order_by(desc(getattr(Mail, pagination.sort_by)))
        else:
            query = query.order_by(asc(getattr(Mail, pagination.sort_by)))
        
        # 페이지네이션
        offset = (pagination.page - 1) * pagination.size
        mails = query.offset(offset).limit(pagination.size).all()
        
        return mails, total
    
    def get_mail_detail(self, db: Session, mail_id: int, user_id: int) -> Optional[Mail]:
        """
        메일 상세 정보를 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            mail_id: 메일 ID
            user_id: 사용자 ID
            
        Returns:
            Optional[Mail]: 메일 객체 또는 None
        """
        # 발신자이거나 수신자인 메일만 조회 가능
        mail = db.query(Mail).filter(
            Mail.id == mail_id,
            or_(
                Mail.sender_id == user_id,
                Mail.recipients.any(MailRecipient.recipient_id == user_id)
            )
        ).first()
        
        if mail:
            # 받은 메일인 경우 읽음 처리
            recipient = db.query(MailRecipient).filter(
                MailRecipient.mail_id == mail_id,
                MailRecipient.recipient_id == user_id
            ).first()
            
            if recipient and not recipient.is_read:
                recipient.is_read = True
                recipient.read_at = datetime.utcnow()
                db.commit()
                
                # 로그 기록
                self._log_mail_action(db, mail_id, "read", "success", "메일을 읽었습니다.")
        
        return mail
    
    def update_mail(self, db: Session, mail_id: int, user_id: int, 
                   mail_data: MailUpdate) -> Optional[Mail]:
        """
        메일을 수정합니다. (임시보관함 메일만 수정 가능)
        
        Args:
            db: 데이터베이스 세션
            mail_id: 메일 ID
            user_id: 사용자 ID
            mail_data: 수정할 메일 데이터
            
        Returns:
            Optional[Mail]: 수정된 메일 객체 또는 None
        """
        try:
            mail = db.query(Mail).filter(
                Mail.id == mail_id,
                Mail.sender_id == user_id,
                Mail.is_draft == True
            ).first()
            
            if not mail:
                return None
            
            # 메일 정보 업데이트
            if mail_data.subject is not None:
                mail.subject = mail_data.subject
            if mail_data.body_text is not None:
                mail.body_text = mail_data.body_text
            if mail_data.body_html is not None:
                mail.body_html = mail_data.body_html
            if mail_data.priority is not None:
                mail.priority = mail_data.priority
            
            # 수신자 업데이트
            if mail_data.recipients is not None:
                # 기존 수신자 삭제
                db.query(MailRecipient).filter(
                    MailRecipient.mail_id == mail_id
                ).delete()
                
                # 새 수신자 추가
                for recipient_data in mail_data.recipients:
                    recipient_user = db.query(MailUser).filter(
                        MailUser.email == recipient_data.email
                    ).first()
                    
                    if not recipient_user:
                        recipient_user = MailUser(
                            email=recipient_data.email,
                            password_hash="external_user",
                            display_name=recipient_data.email.split('@')[0],
                            is_active=False
                        )
                        db.add(recipient_user)
                        db.flush()
                    
                    mail_recipient = MailRecipient(
                        mail_id=mail.id,
                        recipient_id=recipient_user.id,
                        recipient_type=recipient_data.recipient_type
                    )
                    db.add(mail_recipient)
            
            mail.updated_at = datetime.utcnow()
            db.commit()
            
            # 로그 기록
            self._log_mail_action(db, mail_id, "update", "success", "메일이 수정되었습니다.")
            
            return mail
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 메일 수정 실패: {e}")
            raise
    
    def delete_mail(self, db: Session, mail_id: int, user_id: int) -> bool:
        """
        메일을 삭제합니다.
        
        Args:
            db: 데이터베이스 세션
            mail_id: 메일 ID
            user_id: 사용자 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 발신자인 경우 - 임시보관함 메일만 완전 삭제
            if db.query(Mail).filter(
                Mail.id == mail_id,
                Mail.sender_id == user_id,
                Mail.is_draft == True
            ).first():
                # 완전 삭제
                db.query(MailRecipient).filter(MailRecipient.mail_id == mail_id).delete()
                db.query(MailAttachment).filter(MailAttachment.mail_id == mail_id).delete()
                db.query(Mail).filter(Mail.id == mail_id).delete()
            else:
                # 수신자인 경우 - 논리적 삭제
                recipient = db.query(MailRecipient).filter(
                    MailRecipient.mail_id == mail_id,
                    MailRecipient.recipient_id == user_id
                ).first()
                
                if recipient:
                    recipient.is_deleted = True
                    recipient.deleted_at = datetime.utcnow()
                else:
                    return False
            
            db.commit()
            
            # 로그 기록
            self._log_mail_action(db, mail_id, "delete", "success", "메일이 삭제되었습니다.")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 메일 삭제 실패: {e}")
            return False
    
    def save_attachment(self, file_content: bytes, filename: str, 
                      content_type: str) -> Tuple[str, str]:
        """
        첨부파일을 저장합니다.
        
        Args:
            file_content: 파일 내용
            filename: 파일명
            content_type: MIME 타입
            
        Returns:
            Tuple[str, str]: (저장된 파일 경로, 파일 UUID)
        """
        try:
            # 파일 UUID 생성
            file_uuid = str(uuid.uuid4())
            
            # 파일 확장자 추출
            file_ext = Path(filename).suffix
            
            # 저장할 파일명 생성
            saved_filename = f"{file_uuid}{file_ext}"
            
            # 날짜별 디렉토리 생성
            today = datetime.now().strftime("%Y/%m/%d")
            save_dir = self.attachment_path / today
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            file_path = save_dir / saved_filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"✅ 첨부파일 저장 완료: {filename} -> {file_path}")
            return str(file_path), file_uuid
            
        except Exception as e:
            logger.error(f"❌ 첨부파일 저장 실패: {e}")
            raise
    
    def _apply_search_filters(self, query, search: MailSearchParams):
        """
        검색 조건을 쿼리에 적용합니다.
        
        Args:
            query: SQLAlchemy 쿼리 객체
            search: 검색 매개변수
            
        Returns:
            수정된 쿼리 객체
        """
        if search.query:
            search_term = f"%{search.query}%"
            query = query.filter(
                or_(
                    Mail.subject.ilike(search_term),
                    Mail.body_text.ilike(search_term),
                    Mail.body_html.ilike(search_term)
                )
            )
        
        if search.subject:
            query = query.filter(Mail.subject.ilike(f"%{search.subject}%"))
        
        if search.status:
            query = query.filter(Mail.status == search.status)
        
        if search.priority:
            query = query.filter(Mail.priority == search.priority)
        
        if search.is_draft is not None:
            query = query.filter(Mail.is_draft == search.is_draft)
        
        if search.date_from:
            query = query.filter(Mail.created_at >= search.date_from)
        
        if search.date_to:
            query = query.filter(Mail.created_at <= search.date_to)
        
        if search.has_attachments is not None:
            if search.has_attachments:
                query = query.filter(Mail.attachments.any())
            else:
                query = query.filter(~Mail.attachments.any())
        
        return query
    
    def _log_mail_action(self, db: Session, mail_id: int, action: str, 
                        status: str, message: str):
        """
        메일 액션 로그를 기록합니다.
        
        Args:
            db: 데이터베이스 세션
            mail_id: 메일 ID
            action: 액션 타입
            status: 상태
            message: 메시지
        """
        try:
            log = MailLog(
                mail_id=mail_id,
                action=action,
                status=status,
                message=message
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"❌ 로그 기록 실패: {e}")