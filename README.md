# SkyBoot Mail 📧

**SkyBoot Mail**은 FastAPI와 Vue.js를 기반으로 한 현대적인 메일 발송 시스템입니다. Postfix를 통한 안정적인 메일 발송과 직관적인 웹 인터페이스를 제공합니다.

## ✨ 주요 기능

- 🔐 **JWT 기반 인증 시스템** - 안전한 사용자 인증 및 권한 관리
- 📨 **Postfix 연동 메일 발송** - 안정적이고 확장 가능한 메일 발송
- 📊 **메일 발송 이력 관리** - 발송 상태 추적 및 로그 관리
- 🎨 **Vuestic UI 기반 프론트엔드** - 현대적이고 반응형 사용자 인터페이스
- 🗄️ **PostgreSQL 데이터베이스** - 안정적인 데이터 저장

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 80      │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Mail Server   │
                       │   (Postfix)     │
                       │   Port: 25      │
                       └─────────────────┘
```

## 🚀 빠른 시작

### 사전 요구사항

- Git
- Node.js 18+ (개발 환경)
- Python 3.11+ (개발 환경)
- PostgreSQL 15+
- Postfix (메일 서버)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd skyboot.mail2
```

### 2. 환경 설정

```bash
# 백엔드 환경 설정
cp backend/.env.example backend/.env
# 필요에 따라 .env 파일 수정
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
createdb skyboot_mail

# 데이터베이스 초기화
psql -d skyboot_mail -f backend/init.sql
```

### 4. 백엔드 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
# Windows:
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 프론트엔드 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 6. 접속

- **웹 인터페이스**: http://localhost:5173
- **API 문서**: http://localhost:8000/docs

## 📁 프로젝트 구조

```
skyboot.mail2/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── routers/        # API 라우터
│   │   ├── models.py       # 데이터베이스 모델
│   │   ├── schemas.py      # Pydantic 스키마
│   │   ├── auth.py         # 인증 로직
│   │   ├── config.py       # 설정 관리
│   │   └── database.py     # 데이터베이스 연결
│   ├── main.py             # FastAPI 앱 진입점
│   ├── requirements.txt    # Python 의존성
│   ├── init.sql           # 데이터베이스 초기화
│   └── test_mail.py       # 메일 발송 테스트
├── frontend/               # Vue.js 프론트엔드
│   ├── src/
│   │   ├── components/     # Vue 컴포넌트
│   │   ├── views/         # 페이지 컴포넌트
│   │   ├── router/        # Vue Router 설정
│   │   ├── stores/        # Pinia 상태 관리
│   │   └── services/      # API 서비스
│   ├── package.json       # Node.js 의존성
│   ├── vite.config.ts     # Vite 설정
│   └── nginx.conf         # Nginx 설정
└── README.md              # 프로젝트 문서
```

## 🔧 개발 환경 설정

### 백엔드 개발

```bash
```bash
cd backend

# 가상환경 생성 및 활성화
# Linux/Mac:
python -m venv venv
source venv/bin/activate  

# Windows PowerShell:
# Python이 제대로 작동하지 않는 경우 python3.11.exe 사용
python3.11.exe -m venv venv
venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

