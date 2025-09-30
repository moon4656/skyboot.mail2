# SkyBoot Mail SaaS 프로젝트 규칙 (Project Rules)

## 🎯 프로젝트 개요
이 문서는 SkyBoot Mail SaaS 기반 다중 조직 지원 메일서버 프로젝트의 개발 규칙과 가이드라인을 정의합니다. 모든 개발자는 이 규칙을 준수하여 일관성 있고 고품질의 코드를 작성해야 합니다.

**프로젝트 특징:**
- SaaS 기반 다중 조직(Multi-tenant) 지원
- 기업용 메일 서버 시스템
- 확장 가능한 마이크로서비스 아키텍처
- 실시간 모니터링 및 로깅

---

## 🏗️ 프로젝트 아키텍처

### 기술 스택
- **백엔드**: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **프론트엔드**: Vue.js 3, TypeScript, Vite, Pinia, Vuestic UI
- **메일 서버**: Postfix (SMTP), Dovecot (IMAP/POP3)
- **캐시/세션**: Redis
- **백그라운드 작업**: Celery, APScheduler, RQ
- **인증**: JWT 토큰 (python-jose), bcrypt 패스워드 해싱
- **데이터베이스**: PostgreSQL 15+ with Alembic 마이그레이션
- **웹서버**: Nginx (프록시 및 정적 파일 서빙)
- **로깅**: Python logging, structlog
- **모니터링**: Prometheus
- **파일 저장**: boto3 (AWS S3 호환)
- **테스트**: pytest 프레임워크
- **속도 제한**: slowapi, python-limits

### 프로젝트 구조
```
skyboot.mail2/
├── backend/                    # FastAPI 백엔드 서버
│   ├── app/
│   │   ├── router/            # API 라우터 (실제 구조)
│   │   │   ├── auth_router.py          # 인증 관련 API
│   │   │   ├── organization_router.py  # 조직 관리 API
│   │   │   ├── user_router.py          # 사용자 관리 API
│   │   │   ├── mail_core_router.py     # 메일 핵심 기능 API
│   │   │   ├── mail_convenience_router.py # 메일 편의 기능 API
│   │   │   ├── mail_advanced_router.py # 메일 고급 기능 API
│   │   │   ├── mail_setup_router.py    # 메일 설정 API
│   │   │   └── debug_router.py         # 디버그 API (개발용)
│   │   ├── model/             # 데이터베이스 모델
│   │   │   ├── user_model.py           # 사용자 모델
│   │   │   ├── organization_model.py   # 조직 모델
│   │   │   └── mail_model.py           # 메일 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   │   ├── user_schema.py          # 사용자 스키마
│   │   │   ├── organization_schema.py  # 조직 스키마
│   │   │   └── mail_schema.py          # 메일 스키마
│   │   ├── service/           # 비즈니스 로직 서비스
│   │   │   ├── auth_service.py         # 인증 서비스
│   │   │   ├── user_service.py         # 사용자 서비스
│   │   │   ├── organization_service.py # 조직 서비스
│   │   │   └── mail_service.py         # 메일 서비스
│   │   ├── database/          # 데이터베이스 연결
│   │   │   ├── user.py                 # 사용자 DB 연결
│   │   │   └── mail.py                 # 메일 DB 연결
│   │   ├── middleware/        # 미들웨어
│   │   │   ├── tenant_middleware.py    # 다중 조직 미들웨어
│   │   │   └── rate_limit_middleware.py # 속도 제한 미들웨어
│   │   ├── utils/             # 유틸리티 함수
│   │   ├── config.py          # 설정 관리
│   │   └── logging_config.py  # 로깅 설정
│   ├── main.py                # FastAPI 앱 진입점
│   ├── requirements.txt       # Python 의존성
│   ├── init.sql              # 데이터베이스 초기화
│   ├── alembic/              # 데이터베이스 마이그레이션
│   ├── migration/            # 커스텀 마이그레이션 스크립트
│   ├── test/                 # 테스트 코드
│   └── backups/              # 백업 파일
├── frontend/                  # Vue.js 프론트엔드
│   ├── src/
│   │   ├── views/            # 페이지 컴포넌트
│   │   │   ├── Home.vue      # 홈 페이지
│   │   │   ├── Login.vue     # 로그인 페이지
│   │   │   ├── Register.vue  # 회원가입 페이지
│   │   │   └── SendMail.vue  # 메일 발송 페이지
│   │   ├── router/           # Vue Router 설정
│   │   ├── stores/           # Pinia 상태 관리
│   │   ├── services/         # API 서비스
│   │   ├── App.vue           # 메인 앱 컴포넌트
│   │   └── main.ts           # 앱 진입점
│   ├── package.json          # Node.js 의존성
│   ├── vite.config.ts        # Vite 설정
│   └── nginx.conf            # Nginx 설정
├── docs/                     # 프로젝트 문서
├── attachments/              # 첨부파일 저장소
├── backups/                  # 시스템 백업
├── postfix_main.cf          # Postfix 메인 설정
├── postfix_master.cf        # Postfix 마스터 설정
├── dovecot.conf             # Dovecot 설정
└── .trae/rules/             # Trae AI IDE 프로젝트 규칙
```

