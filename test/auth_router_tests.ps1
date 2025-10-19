# ========================================
# 인증 라우터 테스트 시나리오 (auth_router.py)
# SkyBoot Mail SaaS - 다중 조직 지원 메일서버
# ========================================

# 테스트 설정
$BASE_URL = "http://localhost:8001/api/v1"
$AUTH_ENDPOINT = "$BASE_URL/auth"

# 테스트 사용자 정보
$TEST_USER = @{
    userId = "user01"
    password = "test"
}

$TEST_ADMIN = @{
    userId = "admin01"
    password = "test"
}

# 결과 저장 변수
$TEST_RESULTS = @()
$ACCESS_TOKEN_USER = ""
$ACCESS_TOKEN_ADMIN = ""

# 함수: 테스트 결과 기록
function Add-TestResult {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Endpoint,
        [int]$StatusCode,
        [string]$Status,
        [string]$Message = ""
    )
    
    $result = @{
        TestName = $TestName
        Method = $Method
        Endpoint = $Endpoint
        StatusCode = $StatusCode
        Status = $Status
        Message = $Message
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    $script:TEST_RESULTS += $result
    
    $statusIcon = if ($Status -eq "PASS") { "✅" } else { "❌" }
    Write-Host "$statusIcon [$Method] $Endpoint - $TestName ($StatusCode)" -ForegroundColor $(if ($Status -eq "PASS") { "Green" } else { "Red" })
    if ($Message) {
        Write-Host "   💬 $Message" -ForegroundColor Yellow
    }
}

