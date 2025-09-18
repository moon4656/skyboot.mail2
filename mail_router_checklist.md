# Mail Router 엔드포인트 체크리스트

## 📋 전체 엔드포인트 목록 (총 42개)

### 1. 메일 발송 관련
- [ ] **POST /api/mail/send** - 메일 발송
- [ ] **POST /api/mail/drafts** - 임시보관 메일 생성/저장
- [ ] **PUT /api/mail/drafts/{mail_id}** - 임시보관 메일 수정
- [ ] **POST /api/mail/drafts/{mail_id}/send** - 임시보관 메일 발송

### 2. 메일 조회 관련
- [ ] **GET /api/mail/inbox** - 받은 메일 목록
- [ ] **GET /api/mail/inbox/{mail_id}** - 받은 메일 상세
- [ ] **GET /api/mail/sent** - 보낸 메일 목록
- [ ] **GET /api/mail/sent/{mail_id}** - 보낸 메일 상세
- [ ] **GET /api/mail/drafts** - 임시보관함 메일 목록
- [ ] **GET /api/mail/drafts/{mail_id}** - 임시보관함 메일 상세 조회
- [ ] **GET /api/mail/trash** - 휴지통 메일 목록 조회
- [ ] **GET /api/mail/trash/{mail_id}** - 휴지통 메일 상세 조회

### 3. 메일 검색 및 필터링
- [ ] **POST /api/mail/search** - 메일 검색
- [ ] **GET /api/mail/search/suggestions** - 검색 자동완성
- [ ] **POST /api/mail/filter** - 고급 필터 적용
- [ ] **GET /api/mail/unread** - 읽지 않은 메일만 조회
- [ ] **GET /api/mail/starred** - 중요 표시된 메일 조회

### 4. 메일 상태 관리
- [ ] **PATCH /api/mail/status/{mail_id}** - 메일 상태 업데이트
- [ ] **POST /api/mail/{mail_id}/read** - 메일 읽음 처리
- [ ] **POST /api/mail/{mail_id}/unread** - 메일 읽지 않음 처리
- [ ] **POST /api/mail/mark-all-read** - 모든 메일 읽음 처리
- [ ] **POST /api/mail/{mail_id}/star** - 메일 중요 표시
- [ ] **DELETE /api/mail/{mail_id}/star** - 메일 중요 표시 해제

### 5. 메일 삭제 및 복원
- [ ] **DELETE /api/mail/{mail_id}** - 메일 삭제
- [ ] **POST /api/mail/trash/{mail_id}/restore** - 휴지통에서 메일 복원
- [ ] **DELETE /api/mail/trash/{mail_id}/permanent** - 메일 영구 삭제
- [ ] **DELETE /api/mail/trash/empty** - 휴지통 비우기

### 6. 대량 작업
- [ ] **POST /api/mail/bulk/delete** - 여러 메일 일괄 삭제
- [ ] **POST /api/mail/bulk/move** - 여러 메일 일괄 이동
- [ ] **POST /api/mail/bulk/mark-read** - 여러 메일 일괄 읽음 처리

### 7. 첨부파일 관리
- [ ] **GET /api/mail/attachments/{attachment_id}** - 첨부파일 다운로드
- [ ] **GET /api/mail/{mail_id}/attachments** - 메일의 모든 첨부파일 목록 조회
- [ ] **POST /api/mail/attachments/upload** - 첨부파일 미리 업로드
- [ ] **DELETE /api/mail/attachments/{attachment_id}** - 첨부파일 삭제
- [ ] **GET /api/mail/attachments/{attachment_id}/download** - 첨부파일 다운로드

### 8. 폴더 관리
- [ ] **GET /api/mail/folders** - 사용자 폴더 목록 조회
- [ ] **POST /api/mail/folders** - 새 폴더 생성
- [ ] **PUT /api/mail/folders/{folder_id}** - 폴더 이름 수정
- [ ] **DELETE /api/mail/folders/{folder_id}** - 폴더 삭제
- [ ] **POST /api/mail/folders/{folder_id}/move** - 메일을 특정 폴더로 이동

### 9. 통계 및 설정
- [ ] **GET /api/mail/stats** - 메일 통계
- [ ] **GET /api/mail/stats/detailed** - 상세 메일 통계
- [ ] **GET /api/mail/stats/chart** - 차트용 통계 데이터
- [ ] **GET /api/mail/activity** - 메일 활동 로그
- [ ] **GET /api/mail/logs** - 메일 로그 조회

### 10. 사용자 설정
- [ ] **GET /api/mail/settings** - 메일 설정 조회
- [ ] **PUT /api/mail/settings** - 메일 설정 업데이트
- [ ] **GET /api/mail/signature** - 서명 조회
- [ ] **PUT /api/mail/signature** - 서명 설정

### 11. 알림 관리
- [ ] **GET /api/mail/notifications** - 알림 목록 조회
- [ ] **POST /api/mail/notifications/mark-read** - 알림 읽음 처리

---

## 🧪 테스트 진행 상황

### 구문 검사
- [ ] Python 구문 오류 확인
- [ ] Import 문 검증
- [ ] 함수 정의 검증

### 기능 테스트
- [ ] 인증 관련 테스트
- [ ] 데이터베이스 연결 테스트
- [ ] API 응답 형식 검증

### 오류 수정
- [ ] 발견된 오류 목록 작성
- [ ] 오류 수정 완료
- [ ] 재테스트 완료

---

## 📊 완료 상태
- **총 엔드포인트**: 42개
- **테스트 완료**: 0개
- **오류 발견**: 0개
- **수정 완료**: 0개
- **진행률**: 0%

---

*최종 업데이트: 2024-01-XX*