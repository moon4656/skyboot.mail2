"""
메일 관리 서비스

SaaS 다중 조직 지원을 위한 메일 관리 기능
"""
import logging
import uuid
import smtplib
import os
import asyncio
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fastapi import HTTPException

from ..model import Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog, User, Organization, OrganizationUsage
from ..model.mail_model import generate_mail_uuid
from ..schemas.mail_schema import MailCreate, MailSendRequest, RecipientType, MailStatus, MailPriority
from ..config import settings

# Redis 락 관련 import (선택적)
try:
    from ..utils.redis_lock import OrganizationUsageLock, get_redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis 락 모듈을 사용할 수 없습니다. 기본 UPSERT 방식을 사용합니다.")

# 로거 설정
logger = logging.getLogger(__name__)


class MailService:
    """
    메일 서비스 클래스
    SaaS 다중 조직 지원을 위한 메일 발송, 조회, 관리 기능을 제공합니다.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.smtp_server = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        
        # SMTP 설정 로깅
        logger.info(f"🔧 SMTP 설정 로드 - 서버: {self.smtp_server}:{self.smtp_port}, TLS: {self.use_tls}")
        if self.smtp_username:
            logger.info(f"🔐 SMTP 인증 설정됨 - 사용자: {self.smtp_username}")
        else:
            logger.info("📧 SMTP 인증 없음 (로컬 서버 모드)")
    
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
            
            # 일일 메일 발송 제한 검증
            await self._check_daily_email_limit(org_id, organization.max_emails_per_day, len(to_emails))
            
            # 메일 ID 생성 (년월일_시분초_uuid[12] 형식)
            from ..model.mail_model import generate_mail_uuid
            mail_uuid = generate_mail_uuid()
            
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
                # 이메일로 사용자 UUID 찾기
                mail_user = self.db.query(MailUser).filter(
                    MailUser.email == email,
                    MailUser.org_id == org_id
                ).first()
                
                if mail_user:
                    recipient = MailRecipient(
                        mail_uuid=mail_uuid,
                        recipient_uuid=mail_user.user_uuid,
                        recipient_type=RecipientType.TO.value
                    )
                    self.db.add(recipient)
                all_recipients.append(email)
            
            # CC 수신자
            if cc_emails:
                for email in cc_emails:
                    # 이메일로 사용자 UUID 찾기
                    mail_user = self.db.query(MailUser).filter(
                        MailUser.email == email,
                        MailUser.org_id == org_id
                    ).first()
                    
                    if mail_user:
                        recipient = MailRecipient(
                            mail_uuid=mail_uuid,
                            recipient_uuid=mail_user.user_uuid,
                            recipient_type=RecipientType.CC.value
                        )
                        self.db.add(recipient)
                    all_recipients.append(email)
            
            # BCC 수신자
            if bcc_emails:
                for email in bcc_emails:
                    # 이메일로 사용자 UUID 찾기
                    mail_user = self.db.query(MailUser).filter(
                        MailUser.email == email,
                        MailUser.org_id == org_id
                    ).first()
                    
                    if mail_user:
                        recipient = MailRecipient(
                            mail_uuid=mail_uuid,
                            recipient_uuid=mail_user.user_uuid,
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
                action="send",
                details=f"메일 발송 완료 - 수신자: {len(all_recipients)}명, 발송자: {sender_mail_user.email}",
                mail_uuid=mail_uuid,
                user_uuid=sender_mail_user.user_uuid,
                ip_address=None,  # TODO: 실제 요청에서 IP 주소 전달 필요
                user_agent=None   # TODO: 실제 요청에서 User-Agent 전달 필요
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
            
            # 조직 사용량 업데이트
            logger.info(f"🔍 조직 사용량 업데이트 호출 직전 - 조직: {org_id}, 수신자 수: {len(all_recipients)}")
            await self._update_organization_usage(org_id, len(all_recipients))
            logger.info(f"🔍 조직 사용량 업데이트 호출 완료 - 조직: {org_id}")
            
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
                logger.info(f"📎 첨부파일 처리 시작 - 개수: {len(attachments)}")
                for attachment in attachments:
                    if os.path.exists(attachment["file_path"]):
                        with open(attachment["file_path"], "rb") as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            
                            # 파일명을 안전하게 인코딩
                            filename = attachment["filename"]
                            try:
                                # ASCII로 인코딩 가능한지 확인
                                filename.encode('ascii')
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename="{filename}"'
                                )
                            except UnicodeEncodeError:
                                # ASCII로 인코딩할 수 없으면 RFC 2231 방식 사용
                                import urllib.parse
                                encoded_filename = urllib.parse.quote(filename, safe='')
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                                )
                            
                            msg.attach(part)
                        logger.info(f"📎 첨부파일 추가됨: {attachment['filename']}")
                    else:
                        logger.warning(f"⚠️ 첨부파일을 찾을 수 없음: {attachment['file_path']}")
            
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
    
    async def send_email_smtp(
        self,
        sender_email: str,
        recipient_emails: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        org_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        SMTP를 통해 이메일을 발송합니다. (비동기)
        
        Args:
            sender_email: 발송자 이메일
            recipient_emails: 수신자 이메일 목록
            subject: 메일 제목
            body_text: 텍스트 본문
            body_html: HTML 본문 (선택사항)
            org_id: 조직 ID (선택사항)
            attachments: 첨부파일 목록 (선택사항)
            
        Returns:
            발송 결과 딕셔너리
        """
        import asyncio
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        import urllib.parse
        
        logger.info(f"🚀 send_email_smtp 메서드 호출됨 - 조직: {org_id}, 발송자: {sender_email}, 수신자: {len(recipient_emails)}명")
        logger.info(f"📧 SMTP 설정 - 서버: {self.smtp_server}:{self.smtp_port}, TLS: {self.use_tls}")
        
        # 입력 파라미터 타입 로깅
        logger.debug(f"📤 발송자 타입: {type(sender_email)}")
        logger.debug(f"📤 수신자 목록 타입: {type(recipient_emails)}")
        logger.debug(f"📤 제목 타입: {type(subject)}")
        logger.debug(f"📤 텍스트 본문 타입: {type(body_text)}")
        logger.debug(f"📤 HTML 본문 타입: {type(body_html)}")
        logger.debug(f"📤 첨부파일 타입: {type(attachments)}")
        logger.info(f"📤 첨부파일: {len(attachments) if attachments else 0}개")
        
        if attachments:
            for i, attachment in enumerate(attachments):
                logger.debug(f"📤 첨부파일 {i+1}: {attachment}")
                if isinstance(attachment, dict):
                    for key, value in attachment.items():
                        logger.debug(f"📤 첨부파일 {i+1} {key}: {value} (타입: {type(value)})")
        
        def _send_smtp_sync():
            """동기 SMTP 발송 함수"""
            try:
                logger.info(f"📤 SMTP 메일 발송 시작 - 발송자: {sender_email}, 수신자: {len(recipient_emails)}명")
                
                # MIMEMultipart 메시지 생성
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = ', '.join(recipient_emails)
                msg['Subject'] = subject
                
                # 텍스트 본문 추가
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
                
                # HTML 본문 추가 (있는 경우)
                if body_html:
                    msg.attach(MIMEText(body_html, 'html', 'utf-8'))
                
                # 첨부파일 처리
                if attachments:
                    logger.info(f"📎 첨부파일 처리 시작 - 개수: {len(attachments)}")
                    for i, attachment in enumerate(attachments):
                        logger.info(f"📎 첨부파일 {i+1} 처리 중...")
                        logger.debug(f"📎 첨부파일 정보: {attachment}")
                        
                        file_path = attachment.get('file_path')
                        filename = attachment.get('filename')
                        
                        if file_path and os.path.exists(file_path):
                            logger.info(f"📎 파일 존재 확인: {file_path}")
                            try:
                                with open(file_path, 'rb') as f:
                                    logger.info(f"📎 파일 읽기 시작: {filename}")
                                    file_data = f.read()
                                    logger.info(f"📎 파일 읽기 완료 - 크기: {len(file_data)} bytes")
                                
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(file_data)
                                encoders.encode_base64(part)
                                
                                # 파일명 인코딩 처리
                                logger.info(f"📎 파일명 인코딩 시작: {filename}")
                                try:
                                    filename.encode('ascii')
                                    part.add_header(
                                        'Content-Disposition',
                                        f'attachment; filename="{filename}"'
                                    )
                                    logger.info(f"📎 ASCII 헤더 추가 완료")
                                except UnicodeEncodeError:
                                    encoded_filename = urllib.parse.quote(filename)
                                    part.add_header(
                                        'Content-Disposition',
                                        f"attachment; filename*=UTF-8''{encoded_filename}"
                                    )
                                    logger.info(f"📎 RFC 2231 헤더 추가 완료")
                                
                                msg.attach(part)
                                logger.info(f"📎 첨부파일 추가됨: {filename}")
                                
                            except Exception as attach_error:
                                logger.error(f"❌ 첨부파일 처리 중 오류: {str(attach_error)}")
                                import traceback
                                logger.error(f"❌ 상세 스택 트레이스: {traceback.format_exc()}")
                                raise
                        else:
                            logger.warning(f"⚠️ 첨부파일을 찾을 수 없음: {file_path}")
                else:
                    logger.info("📎 첨부파일 없음")
                
                # SMTP 서버 연결 및 발송
                logger.info(f"🔗 SMTP 서버 연결 시도 - 서버: {self.smtp_server}:{self.smtp_port}")
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    logger.info("✅ SMTP 서버 연결 성공")
                    
                    # TLS 사용 시 STARTTLS
                    if self.use_tls:
                        logger.info("🔒 TLS 연결 시작")
                        server.starttls()
                        logger.info("✅ TLS 연결 완료")
                    
                    # 인증 정보가 있으면 로그인
                    if self.smtp_username and self.smtp_password:
                        logger.info(f"🔐 SMTP 인증 시도 - 사용자: {self.smtp_username}")
                        server.login(self.smtp_username, self.smtp_password)
                        logger.info("✅ SMTP 인증 성공")
                    else:
                        logger.info("📧 SMTP 인증 없이 발송 시도 (로컬 서버)")
                    
                    # 메일 발송
                    logger.info("📤 메일 발송 시작")
                    logger.debug(f"📤 메시지 타입: {type(msg)}")
                    
                    server.send_message(msg)
                    logger.info("✅ 메일 발송 완료")
                
                return {
                    "success": True,
                    "message": f"메일이 성공적으로 발송되었습니다. (수신자: {len(recipient_emails)}명)",
                    "recipients_count": len(recipient_emails),
                    "smtp_server": f"{self.smtp_server}:{self.smtp_port}"
                }
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP 인증 실패: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "authentication"
                }
            except smtplib.SMTPConnectError as e:
                error_msg = f"SMTP 서버 연결 실패: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "connection"
                }
            except smtplib.SMTPException as e:
                error_msg = f"SMTP 오류: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "smtp"
                }
            except Exception as e:
                error_msg = f"메일 발송 중 예상치 못한 오류: {str(e)}"
                logger.error(f"❌ {error_msg}")
                import traceback
                logger.error(f"❌ 상세 스택 트레이스: {traceback.format_exc()}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "unknown"
                }
        
        # 동기 SMTP 코드를 비동기로 실행
        try:
            result = await asyncio.to_thread(_send_smtp_sync)
            
            # 메일 발송이 성공한 경우 조직 사용량 업데이트
            if result.get('success', False) and org_id and self.db:
                logger.info(f"🔍 조직 사용량 업데이트 호출 (send_email_smtp) - 조직: {org_id}, 수신자 수: {len(recipient_emails)}")
                try:
                    await self._update_organization_usage(org_id, len(recipient_emails))
                    logger.info(f"✅ 조직 사용량 업데이트 완료 (send_email_smtp) - 조직: {org_id}")
                except Exception as usage_error:
                    logger.error(f"❌ 조직 사용량 업데이트 실패 (send_email_smtp) - 조직: {org_id}, 오류: {str(usage_error)}")
                    logger.error(f"❌ 상세 스택 트레이스: {traceback.format_exc()}")
                    # 사용량 업데이트 실패는 메일 발송 성공에 영향을 주지 않음
            
            return result
        except Exception as e:
            error_msg = f"비동기 실행 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "async"
            }
    
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
            logger.info(f"📬 메일 조회 - 조직 ID: {org_id}, 사용자 ID: {user_uuid}, 폴더: {folder_type}")
            
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
                    Mail.status != MailStatus.TRASH.value
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
                    Mail.status == MailStatus.TRASH.value,
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
            
            # 읽음 처리 (수신자인 경우) - MailInFolder에서 처리
            if is_recipient:
                mail_in_folder = self.db.query(MailInFolder).filter(
                    MailInFolder.mail_uuid == mail_uuid,
                    MailInFolder.user_uuid == mail_user.user_uuid
                ).first()
                if mail_in_folder and not mail_in_folder.is_read:
                    mail_in_folder.is_read = True
                    mail_in_folder.read_at = datetime.now(timezone.utc)
                    self.db.commit()
            
            # 메일 읽기 로그 기록
            mail_log = MailLog(
                action="read",
                details=f"메일 읽기 - 제목: {mail.subject}, 읽기 유형: {'수신자' if is_recipient else '발송자'}",
                mail_uuid=mail_uuid,
                user_uuid=mail_user.user_uuid,
                ip_address=None,  # TODO: 실제 요청에서 IP 주소 전달 필요
                user_agent=None   # TODO: 실제 요청에서 User-Agent 전달 필요
            )
            self.db.add(mail_log)
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
                        "is_read": False,  # MailRecipient에는 is_read가 없음, MailInFolder에서 관리
                        "read_at": None    # MailRecipient에는 read_at가 없음, MailInFolder에서 관리
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
            
            # 메일 로그 기록 (영구 삭제가 아닌 경우만)
            if not permanent:
                mail_log = MailLog(
                    mail_uuid=mail_uuid,
                    user_uuid=mail_user.user_uuid,
                    action="delete",
                    details=f"메일 삭제 - 사용자: {mail_user.email}",
                    ip_address=None,  # TODO: 실제 요청에서 IP 주소 전달 필요
                    user_agent=None   # TODO: 실제 요청에서 User-Agent 전달 필요
                )
                self.db.add(mail_log)
            
            if permanent:
                # 영구 삭제
                if is_sender:
                    # 발송자인 경우 메일 자체를 삭제
                    # 1. 먼저 mail_logs 테이블의 관련 레코드들을 삭제
                    mail_log_records = self.db.query(MailLog).filter(
                        MailLog.mail_uuid == mail_uuid
                    ).all()
                    
                    for log_record in mail_log_records:
                        self.db.delete(log_record)
                        logger.debug(f"🗑️ mail_logs 레코드 삭제 - 메일 UUID: {mail_uuid}, 로그 ID: {log_record.id}")
                    
                    # 2. mail_recipients 테이블의 관련 레코드들을 삭제
                    mail_recipient_records = self.db.query(MailRecipient).filter(
                        MailRecipient.mail_uuid == mail_uuid
                    ).all()
                    
                    for recipient_record in mail_recipient_records:
                        self.db.delete(recipient_record)
                        logger.debug(f"🗑️ mail_recipients 레코드 삭제 - 메일 UUID: {mail_uuid}, 수신자: {recipient_record.recipient_email}")
                    
                    # 3. mail_in_folders 테이블의 관련 레코드들을 삭제
                    mail_in_folder_records = self.db.query(MailInFolder).filter(
                        MailInFolder.mail_uuid == mail_uuid
                    ).all()
                    
                    for record in mail_in_folder_records:
                        self.db.delete(record)
                        logger.debug(f"🗑️ mail_in_folders 레코드 삭제 - 메일 UUID: {mail_uuid}, 폴더 UUID: {record.folder_uuid}")
                    
                    # 4. 그 다음 메일 자체를 삭제
                    self.db.delete(mail)
                    logger.info(f"🗑️ 메일 영구 삭제 완료 - 메일 UUID: {mail_uuid}")
                else:
                    # 수신자인 경우 수신자 레코드만 삭제
                    self.db.delete(recipient_record)
            else:
                # 소프트 삭제 (휴지통으로 이동)
                if is_sender:
                    mail.status = MailStatus.TRASH.value
                    mail.deleted_at = datetime.now(timezone.utc)
                else:
                    recipient_record.is_deleted = True
                    recipient_record.deleted_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 메일 삭제 완료 - 메일 UUID: {mail_uuid}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 메일 삭제 실패: {str(e)}")
            raise

    async def restore_mail(
        self,
        org_id: str,
        user_uuid: str,
        mail_uuid: str
    ) -> bool:
        """
        휴지통에서 메일을 복원합니다.
        
        - 발신자: Mail.status가 TRASH인 경우 원 상태(SENT/DRAFT)로 복원
        - 수신자: MailRecipient.is_deleted가 True인 경우 False로 복원
        """
        try:
            logger.info(f"♻️ 메일 복원 시작 - 조직 ID: {org_id}, 사용자 ID: {user_uuid}, 메일 UUID: {mail_uuid}")
            
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
                Mail.org_id == org_id,
                Mail.mail_uuid == mail_uuid
            ).first()
            if not mail:
                raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
            
            is_sender = mail.sender_uuid == mail_user.user_uuid
            recipient_record = self.db.query(MailRecipient).filter(
                MailRecipient.mail_uuid == mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            ).first()
            is_recipient = recipient_record is not None
            
            if not (is_sender or is_recipient):
                raise HTTPException(status_code=403, detail="이 메일을 복원할 권한이 없습니다.")
            
            if is_sender:
                if mail.status != MailStatus.TRASH.value:
                    raise HTTPException(status_code=400, detail="휴지통에 있는 메일만 복원할 수 있습니다.")
                
                # 원래 상태 추론: 발송 시각 존재 여부로 SENT/DRAFT 결정
                mail.status = MailStatus.SENT.value if mail.sent_at else MailStatus.DRAFT.value
                mail.deleted_at = None
                
                # 로그 기록
                mail_log = MailLog(
                    action="restore_mail",
                    details=f"발신자 복원 - 원래 상태: {mail.status}",
                    mail_uuid=mail.mail_uuid,
                    user_uuid=mail_user.user_uuid,
                    ip_address=None,
                    user_agent=None
                )
                self.db.add(mail_log)
            else:
                # 수신자 복원
                if not recipient_record.is_deleted:
                    raise HTTPException(status_code=400, detail="삭제된 메일만 복원할 수 있습니다.")
                recipient_record.is_deleted = False
                recipient_record.deleted_at = None
                
                mail_log = MailLog(
                    action="restore_mail",
                    details="수신자 복원",
                    mail_uuid=mail.mail_uuid,
                    user_uuid=mail_user.user_uuid,
                    ip_address=None,
                    user_agent=None
                )
                self.db.add(mail_log)
            
            self.db.commit()
            logger.info(f"✅ 메일 복원 완료 - 메일 UUID: {mail_uuid}")
            return True
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 메일 복원 실패: {str(e)}")
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
            logger.info(f"📊 메일 통계 조회 - 조직 ID: {org_id}, 사용자 ID: {user_uuid}")
            
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
                Mail.status != MailStatus.TRASH.value
            ).scalar()
            
            # 읽지 않은 메일 수
            unread_count = self.db.query(func.count(MailRecipient.mail_uuid)).join(Mail).filter(
                Mail.org_id == org_id,
                MailRecipient.recipient_uuid == mail_user.user_uuid,
                MailRecipient.is_read == False,
                Mail.status != MailStatus.TRASH.value
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
                    and_(Mail.sender_uuid == mail_user.user_uuid, Mail.status == MailStatus.TRASH.value),
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
    
    async def _update_organization_usage(
        self,
        org_id: str,
        email_count: int = 1,
        max_retries: int = 3
    ):
        """
        조직의 메일 사용량을 원자적으로 업데이트합니다. (동시성 안전)
        
        Args:
            org_id: 조직 ID
            email_count: 발송된 메일 수 (기본값: 1)
            max_retries: 최대 재시도 횟수 (기본값: 3)
        """
        logger.info(f"🔍 _update_organization_usage 호출됨 - 조직: {org_id}, 메일 수: {email_count}")
        
        for attempt in range(max_retries + 1):
            try:
                # 오늘 날짜 (UTC 기준)
                today = datetime.now(timezone.utc).date()
                now = datetime.now(timezone.utc)
                
                # PostgreSQL UPSERT를 사용한 원자적 업데이트
                # ON CONFLICT를 사용하여 동시성 문제 해결
                upsert_sql = """
                INSERT INTO organization_usage (
                    org_id, usage_date, current_users, current_storage_gb,
                    emails_sent_today, emails_received_today, 
                    total_emails_sent, total_emails_received,
                    created_at, updated_at
                ) VALUES (
                    :org_id, :usage_date, 0, 0,
                    :email_count, 0,
                    :email_count, 0,
                    :now, :now
                )
                ON CONFLICT (org_id, usage_date) 
                DO UPDATE SET
                    emails_sent_today = organization_usage.emails_sent_today + :email_count,
                    total_emails_sent = organization_usage.total_emails_sent + :email_count,
                    updated_at = :now
                RETURNING emails_sent_today, total_emails_sent;
                """
                
                result = self.db.execute(upsert_sql, {
                    'org_id': org_id,
                    'usage_date': today,
                    'email_count': email_count,
                    'now': now
                })
                
                # 결과 가져오기
                row = result.fetchone()
                if row:
                    emails_sent_today, total_emails_sent = row
                    logger.info(f"📊 조직 사용량 원자적 업데이트 완료 - 조직: {org_id}")
                    logger.info(f"   오늘 발송: {emails_sent_today}, 총 발송: {total_emails_sent}")
                else:
                    logger.warning(f"⚠️ UPSERT 결과를 가져올 수 없음 - 조직: {org_id}")
                
                # 트랜잭션 커밋
                self.db.commit()
                logger.info(f"✅ _update_organization_usage 완료 - 조직: {org_id}, 시도: {attempt + 1}")
                return
                
            except Exception as e:
                # 트랜잭션 롤백
                self.db.rollback()
                
                # 동시성 관련 오류인지 확인
                error_str = str(e).lower()
                is_concurrency_error = any(keyword in error_str for keyword in [
                    'deadlock', 'lock', 'concurrent', 'serialization', 'conflict'
                ])
                
                if is_concurrency_error and attempt < max_retries:
                    # 지수 백오프로 재시도
                    wait_time = (2 ** attempt) * 0.1  # 0.1초, 0.2초, 0.4초
                    logger.warning(f"⚠️ 동시성 오류 발생, {wait_time}초 후 재시도 - 조직: {org_id}, 시도: {attempt + 1}, 오류: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ 조직 사용량 업데이트 실패 - 조직: {org_id}, 시도: {attempt + 1}, 오류: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # 사용량 업데이트 실패는 메일 발송을 중단시키지 않음
                    break
    
    async def _update_organization_usage_with_redis_lock(
        self,
        org_id: str,
        email_count: int = 1
    ):
        """
        Redis 분산 락을 사용한 조직 사용량 업데이트 (고도의 동시성 환경용)
        
        Args:
            org_id: 조직 ID
            email_count: 발송된 메일 수 (기본값: 1)
        """
        if not REDIS_AVAILABLE:
            logger.warning(f"⚠️ Redis 사용 불가, 기본 UPSERT 방식으로 대체 - 조직: {org_id}")
            return await self._update_organization_usage(org_id, email_count)
        
        logger.info(f"🔒 Redis 락을 사용한 조직 사용량 업데이트 시작 - 조직: {org_id}, 메일 수: {email_count}")
        
        try:
            redis_client = get_redis_client()
            if not redis_client:
                logger.warning(f"⚠️ Redis 클라이언트 없음, 기본 UPSERT 방식으로 대체 - 조직: {org_id}")
                return await self._update_organization_usage(org_id, email_count)
            
            usage_lock = OrganizationUsageLock(redis_client)
            
            async with usage_lock.lock_organization_usage(org_id, timeout=3) as acquired:
                if not acquired:
                    logger.warning(f"⚠️ Redis 락 획득 실패, 기본 UPSERT 방식으로 대체 - 조직: {org_id}")
                    return await self._update_organization_usage(org_id, email_count)
                
                logger.info(f"🔒 Redis 락 획득 성공 - 조직: {org_id}")
                
                # 락을 획득한 상태에서 기존 방식으로 업데이트
                # (Redis 락 + 기본 ORM 방식)
                today = datetime.now(timezone.utc).date()
                
                # 기존 사용량 레코드 조회
                usage = self.db.query(OrganizationUsage).filter(
                    OrganizationUsage.org_id == org_id,
                    func.date(OrganizationUsage.usage_date) == today
                ).first()
                
                if usage:
                    # 기존 레코드 업데이트
                    old_sent_today = usage.emails_sent_today
                    old_total_sent = usage.total_emails_sent
                    
                    usage.emails_sent_today += email_count
                    usage.total_emails_sent += email_count
                    usage.updated_at = datetime.now(timezone.utc)
                    
                    logger.info(f"📊 Redis 락 하에서 조직 사용량 업데이트 - 조직: {org_id}")
                    logger.info(f"   이전 오늘 발송: {old_sent_today} -> 현재: {usage.emails_sent_today}")
                    logger.info(f"   이전 총 발송: {old_total_sent} -> 현재: {usage.total_emails_sent}")
                else:
                    # 새 레코드 생성
                    usage = OrganizationUsage(
                        org_id=org_id,
                        usage_date=datetime.now(timezone.utc),
                        current_users=0,
                        current_storage_gb=0,
                        emails_sent_today=email_count,
                        emails_received_today=0,
                        total_emails_sent=email_count,
                        total_emails_received=0,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    self.db.add(usage)
                    logger.info(f"📊 Redis 락 하에서 조직 사용량 신규 생성 - 조직: {org_id}, 발송 수: {email_count}")
                
                # 트랜잭션 커밋
                self.db.commit()
                logger.info(f"✅ Redis 락을 사용한 조직 사용량 업데이트 완료 - 조직: {org_id}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Redis 락을 사용한 조직 사용량 업데이트 실패 - 조직: {org_id}, 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Redis 락 실패 시 기본 UPSERT 방식으로 대체
            logger.info(f"🔄 기본 UPSERT 방식으로 재시도 - 조직: {org_id}")
            return await self._update_organization_usage(org_id, email_count)
            pass
    
    async def _check_daily_email_limit(
        self,
        org_id: str,
        max_emails_per_day: int,
        email_count: int
    ):
        """
        일일 메일 발송 제한을 검증합니다.
        
        Args:
            org_id: 조직 ID
            max_emails_per_day: 일일 최대 발송 제한
            email_count: 발송하려는 메일 수
            
        Raises:
            HTTPException: 발송 제한 초과 시
        """
        try:
            # 오늘 날짜 (UTC 기준)
            today = datetime.now(timezone.utc).date()
            
            # 오늘 발송된 메일 수 조회
            usage = self.db.query(OrganizationUsage).filter(
                OrganizationUsage.org_id == org_id,
                func.date(OrganizationUsage.usage_date) == today
            ).first()
            
            current_sent = usage.emails_sent_today if usage else 0
            
            # 발송 제한 검증
            if max_emails_per_day > 0:  # 0은 무제한
                if current_sent + email_count > max_emails_per_day:
                    logger.warning(f"⚠️ 일일 메일 발송 제한 초과 - 조직: {org_id}, 현재: {current_sent}, 요청: {email_count}, 제한: {max_emails_per_day}")
                    raise HTTPException(
                        status_code=429,
                        detail=f"일일 메일 발송 제한을 초과했습니다. (현재: {current_sent}/{max_emails_per_day})"
                    )
            
            logger.info(f"📊 메일 발송 제한 검증 통과 - 조직: {org_id}, 현재: {current_sent}, 요청: {email_count}, 제한: {max_emails_per_day}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 메일 발송 제한 검증 실패 - 조직: {org_id}, 오류: {str(e)}")
            # 검증 실패 시 안전하게 발송 허용 (기본 동작 유지)
            pass