```

# 의존성 설치
pip install -r requirements.txt

# pip 업그레이드
python.exe -m pip install --upgrade pip

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
# Redis 실행
.\Redis\redis-server.exe .\Redis\redis.windows.conf

### 프론트엔드 개발

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 🧪 테스트

### 메일 발송 테스트

```bash
cd backend
python test_mail.py
```

### API 테스트

FastAPI 자동 생성 문서를 통해 API를 테스트할 수 있습니다:

#### 통합 API 문서
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

#### 도메인별 API 문서
- http://localhost:8000/docs - 통합 API 문서
- http://localhost:8000/docs/admin - 관리자 도메인 API 문서
- http://localhost:8000/docs/user - 사용자 도메인 API 문서
- http://localhost:8000/docs/mail - 메일 도메인 API 문서
- http://localhost:8000/docs/business - 비즈니스 도메인 API 문서
- http://localhost:8000/docs/system - 시스템 도메인 API 문서

## 📊 API 엔드포인트

### 🏗️ 도메인별 엔드포인트 구조

SkyBoot Mail은 비즈니스 도메인별로 체계적으로 분류된 API 엔드포인트를 제공합니다:

- 🏢 **Business Domain** (`/api/v1/business/`): 비즈니스 로직 관련 엔드포인트
- 👑 **Admin Domain** (`/api/v1/admin/`): 관리자 기능 관련 엔드포인트  
- ⚙️ **System Domain** (`/api/v1/system/`): 시스템 관리 관련 엔드포인트
- 👤 **User Domain** (`/api/v1/user/`): 사용자 기능 관련 엔드포인트

### 인증
- `POST /api/auth/register` - 사용자 등록
- `POST /api/auth/login` - 로그인
- `POST /api/auth/refresh` - 토큰 갱신
- `POST /api/auth/logout` - 로그아웃

### 메일
- `POST /api/v1/mail/send` - 메일 발송 (multipart/form-data)
- `POST /api/v1/mail/send-json` - 메일 발송 (JSON)
- `GET /api/v1/mail/inbox` - 받은 메일함 조회
- `GET /api/v1/mail/sent` - 보낸 메일함 조회
- `GET /api/v1/mail/search` - 메일 검색
- `GET /api/v1/mail/stats` - 메일 통계
- `GET /api/v1/mail/{mail_id}` - 메일 상세 조회
- `DELETE /api/v1/mail/{mail_id}` - 메일 삭제
- `GET /api/v1/mail/attachment/{attachment_id}/download` - 첨부파일 다운로드

### 조직 관리
- `POST /api/v1/organizations` - 조직 생성 (관리자 전용)
- `GET /api/v1/organizations` - 조직 목록 조회 (관리자 전용)
- `GET /api/v1/organizations/{org_id}` - 조직 정보 조회
- `GET /api/v1/organizations/{org_id}/stats` - 조직 통계 조회
- `GET /api/v1/organizations/current/settings` - 현재 조직 설정 조회
- `GET /api/v1/organizations/{org_id}/settings` - 특정 조직 설정 조회
- `PUT /api/v1/organizations/{org_id}/settings` - 조직 설정 수정

### 사용자 관리
- `GET /api/v1/users/profile` - 사용자 프로필 조회
- `PUT /api/v1/users/profile` - 사용자 프로필 수정
- `POST /api/v1/users/change-password` - 비밀번호 변경

### 시스템
- `GET /health` - 헬스체크
- `GET /` - API 정보

## 📋 조직 설정 옵션

조직별로 다음과 같은 설정을 관리할 수 있습니다:

### 메일 크기 제한
- `max_mail_size_mb`: 최대 메일 크기 (기본값: 25MB)
- `max_attachment_size_mb`: 최대 첨부파일 크기 (기본값: 25MB)

### 발송 제한
- `daily_email_limit`: 일일 메일 발송 제한 (기본값: 1000)
- `hourly_email_limit`: 시간당 메일 발송 제한 (기본값: 100)

### 저장 용량
- `storage_quota_gb`: 조직 저장 용량 할당량 (기본값: 10GB)

### 기능 활성화
- `enable_auto_reply`: 자동 응답 기능 활성화 (기본값: true)
- `enable_forwarding`: 메일 전달 기능 활성화 (기본값: true)
- `enable_spam_filter`: 스팸 필터 활성화 (기본값: true)

### 조직 설정 API 사용 예시

```bash
# 현재 조직 설정 조회
curl -X GET "http://localhost:8000/api/v1/organizations/current/settings" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 조직 설정 수정 (메일 크기 제한 변경)
curl -X PUT "http://localhost:8000/api/v1/organizations/{org_id}/settings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_mail_size_mb": 50,
    "max_attachment_size_mb": 30,
    "daily_email_limit": 2000
  }'
