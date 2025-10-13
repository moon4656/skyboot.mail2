# SkyBoot Mail API 설계 문서 (필드 단위 응답 정리)

본 문서는 주요 엔드포인트의 응답 스키마를 필드 단위로 명확히 기술합니다. 각 섹션은 이미 정의된 라우터와 Pydantic 스키마를 근거로 작성되었습니다.

## 공통 규칙
- `Base URL`: `/api/v1`
- 인증: 대부분의 엔드포인트는 `Bearer` 액세스 토큰 필요
- 조직 컨텍스트: 멀티 테넌트(조직) 지원. 요청 컨텍스트에서 `org_id`/`org_code`가 설정됨
- 권한: 엔드포인트별로 사용자/관리자 권한이 다름
- 페이지네이션: `page`, `limit` 또는 `size`와 `total`, `total_pages` 등 제공

---

## 인증 (Auth)

### POST `/auth/login`
- 설명: 사용자 로그인. 액세스/리프레시 토큰 발급
- 요청 모델: `UserLogin`
- 요청 필드:
  - `user_id` (`str`): 사용자 ID
  - `password` (`str`): 비밀번호
- 응답 모델: `Token`
- 응답 필드:
  - `access_token` (`str`): 액세스 토큰
  - `refresh_token` (`str`): 리프레시 토큰
  - `token_type` (`str`, 기본 `bearer`): 토큰 타입
  - `expires_in` (`int`): 액세스 토큰 만료 시간(초)

### POST `/auth/refresh`
- 설명: 리프레시 토큰으로 액세스 토큰 재발급
- 요청 모델: `TokenRefresh`
- 요청 필드:
  - `refresh_token` (`str`): 리프레시 토큰
- 응답 모델: `AccessToken`
- 응답 필드:
  - `access_token` (`str`): 새 액세스 토큰
  - `token_type` (`str`, 기본 `bearer`): 토큰 타입
  - `expires_in` (`int`): 액세스 토큰 만료 시간(초)

### POST `/auth/register`
- 설명: 조직 내 사용자 등록
- 요청 모델: `UserCreate`
- 요청 필드:
  - `user_id` (`str`)
  - `username` (`str`)
  - `email` (`EmailStr`)
  - `org_code` (`str`)
  - `password` (`str`)
  - `full_name` (`str | None`)
- 응답 모델: `UserResponse`
- 응답 필드:
  - `user_id` (`str`): 사용자 ID
  - `username` (`str`): 사용자명
  - `email` (`EmailStr`): 이메일 주소
  - `org_id` (`str`): 조직 ID
  - `user_uuid` (`str`): 사용자 UUID
  - `role` (`str`): 사용자 역할
  - `is_active` (`bool`): 활성 상태
  - `created_at` (`datetime`): 생성 시간
  - `updated_at` (`datetime | None`): 수정 시간

### GET `/auth/me`
- 설명: 현재 로그인 사용자 정보 조회
- 요청: 본문 없음. `Authorization: Bearer <access_token>` 헤더 필요
- 응답 모델: `UserResponse` (필드는 위와 동일)

---

## 사용자 (Users)

### GET `/users`
- 설명: 사용자 목록 조회(검색/페이지네이션 포함)
- 응답 모델: `Dict[str, Any]` (페이지네이션 래퍼)
- 응답 필드:
  - `users` (`List[UserResponse]`): 사용자 목록
  - `total` (`int`): 전체 사용자 수
  - `page` (`int`): 현재 페이지 번호
  - `limit` (`int`): 페이지당 항목 수
  - `total_pages` (`int`): 전체 페이지 수
- `UserResponse` 필드:
  - `user_id` (`str`)
  - `username` (`str`)
  - `email` (`EmailStr`)
  - `org_id` (`str`)
  - `user_uuid` (`str`)
  - `role` (`str`)
  - `is_active` (`bool`)
  - `created_at` (`datetime`)
  - `updated_at` (`datetime | None`)

### GET `/users/me`
- 설명: 현재 사용자 정보 조회
- 응답 모델: `UserResponse` (필드는 위와 동일)

### GET `/users/{user_id}` / PUT `/users/{user_id}`
- 설명: 사용자 단건 조회/수정
- 응답 모델: `UserResponse` (필드는 위와 동일)

### DELETE `/users/{user_id}`
- 설명: 사용자 삭제(소프트 삭제)
- 응답 모델: `Dict[str, str]`
- 응답 필드:
  - `message` (`str`): 처리 결과 메시지(성공 시 "사용자가 성공적으로 삭제되었습니다.")

### POST `/users/{user_id}/change-password`
- 설명: 사용자 비밀번호 변경
- 응답 모델: `Dict[str, str]`
- 응답 필드:
  - `message` (`str`): 처리 결과 메시지(성공 시 "비밀번호가 성공적으로 변경되었습니다.")