---

## 📝 코딩 규칙

### Python 코딩 스타일
- **PEP 8** 스타일 가이드 엄격히 준수
- **타입 힌트** 모든 함수와 메서드에 필수 적용
- **한국어 docstring** 모든 클래스와 함수에 작성
- **영어 변수명** 의미가 명확한 영어로 작성
- **상수 사용** 매직 넘버 대신 명명된 상수 사용

### 함수 및 클래스 설계
```python
# 올바른 예시
def send_email(recipient: str, subject: str, content: str, sender: str = None) -> Dict[str, Any]:
    """
    이메일을 발송합니다.
    
    Args:
        recipient: 수신자 이메일 주소
        subject: 메일 제목
        content: 메일 본문 내용
        sender: 발송자 이메일 주소 (기본값: 시스템 기본 발송자)
    
    Returns:
        발송 결과를 포함한 딕셔너리
    
    Raises:
        SMTPException: SMTP 서버 연결 오류 발생 시
        ValidationError: 이메일 주소 형식이 잘못된 경우
    """
    pass
```

### FastAPI 개발 규칙
- 모든 엔드포인트에 `summary`와 상세 설명 추가
- Pydantic 모델로 요청/응답 검증
- 적절한 HTTP 상태 코드 사용
- 의존성 주입 패턴 활용
- 비동기 처리 시 `async/await` 사용

### Vue.js 개발 규칙
- **Composition API** 사용 권장
- **TypeScript** 적극 활용
- **Pinia** 를 통한 상태 관리
- 컴포넌트 단위 테스트 작성
- **ESLint** 및 **Prettier** 설정 준수

---

## 🗄️ 데이터베이스 규칙

### 스키마 설계 원칙
- 모든 테이블과 컬럼에 **한국어 주석** 필수
- 적절한 데이터 타입 선택 (UUID, TIMESTAMP WITH TIME ZONE 등)
- 외래 키 관계 명확히 정의
- 성능을 위한 인덱스 설정
- 필수 필드는 `nullable=False` 설정

### 주요 테이블 구조
현재 프로젝트는 다중 조직 지원을 위한 SaaS 구조로 설계되어 있습니다:

