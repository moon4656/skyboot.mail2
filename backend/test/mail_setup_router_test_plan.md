# mail_setup_router.py 테스트 계획서

## 📋 테스트 개요
- **대상 파일**: `c:\Users\eldorado\skyboot.mail2\backend\app\router\mail_setup_router.py`
- **테스트 목적**: 메일 계정 초기화 기능의 정확성 및 안정성 검증
- **테스트 범위**: `/setup-mail-account` 엔드포인트 전체 기능
- **작성일**: 2025-09-30

## 🎯 테스트 대상 기능

### 주요 엔드포인트
- **POST** `/setup-mail-account` - 메일 계정 초기화

### 기능 상세
1. **기존 메일 사용자 확인**: user_uuid 또는 email로 기존 MailUser 검색
2. **기본 폴더 생성**: 기존 사용자의 폴더가 없는 경우 기본 폴더 생성
3. **새 메일 사용자 생성**: 기존 사용자가 없는 경우 새 MailUser 생성
4. **기본 폴더 초기화**: 새 사용자의 기본 폴더 생성 (받은편지함, 보낸편지함, 임시보관함, 휴지통)

## 📝 테스트 시나리오

### 시나리오 1: 신규 사용자 메일 계정 초기화
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

**예상 결과**:
- HTTP 상태 코드: 200
- 새 MailUser 레코드 생성
- 4개의 기본 폴더 생성 (받은편지함, 보낸편지함, 임시보관함, 휴지통)
- 응답 데이터에 mail_user_id, email, display_name 포함

**성공 기준**:
- ✅ MailUser 테이블에 새 레코드 생성
- ✅ MailFolder 테이블에 4개의 시스템 폴더 생성
- ✅ 모든 폴더의 folder_type이 올바르게 설정
- ✅ 응답 메시지: "메일 계정이 성공적으로 초기화되었습니다."

### 시나리오 2: 기존 사용자 메일 계정 재초기화 (폴더 있음)
**목적**: 이미 메일 계정이 설정된 사용자의 중복 처리 방지 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 해당 사용자의 MailUser 레코드가 이미 존재
- 기본 폴더들이 이미 생성되어 있음

**테스트 데이터**:
```json
{
  "user": {
    "user_uuid": "existing-user-uuid-001",
    "email": "existinguser@skyboot.co.kr",
    "username": "existinguser",
    "org_id": "test-org-001"
  }
}
```

**예상 결과**:
- HTTP 상태 코드: 200
- 기존 MailUser 정보 반환
- 새로운 레코드 생성하지 않음
- 응답 메시지: "메일 계정이 이미 설정되어 있습니다."

**성공 기준**:
- ✅ 기존 MailUser 레코드 유지
- ✅ 중복 폴더 생성하지 않음
- ✅ 기존 사용자 정보 정확히 반환

### 시나리오 3: 기존 사용자 메일 계정 재초기화 (폴더 없음)
**목적**: MailUser는 있지만 폴더가 없는 경우의 폴더 생성 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 해당 사용자의 MailUser 레코드가 존재
- 기본 폴더들이 생성되어 있지 않음

**테스트 데이터**:
```json
{
  "user": {
    "user_uuid": "user-without-folders-001",
    "email": "usernofolders@skyboot.co.kr",
    "username": "usernofolders",
    "org_id": "test-org-001"
  }
}
```

**예상 결과**:
- HTTP 상태 코드: 200
- 기존 MailUser 정보 반환
- 4개의 기본 폴더 새로 생성
- 응답 메시지: "메일 계정이 이미 설정되어 있습니다."

**성공 기준**:
- ✅ 기존 MailUser 레코드 유지
- ✅ 4개의 기본 폴더 생성
- ✅ 폴더 타입 및 시스템 플래그 올바르게 설정

### 시나리오 4: 인증되지 않은 사용자 접근
**목적**: 인증 실패 시 적절한 오류 처리 확인

**전제 조건**:
- 유효하지 않은 JWT 토큰 또는 토큰 없음

**테스트 데이터**:
```json
{
  "headers": {
    "Authorization": "Bearer invalid_token"
  }
}
```

**예상 결과**:
- HTTP 상태 코드: 401 (Unauthorized)
- 오류 메시지 반환

**성공 기준**:
- ✅ 401 상태 코드 반환
- ✅ 적절한 인증 오류 메시지
- ✅ 데이터베이스 변경 없음

### 시나리오 5: 데이터베이스 연결 오류
**목적**: 데이터베이스 오류 시 적절한 예외 처리 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 데이터베이스 연결 불가 또는 오류 상황

**예상 결과**:
- HTTP 상태 코드: 500 (Internal Server Error)
- 오류 메시지: "메일 계정 초기화 중 오류가 발생했습니다"
- 트랜잭션 롤백 수행

**성공 기준**:
- ✅ 500 상태 코드 반환
- ✅ 적절한 오류 메시지
- ✅ 데이터베이스 롤백 수행
- ✅ 로그에 오류 기록

### 시나리오 6: 조직 ID 불일치
**목적**: 사용자의 조직 ID와 관련 데이터 일관성 확인

**전제 조건**:
- 유효한 JWT 토큰으로 인증된 사용자
- 사용자의 org_id와 다른 조직의 데이터 존재

**테스트 데이터**:
```json
{
  "user": {
    "user_uuid": "test-user-uuid-002",
    "email": "testuser@skyboot.co.kr",
    "username": "testuser",
    "org_id": "different-org-001"
  }
}
```

