# mail_setup_router.py 테스트 시나리오

## 📋 테스트 개요
- **대상 파일**: `c:\Users\eldorado\skyboot.mail2\backend\app\router\mail_setup_router.py`
- **테스트 목적**: 메일 계정 초기화 기능의 정확성 및 안정성 검증
- **테스트 범위**: `/setup-mail-account` 엔드포인트 전체 기능
- **작성일**: 2025-01-25

## 🎯 테스트 대상 기능

### 주요 엔드포인트
- **POST** `/setup-mail-account` - 메일 계정 초기화

### 기능 상세
1. **기존 메일 사용자 확인**: user_uuid 또는 email로 기존 MailUser 검색
2. **기본 폴더 생성**: 기존 사용자의 폴더가 없는 경우 기본 폴더 생성
3. **새 메일 사용자 생성**: 기존 사용자가 없는 경우 새 MailUser 생성
4. **기본 폴더 초기화**: 새 사용자의 기본 폴더 생성 (받은편지함, 보낸편지함, 임시보관함, 휴지통)

## 📝 테스트 시나리오

### 시나리오 1: 신규 사용자 메일 계정 초기화 ✅
**목적**: 처음 메일 계정을 설정하는 사용자의 정상 처리 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 해당 사용자의 MailUser 레코드가 존재하지 않음
- 데이터베이스 연결 정상

**테스트 데이터**:
```json
{
  "user": {
    "user_uuid": "test-user-uuid-001",
    "email": "newuser@skyboot.co.kr",
    "username": "newuser",
    "org_id": "test-org-001",
    "hashed_password": "$2b$12$hashedpassword"
  }
}
```

**실행 단계**:
1. 유효한 JWT 토큰으로 인증
2. POST `/setup-mail-account` 요청 전송
3. 응답 확인

**예상 결과**:
- HTTP 상태 코드: 200
- 새 MailUser 레코드 생성 확인
- 기본 폴더 4개 생성 확인 (받은편지함, 보낸편지함, 임시보관함, 휴지통)
- 응답 데이터:
```json
{
  "success": true,
  "message": "메일 계정이 성공적으로 초기화되었습니다.",
  "data": {
    "mail_user_id": "test-user-uuid-001",
    "email": "newuser@skyboot.co.kr",
    "display_name": "newuser"
  }
}
```

**성공 기준**:
- ✅ MailUser 테이블에 새 레코드 생성
- ✅ MailFolder 테이블에 4개 기본 폴더 생성
- ✅ 정확한 응답 형식 반환
- ✅ 로그 메시지 정상 출력

---

### 시나리오 2: 기존 사용자 메일 계정 재초기화 ✅
**목적**: 이미 메일 계정이 있는 사용자의 중복 처리 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 해당 사용자의 MailUser 레코드가 이미 존재
- 기본 폴더가 이미 생성되어 있음

**테스트 데이터**:
```json
{
  "existing_mail_user": {
    "user_uuid": "test-user-uuid-002",
    "email": "existinguser@skyboot.co.kr",
    "display_name": "existinguser",
    "is_active": true
  }
}
```

**실행 단계**:
1. 기존 MailUser 및 폴더 데이터 사전 생성
2. 유효한 JWT 토큰으로 인증
3. POST `/setup-mail-account` 요청 전송
4. 응답 확인

**예상 결과**:
- HTTP 상태 코드: 200
- 기존 MailUser 레코드 유지
- 중복 폴더 생성 없음
- 응답 데이터:
```json
{
  "success": true,
  "message": "메일 계정이 이미 설정되어 있습니다.",
  "data": {
    "mail_user_id": "test-user-uuid-002",
    "email": "existinguser@skyboot.co.kr",
    "display_name": "existinguser"
  }
}
```

**성공 기준**:
- ✅ 기존 MailUser 레코드 변경 없음
- ✅ 기존 폴더 구조 유지
- ✅ 정확한 응답 형식 반환
- ✅ 중복 처리 로직 정상 동작

---

### 시나리오 3: 기존 사용자 + 폴더 누락 상황 ✅
**목적**: 메일 사용자는 있지만 기본 폴더가 없는 경우 처리 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 해당 사용자의 MailUser 레코드는 존재
- 기본 폴더가 누락된 상태

**테스트 데이터**:
```json
{
  "mail_user_without_folders": {
    "user_uuid": "test-user-uuid-003",
    "email": "usernofolders@skyboot.co.kr",
    "display_name": "usernofolders",
    "is_active": true
  }
}
```

**실행 단계**:
1. MailUser 레코드만 생성 (폴더 없음)
2. 유효한 JWT 토큰으로 인증
3. POST `/setup-mail-account` 요청 전송
4. 폴더 생성 확인

**예상 결과**:
- HTTP 상태 코드: 200
- 기존 MailUser 레코드 유지
- 누락된 기본 폴더 4개 생성
- 응답 데이터:
```json
{
  "success": true,
  "message": "메일 계정이 이미 설정되어 있습니다.",
  "data": {
    "mail_user_id": "test-user-uuid-003",
    "email": "usernofolders@skyboot.co.kr",
    "display_name": "usernofolders"
  }
}
```

**성공 기준**:
- ✅ 기존 MailUser 레코드 유지
- ✅ 누락된 기본 폴더 생성
- ✅ 폴더 개수 정확히 4개
- ✅ 폴더 타입 정확성 확인

---

