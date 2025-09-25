from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.base import Base
import uuid
from enum import Enum

class OrganizationStatus(str, Enum):
    """조직 상태 열거형"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"

class Organization(Base):
    """조직/기업 모델 - SaaS의 핵심 테넌트"""
    __tablename__ = "organizations"
    
    org_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="조직 고유 ID")
    org_code = Column(String(50), unique=True, index=True, nullable=False, comment="조직 코드 (subdomain용)")
    name = Column(String(200), nullable=False, comment="조직명")
    display_name = Column(String(200), comment="표시용 조직명")
    description = Column(Text, comment="조직 설명")
    
    # 도메인 설정
    domain = Column(String(100), comment="메일 도메인 (예: company.com)")
    subdomain = Column(String(50), unique=True, nullable=False, comment="서브도메인 (예: company)")
    
    # 연락처 정보
    admin_email = Column(String(255), nullable=False, comment="관리자 이메일")
    admin_name = Column(String(100), comment="관리자 이름")
    phone = Column(String(20), comment="연락처")
    address = Column(Text, comment="주소")
    
    # 제한 설정 (구독 시스템 제외하고 기본 제한)
    max_users = Column(Integer, default=10, comment="최대 사용자 수")
    max_storage_gb = Column(Integer, default=10, comment="최대 저장 용량(GB)")
    max_emails_per_day = Column(Integer, default=1000, comment="일일 최대 메일 발송 수")
    
    # 상태 관리
    status = Column(String(20), default=OrganizationStatus.TRIAL, comment="조직 상태")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    trial_ends_at = Column(DateTime(timezone=True), comment="체험판 종료일")
    
    # 설정
    features = Column(Text, comment="활성화된 기능 목록 JSON")
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    deleted_at = Column(DateTime(timezone=True), comment="삭제 시간")
    
    # 관계 설정
    users = relationship("User", back_populates="organization")
    mail_users = relationship("MailUser", back_populates="organization")
    mails = relationship("Mail", back_populates="organization")
    settings = relationship("OrganizationSettings", back_populates="organization", uselist=False)
    usage = relationship("OrganizationUsage", back_populates="organization", uselist=False)
    
    def __repr__(self):
        return f"<Organization(org_code='{self.org_code}', name='{self.name}')>"

class OrganizationSettings(Base):
    """조직별 상세 설정"""
    __tablename__ = "organization_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="조직 ID")
    setting_key = Column(String(100), nullable=False, comment="설정 키")
    setting_value = Column(Text, comment="설정 값")
    setting_type = Column(String(20), default="string", comment="설정 타입 (string, number, boolean, json)")
    description = Column(String(500), comment="설정 설명")
    is_public = Column(Boolean, default=False, comment="공개 설정 여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    organization = relationship("Organization", back_populates="settings")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'setting_key', name='unique_org_setting'),
    )

class OrganizationUsage(Base):
    """조직 사용량 추적"""
    __tablename__ = "organization_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="조직 ID")
    usage_date = Column(DateTime(timezone=True), nullable=False, comment="사용량 기준일")
    
    # 사용량 메트릭
    current_users = Column(Integer, default=0, comment="현재 사용자 수")
    current_storage_gb = Column(Integer, default=0, comment="현재 저장 용량(GB)")
    emails_sent_today = Column(Integer, default=0, comment="오늘 발송된 메일 수")
    emails_received_today = Column(Integer, default=0, comment="오늘 수신된 메일 수")
    
    # 누적 통계
    total_emails_sent = Column(Integer, default=0, comment="총 발송 메일 수")
    total_emails_received = Column(Integer, default=0, comment="총 수신 메일 수")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    organization = relationship("Organization", back_populates="usage")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'usage_date', name='unique_org_usage_date'),
    )