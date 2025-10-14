from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

class RecipientType(str, Enum):
    """수신자 타입 열거형"""
    TO = "to"
    CC = "cc"
    BCC = "bcc"

class MailStatus(str, Enum):
    """메일 상태 열거형"""
    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    TRASH = "trash"
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

# 기본 스키마
class MailUserBase(BaseModel):
    """메일 사용자 기본 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    is_active: bool = Field(True, description="활성 상태")

class MailUserCreate(MailUserBase):
    """메일 사용자 생성 스키마"""
    password: str = Field(..., min_length=8, description="비밀번호")

class MailUserResponse(MailUserBase):
    """메일 사용자 응답 스키마"""
    user_uuid: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 첨부파일 스키마
class AttachmentBase(BaseModel):
    """첨부파일 기본 스키마"""
    filename: str = Field(..., max_length=255, description="파일명")
    file_size: int = Field(..., ge=0, description="파일 크기")
    content_type: str = Field(..., max_length=100, description="MIME 타입")
    is_inline: bool = Field(False, description="인라인 첨부 여부")

class AttachmentResponse(AttachmentBase):
    """첨부파일 응답 스키마"""
    id: int
    attachment_uuid: str
    original_filename: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 수신자 스키마
class RecipientBase(BaseModel):
    """수신자 기본 스키마"""
    email: EmailStr = Field(..., description="수신자 이메일")
    recipient_type: RecipientType = Field(RecipientType.TO.value, description="수신자 타입")

class RecipientResponse(BaseModel):
    """수신자 응답 스키마"""
    id: int
    recipient_type: RecipientType
    is_read: bool
    read_at: Optional[datetime]
    recipient: MailUserResponse
    
    model_config = ConfigDict(from_attributes=True)

# 메일 스키마
class MailBase(BaseModel):
    """메일 기본 스키마"""
    subject: str = Field(..., max_length=500, description="메일 제목")
    body_text: Optional[str] = Field(None, description="메일 본문 (텍스트)")
    body_html: Optional[str] = Field(None, description="메일 본문 (HTML)")
    priority: MailPriority = Field(MailPriority.NORMAL, description="우선순위")

class MailCreate(MailBase):
    """메일 생성 스키마"""
    recipients: List[RecipientBase] = Field(..., min_length=1, description="수신자 목록")
    is_draft: bool = Field(False, description="임시보관함 여부")
    send_immediately: bool = Field(True, description="즉시 발송 여부")

class MailUpdate(BaseModel):
    """메일 수정 스키마"""
    subject: Optional[str] = Field(None, max_length=500, description="메일 제목")
    body_text: Optional[str] = Field(None, description="메일 본문 (텍스트)")
    body_html: Optional[str] = Field(None, description="메일 본문 (HTML)")
    priority: Optional[MailPriority] = Field(None, description="우선순위")
    recipients: Optional[List[RecipientBase]] = Field(None, description="수신자 목록")

class MailResponse(MailBase):
    """메일 응답 스키마"""
    id: int
    mail_uuid: str
    status: MailStatus
    is_draft: bool
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    sender_uuid: MailUserResponse
    recipients: List[RecipientResponse]
    attachments: List[AttachmentResponse]
    
    model_config = ConfigDict(from_attributes=True)

class MailDetailResponse(BaseModel):
    """메일 상세 응답 스키마 - API 응답 형태"""
    success: bool = Field(..., description="성공 여부")
    data: Optional[dict] = Field(None, description="메일 상세 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")

class MailListResponse(BaseModel):
    """메일 목록 응답 스키마"""
    mail_uuid: str
    subject: str
    status: MailStatus
    is_draft: bool
    priority: MailPriority
    sent_at: Optional[datetime]
    created_at: datetime
    sender: Optional[MailUserResponse]
    recipient_count: int
    attachment_count: int
    is_read: Optional[bool] = None  # 받은 메일의 경우에만 사용
    
    model_config = ConfigDict(from_attributes=True)

# 폴더 스키마
class FolderBase(BaseModel):
    """폴더 기본 스키마"""
    name: str = Field(..., max_length=100, description="폴더명")
    folder_type: FolderType = Field(FolderType.CUSTOM, description="폴더 타입")
    parent_id: Optional[int] = Field(None, description="상위 폴더 ID")

class FolderCreate(FolderBase):
    """폴더 생성 스키마"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "중요한 메일",
                "folder_type": "custom",
                "parent_id": 1
            }
        }
    )