### 시나리오 4: 인증 실패 처리 ❌
**목적**: 인증되지 않은 사용자의 접근 차단 확인

**전제 조건**:
- 유효하지 않은 JWT 토큰 또는 토큰 없음
- 데이터베이스 연결 정상

**테스트 데이터**:
```json
{
  "invalid_token": "invalid.jwt.token"
}
```

**실행 단계**:
1. 잘못된 JWT 토큰으로 요청
2. POST `/setup-mail-account` 요청 전송
3. 오류 응답 확인

**예상 결과**:
- HTTP 상태 코드: 401 (Unauthorized)
- 오류 메시지: "Could not validate credentials"
- MailUser 레코드 생성 없음

**성공 기준**:
- ✅ 401 상태 코드 반환
- ✅ 적절한 오류 메시지
- ✅ 데이터베이스 변경 없음
- ✅ 보안 로그 기록

---

### 시나리오 5: 데이터베이스 오류 처리 ❌
**목적**: 데이터베이스 연결 실패 시 오류 처리 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 데이터베이스 연결 실패 또는 오류 상황

**실행 단계**:
1. 데이터베이스 연결 차단 또는 오류 유발
2. 유효한 JWT 토큰으로 인증
3. POST `/setup-mail-account` 요청 전송
4. 오류 응답 확인

**예상 결과**:
- HTTP 상태 코드: 500 (Internal Server Error)
- 오류 메시지: "메일 계정 초기화 중 오류가 발생했습니다"
- 롤백 처리 확인

**성공 기준**:
- ✅ 500 상태 코드 반환
- ✅ 적절한 오류 메시지
- ✅ 트랜잭션 롤백 처리
- ✅ 오류 로그 기록

---

### 시나리오 6: 조직별 데이터 격리 확인 ✅
**목적**: 다중 조직 환경에서 데이터 격리 확인

**전제 조건**:
- 서로 다른 조직의 사용자 2명
- 각각 유효한 JWT 토큰으로 인증

**테스트 데이터**:
```json
{
  "user_org_a": {
    "user_uuid": "test-user-uuid-004",
    "email": "user@org-a.com",
    "org_id": "org-a-001"
  },
  "user_org_b": {
    "user_uuid": "test-user-uuid-005",
    "email": "user@org-b.com",
    "org_id": "org-b-001"
  }
}
```

**실행 단계**:
1. 조직 A 사용자로 메일 계정 초기화
2. 조직 B 사용자로 메일 계정 초기화
3. 각 조직의 데이터 격리 확인

**예상 결과**:
- 각 조직별로 독립적인 MailUser 생성
- 각 조직별로 독립적인 폴더 생성
- 조직 간 데이터 접근 불가

**성공 기준**:
- ✅ 조직별 독립적인 데이터 생성
- ✅ 조직 ID 정확성 확인
- ✅ 데이터 격리 보장
- ✅ 조직별 폴더 구조 독립성

---

## 🔧 테스트 환경 설정

### 필요한 의존성
- FastAPI TestClient
- pytest
- SQLAlchemy (테스트 데이터베이스)
- JWT 토큰 생성 유틸리티

### 테스트 데이터베이스 설정
```python
# 테스트용 인메모리 SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mail_setup.db"
```

### 테스트 사용자 생성
```python
test_users = [
    {
        "user_uuid": "test-user-uuid-001",
        "email": "newuser@skyboot.co.kr",
        "username": "newuser",
        "org_id": "test-org-001",
        "hashed_password": "$2b$12$hashedpassword",
        "is_active": True
    },
    # ... 추가 테스트 사용자
]
```

## 📊 성공 기준 요약

### 기능적 요구사항
- ✅ 신규 사용자 메일 계정 생성
- ✅ 기존 사용자 중복 처리
- ✅ 기본 폴더 자동 생성
- ✅ 조직별 데이터 격리

### 비기능적 요구사항
- ✅ 응답 시간 < 2초
- ✅ 적절한 오류 처리
- ✅ 보안 인증 확인
- ✅ 로그 기록 정확성

### 데이터 무결성
- ✅ 트랜잭션 일관성
- ✅ 외래 키 제약 조건
- ✅ 중복 데이터 방지
- ✅ 롤백 처리 정확성

---

## 📋 테스트 체크리스트

### 준비 단계
- [ ] 테스트 환경 설정 완료
- [ ] 테스트 데이터베이스 초기화
- [ ] JWT 토큰 생성 유틸리티 준비
- [ ] 테스트 사용자 데이터 준비

### 실행 단계
- [ ] 시나리오 1: 신규 사용자 메일 계정 초기화
- [ ] 시나리오 2: 기존 사용자 메일 계정 재초기화
- [ ] 시나리오 3: 기존 사용자 + 폴더 누락 상황
- [ ] 시나리오 4: 인증 실패 처리
- [ ] 시나리오 5: 데이터베이스 오류 처리
- [ ] 시나리오 6: 조직별 데이터 격리 확인

### 검증 단계
- [ ] 응답 형식 검증
- [ ] 데이터베이스 상태 확인
- [ ] 로그 메시지 검증
- [ ] 성능 측정
- [ ] 보안 검증

### 정리 단계
- [ ] 테스트 데이터 정리
- [ ] 결과 보고서 작성
- [ ] 발견된 이슈 문서화
- [ ] 개선 사항 제안

---

*최종 업데이트: 2025-01-25*