```python
# 조직 모델 (organization_model.py)
class Organization(Base):
    """조직 정보를 저장하는 테이블 - SaaS 다중 테넌트 지원"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, comment="조직 고유 ID")
    org_uuid = Column(String, unique=True, comment="조직 UUID")
    name = Column(String, nullable=False, comment="조직명")
    domain = Column(String, unique=True, comment="조직 도메인")
    max_users = Column(Integer, default=100, comment="최대 사용자 수")
    is_active = Column(Boolean, default=True, comment="활성화 상태")
    created_at = Column(DateTime, comment="생성 시간")
    # ... 기타 필드

# 사용자 모델 (user_model.py)
class User(Base):
    """사용자 정보를 저장하는 테이블 - 조직별 분리"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, comment="사용자 고유 ID")
    user_uuid = Column(String, unique=True, comment="사용자 UUID")
    email = Column(String, unique=True, comment="이메일 주소")
    password_hash = Column(String, comment="해시된 비밀번호")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="소속 조직 ID")
    role = Column(Enum(UserRole), comment="사용자 역할")
    is_active = Column(Boolean, default=True, comment="활성화 상태")
    created_at = Column(DateTime, comment="생성 시간")
    # ... 기타 필드

# 메일 모델 (mail_model.py)
class Mail(Base):
    """메일 정보를 저장하는 테이블 - 조직별 분리"""
    __tablename__ = "mails"
    
    mail_id = Column(String, primary_key=True, comment="메일 고유 ID")
    sender_id = Column(Integer, ForeignKey("users.id"), comment="발송자 ID")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="조직 ID")
    subject = Column(String, comment="메일 제목")
    content = Column(Text, comment="메일 본문")
    sent_at = Column(DateTime, comment="발송 시간")
    status = Column(Enum(MailStatus), comment="메일 상태")
    # ... 기타 필드

# 메일 수신자 테이블
class MailRecipient(Base):
    """메일 수신자 정보를 저장하는 테이블"""
    __tablename__ = "mail_recipients"
    
    id = Column(Integer, primary_key=True, comment="수신자 고유 ID")
    mail_id = Column(String, ForeignKey("mails.mail_id"), comment="메일 ID")
    recipient_email = Column(String, comment="수신자 이메일")
    recipient_type = Column(Enum(RecipientType), comment="수신자 타입 (TO, CC, BCC)")
    # ... 기타 필드

# 가상 도메인 테이블 (Postfix 연동)
class VirtualDomain(Base):
    """Postfix 가상 도메인 정보를 저장하는 테이블"""
    __tablename__ = "virtual_domains"
    
    id = Column(Integer, primary_key=True, comment="도메인 ID")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="조직 ID")
    name = Column(String, unique=True, comment="도메인명")
    is_active = Column(Boolean, default=True, comment="활성화 상태")
    # ... 기타 필드
```

### 마이그레이션 규칙
- 모든 스키마 변경은 Alembic 마이그레이션으로 관리
- 롤백 가능한 마이그레이션 작성
- 프로덕션 적용 전 충분한 테스트
- 마이그레이션 스크립트에 상세한 주석 추가

---

## 🔌 API 설계 규칙

### RESTful API 원칙
- HTTP 메서드 적절히 활용 (GET, POST, PUT, DELETE)
- 리소스 중심의 URL 설계
- 일관된 응답 형식 유지
- 에러 응답에 상세한 한국어 메시지 포함

### API 라우터 구조
현재 프로젝트는 기능별로 분리된 라우터 구조를 사용합니다:

- **인증 라우터** (`auth_router.py`): 로그인, 회원가입, 토큰 관리
- **조직 라우터** (`organization_router.py`): 다중 조직 관리, 조직 설정
- **사용자 라우터** (`user_router.py`): 사용자 관리, 프로필 설정
- **메일 핵심 라우터** (`mail_core_router.py`): 메일 발송, 수신, 기본 기능
- **메일 편의 라우터** (`mail_convenience_router.py`): 메일함 관리, 검색
- **메일 고급 라우터** (`mail_advanced_router.py`): 필터링, 자동화 규칙
- **메일 설정 라우터** (`mail_setup_router.py`): 메일 서버 설정, 도메인 관리
- **디버그 라우터** (`debug_router.py`): 개발 환경 전용 디버깅 API

### 엔드포인트 예시
```python
# 메일 핵심 기능 (mail_core_router.py)
@router.post("/send", summary="메일 발송")
async def send_mail(
    mail_data: MailSendRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
):
    """
    메일을 발송합니다. (다중 조직 지원)
    
    - **recipient**: 수신자 이메일 주소
    - **subject**: 메일 제목
    - **content**: 메일 본문
    - **attachments**: 첨부파일 (선택사항)
    - **organization_id**: 조직 ID (자동 설정)
    """
    pass

@router.get("/inbox", summary="받은 메일함 조회")
async def get_inbox(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
):
    """
    사용자의 받은 메일함을 조회합니다. (조직별 분리)
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 메일 수 (기본값: 20, 최대: 100)
    - **organization_id**: 조직 ID (자동 필터링)
    """
    pass

# 조직 관리 (organization_router.py)
@router.post("/", summary="조직 생성")
async def create_organization(
    org_data: OrganizationCreateRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """
    새로운 조직을 생성합니다.
    
    - **name**: 조직명
    - **domain**: 조직 도메인
    - **max_users**: 최대 사용자 수
    - **features**: 사용 가능한 기능 목록
    """
    pass
```

