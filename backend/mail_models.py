from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class MailUser(Base):
    """
    메일 사용자 정보를 저장하는 테이블
    """
    __tablename__ = "mail_users"
    
    id = Column(Integer, primary_key=True, index=True, comment="사용자 고유 ID")
    user_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="사용자 UUID")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="이메일 주소")
    password_hash = Column(String(255), nullable=False, comment="암호화된 비밀번호")
    display_name = Column(String(100), comment="표시 이름")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정 시간")
    
    # 관계 설정
    sent_mails = relationship("Mail", foreign_keys="Mail.sender_id", back_populates="sender")
    received_mails = relationship("MailRecipient", back_populates="recipient")
    draft_mails = relationship("Mail", foreign_keys="Mail.sender_id", back_populates="sender")

class Mail(Base):
    """
    메일 정보를 저장하는 메인 테이블
    """
    __tablename__ = "mails"
    
    id = Column(Integer, primary_key=True, index=True, comment="메일 고유 ID")
    mail_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="메일 UUID")
    sender_id = Column(Integer, ForeignKey("mail_users.id"), nullable=False, comment="발신자 ID")
    subject = Column(String(500), nullable=False, comment="메일 제목")
    body_text = Column(Text, comment="메일 본문 (텍스트)")
    body_html = Column(Text, comment="메일 본문 (HTML)")
    priority = Column(String(10), default="normal", comment="우선순위 (high, normal, low)")
    status = Column(String(20), default="draft", comment="메일 상태 (draft, sent, failed)")
    is_draft = Column(Boolean, default=True, comment="임시보관함 여부")
    sent_at = Column(DateTime, comment="발송 시간")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정 시간")
    
    # 관계 설정
    sender = relationship("MailUser", foreign_keys=[sender_id], back_populates="sent_mails")
    recipients = relationship("MailRecipient", back_populates="mail")
    attachments = relationship("MailAttachment", back_populates="mail")

class MailRecipient(Base):
    """
    메일 수신자 정보를 저장하는 테이블
    """
    __tablename__ = "mail_recipients"
    
    id = Column(Integer, primary_key=True, index=True, comment="수신자 고유 ID")
    mail_id = Column(Integer, ForeignKey("mails.id"), nullable=False, comment="메일 ID")
    recipient_id = Column(Integer, ForeignKey("mail_users.id"), nullable=False, comment="수신자 ID")
    recipient_type = Column(String(10), nullable=False, comment="수신자 타입 (to, cc, bcc)")
    is_read = Column(Boolean, default=False, comment="읽음 여부")
    read_at = Column(DateTime, comment="읽은 시간")
    is_deleted = Column(Boolean, default=False, comment="삭제 여부")
    deleted_at = Column(DateTime, comment="삭제 시간")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="recipients")
    recipient = relationship("MailUser", back_populates="received_mails")

class MailAttachment(Base):
    """
    메일 첨부파일 정보를 저장하는 테이블
    """
    __tablename__ = "mail_attachments"
    
    id = Column(Integer, primary_key=True, index=True, comment="첨부파일 고유 ID")
    attachment_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="첨부파일 UUID")
    mail_id = Column(Integer, ForeignKey("mails.id"), nullable=False, comment="메일 ID")
    filename = Column(String(255), nullable=False, comment="파일명")
    original_filename = Column(String(255), nullable=False, comment="원본 파일명")
    file_size = Column(Integer, nullable=False, comment="파일 크기 (bytes)")
    content_type = Column(String(100), nullable=False, comment="MIME 타입")
    file_path = Column(String(500), nullable=False, comment="파일 저장 경로")
    is_inline = Column(Boolean, default=False, comment="인라인 첨부 여부")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="attachments")

class MailFolder(Base):
    """
    메일 폴더 정보를 저장하는 테이블
    """
    __tablename__ = "mail_folders"
    
    id = Column(Integer, primary_key=True, index=True, comment="폴더 고유 ID")
    folder_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="폴더 UUID")
    user_id = Column(Integer, ForeignKey("mail_users.id"), nullable=False, comment="사용자 ID")
    name = Column(String(100), nullable=False, comment="폴더명")
    folder_type = Column(String(20), nullable=False, comment="폴더 타입 (inbox, sent, draft, trash, custom)")
    parent_id = Column(Integer, ForeignKey("mail_folders.id"), comment="상위 폴더 ID")
    is_system = Column(Boolean, default=False, comment="시스템 폴더 여부")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    
    # 관계 설정
    user = relationship("MailUser")
    parent = relationship("MailFolder", remote_side=[id])
    mail_folders = relationship("MailInFolder", back_populates="folder")

class MailInFolder(Base):
    """
    메일과 폴더의 관계를 저장하는 테이블
    """
    __tablename__ = "mail_in_folders"
    
    id = Column(Integer, primary_key=True, index=True, comment="관계 고유 ID")
    mail_id = Column(Integer, ForeignKey("mails.id"), nullable=False, comment="메일 ID")
    folder_id = Column(Integer, ForeignKey("mail_folders.id"), nullable=False, comment="폴더 ID")
    user_id = Column(Integer, ForeignKey("mail_users.id"), nullable=False, comment="사용자 ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail")
    folder = relationship("MailFolder", back_populates="mail_folders")
    user = relationship("MailUser")

class MailLog(Base):
    """
    메일 처리 로그를 저장하는 테이블
    """
    __tablename__ = "mail_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="로그 고유 ID")
    mail_id = Column(Integer, ForeignKey("mails.id"), nullable=True, comment="메일 ID")
    user_id = Column(Integer, ForeignKey("mail_users.id"), nullable=True, comment="사용자 ID")
    to_email = Column(String(255), comment="수신자 이메일")
    subject = Column(String(500), comment="메일 제목")
    body = Column(Text, comment="메일 본문")
    action = Column(String(50), nullable=False, comment="액션 (send, receive, read, delete, etc.)")
    status = Column(String(20), nullable=False, comment="상태 (success, failed, pending)")
    error_message = Column(Text, comment="에러 메시지")
    message = Column(Text, comment="로그 메시지")
    ip_address = Column(String(45), comment="IP 주소")
    user_agent = Column(String(500), comment="사용자 에이전트")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail")
    user = relationship("MailUser")