### GET `/users/stats/overview`
- 설명: 사용자 통계 조회(관리자)
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `total_users` (`int`): 전체 사용자 수
  - `active_users` (`int`): 활성 사용자 수
  - `admin_users` (`int`): 관리자 사용자 수
  - `recent_users` (`int`): 최근 생성 사용자 수
  - `inactive_users` (`int`): 비활성 사용자 수

### POST `/users/{user_id}/activate`
- 설명: 사용자 활성화(관리자)
- 응답 모델: `Dict[str, str]`
- 응답 필드:
  - `message` (`str`): 처리 결과 메시지(성공 시 "사용자가 성공적으로 활성화되었습니다.")

### POST `/users/{user_id}/deactivate`
- 설명: 사용자 비활성화(관리자)
- 응답 모델: `Dict[str, str]`
- 응답 필드:
  - `message` (`str`): 처리 결과 메시지(성공 시 "사용자가 성공적으로 비활성화되었습니다.")

---

## 조직 (Organizations)

### GET `/organization/list`
- 설명: 조직 목록 조회(관리자 전용)
- 요청 쿼리 파라미터:
  - `page` (`int`, 기본 1)
  - `limit` (`int`, 기본 20, 최대 100)
  - `search` (`str | None`)
  - `is_active` (`bool | None`)
- 응답 모델: `OrganizationListResponse`
- 응답 필드:
  - `organizations` (`List[OrganizationResponse]`): 조직 목록
  - `total` (`int`): 전체 조직 수
  - `page` (`int`): 현재 페이지
  - `limit` (`int`): 페이지당 항목 수
  - `total_pages` (`int`): 전체 페이지 수

- `OrganizationResponse` 필드:
  - `org_id` (`str`): 조직 ID
  - `org_code` (`str`): 조직 코드
  - `subdomain` (`str`): 서브도메인
  - `admin_email` (`str`): 관리자 이메일
  - `name` (`str`): 조직명
  - `domain` (`str | None`): 조직 도메인
  - `description` (`str | None`): 조직 설명
  - `is_active` (`bool`): 활성 상태
  - `max_users` (`int | None`): 최대 사용자 수 제한
  - `max_storage_gb` (`int | None`): 최대 저장공간(GB)
  - `settings` (`dict`): 조직 설정(코어 필드 외 키-값)
  - `created_at` (`datetime`): 생성 시간
  - `updated_at` (`datetime`): 수정 시간

### GET `/organization/current/stats` / GET `/organization/{org_id}/stats`
- 설명: 조직 통계 조회(현재/특정 조직)
- 요청:
  - Path 파라미터: `org_id` (`UUID 형식`) — `/organization/{org_id}/stats`에서만 필요
  - 본문 없음, 인증 필요
- 응답 모델: `OrganizationStatsResponse`
- 응답 필드:
  - `organization` (`OrganizationResponse`): 조직 정보
  - `stats` (`OrganizationStats`): 통계 정보

- `OrganizationStats` 필드:
  - `org_id` (`str`): 조직 ID
  - `total_users` (`int`): 총 사용자 수
  - `active_users` (`int`): 활성 사용자 수
  - `mail_users` (`int`): 메일 사용자 수
  - `storage_used_mb` (`int`): 사용 저장 공간(MB)
  - `storage_limit_mb` (`int`): 저장 공간 제한(MB)
  - `storage_usage_percent` (`float`): 저장 공간 사용률(%)
  - `user_usage_percent` (`float`): 사용자 사용률(%)

### GET `/organization/current/settings` / GET `/organization/{org_id}/settings`
- 설명: 조직 설정 조회
- 요청:
  - Path 파라미터: `org_id` (`UUID 형식`) — `/organization/{org_id}/settings`에서만 필요
  - 본문 없음, 인증 필요
- 응답 모델: `OrganizationSettingsResponse`
- 응답 필드:
  - `organization` (`OrganizationResponse`): 조직 정보
  - `settings` (`OrganizationSettings`): 설정 정보(보안/기능 플래그 등 다수의 딕셔너리 필드 포함)

---

## 메일 설정 (Mail Setup)