### SaaS 메일 서비스 통합
- **다중 조직 지원**: 조직별 메일 도메인 및 사용자 분리
- **Postfix SMTP 서버 연동**: 조직별 가상 도메인 설정
- **Dovecot IMAP/POP3 서버 연동**: 조직별 메일박스 분리
- **백그라운드 작업 처리**: Celery, APScheduler, RQ를 통한 비동기 메일 처리
- **메일 큐 관리**: 조직별 우선순위 및 재시도 메커니즘
- **첨부파일 처리**: boto3를 통한 클라우드 저장소 연동
- **스팸 필터링**: 조직별 스팸 정책 설정
- **모니터링**: Prometheus를 통한 메일 서비스 메트릭 수집
- **속도 제한**: 조직별 메일 발송 제한 및 API 호출 제한

---

## 🔒 보안 규칙

### 인증 및 권한
- **JWT 토큰** 기반 사용자 인증
- **bcrypt** 를 통한 패스워드 해시화
- 토큰 만료 시간 적절히 설정 (액세스: 30분, 리프레시: 7일)
- 역할 기반 접근 제어 (RBAC)
- 이중 인증 (2FA) 지원

### 메일 보안
- **TLS/SSL** 암호화 통신 필수
- **SPF, DKIM, DMARC** 설정
- 스팸 및 피싱 메일 필터링
- 첨부파일 바이러스 검사
- 메일 내용 암호화 옵션

### 데이터 보호
- 민감한 정보는 환경 변수로 관리
- SQL 인젝션 방지 (ORM 사용)
- 입력 데이터 검증 및 sanitization
- HTTPS 사용 필수 (프로덕션)
- 개인정보 암호화 저장

### 접근 로깅 및 감사
```python
# 메일 접근 로그 테이블 (다중 조직 지원)
class MailAccessLog(Base):
    """메일 접근 로그를 기록하는 테이블 - 조직별 분리"""
    __tablename__ = "mail_access_logs"
    
    id = Column(Integer, primary_key=True, comment="로그 고유 ID")
    user_id = Column(Integer, ForeignKey("users.id"), comment="사용자 ID")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="조직 ID")
    action = Column(String, comment="수행된 작업 (send, read, delete, forward 등)")
    mail_id = Column(String, comment="대상 메일 ID")
    ip_address = Column(String, comment="클라이언트 IP 주소")
    user_agent = Column(String, comment="사용자 에이전트")
    request_id = Column(String, comment="요청 추적 ID")
    response_status = Column(Integer, comment="응답 상태 코드")
    processing_time = Column(Float, comment="처리 시간 (초)")
    created_at = Column(DateTime, comment="접근 시간")

# 조직 활동 로그 테이블
class OrganizationActivityLog(Base):
    """조직 활동 로그를 기록하는 테이블"""
    __tablename__ = "organization_activity_logs"
    
    id = Column(Integer, primary_key=True, comment="로그 고유 ID")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="조직 ID")
    admin_user_id = Column(Integer, ForeignKey("users.id"), comment="관리자 ID")
    action = Column(String, comment="수행된 작업")
    target_resource = Column(String, comment="대상 리소스")
    details = Column(JSON, comment="상세 정보")
    created_at = Column(DateTime, comment="수행 시간")

# 시스템 메트릭 로그 테이블
class SystemMetricsLog(Base):
    """시스템 성능 메트릭을 기록하는 테이블"""
    __tablename__ = "system_metrics_logs"
    
    id = Column(Integer, primary_key=True, comment="메트릭 ID")
    organization_id = Column(Integer, ForeignKey("organizations.id"), comment="조직 ID")
    metric_type = Column(String, comment="메트릭 타입 (mail_sent, mail_received, api_calls)")
    metric_value = Column(Float, comment="메트릭 값")
    timestamp = Column(DateTime, comment="측정 시간")
```

---

## 📊 로깅 및 모니터링

### 로깅 시스템
- Python `logging` 모듈 사용
- 구조화된 로그 메시지 작성
- 로그 레벨 적절히 활용 (DEBUG, INFO, WARNING, ERROR)
- 민감한 정보 로깅 금지

