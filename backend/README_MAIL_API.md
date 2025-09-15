# 메일 API 문서

## 개요
FastAPI를 사용하여 구현된 메일 송수신 API입니다. SMTP/IMAP 프로토콜을 통해 메일을 발송하고 수신하며, 모든 메일 데이터를 PostgreSQL 데이터베이스에 저장합니다.

## 주요 기능
- 메일 발송 (첨부파일 포함)
- 받은 메일함 조회
- 보낸 메일함 조회
- 임시보관함 조회
- 메일 상세 조회
- 첨부파일 다운로드
- 메일 통계 조회

## API 엔드포인트

### 1. 메일 발송
```
POST /api/mail/send
```

**요청 파라미터:**
- `to_emails` (string): 수신자 이메일 (쉼표로 구분)
- `cc_emails` (string, optional): 참조 이메일
- `bcc_emails` (string, optional): 숨은참조 이메일
- `subject` (string): 메일 제목
- `content` (string): 메일 내용
- `priority` (string): 우선순위 (HIGH, NORMAL, LOW)
- `attachments` (file[], optional): 첨부파일

**응답 예시:**
```json
{
  "success": true,
  "message": "메일이 성공적으로 발송되었습니다.",
  "data": {
    "mail_id": "mail-uuid-123",
    "sent_at": "2024-12-19T10:30:00Z",
    "recipients_count": 1
  }
}
```

### 2. 받은 메일함 조회
```
GET /api/mail/inbox
```

**쿼리 파라미터:**
- `page` (int, default=1): 페이지 번호
- `limit` (int, default=20): 페이지당 항목 수
- `search` (string, optional): 검색어
- `unread_only` (bool, default=false): 읽지 않은 메일만 조회

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "mails": [
      {
        "mail_id": "mail-uuid-123",
        "subject": "메일 제목",
        "sender_email": "sender@example.com",
        "received_at": "2024-12-19T10:30:00Z",
        "is_read": false,
        "has_attachments": true,
        "priority": "NORMAL"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 100,
      "items_per_page": 20
    }
  }
}
```

### 3. 받은 메일 상세 조회
```
GET /api/mail/inbox/{mail_id}
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "mail_id": "mail-uuid-123",
    "subject": "메일 제목",
    "content": "메일 내용",
    "sender_email": "sender@example.com",
    "sender_name": "발송자 이름",
    "recipients": [
      {
        "email": "recipient@example.com",
        "type": "TO"
      }
    ],
    "received_at": "2024-12-19T10:30:00Z",
    "is_read": true,
    "priority": "NORMAL",
    "attachments": [
      {
        "attachment_id": "att-uuid-123",
        "filename": "document.pdf",
        "file_size": 1024000,
        "content_type": "application/pdf"
      }
    ]
  }
}
```

### 4. 보낸 메일함 조회
```
GET /api/mail/sent
```

**쿼리 파라미터:** (받은 메일함과 동일)

### 5. 보낸 메일 상세 조회
```
GET /api/mail/sent/{mail_id}
```

### 6. 임시보관함 조회
```
GET /api/mail/drafts
```

### 7. 임시보관함 상세 조회
```
GET /api/mail/drafts/{mail_id}
```

### 8. 첨부파일 다운로드
```
GET /api/mail/attachments/{attachment_id}/download
```

### 9. 메일 삭제
```
DELETE /api/mail/{mail_id}
```

### 10. 메일 통계 조회
```
GET /api/mail/stats
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "total_received": 150,
    "total_sent": 75,
    "total_drafts": 5,
    "unread_count": 12,
    "today_received": 8,
    "today_sent": 3
  }
}
```

## 데이터베이스 스키마

### 주요 테이블
1. **mail_users**: 메일 사용자 정보
2. **mails**: 메일 기본 정보
3. **mail_recipients**: 메일 수신자 정보
4. **mail_attachments**: 첨부파일 정보
5. **mail_folders**: 메일 폴더 정보
6. **mail_in_folders**: 메일-폴더 관계
7. **mail_logs**: 메일 처리 로그

## 인증
모든 API는 JWT 토큰 기반 인증이 필요합니다.

**헤더:**
```
Authorization: Bearer <JWT_TOKEN>
```

## 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "MAIL_SEND_FAILED",
    "message": "메일 발송에 실패했습니다.",
    "details": "SMTP 서버 연결 오류"
  }
}
```

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
DATABASE_URL=postgresql://user:password@localhost/dbname
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
JWT_SECRET_KEY=your-secret-key
```

### 3. 데이터베이스 초기화
```python
from mail_database import create_tables, init_default_folders

create_tables()
init_default_folders()
```

### 4. 서버 실행
```bash
uvicorn mail_api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트
```bash
pytest test_mail_api.py -v
```

## 주요 특징
- **비동기 처리**: FastAPI의 async/await 지원
- **데이터베이스 연동**: SQLAlchemy ORM 사용
- **파일 업로드**: 멀티파트 폼 데이터 지원
- **페이지네이션**: 대용량 데이터 효율적 처리
- **검색 기능**: 제목, 내용, 발송자 검색
- **로깅**: 모든 메일 처리 과정 로그 기록
- **에러 처리**: 상세한 에러 메시지 제공

## 보안 고려사항
- JWT 토큰 기반 인증
- 파일 업로드 크기 제한
- SQL 인젝션 방지 (ORM 사용)
- 입력 데이터 검증 (Pydantic)
- CORS 설정

## 성능 최적화
- 데이터베이스 인덱스 설정
- 페이지네이션으로 메모리 사용량 제한
- 비동기 I/O로 동시성 향상
- 첨부파일 스트리밍 다운로드

---

**작성일**: 2024년 12월 19일  
**버전**: 1.0  
**작성자**: STT 프로젝트 개발팀