**예상 결과**:
- HTTP 상태 코드: 200
- 사용자의 org_id로 새 MailUser 생성
- 해당 조직의 폴더 생성

**성공 기준**:
- ✅ 올바른 org_id로 MailUser 생성
- ✅ 폴더의 org_id 일관성 유지
- ✅ 조직별 데이터 분리 확인

## 🧪 테스트 데이터 준비

### 테스트용 사용자 데이터
```python
TEST_USERS = [
    {
        "user_uuid": "test-user-001",
        "email": "testuser1@skyboot.co.kr",
        "username": "testuser1",
        "org_id": "test-org-001",
        "hashed_password": "$2b$12$test.hash.password1"
    },
    {
        "user_uuid": "test-user-002", 
        "email": "testuser2@skyboot.co.kr",
        "username": "testuser2",
        "org_id": "test-org-001",
        "hashed_password": "$2b$12$test.hash.password2"
    },
    {
        "user_uuid": "test-user-003",
        "email": "testuser3@skyboot.co.kr", 
        "username": "testuser3",
        "org_id": "test-org-002",
        "hashed_password": "$2b$12$test.hash.password3"
    }
]
```

### 테스트용 조직 데이터
```python
TEST_ORGANIZATIONS = [
    {
        "org_id": "test-org-001",
        "org_code": "TESTORG001",
        "name": "테스트 조직 1",
        "domain": "testorg1.skyboot.co.kr"
    },
    {
        "org_id": "test-org-002",
        "org_code": "TESTORG002", 
        "name": "테스트 조직 2",
        "domain": "testorg2.skyboot.co.kr"
    }
]
```

### 기본 폴더 검증 데이터
```python
EXPECTED_FOLDERS = [
    {"name": "받은편지함", "folder_type": "inbox", "is_system": True},
    {"name": "보낸편지함", "folder_type": "sent", "is_system": True},
    {"name": "임시보관함", "folder_type": "draft", "is_system": True},
    {"name": "휴지통", "folder_type": "trash", "is_system": True}
]
```

## 📊 성능 및 안정성 테스트

### 성능 기준
- **응답 시간**: 평균 < 500ms, 최대 < 2초
- **동시 요청**: 10개 동시 요청 처리 가능
- **메모리 사용량**: 요청당 < 50MB

### 안정성 테스트
1. **반복 테스트**: 동일 사용자로 100회 연속 요청
2. **동시성 테스트**: 다른 사용자 10명이 동시 요청
3. **부하 테스트**: 1분간 지속적인 요청 처리

## 🔍 검증 포인트

### 데이터베이스 검증
1. **MailUser 테이블**:
   - user_uuid, org_id, email 정확성
   - password_hash 복사 확인
   - display_name = username 확인
   - is_active = True 확인

2. **MailFolder 테이블**:
   - 4개 폴더 생성 확인
   - folder_type 정확성 (inbox, sent, draft, trash)
   - is_system = True 확인
   - user_uuid, org_id 일관성

3. **관계 무결성**:
   - Foreign Key 제약 조건 확인
   - 조직별 데이터 분리 확인

### API 응답 검증
1. **성공 응답 구조**:
   ```json
   {
     "success": true,
     "message": "메일 계정이 성공적으로 초기화되었습니다.",
     "data": {
       "mail_user_id": "user-uuid",
       "email": "user@example.com",
       "display_name": "username"
     }
   }
   ```

2. **오류 응답 구조**:
   ```json
   {
     "detail": "메일 계정 초기화 중 오류가 발생했습니다: 오류내용"
   }
   ```

## 🚀 테스트 실행 계획

### 1단계: 환경 준비
- 테스트 데이터베이스 초기화
- 테스트용 조직 및 사용자 생성
- JWT 토큰 생성

### 2단계: 단위 테스트
- 각 시나리오별 개별 테스트 실행
- 데이터베이스 상태 검증
- 응답 구조 검증

### 3단계: 통합 테스트
- 전체 워크플로우 테스트
- 다중 사용자 시나리오 테스트
- 오류 복구 테스트

### 4단계: 성능 테스트
- 응답 시간 측정
- 동시성 테스트
- 부하 테스트

### 5단계: 최종 검증
- 모든 테스트 결과 종합
- 이슈 및 개선사항 도출
- 테스트 보고서 작성

## 📋 체크리스트

### 기능 테스트
- [ ] 신규 사용자 메일 계정 초기화
- [ ] 기존 사용자 중복 처리 (폴더 있음)
- [ ] 기존 사용자 폴더 생성 (폴더 없음)
- [ ] 인증 실패 처리
- [ ] 데이터베이스 오류 처리
- [ ] 조직 ID 일관성 확인

### 데이터 검증
- [ ] MailUser 레코드 정확성
- [ ] MailFolder 레코드 정확성
- [ ] 관계 무결성 확인
- [ ] 조직별 데이터 분리

### 성능 테스트
- [ ] 응답 시간 기준 충족
- [ ] 동시 요청 처리
- [ ] 메모리 사용량 확인

### 안정성 테스트
- [ ] 반복 테스트 통과
- [ ] 동시성 테스트 통과
- [ ] 부하 테스트 통과

---
**작성자**: Trae AI Assistant  
**작성일**: 2025-09-30  
**버전**: 1.0