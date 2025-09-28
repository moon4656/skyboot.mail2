# 데이터베이스 마이그레이션 보고서

## 📋 개요
모델 파일(`user_model.py`, `organization_model.py`, `mail_model.py`)에 정의된 구조에 맞춰 데이터베이스 테이블을 성공적으로 수정했습니다.

## 🎯 수행된 작업

### 1. 새로 생성된 테이블
- **organizations**: 조직 정보 관리
- **organization_settings**: 조직별 설정 관리
- **organization_usage**: 조직별 사용량 통계
- **mail_recipients**: 메일 수신자 정보
- **mail_attachments**: 메일 첨부파일 정보
- **mail_folders**: 메일 폴더 관리
- **mail_in_folders**: 메일-폴더 관계
- **mail_logs**: 메일 접근 로그
- **login_logs**: 로그인 로그

### 2. 수정된 기존 테이블

#### users 테이블
- `organization_id` 컬럼 추가 (조직 연결)
- 외래키 제약조건 추가: `organizations(id)`

#### mail_users 테이블
- `organization_id` 컬럼 추가 (조직 연결)
- 외래키 제약조건 추가: `organizations(id)`

#### mails 테이블
- `mail_id` 컬럼 추가 (고유 메일 식별자)
- `sender_uuid` 컬럼 추가 (발송자 UUID)
- `recipient_emails` 컬럼 추가 (수신자 목록)
- `cc_emails` 컬럼 추가 (참조 목록)
- `bcc_emails` 컬럼 추가 (숨은참조 목록)
- `reply_to` 컬럼 추가 (답장 주소)
- `message_id` 컬럼 추가 (메시지 ID)
- `in_reply_to` 컬럼 추가 (답장 대상)
- `mail_references` 컬럼 추가 (참조 메시지들)
- `has_attachments` 컬럼 추가 (첨부파일 여부)
- `size_bytes` 컬럼 추가 (메일 크기)
- `organization_id` 컬럼 추가 (조직 연결)
- 외래키 제약조건 추가: `organizations(id)`, `mail_users(user_uuid)`

#### refresh_tokens 테이블
- `user_id` 컬럼을 `user_uuid`로 변경
- 외래키 제약조건 추가: `users(id)`

## 🔗 외래키 관계

### 조직 관련
- `users.organization_id` → `organizations.id`
- `mail_users.organization_id` → `organizations.id`
- `mails.organization_id` → `organizations.id`
- `organization_settings.organization_id` → `organizations.id`
- `organization_usage.organization_id` → `organizations.id`

### 메일 관련
- `mails.sender_uuid` → `mail_users.user_uuid`
- `mail_recipients.recipient_id` → `mail_users.user_uuid`
- `mail_recipients.mail_id` → `mails.mail_id`
- `mail_attachments.mail_id` → `mails.mail_id`
- `mail_in_folders.mail_id` → `mails.mail_id`
- `mail_in_folders.folder_id` → `mail_folders.id`
- `mail_logs.mail_id` → `mails.mail_id`
- `mail_logs.user_uuid` → `mail_users.user_uuid`

### 사용자 관련
- `mail_users.user_id` → `users.id`
- `mail_folders.user_id` → `mail_users.user_id`
- `refresh_tokens.user_uuid` → `users.id`

## 📊 인덱스 추가

### 성능 최적화를 위한 인덱스
- 모든 외래키 컬럼에 인덱스 추가
- 자주 검색되는 컬럼에 인덱스 추가:
  - `mails.status`
  - `mails.sent_at`
  - `mail_recipients.is_read`
  - `mail_logs.action`
  - `mail_logs.created_at`
  - `login_logs.login_status`
  - `login_logs.created_at`

## 🗂️ 기본 데이터

### 기본 조직 생성
- ID: 1
- 이름: "Default Organization"
- 도메인: "default.local"
- 설명: "Default organization for mail system"

### 데이터 마이그레이션
- 모든 기존 사용자를 기본 조직(ID: 1)에 할당
- 모든 기존 메일을 기본 조직에 할당
- 기존 메일에 고유 `mail_id` 생성

## 💬 컬럼 코멘트

모든 테이블과 컬럼에 한국어 코멘트를 추가하여 데이터베이스 구조를 명확히 문서화했습니다.

## ✅ 검증 결과

마이그레이션 후 데이터베이스 구조 검증 결과:
- ✅ 모든 새 테이블이 성공적으로 생성됨
- ✅ 기존 테이블의 컬럼이 올바르게 추가됨
- ✅ 외래키 제약조건이 정상적으로 설정됨
- ✅ 인덱스가 적절히 생성됨
- ✅ 기본 데이터가 올바르게 삽입됨

## 🚀 다음 단계

1. **애플리케이션 코드 업데이트**: 모델 파일과 일치하도록 API 코드 수정
2. **테스트 수행**: 새로운 데이터베이스 구조로 기능 테스트
3. **성능 모니터링**: 새로운 인덱스와 구조의 성능 확인
4. **백업 수행**: 마이그레이션 완료 후 전체 데이터베이스 백업

## 📝 주의사항

- `references`는 PostgreSQL 예약어이므로 `mail_references`로 변경
- 기존 데이터의 무결성을 유지하면서 마이그레이션 수행
- 모든 외래키 제약조건은 기존 데이터와 호환되도록 설정

---

**마이그레이션 완료 시간**: 2024년 12월  
**수행자**: SkyBoot Mail 개발팀  
**상태**: ✅ 성공적으로 완료