### 로깅 패턴 (SaaS 다중 조직 지원)
```python
# 함수 시작 시 (조직 정보 포함)
logger.info(f"📧 {function_name} 시작 - 조직: {org_id}, 사용자: {user_id}, 파라미터: {params}")

# 메일 발송 시작 (조직별 추적)
logger.info(f"📤 메일 발송 시작 - 조직: {org_id}, 발송자: {sender}, 수신자: {recipient}, 제목: {subject}")

# 백그라운드 작업 시작
logger.info(f"🔄 백그라운드 작업 시작 - 작업: {task_name}, 조직: {org_id}, 작업ID: {task_id}")

# 성공 완료 (성능 메트릭 포함)
logger.info(f"✅ {function_name} 완료 - 조직: {org_id}, 처리시간: {duration}ms, 결과: {result_summary}")

# 조직별 제한 도달
logger.warning(f"⚠️ 조직 제한 도달 - 조직: {org_id}, 제한타입: {limit_type}, 현재값: {current_value}")

# 에러 발생 (조직 정보 포함)
logger.error(f"❌ {error_message} - 조직: {org_id}, 사용자: {user_id}")
logger.error(f"Traceback: {traceback.format_exc()}")

# 보안 이벤트
logger.warning(f"🔒 보안 이벤트 - 조직: {org_id}, 이벤트: {security_event}, IP: {ip_address}")

# 성능 메트릭
logger.info(f"📊 성능 메트릭 - 조직: {org_id}, 메트릭: {metric_name}, 값: {metric_value}")
```

### 성능 모니터링 (Prometheus 기반)
- **조직별 API 메트릭**: 요청/응답 시간, 처리량, 에러율 측정
- **메일 서비스 메트릭**: 발송 성공률, 처리 시간, 큐 대기 시간 추적
- **백그라운드 작업 모니터링**: Celery, APScheduler, RQ 작업 성능 추적
- **데이터베이스 성능**: 쿼리 실행 시간, 연결 풀 상태, 조직별 사용량
- **Postfix/Dovecot 모니터링**: 서버 상태, 메일 큐 크기, 처리량
- **시스템 리소스**: CPU, 메모리, 디스크, 네트워크 사용량
- **조직별 사용량 추적**: 메일 발송량, 저장 공간, API 호출 수
- **SLA 모니터링**: 응답 시간, 가용성, 처리량 목표 달성률
- **알림 시스템**: 임계값 초과 시 자동 알림 발송
- **대시보드**: Grafana를 통한 실시간 모니터링 대시보드

---

## 🧪 테스트 규칙

### 테스트 구조
- `test/` 디렉토리에 테스트 코드 구성
- pytest 프레임워크 사용
- 단위 테스트, 통합 테스트, E2E 테스트 구분

### 테스트 커버리지
- 핵심 비즈니스 로직 **80% 이상** 커버리지
- 모든 API 엔드포인트 테스트
- 메일 발송 서비스 모킹 테스트
- 에러 시나리오 테스트

### 테스트 예시
```python
def test_send_email_success():
    """
    메일 발송 성공 테스트
    """
    # Given
    recipient = "test@example.com"
    subject = "테스트 메일"
    content = "안녕하세요, 테스트 메일입니다."
    
    # When
    result = send_email(recipient, subject, content)
    
    # Then
    assert result["status"] == "success"
    assert result["message_id"] is not None

def test_invalid_email_format():
    """
    잘못된 이메일 형식 테스트
    """
    # Given
    invalid_email = "invalid-email"
    
    # When & Then
    with pytest.raises(ValidationError):
        send_email(invalid_email, "제목", "내용")
```

---

## 🚀 배포 및 운영

### 환경 구성
- 개발(Development), 스테이징(Staging), 프로덕션(Production) 환경 분리
- 환경별 설정 파일 관리 (`.env` 파일)
- Docker Compose를 통한 컨테이너화
- Nginx 리버스 프록시 설정

### CI/CD 파이프라인
- 코드 푸시 시 자동 테스트 실행
- 테스트 통과 후 자동 배포
- 롤백 메커니즘 구현
- 배포 전 보안 검사

### 백업 및 복구
- PostgreSQL 데이터베이스 정기 백업
- 메일 데이터 백업 (Dovecot maildir)
- 백업 데이터 암호화
- 복구 절차 문서화
- 재해 복구 계획 수립

---

## 📚 문서화 규칙