### POST `/mail/setup-mail-account`
- 설명: 현재 사용자 메일 계정 초기화(생성/기존 계정 폴더 세팅)
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str`): 처리 메시지
  - `data` (`object`): 계정 정보 오브젝트
    - `mail_user_id` (`str`): 메일 사용자 UUID
    - `email` (`str`): 메일 사용자 이메일
    - `display_name` (`str | None`): 표시 이름

---

## 메일 코어 (Mail Core)

### POST `/api/v1/mail/send`
- 설명: 메일 발송(폼 데이터)
- 요청 Content-Type: `multipart/form-data`
- 요청 Form 필드:
  - `to_emails` (`str`)
  - `cc_emails` (`str | None`)
  - `bcc_emails` (`str | None`)
  - `subject` (`str`)
  - `content` (`str`)
  - `priority` (`MailPriority`)
  - `is_draft` (`str`)
- 요청 파일: `attachments` (`List[UploadFile] | None`)
- 응답 모델: `MailSendResponse`

### POST `/api/v1/mail/send-json`
- 설명: 메일 발송(JSON)
- 요청 모델: `MailSendRequest`
- 응답 모델: `MailSendResponse`

### GET `/api/v1/mail/inbox`
- 설명: 받은 메일함 목록
- 요청 쿼리: `page`, `limit`, `search`, `status`
- 응답 모델: `MailListWithPaginationResponse`

### GET `/api/v1/mail/inbox/{mail_uuid}`
- 설명: 받은 메일 상세
- 응답 모델: `MailDetailResponse`

### GET `/api/v1/mail/sent`
- 설명: 보낸 메일함 목록
- 요청 쿼리: `page`, `limit`, `search`
- 응답 모델: `MailListWithPaginationResponse`

### GET `/api/v1/mail/sent/{mail_uuid}`
- 설명: 보낸 메일 상세
- 응답 모델: `MailDetailResponse`

### GET `/api/v1/mail/drafts`
- 설명: 임시보관함 목록
- 요청 쿼리: `page`, `limit`, `search`
- 응답 모델: `MailListWithPaginationResponse`

### GET `/api/v1/mail/drafts/{mail_uuid}`
- 설명: 임시보관 메일 상세
- 응답 모델: `MailDetailResponse`

### GET `/api/v1/mail/trash`
- 설명: 휴지통 목록
- 요청 쿼리: `page`, `limit`, `search`, `status`
- 응답 모델: `MailListWithPaginationResponse`

### GET `/api/v1/mail/trash/{mail_uuid}`
- 설명: 휴지통 메일 상세
- 응답 모델: `MailDetailResponse`

### GET `/api/v1/mail/attachments/{attachment_id}`
- 설명: 첨부파일 다운로드
- 응답: 파일 다운로드(`FileResponse`)

### DELETE `/api/v1/mail/{mail_uuid}`
- 설명: 메일 삭제(영구 삭제 또는 휴지통 이동)
- 요청 쿼리: `permanent` (`bool`, 기본 `false`)
- 응답: `Dict[str, Any]` — `success`, `message`, `data.mail_uuid`, `data.permanent`

---

## 메일 편의 (Convenience)

### 공통 응답 래퍼: `APIResponse`
- 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str | None`): 설명/오류 메시지
  - `data` (`object | None`): 실제 데이터(payload)

### GET `/api/v1/mail/unread`, GET `/api/v1/mail/starred`
- 설명: 읽지 않은 메일/중요 표시 메일 조회(페이지네이션)
- 응답 모델: `APIResponse`
- `data` 필드 구조(공통):
  - `mails` (`List[object]`): 메일 목록
    - `id` (`str`): 메일 UUID
    - `subject` (`str`): 제목
    - `sender_email` (`str`): 발신자 이메일
    - `to_emails` (`List[str]`): 수신자 이메일 목록(TO)
    - `status` (`MailStatus`): 메일 상태
    - `priority` (`MailPriority`): 우선순위
    - `has_attachments` (`bool`): 첨부파일 여부
    - `created_at` (`datetime`): 생성 시간
    - `sent_at` (`datetime | None`): 발송 시간
    - `is_read` (`bool`): 현재 사용자 기준 읽음 여부
  - `total` (`int`): 전체 개수
  - `page` (`int`): 현재 페이지
  - `limit` (`int`): 페이지당 개수
  - `pages` (`int`): 전체 페이지 수

### POST `/api/v1/mail/{mail_uuid}/read`, POST `/api/v1/mail/{mail_uuid}/unread`
- 설명: 메일 읽음/읽지 않음 처리
- 응답 모델: `APIResponse`
- `message` 예시: "메일이 읽음 처리되었습니다.", "메일이 읽지 않음 처리되었습니다."
- `data` 필드 구조:
  - `mail_uuid` (`str`): 대상 메일 UUID
  - `read_at` (`datetime | None`): 읽음 처리 시각(읽지 않음 처리 시 `None`)
  - `is_read` (`bool`): 읽음 여부(true/false)

### POST `/api/v1/mail/mark-all-read`
- 설명: 폴더 내 모든 메일 읽음 처리
- 응답 모델: `APIResponse`
- `message` 예시: "N개의 메일이 읽음 처리되었습니다."
- `data` 필드:
  - `updated_count` (`int`): 읽음 처리된 메일 수
  - `folder_type` (`str`): 적용된 폴더(`inbox|sent|drafts|trash`)