```

### 메일 크기 제한 검증

메일 발송 시 다음과 같은 크기 제한이 적용됩니다:

1. **개별 첨부파일 크기**: `max_attachment_size_mb` 설정값 초과 시 413 에러
2. **전체 메일 크기**: 본문 + 모든 첨부파일 크기가 `max_mail_size_mb` 초과 시 413 에러
3. **일일 발송 제한**: `daily_email_limit` 초과 시 429 에러

```json
// 413 에러 응답 예시 (크기 초과)
{
  "detail": "메일 크기가 조직 제한(25MB)을 초과했습니다."
}

// 429 에러 응답 예시 (발송 제한 초과)
{
  "detail": "일일 메일 발송 제한(1000)에 도달했습니다."
}
```

## 🔐 보안 고려사항

- JWT 토큰 기반 인증
- 비밀번호 해싱 (bcrypt)
- CORS 설정
- SQL 인젝션 방지 (SQLAlchemy ORM)
- 환경 변수를 통한 민감한 정보 관리

# postfix restart
sudo systemctl restart postfix

# postfix status
sudo systemctl status postfix

# wsl 에서 postfix 테스트
echo "Test mail from Postfix on WSL" | mail -s "Test" moon4656@hibiznet.com

## 🔧 포트 설정
### 기본 포트

- `5173`: 프론트엔드 (Vite 개발 서버)
- `8000`: 백엔드 API
- `5432`: PostgreSQL
- `25`: Postfix SMTP

## 🔧 설정 옵션

### 환경 변수 (.env)

```env
# 데이터베이스
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/skyboot_mail

# JWT 설정
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP 설정
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_USERNAME=admin
SMTP_PASSWORD=admin123
SMTP_FROM_EMAIL=noreply@localhost
SMTP_FROM_NAME=SkyBoot Mail

# 애플리케이션 설정
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## 📝 사용법

### 1. 사용자 등록 및 로그인
1. 웹 인터페이스에 접속
2. "회원가입" 버튼 클릭
3. 사용자 정보 입력 후 계정 생성
4. 로그인하여 메일 발송 페이지 접근

### 2. 메일 발송
1. 로그인 후 "메일 발송" 페이지 이동
2. 수신자 이메일, 제목, 본문 입력
3. "메일 발송" 버튼 클릭
4. 발송 결과 확인

### 3. 발송 이력 확인
- 메일 발송 페이지 우측에서 최근 발송 이력 확인
- 발송 상태 (성공/실패) 및 시간 정보 제공

## 🚨 문제 해결

### 일반적인 문제

1. **메일 발송 실패**
   - Postfix 서비스 상태 확인
   - SMTP 설정 검증
   - 네트워크 연결 확인

2. **데이터베이스 연결 오류**
   - PostgreSQL 서비스 상태 확인
   - 데이터베이스 URL 설정 확인

3. **프론트엔드 빌드 오류**
   - Node.js 버전 확인 (18+)
   - 의존성 재설치: `npm ci`

### 로그 확인

