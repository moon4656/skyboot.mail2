# SkyBoot Mail 📧

**SkyBoot Mail**은 FastAPI와 Vue.js를 기반으로 한 현대적인 메일 발송 시스템입니다. Postfix를 통한 안정적인 메일 발송과 직관적인 웹 인터페이스를 제공합니다.

## ✨ 주요 기능

- 🔐 **JWT 기반 인증 시스템** - 안전한 사용자 인증 및 권한 관리
- 📨 **Postfix 연동 메일 발송** - 안정적이고 확장 가능한 메일 발송
- 📊 **메일 발송 이력 관리** - 발송 상태 추적 및 로그 관리
- 🎨 **Vuestic UI 기반 프론트엔드** - 현대적이고 반응형 사용자 인터페이스
- 🐳 **Docker 컨테이너화** - 쉬운 배포 및 확장
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

- Docker & Docker Compose
- Git
- Node.js 18+ (개발 환경)
- Python 3.11+ (개발 환경)

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

### 3. Docker Compose로 실행

#### 프로덕션 환경
```bash
docker-compose up -d
```

#### 개발 환경
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 4. 접속

- **웹 인터페이스**: http://localhost
- **API 문서**: http://localhost:8000/docs
- **MailHog (개발용)**: http://localhost:8025

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
│   ├── Dockerfile          # Docker 이미지 빌드
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
│   ├── Dockerfile         # Docker 이미지 빌드
│   └── nginx.conf         # Nginx 설정
├── docker-compose.yml      # 프로덕션 Docker Compose
├── docker-compose.dev.yml  # 개발 Docker Compose
└── README.md              # 프로젝트 문서
```

## 🔧 개발 환경 설정

### 백엔드 개발

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## 📊 API 엔드포인트

### 인증
- `POST /api/auth/register` - 사용자 등록
- `POST /api/auth/login` - 로그인
- `POST /api/auth/refresh` - 토큰 갱신
- `POST /api/auth/logout` - 로그아웃

### 메일
- `POST /api/mail/send` - 메일 발송
- `GET /api/mail/logs` - 메일 발송 이력 조회

### 시스템
- `GET /health` - 헬스체크
- `GET /` - API 정보

## 🔐 보안 고려사항

- JWT 토큰 기반 인증
- 비밀번호 해싱 (bcrypt)
- CORS 설정
- SQL 인젝션 방지 (SQLAlchemy ORM)
- 환경 변수를 통한 민감한 정보 관리

## 🐳 Docker 설정

### 서비스 구성

- **frontend**: Nginx + Vue.js 빌드 결과물
- **backend**: FastAPI + Uvicorn
- **postgres**: PostgreSQL 15
- **postfix**: 메일 서버
- **redis**: 세션 관리 (선택사항)
- **mailhog**: 개발용 메일 테스트 도구

### 포트 매핑

- `80`: 프론트엔드 (Nginx)
- `8000`: 백엔드 API
- `5432`: PostgreSQL
- `25`: Postfix SMTP
- `6379`: Redis
- `8025`: MailHog 웹 UI (개발용)

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
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postfix
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

**SkyBoot Mail** - 현대적이고 안정적인 메일 발송 솔루션 🚀