class FolderUpdate(BaseModel):
    """폴더 수정 스키마"""
    name: Optional[str] = Field(None, max_length=100, description="폴더명")
    folder_type: Optional[FolderType] = Field(None, description="폴더 타입")
    parent_id: Optional[int] = Field(None, description="상위 폴더 ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "업무 메일",
                "folder_type": "custom",
                "parent_id": 1
            }
        }
    )

class FolderResponse(FolderBase):
    """폴더 응답 스키마"""
    id: int
    folder_uuid: str
    is_system: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 페이지네이션 및 검색 스키마
class PaginationParams(BaseModel):
    """페이지네이션 매개변수"""
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="정렬 순서")

class PaginatedResponse(BaseModel):
    """페이지네이션 응답 스키마"""
    items: List[Union[MailListResponse, MailResponse]]
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

# 검색 스키마
class MailSearchParams(BaseModel):
    """메일 검색 매개변수"""
    query: Optional[str] = Field(None, description="검색어 (제목, 본문, 발신자)")
    sender_email: Optional[str] = Field(None, description="발신자 이메일")
    recipient_email: Optional[str] = Field(None, description="수신자 이메일")
    subject: Optional[str] = Field(None, description="제목 검색")
    status: Optional[MailStatus] = Field(None, description="메일 상태")
    priority: Optional[MailPriority] = Field(None, description="우선순위")
    is_draft: Optional[bool] = Field(None, description="임시보관함 여부")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    has_attachments: Optional[bool] = Field(None, description="첨부파일 포함 여부")