# 함수: HTTP 요청 실행
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    try {
        $params = @{
            Method = $Method
            Uri = $Uri
            Headers = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params
        return @{
            Success = $true
            StatusCode = 200
            Data = $response
        }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { 
            [int]$_.Exception.Response.StatusCode 
        } else { 
            500 
        }
        
        return @{
            Success = $false
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
}

Write-Host "🚀 인증 라우터 테스트 시작" -ForegroundColor Cyan
Write-Host "=" * 50

# ========================================
# 1. 사용자 로그인 테스트 (POST /auth/login)
# ========================================

Write-Host "`n📝 1. 사용자 로그인 테스트" -ForegroundColor Yellow

# 1-1. 일반 사용자 로그인 (user01)
$loginData = @{
    user_id = $TEST_USER.user_id
    password = $TEST_USER.password
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $loginData

if ($result.Success) {
    $ACCESS_TOKEN_USER = $result.Data.access_token
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "PASS" -Message "토큰 획득 성공"
} else {
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-2. 관리자 로그인 (admin01)
$adminLoginData = @{
    user_id = $TEST_ADMIN.user_id
    password = $TEST_ADMIN.password
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $adminLoginData

if ($result.Success) {
    $ACCESS_TOKEN_ADMIN = $result.Data.access_token
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "PASS" -Message "관리자 토큰 획득 성공"
} else {
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-3. 잘못된 비밀번호로 로그인 시도
$wrongPasswordData = @{
    user_id = $TEST_USER.user_id
    password = "wrongpassword"
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $wrongPasswordData

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "잘못된 비밀번호 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 인증 실패"
} else {
    Add-TestResult -TestName "잘못된 비밀번호 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# 1-4. 존재하지 않는 사용자 로그인 시도
$nonExistentUserData = @{
    user_id = "user02"
    password = "test"
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $nonExistentUserData

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "존재하지 않는 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 인증 실패"
} else {
    Add-TestResult -TestName "존재하지 않는 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# ========================================
# 2. 토큰 검증 테스트 (GET /auth/me)
# ========================================

Write-Host "`n🔍 2. 토큰 검증 테스트" -ForegroundColor Yellow

# 2-1. 유효한 사용자 토큰으로 프로필 조회
if ($ACCESS_TOKEN_USER) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/me" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "사용자 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "PASS" -Message "사용자 정보: $($result.Data.email)"
    } else {
        Add-TestResult -TestName "사용자 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 2-2. 유효한 관리자 토큰으로 프로필 조회
if ($ACCESS_TOKEN_ADMIN) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/me" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "PASS" -Message "관리자 정보: $($result.Data.email)"
    } else {
        Add-TestResult -TestName "관리자 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 2-3. 잘못된 토큰으로 프로필 조회
$headers = @{ "Authorization" = "Bearer invalid_token" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/me" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "잘못된 토큰 검증" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 인증 실패"
} else {
    Add-TestResult -TestName "잘못된 토큰 검증" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# 2-4. 토큰 없이 프로필 조회
$result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/me"

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "토큰 없이 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 인증 실패"
} else {
    Add-TestResult -TestName "토큰 없이 프로필 조회" -Method "GET" -Endpoint "/auth/me" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# ========================================
# 3. 조직 사용자 목록 조회 테스트 (GET /auth/organization/users)
# ========================================

Write-Host "`n👥 3. 조직 사용자 목록 조회 테스트" -ForegroundColor Yellow

# 3-1. 관리자 권한으로 조직 사용자 목록 조회
if ($ACCESS_TOKEN_ADMIN) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/organization/users" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 조직 사용자 목록 조회" -Method "GET" -Endpoint "/auth/organization/users" -StatusCode $result.StatusCode -Status "PASS" -Message "사용자 수: $($result.Data.users.Count)"
    } else {
        Add-TestResult -TestName "관리자 조직 사용자 목록 조회" -Method "GET" -Endpoint "/auth/organization/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 3-2. 일반 사용자 권한으로 조직 사용자 목록 조회 (권한 부족 예상)
if ($ACCESS_TOKEN_USER) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$AUTH_ENDPOINT/organization/users" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 사용자 목록 조회" -Method "GET" -Endpoint "/auth/organization/users" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 사용자 목록 조회" -Method "GET" -Endpoint "/auth/organization/users" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 4. 비밀번호 변경 테스트 (PUT /auth/change-password)
# ========================================

Write-Host "`n🔐 4. 비밀번호 변경 테스트" -ForegroundColor Yellow

# 4-1. 유효한 토큰으로 비밀번호 변경 (실제로는 변경하지 않음)
if ($ACCESS_TOKEN_USER) {
    $passwordChangeData = @{
        current_password = $TEST_USER.password
        new_password = "newtest123"
        confirm_password = "newtest123"
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$AUTH_ENDPOINT/change-password" -Headers $headers -Body $passwordChangeData
    
    if ($result.Success) {
        Add-TestResult -TestName "비밀번호 변경" -Method "PUT" -Endpoint "/auth/change-password" -StatusCode $result.StatusCode -Status "PASS" -Message "비밀번호 변경 성공"
        
        # 원래 비밀번호로 되돌리기
        $revertPasswordData = @{
            current_password = "newtest123"
            new_password = $TEST_USER.password
            confirm_password = $TEST_USER.password
        } | ConvertTo-Json
        
        Invoke-ApiRequest -Method "PUT" -Uri "$AUTH_ENDPOINT/change-password" -Headers $headers -Body $revertPasswordData | Out-Null
    } else {
        Add-TestResult -TestName "비밀번호 변경" -Method "PUT" -Endpoint "/auth/change-password" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 4-2. 잘못된 현재 비밀번호로 변경 시도
if ($ACCESS_TOKEN_USER) {
    $wrongCurrentPasswordData = @{
        current_password = "wrongcurrent"
        new_password = "newtest123"
        confirm_password = "newtest123"
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$AUTH_ENDPOINT/change-password" -Headers $headers -Body $wrongCurrentPasswordData
    
    if (!$result.Success -and $result.StatusCode -eq 400) {
        Add-TestResult -TestName "잘못된 현재 비밀번호로 변경" -Method "PUT" -Endpoint "/auth/change-password" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 변경 거부"
    } else {
        Add-TestResult -TestName "잘못된 현재 비밀번호로 변경" -Method "PUT" -Endpoint "/auth/change-password" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
    }
}

# ========================================
# 5. 로그아웃 테스트 (POST /auth/logout)
# ========================================

Write-Host "`n🚪 5. 로그아웃 테스트" -ForegroundColor Yellow

# 5-1. 유효한 토큰으로 로그아웃
if ($ACCESS_TOKEN_USER) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/logout" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "사용자 로그아웃" -Method "POST" -Endpoint "/auth/logout" -StatusCode $result.StatusCode -Status "PASS" -Message "로그아웃 성공"
    } else {
        Add-TestResult -TestName "사용자 로그아웃" -Method "POST" -Endpoint "/auth/logout" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 5-2. 토큰 없이 로그아웃 시도
$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/logout"

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "토큰 없이 로그아웃" -Method "POST" -Endpoint "/auth/logout" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 인증 실패"
} else {
    Add-TestResult -TestName "토큰 없이 로그아웃" -Method "POST" -Endpoint "/auth/logout" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# ========================================
# 6. 토큰 갱신 테스트 (POST /auth/refresh)
# ========================================

Write-Host "`n🔄 6. 토큰 갱신 테스트" -ForegroundColor Yellow

# 새로운 로그인으로 리프레시 토큰 획득
$loginData = @{
    email = $TEST_USER.email
    password = $TEST_USER.password
} | ConvertTo-Json

$loginResult = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $loginData

if ($loginResult.Success -and $loginResult.Data.refresh_token) {
    # 6-1. 유효한 리프레시 토큰으로 갱신
    $refreshData = @{
        refresh_token = $loginResult.Data.refresh_token
    } | ConvertTo-Json
    
    $result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/refresh" -Body $refreshData
    
    if ($result.Success) {
        Add-TestResult -TestName "토큰 갱신" -Method "POST" -Endpoint "/auth/refresh" -StatusCode $result.StatusCode -Status "PASS" -Message "새 토큰 발급 성공"
    } else {
        Add-TestResult -TestName "토큰 갱신" -Method "POST" -Endpoint "/auth/refresh" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 6-2. 잘못된 리프레시 토큰으로 갱신 시도
$invalidRefreshData = @{
    refresh_token = "invalid_refresh_token"
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/refresh" -Body $invalidRefreshData

if (!$result.Success -and $result.StatusCode -eq 401) {
    Add-TestResult -TestName "잘못된 리프레시 토큰 갱신" -Method "POST" -Endpoint "/auth/refresh" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 갱신 실패"
} else {
    Add-TestResult -TestName "잘못된 리프레시 토큰 갱신" -Method "POST" -Endpoint "/auth/refresh" -StatusCode $result.StatusCode -Status "FAIL" -Message "보안 취약점 발견"
}

# ========================================
# 테스트 결과 요약
# ========================================

Write-Host "`n📊 테스트 결과 요약" -ForegroundColor Cyan
Write-Host "=" * 50

$totalTests = $TEST_RESULTS.Count
$passedTests = ($TEST_RESULTS | Where-Object { $_.Status -eq "PASS" }).Count
$failedTests = ($TEST_RESULTS | Where-Object { $_.Status -eq "FAIL" }).Count

Write-Host "총 테스트: $totalTests" -ForegroundColor White
Write-Host "성공: $passedTests" -ForegroundColor Green
Write-Host "실패: $failedTests" -ForegroundColor Red
Write-Host "성공률: $([math]::Round(($passedTests / $totalTests) * 100, 2))%" -ForegroundColor Yellow

# 실패한 테스트 상세 정보
if ($failedTests -gt 0) {
    Write-Host "`n❌ 실패한 테스트 상세:" -ForegroundColor Red
    $TEST_RESULTS | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  - $($_.TestName): $($_.Message)" -ForegroundColor Red
    }
}

# 결과를 JSON 파일로 저장
$resultFile = "auth_router_test_results.json"
$TEST_RESULTS | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host "`n💾 테스트 결과가 '$resultFile'에 저장되었습니다." -ForegroundColor Green

Write-Host "`n🏁 인증 라우터 테스트 완료" -ForegroundColor Cyan