### API 문서
- FastAPI 자동 생성 문서 활용
- 모든 엔드포인트에 상세 설명 추가
- 요청/응답 예시 제공
- 에러 코드 및 메시지 문서화

### 코드 문서
- README.md 파일 최신 상태 유지
- 설치 및 실행 가이드 제공
- 아키텍처 다이어그램 포함
- 변경 이력 관리 (CHANGELOG.md)
- 메일 서버 설정 가이드 제공

---

## 📈 성능 최적화

### 데이터베이스 최적화
- 자주 사용되는 쿼리에 인덱스 추가
- N+1 쿼리 문제 방지
- 페이지네이션 구현
- 오래된 메일 데이터 아카이빙
- 연결 풀링 최적화

### API 성능 개선
- 비동기 처리 활용
- Redis 캐싱 전략 적용
- 응답 데이터 크기 최소화
- 압축 사용 (gzip)
- CDN 활용 (정적 파일)

### 메일 서버 최적화
- Postfix 큐 관리 최적화
- Dovecot 인덱스 최적화
- 메일 압축 및 아카이빙
- 스팸 필터 성능 튜닝

---

## 🔍 코드 리뷰 가이드

### 리뷰 체크리스트
- [ ] 요구사항 충족 여부
- [ ] 코딩 스타일 준수
- [ ] 보안 취약점 검토
- [ ] 성능 영향도 분석
- [ ] 테스트 코드 작성 여부
- [ ] 문서 업데이트 여부
- [ ] 메일 서버 설정 검토

### 리뷰 우선순위
- **🔴 필수**: 보안, 메일 발송 기능, 에러 처리
- **🟡 권장**: 성능 최적화, 코드 품질
- **🟢 선택**: 고급 기능, 추가 최적화

---

## 🛠️ 개발 도구 및 설정

### 필수 도구
- **IDE**: Trae AI (권장), VS Code
- **Python**: 3.11 이상
- **Node.js**: 18 이상
- **데이터베이스**: PostgreSQL 15 이상
- **컨테이너**: Docker, Docker Compose
- **버전 관리**: Git

### 개발 환경 설정
```bash
# 저장소 클론
git clone <repository-url>
cd skyboot.mail2

# 백엔드 설정
cd backend
python3.11 -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt

# 프론트엔드 설정
cd ../frontend
npm install

# 환경 변수 설정
cp backend/.env.example backend/.env
# .env 파일 편집 (데이터베이스, Redis, 메일 서버 설정)

# Docker Compose 실행 (PostgreSQL, Redis, Postfix 포함)
docker-compose -f docker-compose.dev.yml up -d

# 데이터베이스 마이그레이션
cd backend
alembic upgrade head

# 개발 서버 실행
# 백엔드: uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 프론트엔드: npm run dev
# Celery 워커: celery -A app.celery worker --loglevel=info
# Celery Beat: celery -A app.celery beat --loglevel=info

# 테스트 실행
pytest backend/tests/
npm run test  # 프론트엔드 테스트

# 코드 품질 검사
flake8 backend/
black backend/
npm run lint  # 프론트엔드 린트
```

---

## 📋 체크리스트

### 새 기능 개발 시
- [ ] 요구사항 명확히 정의
- [ ] 데이터베이스 스키마 검토
- [ ] API 설계 문서 작성
- [ ] 보안 영향도 분석
- [ ] 테스트 계획 수립
- [ ] 성능 영향도 검토
- [ ] 메일 서버 설정 검토

### 코드 작성 시
- [ ] PEP 8 스타일 준수
- [ ] 타입 힌트 추가
- [ ] 한국어 docstring 작성
- [ ] 에러 처리 구현
- [ ] 로깅 추가
- [ ] 입력 검증 로직
- [ ] 메일 보안 검증

### 배포 전
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 보안 검토 완료
- [ ] 성능 테스트 수행
- [ ] 문서 업데이트
- [ ] 백업 완료
- [ ] 메일 서버 설정 검증
- [ ] SSL/TLS 인증서 확인

---

**이 프로젝트 규칙은 기업용 메일서버 프로젝트의 품질과 일관성을 보장하기 위한 필수 가이드라인입니다.**

**마지막 업데이트**: 2025년 09월  
**작성자**: SkyBoot Mail 개발팀  
**버전**: 2.0