# API 응답 스키마
class APIResponse(BaseModel):
    """API 응답 기본 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Union[dict, list]] = Field(None, description="응답 데이터")

class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[dict] = Field(None, description="에러 상세 정보")

# 메일 발송 결과 스키마
class SendMailResult(BaseModel):
    """메일 발송 결과 스키마"""
    mail_uuid: str = Field(..., description="메일 UUID")
    status: MailStatus = Field(..., description="발송 상태")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    message: str = Field(..., description="결과 메시지")
    failed_recipients: List[str] = Field(default_factory=list, description="발송 실패 수신자")

# 메일 발송 요청/응답 스키마
class MailSendRequest(BaseModel):
    """메일 발송 요청 스키마"""
    to: List[EmailStr] = Field(..., description="수신자 목록")
    cc: Optional[List[EmailStr]] = Field(None, description="참조 수신자 목록")
    bcc: Optional[List[EmailStr]] = Field(None, description="숨은 참조 수신자 목록")
    subject: str = Field(..., max_length=500, description="메일 제목")
    body_text: Optional[str] = Field(None, description="메일 본문 (텍스트)")
    body_html: Optional[str] = Field(None, description="메일 본문 (HTML)")
    priority: MailPriority = Field(MailPriority.NORMAL, description="우선순위")
    is_draft: bool = Field(False, description="임시보관함 여부")

class MailSendResponse(BaseModel):
    """메일 발송 응답 스키마"""
    success: bool = Field(..., description="발송 성공 여부")
    mail_uuid: str = Field(..., description="메일 UUID")
    message: str = Field(..., description="응답 메시지")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    failed_recipients: List[str] = Field(default_factory=list, description="발송 실패 수신자")

# 메일 검색 요청/응답 스키마
class MailSearchRequest(BaseModel):
    """메일 검색 요청 스키마"""
    query: Optional[str] = Field(None, description="검색어")
    sender_email: Optional[str] = Field(None, description="발신자 이메일")
    recipient_email: Optional[str] = Field(None, description="수신자 이메일")
    subject: Optional[str] = Field(None, description="제목 검색")
    status: Optional[MailStatus] = Field(None, description="메일 상태")
    folder_type: Optional[FolderType] = Field(None, description="폴더 타입 (inbox, sent, draft, trash)")
    priority: Optional[MailPriority] = Field(None, description="우선순위")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 항목 수")

class MailSearchResponse(BaseModel):
    """메일 검색 응답 스키마"""
    mails: List[MailListResponse] = Field(..., description="검색된 메일 목록")
    total: int = Field(..., description="총 검색 결과 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="총 페이지 수")

# 페이지네이션 응답 스키마
class PaginationResponse(BaseModel):
    """페이지네이션 응답 스키마"""
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")
    total: int = Field(..., description="총 항목 수")
    total_pages: int = Field(..., description="총 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

# 메일 목록과 페이지네이션을 포함하는 응답 스키마
class MailListWithPaginationResponse(BaseModel):
    """메일 목록과 페이지네이션 응답 스키마"""
    mails: List[MailListResponse] = Field(..., description="메일 목록")
    pagination: PaginationResponse = Field(..., description="페이지네이션 정보")

# 통계 스키마
class MailStats(BaseModel):
    """메일 통계 스키마"""
    total_sent: int = Field(..., description="총 발송 메일 수")
    total_received: int = Field(..., description="총 수신 메일 수")
    total_drafts: int = Field(..., description="총 임시보관 메일 수")
    unread_count: int = Field(..., description="읽지 않은 메일 수")
    today_sent: int = Field(..., description="오늘 발송 메일 수")
    today_received: int = Field(..., description="오늘 수신 메일 수")

class MailStatsResponse(BaseModel):
    """메일 통계 응답 스키마"""
    stats: MailStats = Field(..., description="메일 통계")
    success: bool = Field(True, description="성공 여부")
    message: str = Field("통계 조회 성공", description="응답 메시지")

# 조직 일일 사용량 스키마
class OrgDailyUsage(BaseModel):
    """조직 일일 사용량"""
    usage_date: datetime = Field(..., description="사용량 기준일")
    emails_sent_today: int = Field(0, description="오늘 발송된 메일 수")
    emails_received_today: int = Field(0, description="오늘 수신된 메일 수")
    total_emails_sent: int = Field(0, description="총 발송 메일 수")
    total_emails_received: int = Field(0, description="총 수신 메일 수")
    current_users: int = Field(0, description="현재 사용자 수")
    current_storage_gb: int = Field(0, description="현재 저장 용량(GB)")

class OrgUsageTodayResponse(BaseModel):
    """조직 오늘 사용량 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("오늘 사용량 조회 성공", description="응답 메시지")
    usage: OrgDailyUsage = Field(..., description="일일 사용량")
    daily_limit: Optional[int] = Field(None, description="일일 발송 제한 (0=무제한)")
    usage_percent: Optional[float] = Field(None, description="일일 제한 대비 사용률 (%)")
    remaining_until_limit: Optional[int] = Field(None, description="제한까지 남은 발송 가능 수")