### POST `/api/v1/mail/{mail_uuid}/star`, DELETE `/api/v1/mail/{mail_uuid}/star`
- 설명: 중요 표시/해제
- 응답 모델: `APIResponse`
- `message` 예시: "메일이 중요 표시되었습니다.", "메일 중요 표시가 해제되었습니다."
- `data` 필드:
  - `mail_uuid` (`str`): 대상 메일 UUID
  - `priority` (`MailPriority`): 변경된 우선순위(`HIGH` 또는 `NORMAL`)

### GET `/api/v1/mail/search/suggestions`
- 설명: 검색 자동완성 제안
- 응답 모델: `APIResponse`
- `data` 예시:
  - `suggestions` (`List[str]`): 제안 문자열 목록

---

## 메일 고급 (Advanced)

### GET `/mail/folders`
- 설명: 사용자 폴더 목록 조회
- 응답 모델: `FolderListResponse`
- 응답 필드:
  - `folders` (`List[object]`): 폴더 목록
    - `folder_uuid` (`str`): 폴더 UUID
    - `name` (`str`): 폴더명
    - `folder_type` (`str`): 폴더 유형(`inbox|sent|drafts|trash|custom` 등)
    - `mail_count` (`int`): 폴더 내 메일 수
    - `created_at` (`datetime`): 생성 시간

### POST `/mail/folders`
- 설명: 폴더 생성
- 응답 모델: `FolderCreateResponse`
- 응답 필드:
  - `id` (`int`): 내부 ID
  - `folder_uuid` (`str`): 폴더 UUID
  - `name` (`str`): 폴더명
  - `folder_type` (`str`): 폴더 유형
  - `mail_count` (`int`): 초기 메일 수(일반적으로 0)
  - `created_at` (`datetime`): 생성 시간

### PUT `/mail/folders/{folder_uuid}`
- 설명: 폴더 수정(시스템 폴더 제외)
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `folder_uuid` (`str`)
  - `name` (`str`)
  - `folder_type` (`str`)
  - `mail_count` (`int`)
  - `created_at` (`datetime`)
  - `updated_at` (`datetime`)

### DELETE `/mail/folders/{folder_uuid}`
- 설명: 폴더 삭제(시스템 폴더 제외)
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str`): 처리 메시지(성공 시 "폴더가 삭제되었습니다.")
  - `data` (`object`): 부가 정보
    - `folder_uuid` (`str`): 삭제된 폴더 UUID

### POST `/mail/folders/{folder_uuid}/mails/{mail_uuid}`
- 설명: 메일을 특정 폴더로 이동
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str`): 처리 메시지
  - `data` (`object`): 이동 결과 정보
    - `mail_uuid` (`str`): 이동된 메일 UUID
    - `folder_uuid` (`str`): 대상 폴더 UUID
    - `folder_name` (`str`): 대상 폴더명

### POST `/mail/backup`
- 설명: 메일 백업 파일(zip) 생성
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str`): 처리 메시지
  - `data` (`object`): 백업 메타정보
    - `backup_filename` (`str`): 생성된 백업 파일명
    - 기타 내부 수치(메일/첨부 포함 여부 등) 포함 가능

### GET `/mail/backup/{backup_filename}`
- 설명: 백업 파일 다운로드
- 응답: 파일 다운로드(`FileResponse`)
- 헤더: `Content-Disposition` 등 파일 전송 헤더 포함

### POST `/mail/restore`
- 설명: 백업 파일로부터 메일 복원
- 응답 모델: `Dict[str, Any]`
- 응답 필드:
  - `success` (`bool`): 성공 여부
  - `message` (`str`): 처리 메시지(복원/건너뜀 개수 포함)
  - `data` (`object`): 복원 결과
    - `restored_count` (`int`): 복원된 메일 수
    - `skipped_count` (`int`): 건너뛴 메일 수(중복 등)
    - `overwrite_existing` (`bool`): 기존 메일 덮어쓰기 여부

### GET `/mail/analytics`
- 설명: 기간별 메일 분석(요약 통계)
- 응답 모델: `Dict[str, Any]`
- 응답 필드: 구현에 따라 유동적(예: 발송/수신 수, 우선순위 분포 등)

---

## 비고
- 본 문서의 필드 정의는 `backend/app/schemas/*.py`의 Pydantic 모델을 기준으로 함
- 실제 응답 래핑(`APIResponse` 등)이 있는 경우, 상위 키(`success`, `message`, `data`)가 추가될 수 있음
- 멀티 조직 환경에서는 요청 컨텍스트에 설정된 `org_id`/`org_code`에 의해 데이터 범위가 제한됨
- 경로 표기는 `/api/v1` 기준으로 업데이트됨