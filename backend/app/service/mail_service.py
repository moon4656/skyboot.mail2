"""
메일 관리 서비스

SaaS 다중 조직 지원을 위한 메일 관리 기능
"""
import logging
import uuid
import smtplib
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fastapi import HTTPException

from ..model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog, User, Organization
from ..schemas.mail_schema import MailCreate, MailSendRequest, RecipientType, MailStatus, MailPriority
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)


class MailService:
    """
    메일 서비스 클래스
    SaaS 다중 조직 지원을 위한 메일 발송, 조회, 관리 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.smtp_server = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
    
    async def send_mail(
        self,
        org_id: str,
        sender_uuid: str,
        to_emails: List[str],
        subject: str,
        content: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        priority: MailPriority = MailPriority.NORMAL,
        attachments: Optional[List[Dict[str, Any]]] = None,
        save_to_sent: bool = True
    ) -> Dict[str, Any]:
        """
        조직 내에서 메일을 발송합니다.
        
        Args:
            org_id: 조직 ID
            sender_uuid: 발송자 사용자 ID
            to_emails: 수신자 이메일 목록
            subject: 메일 제목
            content: 메일 내용
            cc_emails: 참조 이메일 목록
            bcc_emails: 숨은참조 이메일 목록
            priority: 메일 우선순위
            attachments: 첨부파일 목록
            save_to_sent: 보낸 메일함에 저장 여부
            
        Returns:
            발송 결과 딕셔너리
        """
        try:
            logger.info(f"📤 메일 발송 시작 - 조직 ID: {org_id}, 발송자 ID: {sender_uuid}, 수신자: {to_emails}, 제목: {subject}")
            
            # 조직 및 사용자 검증
            organization = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not organization or not organization.is_active:
                raise HTTPException(status_code=404, detail="조직을 찾을 수 없거나 비활성화되었습니다.")
            
            sender = self.db.query(User).filter(
                User.user_uuid == sender_uuid,
                User.org_id == org_id,
                User.is_active == True
            ).first()
            if not sender:
                raise HTTPException(status_code=404, detail="발송자를 찾을 수 없습니다.")
            
            # 발송자 메일 사용자 조회
            sender_mail_user = self.db.query(MailUser).filter(
                MailUser.user_uuid == sender_uuid,
                MailUser.org_id == org_id
            ).first()
            if not sender_mail_user:
                raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")
            
            # 메일 ID 생성
            mail_uuid = str(uuid.uuid4())
            
            # 메일 레코드 생성
            mail = Mail(
                mail_uuid=mail_uuid,
                org_id=org_id,
                sender_uuid=sender_mail_user.user_uuid,
                sender_email=sender_mail_user.email,
                subject=subject,
                content=content,
                priority=priority.value,
                status=MailStatus.SENT.value,
                sent_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(mail)
            
            # 수신자 정보 저장
            all_recipients = []
            
            # TO 수신자
            for email in to_emails:
                recipient = MailRecipient(
                    mail_uuid=mail_uuid,
                    recipient_email=email,
                    recipient_type=RecipientType.TO.value
                )
                self.db.add(recipient)
                all_recipients.append(email)
            
            # CC 수신자
            if cc_emails:
                for email in cc_emails:
                    recipient = MailRecipient(
                        mail_uuid=mail_uuid,
                        recipient_email=email,
                        recipient_type=RecipientType.CC.value
                    )
                    self.db.add(recipient)
                    all_recipients.append(email)
            
            # BCC 수신자
            if bcc_emails:
                for email in bcc_emails:
                    recipient = MailRecipient(
                        mail_uuid=mail_uuid,
                        recipient_email=email,
                        recipient_type=RecipientType.BCC.value
                    )
                    self.db.add(recipient)
                    all_recipients.append(email)
            
            # 첨부파일 정보 저장
            if attachments:
                for attachment in attachments:
                    mail_attachment = MailAttachment(
                        mail_uuid=mail_uuid,
                        filename=attachment["filename"],
                        file_path=attachment["file_path"],
                        file_size=attachment["file_size"],
                        content_type=attachment["content_type"]
                    )
                    self.db.add(mail_attachment)
            
            # 실제 메일 발송 (SMTP)
            await self._send_smtp_mail(
                sender_mail_user.email,
                all_recipients,
                subject,
                content,
                attachments
            )
            
            # 메일 로그 기록
            mail_log = MailLog(
                mail_uuid=mail_uuid,
                action="send",
                user_email=sender_mail_user.email,
                details=f"메일 발송 완료 - 수신자: {len(all_recipients)}명",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(mail_log)
            
            # 보낸 메일함에 저장
            if save_to_sent:
                sent_folder = await self._get_or_create_folder(org_id, sender_uuid, "sent")
                mail_in_folder = MailInFolder(
                    mail_uuid=mail_uuid,
                    folder_uuid=sent_folder.folder_uuid,
                    user_uuid=sender_uuid
                )
                self.db.add(mail_in_folder)
            
            self.db.commit()
            
            logger.info(f"✅ 메일 발송 완료 - 메일 UUID: {mail_uuid}")
            
            return {
                "success": True,
                "mail_uuid": mail_uuid,
                "message": "메일이 성공적으로 발송되었습니다.",
                "recipients_count": len(all_recipients),
                "sent_at": mail.sent_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 메일 발송 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"메일 발송 중 오류가 발생했습니다: {str(e)}")
    
    async def _send_smtp_mail(
        self,
        sender_email: str,
        recipients: List[str],
        subject: str,
        content: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ):
        """
        SMTP를 통해 실제 메일을 발송합니다.
        
        Args:
            sender_email: 발송자 이메일
            recipients: 수신자 이메일 목록
            subject: 메일 제목
            content: 메일 내용
            attachments: 첨부파일 목록
        """
        try:
            # MIME 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # 메일 본문 추가
            msg.attach(MIMEText(content, 'html', 'utf-8'))
            
            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment["file_path"]):
                        with open(attachment["file_path"], "rb") as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {attachment["filename"]}'
                            )
                            msg.attach(part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
                
            logger.info(f"✅ SMTP 메일 발송 성공 - 수신자: {len(recipients)}명")
            
        except Exception as e:
            logger.error(f"❌ SMTP 메일 발송 실패: {str(e)}")
            raise
    
    async def get_mails_by_folder(
        self,
        org_id: str,
        user_uuid: str,
        folder_type: str,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[MailStatus] = None
    ) -> Dict[str, Any]:
        """
        조직 내 사용자의 특정 폴더 메일을 조회합니다.
        
        Args:
            org_id: 조직 ID
            user_uuid: 사용자 UUID
            folder_type: 폴더 타입 (inbox, sent, drafts, trash)
            page: 페이지 번호
            limit: 페이지당 항목 수
            search: 검색어
            status: 메일 상태 필터
            
        Returns:
            메일 목록 및 페이지네이션 정보
        """
        try:
            logger.info(f"📬 메일 조회 - 조직 ID: {org_id}, 사용자 ID: {user_id}, 폴더: {folder_type}")
            
            # 사용자 검증
            user = self.db.query(User).filter(
                User.user_uuid == user_uuid,
                User.org_id == org_id,
                User.is_active == True
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 메일 사용자 조회
            mail_user = self.db.query(MailUser).filter(
                MailUser.user_uuid == user_uuid,
                MailUser.org_id == org_id
            ).first()
            if not mail_user:
                raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")
            
            # 오프셋 계산
            offset = (page - 1) * limit
            
            # 폴더별 쿼리 구성
            if folder_type == "inbox":
                # 받은 메일함
                query = self.db.query(Mail).join(
                    MailRecipient, Mail.mail_uuid == MailRecipient.mail_uuid
                ).filter(
                    Mail.org_id == org_id,
                    MailRecipient.recipient_uuid == mail_user.user_uuid,
                    Mail.status != MailStatus.DELETED.value
                )
            elif folder_type == "sent":
                # 보낸 메일함
                query = self.db.query(Mail).filter(
                    Mail.org_id == org_id,
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.status == MailStatus.SENT.value
                )
            elif folder_type == "drafts":
                # 임시보관함
                query = self.db.query(Mail).filter(
                    Mail.org_id == org_id,
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.status == MailStatus.DRAFT.value
                )
            elif folder_type == "trash":
                # 휴지통 - 삭제된 메일만 조회
                query = self.db.query(Mail).filter(
                    Mail.org_id == org_id,
                    Mail.status == MailStatus.DELETED.value,
                    or_(
                        Mail.sender_uuid == mail_user.user_uuid,
                        Mail.mail_uuid.in_(
                            self.db.query(MailRecipient.mail_uuid).filter(
                                MailRecipient.recipient_uuid == mail_user.user_uuid
                            )
                        )
                    )
                )
            else:
                raise HTTPException(status_code=400, detail=f"지원하지 않는 폴더 타입: {folder_type}")
            
            # 검색 조건 추가
            if search:
                query = query.filter(
                    or_(
                        Mail.subject.ilike(f"%{search}%"),
                        Mail.content.ilike(f"%{search}%"),
                        Mail.sender_email.ilike(f"%{search}%")
                    )
                )
            
            # 상태 필터 추가
            if status:
                query = query.filter(Mail.status == status.value)
            
            # 정렬 및 페이지네이션
            total_count = query.count()
            mails = query.order_by(desc(Mail.created_at)).offset(offset).limit(limit).all()
            
            # 결과 포맷팅
            mail_list = []
            for mail in mails:
                # 수신자 정보 조회
                recipients = self.db.query(MailRecipient).filter(
                    MailRecipient.mail_uuid == mail.mail_uuid
                ).all()
                
                # 첨부파일 정보 조회
                attachments = self.db.query(MailAttachment).filter(
                    MailAttachment.mail_uuid == mail.mail_uuid
                ).all()
                
                mail_data = {
                    "mail_uuid": mail.mail_uuid,
                    "sender_email": mail.sender_email,
                    "subject": mail.subject,
                    "content": mail.content[:200] + "..." if len(mail.content) > 200 else mail.content,
                    "priority": mail.priority,
                    "status": mail.status,
                    "sent_at": mail.sent_at.isoformat() if mail.sent_at else None,
                    "created_at": mail.created_at.isoformat(),
                    "recipients": [
                        {
                            "email": r.recipient_email,
                            "type": r.recipient_type,
                            "is_read": r.is_read
                        } for r in recipients
                    ],
                    "attachments_count": len(attachments),
                    "has_attachments": len(attachments) > 0
                }
                mail_list.append(mail_data)
            
            return {
                "mails": mail_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": (total_count + limit - 1) // limit,
                    "total_items": total_count,
                    "items_per_page": limit
                },
                "folder_type": folder_type
            }
            
        except Exception as e:
            logger.error(f"❌ 메일 조회 실패: {str(e)}")
            raise
    
    async def get_mail_detail(
        self,
        org_id: str,
        user_uuid: str,
        mail_uuid: str
    ) -> Dict[str, Any]:
        """
        조직 내 사용자의 특정 메일 상세 정보를 조회합니다.
        
        Args:
            org_id: 조직 ID
            user_uuid: 사용자 UUID
            mail_uuid: 메일 UUID
            
        Returns:
            메일 상세 정보
        """
        try:
            logger.info(f"📧 메일 상세 조회 - 조직 ID: {org_id}, 사용자 ID: {user_uuid}, 메일 UUID: {mail_uuid}")
            
            # 사용자 검증
            user = self.db.query(User).filter(
                User.user_uuid == user_uuid,
                User.org_id == org_id,
                User.is_active == True
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 메일 사용자 조회
            mail_user = self.db.query(MailUser).filter(
                MailUser.user_uuid == user.user_uuid,
                MailUser.org_id == org_id
            ).first()
            if not mail_user:
                raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")
            
            # 메일 조회 (조직 내에서만)
            mail = self.db.query(Mail).filter(
                Mail.mail_uuid == mail_uuid,
                Mail.org_id == org_id
            ).first()
            if not mail:
                raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
            
            # 접근 권한 확인 (발송자이거나 수신자여야 함)
            is_sender = mail.sender_uuid == mail_user.user_uuid
            is_recipient = self.db.query(MailRecipient).filter(
                MailRecipient.mail_uuid == mail_uuid,
                MailRecipient.recipient_email == mail_user.email
            ).first() is not None
            
            if not (is_sender or is_recipient):
                raise HTTPException(status_code=403, detail="메일에 접근할 권한이 없습니다.")
            
            # 수신자 정보 조회
            recipients = self.db.query(MailRecipient).filter(
                MailRecipient.mail_uuid == mail_uuid
            ).all()
            
            # 첨부파일 정보 조회
            attachments = self.db.query(MailAttachment).filter(
                MailAttachment.mail_uuid == mail_uuid
            ).all()
            
            # 읽음 처리 (수신자인 경우)
            if is_recipient:
                recipient_record = self.db.query(MailRecipient).filter(
                    MailRecipient.mail_uuid == mail_uuid,
                    MailRecipient.recipient_email == mail_user.email
                ).first()
                if recipient_record and not recipient_record.is_read:
                    recipient_record.is_read = True
                    recipient_record.read_at = datetime.now(timezone.utc)
                    self.db.commit()
            
            return {
                "mail_uuid": mail.mail_uuid,
                "sender_email": mail.sender_email,
                "subject": mail.subject,
                "content": mail.content,
                "priority": mail.priority,
                "status": mail.status,
                "sent_at": mail.sent_at.isoformat() if mail.sent_at else None,
                "created_at": mail.created_at.isoformat(),
                "recipients": [
                    {
                        "email": r.recipient_email,
                        "type": r.recipient_type,
                        "is_read": r.is_read,
                        "read_at": r.read_at.isoformat() if r.read_at else None
                    } for r in recipients
                ],
                "attachments": [
                    {
                        "attachment_id": a.attachment_id,
                        "filename": a.filename,
                        "file_size": a.file_size,
                        "content_type": a.content_type
                    } for a in attachments
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ 메일 상세 조회 실패: {str(e)}")
            raise
    
    async def delete_mail(
        self,
        org_id: str,
        user_uuid: str,
        mail_uuid: str,
        permanent: bool = False
    ) -> bool:
        """
        조직 내 사용자의 메일을 삭제합니다.
        
        Args:
            org_id: 조직 ID
            user_uuid: str,
            mail_uuid: str,
            permanent: bool = False
            
        Returns:
            삭제 성공 여부
        """
        try:
            logger.info(f"🗑️ 메일 삭제 - 조직 ID: {org_id}, 사용자 UUID: {user_uuid}, 메일 UUID: {mail_uuid}, 영구삭제: {permanent}")
            
            # 사용자 검증
            user = self.db.query(User).filter(
                User.user_uuid == user_uuid,
                User.org_id == org_id,
                User.is_active == True
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 메일 사용자 조회
            mail_user = self.db.query(MailUser).filter(
                MailUser.user_uuid == user_uuid,
                MailUser.org_id == org_id
            ).first()
            if not mail_user:
                raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")
            
            # 메일 조회
            mail = self.db.query(Mail).filter(
                Mail.mail_uuid == mail_uuid,
                Mail.org_id == org_id
            ).first()
            if not mail:
                raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
            
            # 접근 권한 확인
            is_sender = mail.sender_uuid == mail_user.user_uuid
            recipient_record = self.db.query(MailRecipient).filter(
                MailRecipient.mail_uuid == mail_uuid,
                MailRecipient.recipient_email == mail_user.email
            ).first()
            
            if not (is_sender or recipient_record):
                raise HTTPException(status_code=403, detail="메일을 삭제할 권한이 없습니다.")
            
            if permanent:
                # 영구 삭제
                if is_sender:
                    # 발송자인 경우 메일 자체를 삭제
                    self.db.delete(mail)
                else:
                    # 수신자인 경우 수신자 레코드만 삭제
                    self.db.delete(recipient_record)
            else:
                # 소프트 삭제 (휴지통으로 이동)
                if is_sender:
                    mail.status = MailStatus.DELETED.value
                    mail.deleted_at = datetime.now(timezone.utc)
                else:
                    recipient_record.is_deleted = True
                    recipient_record.deleted_at = datetime.now(timezone.utc)
            
            # 메일 로그 기록
            mail_log = MailLog(
                mail_uuid=mail_uuid,
                action="delete" if not permanent else "permanent_delete",
                user_email=mail_user.email,
                details=f"메일 {'영구 ' if permanent else ''}삭제",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(mail_log)
            
            self.db.commit()
            
            logger.info(f"✅ 메일 삭제 완료 - 메일 UUID: {mail_uuid}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 메일 삭제 실패: {str(e)}")
            raise
    
    async def get_mail_stats(
        self,
        org_id: str,
        user_uuid: str
    ) -> Dict[str, Any]:
        """
        조직 내 사용자의 메일 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            user_uuid: 사용자 UUID
            
        Returns:
            메일 통계 정보
        """
        try:
            logger.info(f"📊 메일 통계 조회 - 조직 ID: {org_id}, 사용자 ID: {user_id}")
            
            # 사용자 검증
            user = self.db.query(User).filter(
                User.user_uuid == user_uuid,
                User.org_id == org_id,
                User.is_active == True
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 메일 사용자 조회
            mail_user = self.db.query(MailUser).filter(
                MailUser.user_uuid == user_uuid,
                MailUser.org_id == org_id
            ).first()
            if not mail_user:
                raise HTTPException(status_code=404, detail="메일 사용자를 찾을 수 없습니다.")
            
            # 보낸 메일 수
            sent_count = self.db.query(func.count(Mail.mail_uuid)).filter(
                Mail.org_id == org_id,
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.SENT.value
            ).scalar()
            
            # 받은 메일 수
            received_count = self.db.query(func.count(MailRecipient.mail_uuid)).join(Mail).filter(
                Mail.org_id == org_id,
                MailRecipient.recipient_uuid == mail_user.user_uuid,
                Mail.status != MailStatus.DELETED.value
            ).scalar()
            
            # 읽지 않은 메일 수
            unread_count = self.db.query(func.count(MailRecipient.mail_uuid)).join(Mail).filter(
                Mail.org_id == org_id,
                MailRecipient.recipient_uuid == mail_user.user_uuid,
                MailRecipient.is_read == False,
                Mail.status != MailStatus.DELETED.value
            ).scalar()
            
            # 임시보관함 메일 수
            draft_count = self.db.query(func.count(Mail.mail_uuid)).filter(
                Mail.org_id == org_id,
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.status == MailStatus.DRAFT.value
            ).scalar()
            
            # 휴지통 메일 수
            trash_count = self.db.query(func.count(Mail.mail_uuid)).filter(
                Mail.org_id == org_id,
                or_(
                    and_(Mail.sender_uuid == mail_user.user_uuid, Mail.status == MailStatus.DELETED.value),
                    and_(
                        Mail.mail_uuid.in_(
                            self.db.query(MailRecipient.mail_uuid).filter(
                                MailRecipient.recipient_uuid == mail_user.user_uuid,
                                MailRecipient.is_deleted == True
                            )
                        )
                    )
                )
            ).scalar()
            
            return {
                "sent_count": sent_count or 0,
                "received_count": received_count or 0,
                "unread_count": unread_count or 0,
                "draft_count": draft_count or 0,
                "trash_count": trash_count or 0,
                "total_count": (sent_count or 0) + (received_count or 0)
            }
            
        except Exception as e:
            logger.error(f"❌ 메일 통계 조회 실패: {str(e)}")
            raise
    
    async def _get_or_create_folder(
        self,
        org_id: str,
        user_uuid: str,
        folder_name: str
    ) -> MailFolder:
        """
        폴더를 조회하거나 생성합니다.
        
        Args:
            org_id: 조직 UUID
            user_uuid: 사용자 UUID
            folder_name: 폴더명
            
        Returns:
            폴더 객체
        """
        folder = self.db.query(MailFolder).filter(
            MailFolder.user_uuid == user_uuid,  
            MailFolder.name == folder_name
        ).first()
        
        if not folder:
            folder = MailFolder(
                folder_uuid=str(uuid.uuid4()),
                user_uuid=user_uuid,
                name=folder_name,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(folder)
            self.db.flush()
        
        return folder