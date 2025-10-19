# SkyBoot Mail SaaS - API 테스트 스크립트 가이드

## 📋 개요

이 디렉토리에는 SkyBoot Mail SaaS의 모든 API 엔드포인트를 테스트하는 PowerShell 스크립트들이 포함되어 있습니다.

## 📁 파일 구조

```
test/
├── README.md                          # 이 파일
├── run_all_tests.ps1                  # 🎯 마스터 테스트 실행 스크립트
├── analyze_test_results.ps1           # 📊 테스트 결과 분석 스크립트
├── auth_router_tests.ps1              # 🔐 인증 라우터 테스트
├── organization_router_tests.ps1      # 🏢 조직 관리 라우터 테스트
├── user_router_tests.ps1              # 👤 사용자 관리 라우터 테스트
├── mail_core_router_tests.ps1         # 📧 메일 핵심 기능 테스트
├── mail_convenience_router_tests.ps1  # 📬 메일 편의 기능 테스트
├── mail_advanced_router_tests.ps1     # 🔧 메일 고급 기능 테스트
├── mail_setup_router_tests.ps1        # ⚙️ 메일 설정 테스트
├── addressbook_router_tests.ps1       # 📇 주소록 라우터 테스트
├── debug_router_tests.ps1             # 🐛 디버그 라우터 테스트
├── monitoring_router_tests.ps1        # 📊 모니터링 라우터 테스트
├── theme_router_tests.ps1             # 🎨 테마 라우터 테스트
├── results/                           # 📁 테스트 결과 저장 디렉토리
└── reports/                           # 📁 분석 리포트 저장 디렉토리
```

## 🚀 빠른 시작

### 1. 전체 테스트 실행 (권장)

```powershell
# 기본 실행 (모든 라우터 테스트)
.\run_all_tests.ps1

# 특정 서버 URL 지정
.\run_all_tests.ps1 -BaseUrl "http://localhost:8000"

# 특정 라우터만 테스트
.\run_all_tests.ps1 -IncludeRouters @("Auth", "User", "Mail Core")

# 특정 라우터 제외
.\run_all_tests.ps1 -ExcludeRouters @("Debug", "Monitoring")

# 실패 시에도 계속 진행
.\run_all_tests.ps1 -ContinueOnError

# HTML 리포트 생성
.\run_all_tests.ps1 -GenerateReport
```

### 2. 개별 라우터 테스트

```powershell
# 인증 라우터만 테스트
.\auth_router_tests.ps1

# 메일 핵심 기능만 테스트
.\mail_core_router_tests.ps1 -BaseUrl "http://localhost:8000"

# 조직 관리 기능만 테스트 (관리자 계정 필요)
.\organization_router_tests.ps1 -AdminEmail "admin@test.com" -AdminPassword "password123"
```

### 3. 테스트 결과 분석

```powershell
# 최신 테스트 결과 분석
.\analyze_test_results.ps1

# 특정 결과 파일 분석
.\analyze_test_results.ps1 -SpecificResultFile ".\results\integrated_test_results_20241219_143022.json"

# 상세 HTML 리포트 생성 및 자동 열기
.\analyze_test_results.ps1 -GenerateDetailedReport -OpenReport

# 차트 포함 리포트 생성
.\analyze_test_results.ps1 -GenerateCharts
```

## ⚙️ 설정 및 요구사항

### 사전 요구사항

1. **PowerShell 5.0 이상**
2. **SkyBoot Mail SaaS 서버 실행 중**
3. **네트워크 연결** (API 서버 접근 가능)

### 기본 설정

```powershell
# 기본 서버 URL
$BaseUrl = "http://localhost:8000"

# 기본 관리자 계정
$AdminEmail = "admin@skyboot.com"
$AdminPassword = "admin123!@#"

# 기본 사용자 계정
$UserEmail = "user@skyboot.com"
$UserPassword = "user123!@#"
```

### 환경 변수 설정 (선택사항)

```powershell
# PowerShell 프로필에 추가
$env:SKYBOOT_API_URL = "http://localhost:8000"
$env:SKYBOOT_ADMIN_EMAIL = "admin@skyboot.com"
$env:SKYBOOT_ADMIN_PASSWORD = "admin123!@#"
$env:SKYBOOT_USER_EMAIL = "user@skyboot.com"
$env:SKYBOOT_USER_PASSWORD = "user123!@#"
```

