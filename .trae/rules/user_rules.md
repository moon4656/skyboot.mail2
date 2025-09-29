# 기업용 메일서버 프로젝트 사용자 규칙 (User Rules)

## 📋 목차
1. [개발 환경 규칙](#개발-환경-규칙)
2. [코드 작성 규칙](#코드-작성-규칙)
3. [데이터베이스 규칙](#데이터베이스-규칙)
4. [API 설계 규칙](#api-설계-규칙)
5. [보안 규칙](#보안-규칙)
6. [메일 서버 규칙](#메일-서버-규칙)
7. [로깅 및 모니터링 규칙](#로깅-및-모니터링-규칙)
8. [테스트 규칙](#테스트-규칙)
9. [배포 및 운영 규칙](#배포-및-운영-규칙)
10. [문서화 규칙](#문서화-규칙)
11. [성능 및 최적화 규칙](#성능-및-최적화-규칙)

---

## 🛠️ 개발 환경 규칙

### 1.1 프로젝트 구조 (SaaS 다중 조직 지원)
- **백엔드**: `backend/` 디렉토리에 FastAPI 기반 SaaS 메일 서버 API
  - `backend/app/` - 메인 애플리케이션 코드
    - `backend/app/database/` - 데이터베이스 연결 및 설정
    - `backend/app/middleware/` - 미들웨어 (CORS, 인증, 테넌트 등)
    - `backend/app/model/` - SQLAlchemy 데이터베이스 모델
    - `backend/app/router/` - API 라우터 (auth, organization, user, mail 등)
    - `backend/app/schemas/` - Pydantic 스키마
    - `backend/app/service/` - 비즈니스 로직 서비스
    - `backend/app/utils/` - 유틸리티 함수
  - `backend/alembic/` - 데이터베이스 마이그레이션 스크립트 (Alembic)
  - `backend/tests/` - 모든 백엔드 테스트 코드 (pytest 기반)
- **프론트엔드**: `frontend/` 디렉토리에 Vue.js 3 + TypeScript 기반 SaaS 웹 메일 클라이언트
  - `frontend/src/` - 메인 소스 코드
    - `frontend/src/router/` - Vue Router 설정
    - `frontend/src/services/` - API 서비스 클래스
    - `frontend/src/stores/` - Pinia 상태 관리
    - `frontend/src/views/` - 페이지 컴포넌트
  - `frontend/tests/` - 프론트엔드 테스트 코드
- **메일 서버**: Postfix (SMTP), Dovecot (IMAP/POP3) 설정 파일 (조직별 가상 도메인 지원)
- **환경 설정**: `.env` 파일을 사용하여 환경별 설정 관리 (Redis, PostgreSQL, 메일 서버 포함)
- **의존성 관리**: `requirements.txt` (Python), `package.json` (Node.js)
- **컨테이너화**: `docker-compose.yml`, `docker-compose.dev.yml` (PostgreSQL, Redis, Postfix 포함)

### 1.2 환경 변수 관리 (SaaS 다중 조직 지원)
- 모든 민감한 정보는 `.env` 파일에 저장
- `.env.example` 파일로 필수 환경 변수 템플릿 제공
- **데이터베이스 설정**: PostgreSQL 연결 정보 (조직별 데이터 분리)
- **Redis 설정**: 캐시, 세션, 백그라운드 작업 큐 관리
- **메일 서버 설정**: SMTP, IMAP 포트, 인증 정보 (조직별 가상 도메인)
- **백그라운드 작업**: Celery, APScheduler, RQ 설정
- **클라우드 저장소**: boto3 AWS S3 설정 (첨부파일 저장)
- **모니터링**: Prometheus 메트릭 수집 설정
- **보안**: JWT 시크릿 키, 암호화 키
- **조직 설정**: 기본 조직 정보, 제한 정책
- 프로덕션 환경에서는 환경 변수로 직접 설정

### 1.3 버전 관리
- Git을 사용한 소스 코드 관리
- 브랜치 전략: `main` (프로덕션), `develop` (개발), `feature/*` (기능 개발)
- 커밋 메시지는 한국어로 명확하게 작성
- 메일 서버 설정 파일도 버전 관리에 포함

### 1.4 개발 도구 (SaaS 기술 스택)
- **IDE**: Trae AI (권장), VS Code
- **Python**: 3.11 이상 (FastAPI, SQLAlchemy, Alembic)
- **Node.js**: 18 이상 (Vue.js 3, TypeScript, Vite)
- **데이터베이스**: PostgreSQL 15 이상
- **캐시/큐**: Redis (세션, 캐시, 백그라운드 작업 큐)
- **백그라운드 작업**: Celery, APScheduler, RQ
- **모니터링**: Prometheus, Grafana
- **클라우드 저장소**: AWS S3 (boto3)
- **컨테이너**: Docker, Docker Compose
- **메일 서버**: Postfix (SMTP), Dovecot (IMAP/POP3)
- **웹서버**: Nginx (리버스 프록시)
- **UI 프레임워크**: Vuestic UI
- **테스트**: pytest (백엔드), Vitest (프론트엔드)

---

## 💻 코드 작성 규칙

### 2.1 Python 코딩 스타일
- PEP 8 스타일 가이드 준수
- 함수와 클래스에 한국어 docstring 작성
- 변수명과 함수명은 영어로, 주석은 한국어로 작성
- 타입 힌트 사용 필수 (`typing` 모듈 활용)
- 메일 관련 함수는 명확한 네이밍 (예: `send_email`, `parse_mail_header`)

### 2.2 FastAPI 개발 규칙 (SaaS 다중 조직 지원)
- 모든 엔드포인트에 `summary`와 상세 docstring 작성
- Pydantic 모델을 사용한 요청/응답 검증
- 의존성 주입(Dependency Injection) 패턴 활용
- **조직별 데이터 분리**: 모든 API에서 조직 컨텍스트 확인
- **테넌트 미들웨어**: 요청별 조직 정보 자동 추출
- **권한 기반 접근 제어**: 조직 내 역할별 권한 관리
- 비동기 처리가 필요한 경우 `async/await` 사용
- **백그라운드 작업**: Celery, APScheduler, RQ를 통한 메일 발송 및 처리
- **API 버전 관리**: 조직별 기능 차이 지원
- **속도 제한**: 조직별 API 호출 제한 적용
- **모니터링**: Prometheus 메트릭 수집 및 추적

### 2.3 Vue.js 개발 규칙 (SaaS 프론트엔드)
- **Composition API** 사용 권장 (Vue 3)
- **TypeScript** 적극 활용 (타입 안정성)
- **Pinia**를 통한 상태 관리 (조직별 상태 분리)
- **Vuestic UI** 컴포넌트 라이브러리 활용
- **조직별 테마**: 조직별 브랜딩 및 UI 커스터마이징
- **다국어 지원**: i18n을 통한 국제화
- 컴포넌트 단위 개발 및 재사용성 고려
- **반응형 디자인**: 모바일 및 데스크톱 지원
- **API 서비스**: axios 기반 API 클라이언트
- **라우터 가드**: 조직별 접근 권한 확인
- ESLint 및 Prettier 설정 준수
- **성능 최적화**: 코드 스플리팅, 레이지 로딩

### 2.4 에러 처리
- 모든 예외는 적절한 HTTP 상태 코드와 함께 처리
- 사용자 친화적인 한국어 에러 메시지 제공
- 메일 발송 실패 시 재시도 메커니즘 구현
- 로깅을 통한 에러 추적 및 디버깅 정보 기록

---

## 🗄️ 데이터베이스 규칙

### 3.1 스키마 설계 (SaaS 다중 조직 지원)
- PostgreSQL을 기본 데이터베이스로 사용
- SQLAlchemy ORM을 통한 데이터베이스 접근
- 모든 테이블과 컬럼에 한국어 주석 작성
- **조직별 데이터 분리**: 모든 주요 테이블에 `organization_id` 외래 키
- **조직 모델**: `Organization` 테이블로 다중 테넌트 지원
- **사용자 모델**: 조직별 사용자 관리 및 역할 기반 권한
- **메일 모델**: 조직별 메일 데이터 분리 및 수신자 관리
- UUID 사용으로 보안성 강화 (조직 및 사용자 식별)
- Postfix/Dovecot 연동을 위한 가상 테이블 설계 (조직별 도메인)
- **감사 로그**: 조직별 활동 추적 및 시스템 메트릭

### 3.2 테이블 명명 규칙 (SaaS 구조)
- 테이블명: 복수형 snake_case (예: `organizations`, `users`, `mails`, `mail_recipients`)
- 컬럼명: snake_case (예: `created_at`, `organization_id`, `email_address`)
- 인덱스명: `idx_테이블명_컬럼명` 형식
- **조직 관련 테이블**: `organizations`, `organization_activity_logs`
- **메일 관련 테이블**: `mails`, `mail_recipients`, `mail_access_logs`
- **가상 도메인 테이블**: `virtual_domains`, `virtual_aliases` (Postfix 연동)
- **시스템 테이블**: `system_metrics_logs`, `background_tasks`
- **외래 키**: `organization_id`, `user_id` 등 일관된 명명

### 3.3 데이터 무결성
- 필수 필드는 `nullable=False` 설정
- 외래 키 관계 명확히 정의
- 이메일 주소 유효성 검증 제약 조건
- 적절한 인덱스 설정으로 성능 최적화
- 타임스탬프 필드는 timezone 정보 포함

### 3.4 마이그레이션 관리 (Alembic)
- **Alembic**을 사용한 데이터베이스 스키마 버전 관리
- 모든 스키마 변경은 마이그레이션 스크립트로 관리
- **조직별 데이터 분리**: 기존 데이터 마이그레이션 시 조직 컨텍스트 고려
- **Postfix/Dovecot 연동**: 가상 도메인 테이블 변경 시 메일 서버 재시작 고려
- `backend/alembic/` 디렉토리에 관련 스크립트 저장
- **마이그레이션 명령어**:
  - `alembic revision --autogenerate -m "설명"` (새 마이그레이션 생성)
  - `alembic upgrade head` (최신 버전으로 업그레이드)
  - `alembic downgrade -1` (이전 버전으로 다운그레이드)
- **환경별 설정**: 개발, 스테이징, 프로덕션 환경별 마이그레이션 관리

### 3.5 메일 데이터 관리
- 메일 내용은 별도 테이블로 분리 저장
- 첨부파일은 파일 시스템에 저장, 경로만 DB에 기록
- 대용량 메일함 처리를 위한 파티셔닝 고려
- 오래된 메일 데이터 아카이빙 정책 수립

---

## 🔌 API 설계 규칙

### 4.1 RESTful API 설계
- HTTP 메소드 적절히 활용 (GET, POST, PUT, DELETE)
- 리소스 중심의 URL 설계
- 일관된 응답 형식 유지
- 메일 관련 리소스: `/api/mail/`, `/api/users/`, `/api/domains/`

### 4.2 엔드포인트 명명 규칙 (SaaS API 구조)
- URL은 소문자와 하이픈 사용
- 복수형 명사 사용 (예: `/api/organizations/`, `/api/users/`)
- **조직별 API 그룹화**:
  - `/api/auth/` - 인증 관련 (로그인, 회원가입, 토큰 관리)
  - `/api/organizations/` - 조직 관리 (생성, 수정, 삭제, 설정)
  - `/api/users/` - 사용자 관리 (조직 내 사용자)
  - `/api/mail/core/` - 핵심 메일 기능 (발송, 수신, 관리)
  - `/api/mail/convenience/` - 편의 기능 (템플릿, 자동 응답)
  - `/api/mail/advanced/` - 고급 기능 (분석, 추적, 보고서)
  - `/api/mail/setup/` - 메일 서버 설정 (도메인, 인증)
  - `/api/debug/` - 디버깅 및 테스트 (개발 환경)
- **조직 컨텍스트**: 모든 API에서 조직 정보 자동 추출
- 버전 관리 고려 (필요시 `/v1/` 접두사)

### 4.3 응답 형식
- JSON 형식으로 응답
- 성공/실패 상태 명확히 구분
- 에러 응답에는 상세한 메시지 포함
- 페이지네이션 지원 (`limit`, `offset` 파라미터)
- 메일 목록 조회 시 필터링 옵션 제공

### 4.4 메일 API 특화 기능 (SaaS 다중 조직)
- **핵심 메일 기능** (`/api/mail/core/`):
  - 메일 발송 API (단일, 대량, 예약 발송)
  - 메일함 조회 API (받은편지함, 보낸편지함, 임시보관함)
  - 메일 검색 및 필터링 API
  - 첨부파일 업로드/다운로드 API (AWS S3 연동)
- **편의 기능** (`/api/mail/convenience/`):
  - 메일 템플릿 관리 API
  - 자동 응답 설정 API
  - 메일 서명 관리 API
  - 연락처 및 그룹 관리 API
- **고급 기능** (`/api/mail/advanced/`):
  - 메일 추적 및 분석 API
  - 발송 통계 및 보고서 API
  - A/B 테스트 API
  - 스팸 필터 관리 API
- **조직별 설정**: 모든 API에서 조직 컨텍스트 자동 적용
- **백그라운드 처리**: 대량 메일 발송 시 비동기 처리

---

## 🔒 보안 규칙

### 5.1 인증 및 권한 관리
- JWT 토큰 기반 사용자 인증
- 액세스 토큰 (30분), 리프레시 토큰 (7일) 분리
- 패스워드는 bcrypt로 해시화하여 저장
- 역할 기반 접근 제어 (RBAC)
- 이중 인증 (2FA) 지원

### 5.2 메일 보안
- TLS/SSL 암호화 통신 필수
- SPF, DKIM, DMARC 설정
- 스팸 및 피싱 메일 필터링
- 첨부파일 바이러스 검사
- 메일 내용 암호화 옵션

### 5.3 데이터 보호
- 민감한 정보는 환경 변수로 관리
- SQL 인젝션 방지 (ORM 사용)
- 입력 데이터 검증 및 sanitization
- HTTPS 사용 필수 (프로덕션)
- 개인정보 암호화 저장

### 5.4 접근 로깅
- 모든 로그인 시도 기록 (`login_logs` 테이블)
- 메일 접근 로그 기록 (`mail_access_logs` 테이블)
- IP 주소 및 User-Agent 정보 저장
- 실패한 인증 시도 모니터링
- 의심스러운 활동 자동 탐지

---

## 📧 메일 서버 규칙

### 6.1 Postfix 설정
- SMTP 서버 설정 및 최적화
- 가상 도메인 및 사용자 관리
- 메일 큐 관리 및 모니터링
- 스팸 필터링 설정
- TLS/SSL 인증서 설정

### 6.2 Dovecot 설정
- IMAP/POP3 서버 설정
- 메일박스 형식 (Maildir) 설정
- 사용자 인증 연동
- 메일 인덱싱 최적화
- 백업 및 복구 설정

### 6.3 메일 처리 규칙
- 메일 발송 우선순위 관리
- 대용량 첨부파일 처리
- 메일 전달 규칙 설정
- 자동 응답 및 부재중 메시지
- 메일 보관 정책

### 6.4 도메인 관리
- 가상 도메인 추가/삭제
- DNS 설정 (MX, SPF, DKIM 레코드)
- 도메인별 메일 정책 설정
- 서브도메인 메일 처리

---

## 📊 로깅 및 모니터링 규칙

### 7.1 로깅 시스템
- Python `logging` 모듈 사용
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 파일 로테이션 설정 (크기 및 시간 기반)
- 구조화된 로그 메시지 (타임스탬프, 레벨, 메시지)
- 메일 서버 로그와 애플리케이션 로그 분리

### 7.2 로그 내용
- API 요청/응답 로깅
- 메일 발송/수신 로그
- 사용자 인증 및 권한 로그
- 에러 발생 시 상세 스택 트레이스
- 성능 메트릭 (응답 시간, 처리량)

### 7.3 성능 모니터링
- 메일 발송 성공률 및 처리 시간
- 데이터베이스 쿼리 성능 모니터링
- Postfix/Dovecot 서버 상태 모니터링
- 시스템 리소스 사용량 추적
- 메일 큐 상태 모니터링

### 7.4 알림 시스템
- 메일 서버 장애 시 즉시 알림
- 스팸 메일 급증 시 알림
- 디스크 용량 부족 경고
- 비정상적인 로그인 시도 알림

---

## 🧪 테스트 규칙

### 8.1 테스트 구조 (SaaS 다중 조직 지원)
- **백엔드 테스트**: `/backend/tests/` 디렉토리에 모든 백엔드 테스트 코드 구성
- **프론트엔드 테스트**: `/frontend/tests/` 디렉토리에 프론트엔드 테스트 코드 구성
- **pytest 프레임워크** 사용 (백엔드), **Vitest** 사용 (프론트엔드)
- **테스트 분류**:
  - 단위 테스트: 개별 함수 및 클래스 테스트
  - 통합 테스트: API 엔드포인트 및 데이터베이스 연동 테스트
  - E2E 테스트: 전체 워크플로우 테스트
  - **조직별 테스트**: 다중 조직 환경에서의 데이터 분리 테스트
- **메일 서버 테스트**: 별도 테스트 환경 사용 (Docker 컨테이너)
- **테스트 파일 명명 규칙**: `test_*.py` (예: `test_mail_api.py`, `test_organization.py`)
- **테스트 클래스 명명 규칙**: `Test*` (예: `TestMailAPI`, `TestOrganization`)
- **픽스처 관리**: 조직별 테스트 데이터 및 사용자 계정 설정

### 8.2 테스트 커버리지
- 핵심 비즈니스 로직 80% 이상 커버리지
- 모든 API 엔드포인트 테스트
- 메일 발송/수신 기능 테스트
- 데이터베이스 연동 테스트
- 보안 기능 테스트

### 8.3 테스트 데이터 (SaaS 다중 조직)
- **백엔드 테스트 데이터**: `/backend/tests/` 폴더 내에 테스트용 데이터 파일 구성
- **조직별 테스트 시나리오**: 다중 조직 환경에서의 데이터 분리 테스트
- **실제 메일 시나리오**: 조직별 메일 발송 및 수신 테스트
- **다양한 메일 형식**: HTML, 텍스트, 멀티파트 메일 테스트
- **첨부파일 처리**: 이미지, 문서, 압축파일 (AWS S3 연동 테스트)
- **에러 시나리오**: 잘못된 이메일 형식, 권한 오류, 조직 접근 제한 등
- **성능 테스트**: 대용량 메일 처리, 동시 접속, 조직별 제한 테스트
- **백그라운드 작업 테스트**: Celery, APScheduler, RQ 작업 테스트
- **테스트용 조직 및 사용자**: 다중 조직 환경 시뮬레이션
- **Mock 데이터**: 외부 서비스 (AWS S3, Prometheus) 모킹
- **Fixture 파일**: 조직별 설정 및 권한 테스트 데이터

### 8.4 메일 서버 테스트
- SMTP 연결 테스트
- IMAP/POP3 연결 테스트
- TLS/SSL 인증서 검증
- 스팸 필터링 테스트
- 백업/복구 테스트

### 8.5 테스트 실행 방법 (SaaS 환경)
- **백엔드 테스트 실행**: `cd backend && python -m pytest tests/`
- **특정 테스트 파일 실행**: `python -m pytest tests/test_mail_api.py`
- **조직별 테스트 실행**: `python -m pytest tests/test_organization.py`
- **테스트 커버리지 확인**: `python -m pytest tests/ --cov=app --cov-report=html`
- **테스트 결과 리포트**: `python -m pytest tests/ --html=reports/report.html`
- **병렬 테스트 실행**: `python -m pytest tests/ -n auto` (pytest-xdist 필요)
- **프론트엔드 테스트**: `cd frontend && npm run test`
- **E2E 테스트**: `npm run test:e2e`
- **테스트 환경 변수**: 
  - `TEST_DATABASE_URL` (테스트 PostgreSQL)
  - `TEST_REDIS_URL` (테스트 Redis)
  - `TEST_AWS_S3_BUCKET` (테스트 S3 버킷)
  - `TEST_ORGANIZATION_ID` (테스트 조직 ID)
- **Docker 테스트 환경**: `docker-compose -f docker-compose.test.yml up -d`

---

## 🚀 배포 및 운영 규칙

### 9.1 환경 구성
- 개발(Development), 스테이징(Staging), 프로덕션(Production) 환경 분리
- Docker Compose를 통한 컨테이너화
- 환경별 설정 파일 관리
- Nginx 리버스 프록시 설정

### 9.2 서버 설정
- uvicorn ASGI 서버 사용
- 프로덕션에서는 Gunicorn + uvicorn workers 권장
- SSL/TLS 인증서 설정 (Let's Encrypt)
- 방화벽 설정 (포트 25, 587, 993, 995)

### 9.3 데이터베이스 운영
- PostgreSQL 정기 백업 수행
- 메일 데이터 백업 (Dovecot maildir)
- 인덱스 최적화
- 로그 테이블 정리 정책
- 성능 모니터링 및 튜닝

### 9.4 메일 서버 운영
- Postfix/Dovecot 서비스 모니터링
- 메일 큐 정리 및 최적화
- 스팸 필터 업데이트
- DNS 레코드 관리
- 인증서 갱신 자동화

### 9.5 백업 및 복구
- 데이터베이스 일일 백업
- 메일 데이터 실시간 백업
- 설정 파일 백업
- 재해 복구 계획 수립
- 백업 데이터 암호화

---

## 📚 문서화 규칙

### 10.1 API 문서화
- FastAPI 자동 생성 문서 활용 (Swagger UI)
- 모든 엔드포인트에 상세 설명 작성
- 요청/응답 예시 제공
- 에러 코드 및 메시지 문서화
- 메일 API 사용 가이드 제공

### 10.2 코드 문서화
- 모든 함수와 클래스에 docstring 작성
- 복잡한 로직에는 인라인 주석 추가
- README.md 파일로 프로젝트 개요 제공
- 설치 및 실행 가이드 작성
- 메일 서버 설정 가이드 제공

### 10.3 데이터베이스 문서화
- 테이블 스키마 다이어그램
- 컬럼별 상세 설명
- 관계 정의 및 제약 조건
- 마이그레이션 히스토리
- Postfix/Dovecot 연동 테이블 설명

### 10.4 운영 문서화
- 서버 설정 가이드
- 트러블슈팅 가이드
- 백업/복구 절차
- 모니터링 대시보드 사용법
- 보안 정책 문서

---

## ⚡ 성능 및 최적화 규칙

### 11.1 응답 시간 최적화
- 메일 발송 응답 시간 모니터링
- 데이터베이스 쿼리 최적화
- 적절한 인덱스 설정
- Redis 캐싱 전략 적용
- CDN 활용 (정적 파일)

### 11.2 리소스 관리
- 메일 첨부파일 크기 제한
- 메모리 사용량 모니터링
- 동시 메일 발송 제한
- 타임아웃 설정
- 디스크 용량 관리

### 11.3 확장성 고려
- 마이크로서비스 아키텍처 고려
- 로드 밸런싱 준비
- 데이터베이스 샤딩 계획
- 메일 서버 클러스터링
- 자동 스케일링 설정

### 11.4 메일 서버 최적화
- Postfix 큐 관리 최적화
- Dovecot 인덱스 최적화
- 메일 압축 및 아카이빙
- 스팸 필터 성능 튜닝
- 네트워크 대역폭 최적화

---

## 📝 추가 고려사항

### 규칙 준수 체크리스트
- [ ] 환경 변수 설정 확인
- [ ] 데이터베이스 마이그레이션 실행
- [ ] 메일 서버 설정 검증
- [ ] API 문서 업데이트
- [ ] 테스트 코드 작성
- [ ] 로깅 설정 확인
- [ ] 보안 검토 완료
- [ ] 성능 테스트 수행
- [ ] 백업 설정 확인
- [ ] SSL/TLS 인증서 검증
- [ ] DNS 레코드 설정
- [ ] 문서화 완료

### 규칙 위반 시 대응
1. 코드 리뷰를 통한 사전 방지
2. 자동화된 테스트로 품질 보장
3. 지속적인 모니터링 및 개선
4. 팀 내 규칙 공유 및 교육
5. 메일 서버 보안 정책 준수

### 긴급 상황 대응
- 메일 서버 장애 시 복구 절차
- 보안 침해 시 대응 방안
- 데이터 손실 시 복구 계획
- 스팸 공격 시 차단 방법
- 서비스 중단 시 커뮤니케이션 계획

---

**마지막 업데이트**: 2024년 12월  
**작성자**: SkyBoot Mail 개발팀  
**버전**: 2.0