class OrgUsageHistoryResponse(BaseModel):
    """조직 사용량 히스토리 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("사용량 히스토리 조회 성공", description="응답 메시지")
    items: List[OrgDailyUsage] = Field(default_factory=list, description="일일 사용량 목록")
    total: int = Field(0, description="총 항목 수")

# 폴더 관련 응답 스키마
class FolderInfo(BaseModel):
    """폴더 정보 스키마"""
    folder_uuid: str = Field(..., description="폴더 UUID")
    name: str = Field(..., description="폴더명")
    folder_type: FolderType = Field(..., description="폴더 타입")
    mail_count: int = Field(..., description="폴더 내 메일 수")
    created_at: datetime = Field(..., description="생성 시간")

class FolderListResponse(BaseModel):
    """폴더 목록 응답 스키마"""
    folders: List[FolderInfo] = Field(..., description="폴더 목록")

class FolderCreateResponse(BaseModel):
    """폴더 생성 응답 스키마"""
    id: int = Field(..., description="폴더 ID")
    folder_uuid: str = Field(..., description="폴더 UUID")
    name: str = Field(..., description="폴더명")
    folder_type: FolderType = Field(..., description="폴더 타입")
    mail_count: int = Field(..., description="폴더 내 메일 수")
    created_at: datetime = Field(..., description="생성 시간")

# ===== 템플릿/서명/라벨/규칙/예약발송 스키마 =====

class TemplateItem(BaseModel):
    """템플릿 항목"""
    template_id: str = Field(..., description="템플릿 ID")
    name: str = Field(..., description="템플릿 이름")
    subject: Optional[str] = Field(None, description="템플릿 제목")
    body_text: Optional[str] = Field(None, description="템플릿 본문 (텍스트)")
    body_html: Optional[str] = Field(None, description="템플릿 본문 (HTML)")

class OrgTemplatesResponse(BaseModel):
    """조직 템플릿 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("템플릿 조회 성공", description="응답 메시지")
    templates: List[TemplateItem] = Field(default_factory=list, description="템플릿 목록")

class SignatureResponse(BaseModel):
    """서명 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("서명 조회 성공", description="응답 메시지")
    org_default_signature: Optional[str] = Field(None, description="조직 기본 서명")
    user_signature: Optional[str] = Field(None, description="사용자 서명")

class SignatureUpdateRequest(BaseModel):
    """서명 업데이트 요청"""
    signature: str = Field(..., description="사용자 서명 내용")

class LabelItem(BaseModel):
    """라벨(커스텀 폴더) 항목"""
    folder_uuid: str = Field(..., description="폴더 UUID")
    name: str = Field(..., description="라벨명")

class LabelsResponse(BaseModel):
    """라벨 목록 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("라벨 조회 성공", description="응답 메시지")
    labels: List[LabelItem] = Field(default_factory=list, description="라벨 목록")

class RuleItem(BaseModel):
    """메일 규칙 항목 (간단한 JSON 표현)"""
    rule_id: str = Field(..., description="규칙 ID")
    name: str = Field(..., description="규칙 이름")
    condition: dict = Field(default_factory=dict, description="적용 조건")
    action: dict = Field(default_factory=dict, description="실행 동작")

class OrgRulesResponse(BaseModel):
    """조직 규칙 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("규칙 조회 성공", description="응답 메시지")
    rules: List[RuleItem] = Field(default_factory=list, description="규칙 목록")

class ScheduleRequest(BaseModel):
    """예약발송 요청"""
    mail_uuid: str = Field(..., description="예약할 메일 UUID")
    scheduled_at: datetime = Field(..., description="예약 발송 시간(UTC)")

class RescheduleRequest(BaseModel):
    """예약 재설정 요청"""
    mail_uuid: str = Field(..., description="재예약할 메일 UUID")
    scheduled_at: datetime = Field(..., description="새 예약 발송 시간(UTC)")

class ScheduleResponse(BaseModel):
    """예약 설정 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("예약 설정 성공", description="응답 메시지")
    mail_uuid: str = Field(..., description="메일 UUID")
    scheduled_at: datetime = Field(..., description="예약 발송 시간")