## 📊 테스트 결과 이해하기

### 성공 기준

- ✅ **성공**: 예상된 상태 코드와 응답 구조
- ⚠️ **성공 (예상된 실패)**: 의도적인 실패 테스트 (예: 권한 없음, 잘못된 입력)
- ❌ **실패**: 예상과 다른 응답 또는 오류

### 결과 파일 구조

```json
{
  "TestInfo": {
    "TestName": "Auth Router Tests",
    "StartTime": "2024-12-19T14:30:22",
    "EndTime": "2024-12-19T14:32:15",
    "Duration": "00:01:53"
  },
  "Statistics": {
    "TotalTests": 25,
    "SuccessfulTests": 23,
    "FailedTests": 2,
    "SuccessRate": 92.0
  },
  "TestResults": [
    {
      "TestName": "사용자 로그인",
      "Method": "POST",
      "Endpoint": "/auth/login",
      "StatusCode": 200,
      "Status": "성공",
      "ResponseTime": 245,
      "Details": "로그인 성공"
    }
  ]
}
```

## 🔧 고급 사용법

### 1. 커스텀 테스트 시나리오

```powershell
# 특정 조건으로 테스트 실행
.\run_all_tests.ps1 `
    -BaseUrl "https://api.skyboot.com" `
    -AdminEmail "admin@company.com" `
    -AdminPassword "SecurePassword123!" `
    -IncludeRouters @("Auth", "Organization", "User") `
    -GenerateReport `
    -ContinueOnError
```

### 2. 성능 테스트

```powershell
# 부하 테스트 (각 엔드포인트 10회 연속 호출)
.\mail_core_router_tests.ps1 -PerformanceTest -TestIterations 10
```

### 3. 배치 테스트

```powershell
# 여러 환경에서 테스트
$environments = @(
    @{ Url = "http://localhost:8000"; Name = "Local" },
    @{ Url = "https://dev.skyboot.com"; Name = "Development" },
    @{ Url = "https://staging.skyboot.com"; Name = "Staging" }
)

foreach ($env in $environments) {
    Write-Host "Testing $($env.Name) environment..."
    .\run_all_tests.ps1 -BaseUrl $env.Url -OutputDir ".\results\$($env.Name)"
}
```

## 📈 모니터링 및 CI/CD 통합

### Jenkins 파이프라인 예시

```groovy
pipeline {
    agent any
    stages {
        stage('API Tests') {
            steps {
                powershell '''
                    cd test
                    .\run_all_tests.ps1 -BaseUrl "${API_URL}" -GenerateReport
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'test/reports',
                        reportFiles: '*.html',
                        reportName: 'API Test Report'
                    ])
                }
            }
        }
    }
}
```

### GitHub Actions 예시

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  api-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run API Tests
        run: |
          cd test
          .\run_all_tests.ps1 -BaseUrl "${{ secrets.API_URL }}" -GenerateReport
        shell: powershell
        
      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test/results/
```

## 🐛 문제 해결

### 일반적인 문제

1. **연결 오류**
   ```
   해결: 서버가 실행 중인지 확인, 방화벽 설정 확인
   ```

2. **인증 실패**
   ```
   해결: 관리자/사용자 계정 정보 확인, 데이터베이스 초기 데이터 확인
   ```

3. **권한 오류**
   ```
   해결: PowerShell 실행 정책 확인 (Set-ExecutionPolicy RemoteSigned)
   ```

4. **스크립트 실행 오류**
   ```powershell
   # 실행 정책 변경
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### 로그 확인

```powershell
# 상세 로그 출력
.\run_all_tests.ps1 -Verbose

# 디버그 모드
$DebugPreference = "Continue"
.\run_all_tests.ps1
```

## 📞 지원

- **개발팀**: SkyBoot Mail 개발팀
- **문서**: 프로젝트 Wiki 참조
- **이슈 리포트**: GitHub Issues 또는 내부 이슈 트래커

---

**📝 참고**: 이 테스트 스크립트들은 개발 및 테스트 환경에서 사용하도록 설계되었습니다. 프로덕션 환경에서는 주의해서 사용하세요.