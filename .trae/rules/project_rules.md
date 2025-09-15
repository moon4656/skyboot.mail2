# 기업용 메일서버 프로젝트 규칙 (Project Rules)

## 🎯 프로젝트 개요
이 문서는 기업용 메일서버 프로젝트의 개발 규칙과 가이드라인을 정의합니다. 모든 개발자는 이 규칙을 준수하여 일관성 있고 고품질의 코드를 작성해야 합니다.

---

## 🏗️ 프로젝트 아키텍처

### 기술 스택
- **백엔드**: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **프론트엔드**: Vue.js 3, TypeScript, Vite, Pinia
- **메일 서버**: Postfix (SMTP), Dovecot (IMAP/POP3)
- **캐시/세션**: Redis
- **인증**: JWT 토큰, bcrypt 패스워드 해싱
- **데이터베이스**: PostgreSQL 15+ with Alembic 마이그레이션
- **컨테이너화**: Docker, Docker Compose
- **웹서버**: Nginx (프록시 및 정적 파일 서빙)
- **로깅**: Python logging 모듈
- **테스트**: pytest 프레임워크

### 프로젝트 구조
```
skyboot.mail2/
├── backend/                 # FastAPI 백엔드 서버
│   ├── app/
│   │   ├── routers/        # API 라우터
│   │   ├── models.py       # 데이터베이스 모델
│   │   ├── schemas.py      # Pydantic 스키마
│   │   ├── auth.py         # 인증 및 권한 관리
│   │   ├── config.py       # 설정 관리
│   │   ├── database.py     # 데이터베이스 연결
│   │   └── mail_service.py # 메일 발송 서비스
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
├── docker-compose.yml      # 프로덕션 Docker Compose
├── docker-compose.dev.yml  # 개발 Docker Compose
├── postfix_main.cf        # Postfix 메인 설정
├── postfix_master.cf      # Postfix 마스터 설정
└── .trae/rules/           # Trae AI IDE 프로젝트 규칙
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
```python
# 메일 사용자 테이블
class MailUser(Base):
    # 메일 시스템 사용자 정보를 저장하는 테이블
    id = Column(Integer, primary_key=True, comment="사용자 고유 ID")
    user_uuid = Column(String, unique=True, comment="사용자 UUID")
    email = Column(String, unique=True, comment="이메일 주소")
    password_hash = Column(String, comment="해시된 비밀번호")
    # ... 기타 필드

# 메일 테이블
class Mail(Base):
    # 메일 정보를 저장하는 테이블
    mail_id = Column(String, primary_key=True, comment="메일 고유 ID")
    sender_email = Column(String, comment="발송자 이메일")
    subject = Column(String, comment="메일 제목")
    content = Column(Text, comment="메일 본문")
    sent_at = Column(DateTime, comment="발송 시간")
    # ... 기타 필드

# 가상 도메인 테이블 (Postfix 연동)
class VirtualDomain(Base):
    # Postfix 가상 도메인 정보를 저장하는 테이블
    id = Column(Integer, primary_key=True, comment="도메인 ID")
    name = Column(String, unique=True, comment="도메인명")
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

### 엔드포인트 예시
```python
@app.post("/api/mail/send", summary="메일 발송")
async def send_mail(
    mail_data: MailSendRequest,
    current_user: MailUser = Depends(get_current_user)
):
    """
    메일을 발송합니다.
    
    - **recipient**: 수신자 이메일 주소
    - **subject**: 메일 제목
    - **content**: 메일 본문
    - **attachments**: 첨부파일 (선택사항)
    """
    pass

@app.get("/api/mail/inbox", summary="받은 메일함 조회")
async def get_inbox(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: MailUser = Depends(get_current_user)
):
    """
    사용자의 받은 메일함을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 메일 수 (기본값: 20, 최대: 100)
    """
    pass
```

### 메일 서비스 통합
- Postfix SMTP 서버 연동
- Dovecot IMAP/POP3 서버 연동
- 메일 큐 관리 및 재시도 메커니즘
- 첨부파일 처리 및 저장
- 스팸 필터링 및 바이러스 검사

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

### 접근 로깅
```python
# 메일 접근 로그 테이블
class MailAccessLog(Base):
    # 메일 접근 로그를 기록하는 테이블
    id = Column(Integer, primary_key=True)
    user_uuid = Column(String, comment="사용자 UUID")
    action = Column(String, comment="수행된 작업 (send, read, delete 등)")
    mail_id = Column(String, comment="대상 메일 ID")
    ip_address = Column(String, comment="클라이언트 IP 주소")
    user_agent = Column(String, comment="사용자 에이전트")
    created_at = Column(DateTime, comment="접근 시간")
```

---

## 📊 로깅 및 모니터링

### 로깅 시스템
- Python `logging` 모듈 사용
- 구조화된 로그 메시지 작성
- 로그 레벨 적절히 활용 (DEBUG, INFO, WARNING, ERROR)
- 민감한 정보 로깅 금지

### 로깅 패턴
```python
# 함수 시작 시
logger.info(f"📧 {function_name} 시작 - 파라미터: {params}")

# 메일 발송 시작
logger.info(f"📤 메일 발송 시작 - 수신자: {recipient}, 제목: {subject}")

# 성공 완료
logger.info(f"✅ {function_name} 완료 - 결과: {result_summary}")

# 에러 발생
logger.error(f"❌ {error_message}")
logger.error(f"Traceback: {traceback.format_exc()}")
```

### 성능 모니터링
- API 요청/응답 시간 측정
- 메일 발송 성공률 및 처리 시간 추적
- 데이터베이스 쿼리 성능 추적
- Postfix/Dovecot 서버 상태 모니터링
- 시스템 리소스 사용량 모니터링

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
# .env 파일 편집

# Docker Compose 실행
docker-compose -f docker-compose.dev.yml up -d

# 개발 서버 실행
# 백엔드: uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 프론트엔드: npm run dev
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

**마지막 업데이트**: 2024년 12월  
**작성자**: SkyBoot Mail 개발팀  
**버전**: 2.0