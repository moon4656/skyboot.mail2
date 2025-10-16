from sqlalchemy import BigInteger, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.user import Base
import uuid
from datetime import datetime
from enum import Enum

# 열거형 정의
class RecipientType(str, Enum):
    """수신자 타입 열거형"""
    TO = "to"
    CC = "cc"
    BCC = "bcc"

class MailStatus(str, Enum):
    """메일 상태 열거형"""
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"

class MailPriority(str, Enum):
    """메일 우선순위 열거형"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class FolderType(str, Enum):
    """폴더 타입 열거형"""
    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    TRASH = "trash"
    CUSTOM = "custom"

def generate_mail_user_uuid(ctx=None):
    """메일 사용자 UUID 생성 함수"""
    return str(uuid.uuid4())

class MailUser(Base):
    """메일 사용자 모델 - 조직 연결"""
    __tablename__ = "mail_users"
    
    user_id = Column(String(50), primary_key=True, index=True, comment="연결된 사용자 ID")
    user_uuid = Column(String(36), unique=True, index=True, default=generate_mail_user_uuid, comment="사용자 UUID")
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="소속 조직 ID")
    
    email = Column(String(255), index=True, nullable=False, comment="이메일 주소")
    password_hash = Column(String(255), nullable=False, comment="해시된 비밀번호")
    display_name = Column(String(100), comment="표시 이름")
    
    # 메일 설정
    signature = Column(Text, comment="메일 서명")
    auto_reply_enabled = Column(Boolean, default=False, comment="자동 응답 활성화")
    auto_reply_message = Column(Text, comment="자동 응답 메시지")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    storage_used_mb = Column(Integer, default=0, comment="사용 중인 저장 용량(MB)")
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    organization = relationship("Organization", back_populates="mail_users")
    sent_mails = relationship("Mail", foreign_keys="Mail.sender_uuid", back_populates="sender")
    folders = relationship("MailFolder", back_populates="user")
    mail_logs = relationship("MailLog", back_populates="user")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'email', name='unique_org_mail_email'),
    )

def generate_mail_uuid() -> str:
    """메일 ID 생성 (년월일_시분초_uuid[12] 형태)"""
    from datetime import datetime
    import uuid
    
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    mail_uuid = str(uuid.uuid4()).replace('-', '')[:12]  # UUID 앞 12자리만 사용 (하이픈 제거)
    return f"{timestamp}_{mail_uuid}"

class Mail(Base):
    """메일 모델 - 조직 연결"""
    __tablename__ = "mails"
    
    mail_uuid = Column(String(50), primary_key=True, index=True, default=generate_mail_uuid, comment="메일 고유 UUID")
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="조직 ID")
    sender_uuid = Column(String(36), ForeignKey("mail_users.user_uuid"), nullable=False, comment="발송자 UUID")
    subject = Column(String(255), nullable=False, comment="메일 제목")
    body_text = Column(Text, comment="메일 본문 (텍스트)")
    body_html = Column(Text, comment="메일 본문 (HTML)")
    priority = Column(String(10), default="normal", comment="우선순위")
    status = Column(String(20), default="sent", comment="메일 상태")
    is_draft = Column(Boolean, default=False, comment="임시저장 여부")
    message_id = Column(String(255), comment="메시지 ID")
    in_reply_to = Column(String(255), comment="답장 대상 메시지 ID")
    references = Column(Text, comment="참조 메시지 ID들")
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="발송 시간")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    organization = relationship("Organization", back_populates="mails")
    sender = relationship("MailUser", foreign_keys=[sender_uuid], back_populates="sent_mails")
    recipients = relationship("MailRecipient", back_populates="mail")
    attachments = relationship("MailAttachment", back_populates="mail")
    mail_in_folders = relationship("MailInFolder", back_populates="mail")
    logs = relationship("MailLog", back_populates="mail")

class MailRecipient(Base):
    """메일 수신자 모델"""
    __tablename__ = "mail_recipients"
    
    id = Column(BigInteger, primary_key=True, index=True)
    mail_uuid = Column(String(50), ForeignKey("mails.mail_uuid"), nullable=False, comment="메일 UUID (mails.mail_uuid 참조)")
    recipient_uuid = Column(String(50), ForeignKey("mail_users.user_uuid"), nullable=True, comment="수신자 UUID (mail_users.user_uuid 참조)")
    recipient_email = Column(String(255), nullable=False, comment="수신자 이메일 주소")
    recipient_type = Column(String(10), default=RecipientType.TO.value, comment="수신자 타입")
    created_at = Column(DateTime, server_default=func.now(), comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="recipients")
    recipient = relationship("MailUser", foreign_keys=[recipient_uuid])

class MailAttachment(Base):
    """메일 첨부파일 모델"""
    __tablename__ = "mail_attachments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    attachment_uuid = Column(String(255), unique=True, nullable=False, comment="첨부파일 UUID")
    mail_uuid = Column(String(50), ForeignKey("mails.mail_uuid"), nullable=False, comment="메일 UUID (mails.mail_uuid 참조)")
    filename = Column(String(255), nullable=False, comment="파일명")
    file_path = Column(String(500), nullable=False, comment="파일 저장 경로")
    file_size = Column(BigInteger, nullable=False, comment="파일 크기 (bytes)")
    content_type = Column(String(100), comment="MIME 타입")
    created_at = Column(DateTime, server_default=func.now(), comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="attachments")

class MailFolder(Base):
    """메일 폴더 모델"""
    __tablename__ = "mail_folders"
    
    id = Column(Integer, primary_key=True, index=True, comment="폴더 ID")
    folder_uuid = Column(String(36), unique=True, comment="폴더 UUID")
    user_uuid = Column(String(36), ForeignKey("mail_users.user_uuid"), nullable=False, index=True, comment="사용자 UUID")
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="조직 ID")
    name = Column(String(100), nullable=False, comment="폴더명")
    folder_type = Column(SQLEnum(FolderType, values_callable=lambda x: [e.value for e in x]), default=FolderType.CUSTOM, comment="폴더 타입")
    parent_id = Column(Integer, ForeignKey("mail_folders.id"), comment="상위 폴더 ID")
    is_system = Column(Boolean, default=False, comment="시스템 폴더 여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    user = relationship("MailUser", back_populates="folders")
    parent = relationship("MailFolder", remote_side=[id])
    mail_relations = relationship("MailInFolder", back_populates="folder")

class MailInFolder(Base):
    """메일-폴더 관계 모델"""
    __tablename__ = "mail_in_folders"
    
    id = Column(BigInteger, primary_key=True, index=True)
    mail_uuid = Column(String(50), ForeignKey("mails.mail_uuid"), nullable=False, comment="메일 UUID (mails.mail_uuid 참조)")
    folder_uuid = Column(String(36), ForeignKey("mail_folders.folder_uuid"), nullable=False, comment="폴더 UUID")
    user_uuid = Column(String(36), ForeignKey("mail_users.user_uuid"), nullable=False, comment="사용자 UUID")
    is_read = Column(Boolean, default=False, comment="읽음 상태")
    read_at = Column(DateTime(timezone=True), comment="읽은 시간")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="mail_in_folders")
    folder = relationship("MailFolder", back_populates="mail_relations")
    user = relationship("MailUser")

class MailLog(Base):
    """메일 로그 모델"""
    __tablename__ = "mail_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    mail_uuid = Column(String(50), ForeignKey("mails.mail_uuid"), nullable=False, comment="메일 UUID (mails.mail_uuid 참조)")
    user_uuid = Column(String(36), ForeignKey("mail_users.user_uuid"), comment="사용자 UUID")
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="조직 ID")
    action = Column(String(50), nullable=False, comment="수행된 작업")
    details = Column(Text, comment="상세 내용")
    ip_address = Column(String(45), comment="IP 주소")
    user_agent = Column(String(500), comment="사용자 에이전트")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    # 관계 설정
    mail = relationship("Mail", back_populates="logs")
    user = relationship("MailUser", back_populates="mail_logs")
    organization = relationship("Organization", back_populates="mail_logs")