class ScheduleDispatchResponse(BaseModel):
    """예약 발송 처리 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("예약 메일 발송 완료", description="응답 메시지")
    processed_count: int = Field(..., description="발송 처리된 메일 수")

# ===== 필터/저장된 검색 스키마 =====

class DateRange(BaseModel):
    """날짜 범위 스키마"""
    min_date: Optional[datetime] = Field(None, description="최소 날짜")
    max_date: Optional[datetime] = Field(None, description="최대 날짜")

class FiltersResponse(BaseModel):
    """조직별 필터 제공 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("필터 조회 성공", description="응답 메시지")
    statuses: List[MailStatus] = Field(default_factory=list, description="사용 가능한 상태 목록")
    priorities: List[MailPriority] = Field(default_factory=list, description="사용 가능한 우선순위 목록")
    sender_domains: List[str] = Field(default_factory=list, description="발신자 도메인 목록")
    date_range: DateRange = Field(default_factory=DateRange, description="조직 메일 날짜 범위")
    has_attachments_options: List[bool] = Field(default_factory=lambda: [True, False], description="첨부파일 옵션")

class SavedSearchItem(BaseModel):
    """저장된 검색 항목"""
    search_id: str = Field(..., description="저장된 검색 ID")
    name: str = Field(..., description="저장된 검색 이름")
    query: Optional[str] = Field(None, description="검색어")
    filters: Optional[dict] = Field(default_factory=dict, description="필터 조건 (키-값 JSON)")
    created_at: Optional[datetime] = Field(None, description="생성 일시")

class SavedSearchesResponse(BaseModel):
    """저장된 검색 목록 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("저장된 검색 조회 성공", description="응답 메시지")
    searches: List[SavedSearchItem] = Field(default_factory=list, description="저장된 검색 목록")

# ===== 첨부파일 관리 스키마 =====

class AttachmentItem(BaseModel):
    """조직 단위 첨부파일 목록 항목"""
    attachment_uuid: str = Field(..., description="첨부파일 UUID")
    mail_uuid: str = Field(..., description="메일 UUID")
    filename: str = Field(..., description="파일명")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    content_type: Optional[str] = Field(None, description="MIME 타입")
    created_at: datetime = Field(..., description="생성 일시")

class AttachmentsResponse(BaseModel):
    """조직 첨부파일 목록 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("첨부파일 조회 성공", description="응답 메시지")
    attachments: List[AttachmentItem] = Field(default_factory=list, description="첨부파일 목록")
    page: int = Field(1, description="페이지 번호")
    limit: int = Field(20, description="페이지당 항목 수")
    total: int = Field(0, description="총 항목 수")
    total_pages: int = Field(0, description="총 페이지 수")

class VirusScanRequest(BaseModel):
    """바이러스 검사 요청"""
    attachment_uuids: List[str] = Field(..., min_length=1, description="검사할 첨부파일 UUID 목록")

class VirusScanResultItem(BaseModel):
    """바이러스 검사 결과 항목"""
    attachment_uuid: str = Field(..., description="첨부파일 UUID")
    status: str = Field(..., description="검사 상태 (clean/infected/error)")
    engine: str = Field("builtin", description="검사 엔진")
    message: Optional[str] = Field(None, description="상세 메시지")
    sha256: Optional[str] = Field(None, description="파일 SHA256 해시")

class VirusScanResponse(BaseModel):
    """바이러스 검사 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("바이러스 검사 완료", description="응답 메시지")
    results: List[VirusScanResultItem] = Field(default_factory=list, description="검사 결과 목록")
    infected_count: int = Field(0, description="감염 의심 파일 수")

class AttachmentPreviewResponse(BaseModel):
    """첨부파일 미리보기 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("미리보기 제공", description="응답 메시지")
    attachment_uuid: str = Field(..., description="첨부파일 UUID")
    filename: str = Field(..., description="파일명")
    content_type: Optional[str] = Field(None, description="콘텐츠 타입")
    preview_type: str = Field(..., description="미리보기 타입 (text/image/unsupported)")
    preview_text: Optional[str] = Field(None, description="텍스트 파일 미리보기")
    preview_data_url: Optional[str] = Field(None, description="이미지 데이터 URL(Base64)")
    download_url: Optional[str] = Field(None, description="다운로드 URL")