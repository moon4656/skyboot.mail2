# Mail Router 엔드포인트 테스트 체크리스트

## 📧 메일 발송 및 기본 기능 API
- [ ] **POST /send** - 메일 발송
- [ ] **GET /inbox** - 받은 메일함 조회 (페이지네이션)
- [ ] **GET /inbox/{mail_id}** - 받은 메일 상세 조회
- [ ] **GET /sent** - 보낸 메일함 조회 (페이지네이션)
- [ ] **GET /sent/{mail_id}** - 보낸 메일 상세 조회
- [ ] **GET /drafts** - 임시보관함 조회 (페이지네이션)
- [ ] **GET /drafts/{mail_id}** - 임시보관함 상세 조회
- [ ] **GET /trash** - 휴지통 조회 (페이지네이션)
- [ ] **GET /trash/{mail_id}** - 휴지통 상세 조회

## 🔍 검색 및 필터 API
- [ ] **GET /search** - 메일 검색
- [ ] **GET /stats** - 메일 통계 조회
- [ ] **GET /attachments/{attachment_id}/download** - 첨부파일 다운로드
- [ ] **GET /search/autocomplete** - 검색 자동완성
- [ ] **POST /filter/advanced** - 고급 필터 적용
- [ ] **GET /unread** - 읽지 않은 메일 조회
- [ ] **GET /starred** - 중요 표시된 메일 조회
- [ ] **GET /stats/detailed** - 상세 메일 통계 조회
- [ ] **GET /stats/chart** - 차트용 통계 데이터 조회
- [ ] **GET /activity-log** - 메일 활동 로그 조회

## ✏️ 메일 상태 관리 API
- [ ] **PUT /{mail_id}/status** - 메일 상태 업데이트
- [ ] **DELETE /{mail_id}** - 메일 삭제 (휴지통 이동)
- [ ] **GET /{mail_id}/logs** - 메일 로그 조회
- [ ] **POST /{mail_id}/read** - 메일 읽음 처리
- [ ] **POST /{mail_id}/unread** - 메일 읽지 않음 처리
- [ ] **POST /mark-all-read** - 모든 메일 읽음 처리
- [ ] **POST /{mail_id}/star** - 메일 중요 표시
- [ ] **DELETE /{mail_id}/star** - 메일 중요 표시 해제

## 📁 폴더 관리 API
- [ ] **GET /folders** - 폴더 목록 조회
- [ ] **POST /folders** - 새 폴더 생성
- [ ] **PUT /folders/{folder_id}** - 폴더 수정
- [ ] **DELETE /folders/{folder_id}** - 폴더 삭제
- [ ] **POST /{mail_id}/move** - 메일 이동
- [ ] **POST /bulk-action** - 메일 대량 작업

## 🗑️ 휴지통 관리 API
- [ ] **POST /trash/{mail_id}/restore** - 휴지통에서 메일 복원
- [ ] **DELETE /trash/{mail_id}/permanent** - 메일 영구 삭제
- [ ] **DELETE /trash/empty** - 휴지통 비우기

## 📎 첨부파일 관리 API
- [ ] **GET /{mail_id}/attachments** - 메일의 모든 첨부파일 목록 조회
- [ ] **POST /attachments/upload** - 첨부파일 미리 업로드
- [ ] **DELETE /attachments/{attachment_id}** - 첨부파일 삭제

## 📝 임시보관함 고급 기능 API
- [ ] **POST /drafts/create** - 임시보관 메일 생성
- [ ] **PUT /drafts/{draft_id}** - 임시보관 메일 수정
- [ ] **POST /drafts/{draft_id}/send** - 임시보관 메일 발송

## ⚙️ 사용자 설정 API
- [ ] **GET /settings** - 메일 설정 조회
- [ ] **PUT /settings** - 메일 설정 업데이트
- [ ] **GET /signature** - 서명 조회
- [ ] **PUT /signature** - 서명 설정

## 🔔 알림 및 실시간 기능 API
- [ ] **GET /notifications** - 알림 목록 조회
- [ ] **POST /notifications/{notification_id}/read** - 알림 읽음 처리
- [ ] **GET /ws** - WebSocket 연결 (실시간 알림)

## 📊 대량 작업 API
- [ ] **POST /bulk/delete** - 일괄 삭제
- [ ] **POST /bulk/move** - 일괄 이동
- [ ] **POST /bulk/read** - 일괄 읽음 처리

---

## 테스트 진행 상황
- **총 엔드포인트 수**: 42개
- **완료된 테스트**: 0개
- **진행률**: 0%

## 테스트 우선순위
1. **High Priority**: 메일 발송, 받은메일함, 보낸메일함 등 핵심 기능
2. **Medium Priority**: 검색, 필터, 폴더 관리 등 부가 기능
3. **Low Priority**: 통계, 로그, 고급 기능 등

## 테스트 결과 기록
각 엔드포인트 테스트 완료 시 다음 정보를 기록:
- ✅ 성공: 정상 응답 및 예상 결과
- ❌ 실패: 오류 내용 및 수정 사항
- ⚠️ 주의: 부분적 성공 또는 개선 필요 사항

---
*마지막 업데이트: 2024년 12월*