```bash
# 백엔드 로그 (개발 서버 실행 시 콘솔에서 확인)
# 프론트엔드 로그 (브라우저 개발자 도구에서 확인)
# Postfix 로그
sudo tail -f /var/log/mail.log
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

# 1. 로그인하여 토큰 받기
- $loginResponse = Invoke-RestMethod -Uri "http://localhost:9000/auth/login" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"email":"demo@skyboot.co.kr","password":"demo123"}'

# 2. 토큰을 사용하여 메일 발송
- $token = $loginResponse.access_token
- $mailResponse = Invoke-RestMethod -Uri "http://localhost:9000/mail/send" `
    -Method POST `
    -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
    -Body '{"to_email":"moon4656@gmail.com","subject":"테스트 메일","body":"안녕하세요, 테스트 메일입니다."}'


## 📋 기능 고도화 4단계
# Phase 1: 핵심 기능 + 제한 강제
1. 메일 핵심 기능 완성(폴더/읽음/중요/이동/삭제) v
2. 일일 메일 발송 제한 검증 v
   - `/mail/send` 및 `/mail/send-json` 엔드포인트는 SMTP 발송 전에 조직의 `max_emails_per_day` 제한을 확인합니다.
   - 제한값이 0이면 무제한 발송으로 처리합니다.
   - 오늘 발송된 누적 수(`OrganizationUsage`)와 이번 발송 대상 수를 합산하여 제한을 초과하면 `429 Too Many Requests` 에러를 반환합니다.
   - 성공적으로 발송되면 수신자 수만큼 `OrganizationUsage`가 업데이트됩니다.
3. 저장 용량 및 첨부파일 크기 제한 강제 v
   - `/mail/send` 및 `/mail/send-json` 엔드포인트는 각 메일의 본문/제목 크기와 첨부파일 크기를 확인합니다.
   - 제한값을 초과하면 `413 Payload Too Large` 에러를 반환합니다.
   - 기본 제한: 25MB 메일 크기, 25MB 첨부파일 크기 (조직 설정 기본값)
   - 조직별로 사용자 정의 가능: `OrganizationSettings`의 `max_mail_size_mb`, `max_attachment_size_mb`로 변경

# Phase 2: 실시간 모니터링 및 통계
1. 사용량 자동 업데이트 로직 v
   - `/mail/send` 및 `/mail/send-json` 엔드포인트는 성공적으로 발송된 경우에만 `OrganizationUsage`를 업데이트합니다.
   - 매일 자정에 누적 발송 수를 0으로 리셋합니다.
   - 구현 상세:
     - 성공 시 업데이트: `backend/app/service/mail_service.py`의 `send_email_smtp` 내부에서 SMTP 발송 결과가 성공(`result.get('success', False)`)인 경우에만 `_update_organization_usage(org_id, recipients_count)`를 호출합니다.
     - 자정 리셋: `backend/app/tasks/usage_reset.py`의 `reset_daily_email_usage` 함수를 `backend/main.py` 생명주기에서 APScheduler(`AsyncIOScheduler`, `CronTrigger(hour=0, minute=0, timezone="Asia/Seoul")`)로 매일 00:00(Asia/Seoul)에 실행합니다.
     - 동시성 안전: 사용량 업데이트는 PostgreSQL `UPSERT`로 원자적으로 처리하며, 고동시성 환경에서는 Redis 락(`OrganizationUsageLock`) 사용으로 보호하고 실패 시 UPSERT로 폴백합니다.
2. 실시간 통계 계산 및 사용량 추적 개선 v
   - `/mail/usage` 엔드포인트는 조직별로 오늘까지의 발송 통계를 제공합니다.
   - `/mail/usage/history` 엔드포인트는 조직별로 발송 이력 통계를 제공합니다.
3. 임계값 알림(80%/90%/100%) 구성 v
   - `/mail/usage` 엔드포인트는 조직별로 오늘까지의 발송 통계를 제공합니다.
   - `/mail/usage/history` 엔드포인트는 조직별로 발송 이력 통계를 제공합니다.
   - 임계값을 초과하면 조직 관리자에게 알림을 보냅니다.
   - 구현 상세:
     - 임계값 판정 시점: 실제 메일 발송이 성공하여 사용량이 증가한 직후(`send_mail`, `send_email_smtp`)에 판정합니다.
     - 판정 로직: 업데이트된 `emails_sent_today`와 직전 값(`emails_sent_today - 증가량`)을 비교하여 80%/90%/100% 경계값을 "아래→위"로 최초로 넘는 경우에만 알림을 보냅니다.
     - 메일 전송: 조직 관리자 이메일(`organizations.admin_email`)로 알림 메일을 발송합니다. 발신자는 `no-reply@{organization.domain}` → SMTP 사용자명 → `no-reply@localhost` 순으로 폴백합니다.
     - 안전장치: `max_emails_per_day`가 비어있거나 0 이하인 경우 임계값 알림을 건너뜁니다.
     - 코드 위치: `backend/app/service/mail_service.py`의 `_update_organization_usage`가 업데이트 후 오늘/총 발송 값을 반환하고, `_notify_usage_thresholds`가 임계값 판정 및 알림 발송을 수행합니다.

# Phase 3: 편의 기능과 생산성 향상
1. 템플릿·서명·예약발송·스누즈·규칙/라벨 v
   - `/mail/templates` 엔드포인트는 조직별로 템플릿을 제공합니다.
   - `/mail/signatures` 엔드포인트는 조직별로 서명을 제공합니다.
   - `/mail/reschedule` 엔드포인트는 예약된 메일을 수정합니다.
   - `/mail/schedule` 엔드포인트는 예약된 메일을 발송합니다.
   - `/mail/rules` 엔드포인트는 조직별로 규칙을 제공합니다.
   - `/mail/labels` 엔드포인트는 조직별로 라벨을 제공합니다.
2. 검색·필터·저장된 검색(FTS 기반) v
   - `/mail/search` 엔드포인트는 조직별로 메일을 검색합니다.
   - `/mail/filters` 엔드포인트는 조직별로 필터를 제공합니다.
   - `/mail/saved-searches` 엔드포인트는 조직별로 저장된 검색을 제공합니다.
3. 첨부파일 관리(클라우드 저장·바이러스 검사·미리보기) v
   - `/mail/attachments` 엔드포인트는 조직별로 첨부파일을 제공합니다.
   - `/mail/attachments/virus-scan` 엔드포인트는 첨부파일을 바이러스 검사합니다.
   - `/mail/attachments/preview` 엔드포인트는 첨부파일 미리보기를 제공합니다.

# Phase 4: 보안·관리·운영 고도화
1. 보안·인증(2FA·SSO·RBAC·속도 제한) v
   - `/auth/login` 엔드포인트는 2FA 인증을 요구합니다.
   - `/auth/sso` 엔드포인트는 SSO 인증을 제공합니다.
   - `/auth/roles` 엔드포인트는 조직별로 역할을 제공합니다.
   - `/auth/rate-limit` 엔드포인트는 API 호출 속도를 제한합니다.
2. 모니터링·감사·관리 대시보드 v
   - `/monitoring/usage` 엔드포인트는 조직별로 사용량 통계를 제공합니다.
   - `/monitoring/audit` 엔드포인트는 조직별로 감사 로그를 제공합니다.
   - `/monitoring/dashboard` 엔드포인트는 조직별로 대시보드를 제공합니다.
3. 국제화·브랜딩(i18n·조직별 테마) 및 PWA·오프라인·푸시 알림 v
   - `/i18n` 엔드포인트는 조직별로 다국어 지원을 제공합니다.
   - `/themes` 엔드포인트는 조직별로 테마를 제공합니다.
   - `/pwa` 엔드포인트는 PWA 기능을 제공합니다.
   - `/offline` 엔드포인트는 오프라인 기능을 제공합니다.
   - `/push-notifications` 엔드포인트는 푸시 알림을 제공합니다.
4. DevOps·테스트·백업/복구 체계 정비 v
   - `/devops/backup` 엔드포인트는 백업을 수행합니다.
   - `/devops/restore` 엔드포인트는 복구를 수행합니다.
   - `/devops/test` 엔드포인트는 테스트를 수행합니다.
5. 모니터링·감사·관리 대시보드 개선 
   - 프론트엔드 대시보드 구현 - Vue.js로 모니터링 UI 개발 (보류)
   - 알림 시스템 구현 - 임계값 초과 시 자동 알림
   - 메트릭 수집 자동화 - 백그라운드 작업으로 정기적 데이터 수집
   - 성능 최적화 - 대용량 데이터 처리를 위한 최적화

**SkyBoot Mail** - 현대적이고 안정적인 메일 발송 솔루션 🚀
