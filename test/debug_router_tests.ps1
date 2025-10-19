# ===================================================================
# SkyBoot Mail SaaS - Debug Router 테스트 시나리오
# ===================================================================
# 파일: debug_router_tests.ps1
# 설명: 디버그 라우터의 모든 엔드포인트에 대한 종합적인 테스트
# 작성일: 2024-01-20
# ===================================================================

# 테스트 설정
$BaseUrl = "http://localhost:8001/api/v1"
$TestResults = @()
$TestStartTime = Get-Date

# 색상 출력 함수
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Magenta" = [ConsoleColor]::Magenta
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# 테스트 결과 기록 함수
function Add-TestResult {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Endpoint,
        [int]$StatusCode,
        [string]$Status,
        [string]$Details = "",
        [object]$Response = $null
    )
    
    $script:TestResults += [PSCustomObject]@{
        TestName = $TestName
        Method = $Method
        Endpoint = $Endpoint
        StatusCode = $StatusCode
        Status = $Status
        Details = $Details
        Response = $Response
        Timestamp = Get-Date
    }
}

# HTTP 요청 함수
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
            ContentType = $ContentType
            UseBasicParsing = $true
        }
        
        if ($Body -and $Method -in @("POST", "PUT", "PATCH")) {
            if ($Body -is [string]) {
                $params.Body = $Body
            } else {
                $params.Body = $Body | ConvertTo-Json -Depth 10
            }
        }
        
        $response = Invoke-WebRequest @params
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content | ConvertFrom-Json
            Headers = $response.Headers
        }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { 
            [int]$_.Exception.Response.StatusCode 
        } else { 
            0 
        }
        
        $errorContent = if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $errorBody = $reader.ReadToEnd()
                $reader.Close()
                $stream.Close()
                $errorBody | ConvertFrom-Json
            }
            catch {
                @{ detail = $_.Exception.Message }
            }
        } else {
            @{ detail = $_.Exception.Message }
        }
        
        return @{
            Success = $false
            StatusCode = $statusCode
            Content = $errorContent
            Error = $_.Exception.Message
        }
    }
}

Write-ColorOutput "🚀 SkyBoot Mail Debug Router 테스트 시작" "Cyan"
Write-ColorOutput "📅 테스트 시작 시간: $TestStartTime" "Blue"
Write-ColorOutput "🌐 기본 URL: $BaseUrl" "Blue"
Write-ColorOutput "=" * 80 "Blue"

# ===================================================================
# 1. 대시보드 테스트 데이터 조회 테스트
# ===================================================================
Write-ColorOutput "`n📊 1. 대시보드 테스트 데이터 조회 테스트" "Yellow"

# 1.1 대시보드 테스트 데이터 조회 (인증 없이)
Write-ColorOutput "1.1 대시보드 테스트 데이터 조회 (인증 없이)" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/dashboard-test"

if ($response.Success -and $response.StatusCode -eq 200) {
    Write-ColorOutput "✅ 대시보드 테스트 데이터 조회 성공" "Green"
    Write-ColorOutput "   - 시스템 상태: $($response.Content.system_status.status)" "Green"
    Write-ColorOutput "   - 서비스 수: $($response.Content.system_status.services.Count)" "Green"
    Write-ColorOutput "   - 사용량 통계 항목: $($response.Content.usage_stats.Count)" "Green"
    Write-ColorOutput "   - 실시간 로그 수: $($response.Content.realtime_logs.Count)" "Green"
    Add-TestResult -TestName "대시보드 테스트 데이터 조회" -Method "GET" -Endpoint "/debug/dashboard-test" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
} else {
    Write-ColorOutput "❌ 대시보드 테스트 데이터 조회 실패: $($response.Content.detail)" "Red"
    Add-TestResult -TestName "대시보드 테스트 데이터 조회" -Method "GET" -Endpoint "/debug/dashboard-test" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
}

# ===================================================================
# 2. 사용자 로그인 (컨텍스트 테스트용)
# ===================================================================
Write-ColorOutput "`n🔐 2. 사용자 로그인 (컨텍스트 테스트용)" "Yellow"

# 2.1 일반 사용자 로그인
Write-ColorOutput "2.1 일반 사용자 로그인 (user01/test)" "White"
$loginData = @{
    username = "user01"
    password = "test"
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/auth/login" -Body $loginData

if ($response.Success -and $response.StatusCode -eq 200) {
    $UserToken = $response.Content.access_token
    $UserHeaders = @{ "Authorization" = "Bearer $UserToken" }
    Write-ColorOutput "✅ 일반 사용자 로그인 성공" "Green"
    Write-ColorOutput "   - 토큰 타입: $($response.Content.token_type)" "Green"
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Status "성공"
} else {
    Write-ColorOutput "❌ 일반 사용자 로그인 실패: $($response.Content.detail)" "Red"
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    $UserToken = $null
    $UserHeaders = @{}
}

# 2.2 관리자 로그인
Write-ColorOutput "2.2 관리자 로그인 (admin01/test)" "White"
$adminLoginData = @{
    username = "admin01"
    password = "test"
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/auth/login" -Body $adminLoginData

if ($response.Success -and $response.StatusCode -eq 200) {
    $AdminToken = $response.Content.access_token
    $AdminHeaders = @{ "Authorization" = "Bearer $AdminToken" }
    Write-ColorOutput "✅ 관리자 로그인 성공" "Green"
    Write-ColorOutput "   - 토큰 타입: $($response.Content.token_type)" "Green"
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Status "성공"
} else {
    Write-ColorOutput "❌ 관리자 로그인 실패: $($response.Content.detail)" "Red"
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    $AdminToken = $null
    $AdminHeaders = @{}
}

# ===================================================================
# 3. 컨텍스트 디버그 정보 조회 테스트
# ===================================================================
Write-ColorOutput "`n🔍 3. 컨텍스트 디버그 정보 조회 테스트" "Yellow"

if ($UserToken) {
    # 3.1 일반 사용자 컨텍스트 디버그 정보 조회
    Write-ColorOutput "3.1 일반 사용자 컨텍스트 디버그 정보 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 일반 사용자 컨텍스트 디버그 정보 조회 성공" "Green"
        Write-ColorOutput "   - 사용자 이메일: $($response.Content.current_user.email)" "Green"
        Write-ColorOutput "   - 사용자 UUID: $($response.Content.current_user.user_uuid)" "Green"
        Write-ColorOutput "   - 조직 ID: $($response.Content.current_user.org_id)" "Green"
        Write-ColorOutput "   - 사용자 역할: $($response.Content.current_user.role)" "Green"
        Write-ColorOutput "   - URL 경로: $($response.Content.url.path)" "Green"
        Add-TestResult -TestName "일반 사용자 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 일반 사용자 컨텍스트 디버그 정보 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "일반 사용자 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

if ($AdminToken) {
    # 3.2 관리자 컨텍스트 디버그 정보 조회
    Write-ColorOutput "3.2 관리자 컨텍스트 디버그 정보 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 관리자 컨텍스트 디버그 정보 조회 성공" "Green"
        Write-ColorOutput "   - 사용자 이메일: $($response.Content.current_user.email)" "Green"
        Write-ColorOutput "   - 사용자 UUID: $($response.Content.current_user.user_uuid)" "Green"
        Write-ColorOutput "   - 조직 ID: $($response.Content.current_user.org_id)" "Green"
        Write-ColorOutput "   - 사용자 역할: $($response.Content.current_user.role)" "Green"
        Write-ColorOutput "   - URL 경로: $($response.Content.url.path)" "Green"
        Add-TestResult -TestName "관리자 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 관리자 컨텍스트 디버그 정보 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "관리자 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# 3.3 인증 없이 컨텍스트 디버그 정보 조회 시도 (실패 예상)
Write-ColorOutput "3.3 인증 없이 컨텍스트 디버그 정보 조회 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 컨텍스트 디버그 정보 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 4. 조직 생성 테스트 (디버그용)
# ===================================================================
Write-ColorOutput "`n🏢 4. 조직 생성 테스트 (디버그용)" "Yellow"

# 4.1 새 조직 생성
Write-ColorOutput "4.1 새 조직 생성" "White"
$orgData = @{
    name = "테스트 조직 $(Get-Date -Format 'yyyyMMddHHmmss')"
    org_code = "TEST$(Get-Date -Format 'HHmmss')"
    domain = "test$(Get-Date -Format 'HHmmss').example.com"
    max_users = 50
    is_active = $true
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-organization" -Body $orgData

if ($response.Success -and $response.StatusCode -eq 200) {
    $CreatedOrgId = $response.Content.org_id
    Write-ColorOutput "✅ 조직 생성 성공" "Green"
    Write-ColorOutput "   - 조직 ID: $($response.Content.org_id)" "Green"
    Write-ColorOutput "   - 조직명: $($response.Content.name)" "Green"
    Write-ColorOutput "   - 조직 코드: $($response.Content.org_code)" "Green"
    Write-ColorOutput "   - 도메인: $($response.Content.domain)" "Green"
    Write-ColorOutput "   - 최대 사용자: $($response.Content.max_users)" "Green"
    Add-TestResult -TestName "조직 생성" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
} else {
    Write-ColorOutput "❌ 조직 생성 실패: $($response.Content.detail)" "Red"
    Add-TestResult -TestName "조직 생성" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    $CreatedOrgId = $null
}

# 4.2 중복 조직 생성 시도 (실패 예상)
Write-ColorOutput "4.2 중복 조직 생성 시도" "White"
$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-organization" -Body $orgData

if ($response.StatusCode -eq 400) {
    Write-ColorOutput "✅ 중복 조직 생성 시 400 오류 정상 반환" "Green"
    Add-TestResult -TestName "중복 조직 생성 시도" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "중복 조직"
} else {
    Write-ColorOutput "❌ 중복 조직 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "중복 조직 생성 시도" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 4.3 잘못된 데이터로 조직 생성 시도
Write-ColorOutput "4.3 잘못된 데이터로 조직 생성 시도" "White"
$invalidOrgData = @{
    name = ""  # 빈 이름
    org_code = "INVALID"
    domain = "invalid-domain"  # 잘못된 도메인 형식
    max_users = -1  # 음수 값
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-organization" -Body $invalidOrgData

if ($response.StatusCode -in @(400, 422)) {
    Write-ColorOutput "✅ 잘못된 데이터로 조직 생성 시 오류 정상 반환" "Green"
    Add-TestResult -TestName "잘못된 데이터로 조직 생성" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 데이터"
} else {
    Write-ColorOutput "❌ 잘못된 데이터로 조직 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "잘못된 데이터로 조직 생성" -Method "POST" -Endpoint "/debug/create-organization" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 5. 사용자 생성 테스트 (디버그용)
# ===================================================================
Write-ColorOutput "`n👤 5. 사용자 생성 테스트 (디버그용)" "Yellow"

if ($CreatedOrgId) {
    # 5.1 새 사용자 생성
    Write-ColorOutput "5.1 새 사용자 생성" "White"
    $userData = @{
        email = "testuser$(Get-Date -Format 'HHmmss')@test.com"
        password = "testpassword123"
        full_name = "테스트 사용자"
        org_id = $CreatedOrgId
        role = "user"
        is_active = $true
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-user" -Body $userData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        $CreatedUserId = $response.Content.user_id
        Write-ColorOutput "✅ 사용자 생성 성공" "Green"
        Write-ColorOutput "   - 사용자 ID: $($response.Content.user_id)" "Green"
        Write-ColorOutput "   - 사용자 UUID: $($response.Content.user_uuid)" "Green"
        Write-ColorOutput "   - 이메일: $($response.Content.email)" "Green"
        Write-ColorOutput "   - 사용자명: $($response.Content.username)" "Green"
        Write-ColorOutput "   - 조직 ID: $($response.Content.org_id)" "Green"
        Write-ColorOutput "   - 역할: $($response.Content.role)" "Green"
        Add-TestResult -TestName "사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 사용자 생성 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        $CreatedUserId = $null
    }
    
    # 5.2 중복 사용자 생성 시도 (실패 예상)
    Write-ColorOutput "5.2 중복 사용자 생성 시도" "White"
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-user" -Body $userData
    
    if ($response.StatusCode -eq 400) {
        Write-ColorOutput "✅ 중복 사용자 생성 시 400 오류 정상 반환" "Green"
        Add-TestResult -TestName "중복 사용자 생성 시도" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "중복 사용자"
    } else {
        Write-ColorOutput "❌ 중복 사용자 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "중복 사용자 생성 시도" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
} else {
    Write-ColorOutput "⚠️ 조직이 생성되지 않아 사용자 생성 테스트를 건너뜁니다" "Yellow"
    Add-TestResult -TestName "사용자 생성 테스트" -Method "POST" -Endpoint "/debug/create-user" -StatusCode 0 -Status "건너뜀" -Details "조직 생성 실패로 인한 건너뜀"
}

# 5.3 존재하지 않는 조직으로 사용자 생성 시도
Write-ColorOutput "5.3 존재하지 않는 조직으로 사용자 생성 시도" "White"
$invalidUserData = @{
    email = "invalid$(Get-Date -Format 'HHmmss')@test.com"
    password = "testpassword123"
    full_name = "잘못된 사용자"
    org_id = "non-existent-org-id"
    role = "user"
    is_active = $true
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-user" -Body $invalidUserData

if ($response.StatusCode -eq 404) {
    Write-ColorOutput "✅ 존재하지 않는 조직으로 사용자 생성 시 404 오류 정상 반환" "Green"
    Add-TestResult -TestName "존재하지 않는 조직으로 사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "존재하지 않는 조직"
} else {
    Write-ColorOutput "❌ 존재하지 않는 조직으로 사용자 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "존재하지 않는 조직으로 사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 5.4 잘못된 이메일 형식으로 사용자 생성 시도
Write-ColorOutput "5.4 잘못된 이메일 형식으로 사용자 생성 시도" "White"
$invalidEmailUserData = @{
    email = "invalid-email-format"  # 잘못된 이메일 형식
    password = "testpassword123"
    full_name = "잘못된 이메일 사용자"
    org_id = if ($CreatedOrgId) { $CreatedOrgId } else { "test-org-id" }
    role = "user"
    is_active = $true
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/debug/create-user" -Body $invalidEmailUserData

if ($response.StatusCode -in @(400, 422)) {
    Write-ColorOutput "✅ 잘못된 이메일 형식으로 사용자 생성 시 오류 정상 반환" "Green"
    Add-TestResult -TestName "잘못된 이메일 형식으로 사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 이메일 형식"
} else {
    Write-ColorOutput "❌ 잘못된 이메일 형식으로 사용자 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "잘못된 이메일 형식으로 사용자 생성" -Method "POST" -Endpoint "/debug/create-user" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 6. 권한 및 보안 테스트
# ===================================================================
Write-ColorOutput "`n🔒 6. 권한 및 보안 테스트" "Yellow"

# 6.1 잘못된 토큰으로 컨텍스트 디버그 정보 조회 시도
Write-ColorOutput "6.1 잘못된 토큰으로 컨텍스트 디버그 정보 조회 시도" "White"
$invalidHeaders = @{ "Authorization" = "Bearer invalid-token-12345" }
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context" -Headers $invalidHeaders

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 잘못된 토큰으로 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "잘못된 토큰으로 컨텍스트 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 토큰"
} else {
    Write-ColorOutput "❌ 잘못된 토큰으로 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "잘못된 토큰으로 컨텍스트 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 6.2 만료된 토큰으로 접근 시도 (시뮬레이션)
Write-ColorOutput "6.2 만료된 토큰으로 접근 시도" "White"
$expiredHeaders = @{ "Authorization" = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjA5NDU5MjAwfQ.expired" }
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context" -Headers $expiredHeaders

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 만료된 토큰으로 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "만료된 토큰으로 컨텍스트 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "만료된 토큰"
} else {
    Write-ColorOutput "❌ 만료된 토큰으로 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "만료된 토큰으로 컨텍스트 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 7. 성능 및 부하 테스트
# ===================================================================
Write-ColorOutput "`n⚡ 7. 성능 및 부하 테스트" "Yellow"

# 7.1 대시보드 테스트 데이터 연속 조회 (부하 테스트)
Write-ColorOutput "7.1 대시보드 테스트 데이터 연속 조회 (10회)" "White"
$successCount = 0
$totalTime = 0

for ($i = 1; $i -le 10; $i++) {
    $startTime = Get-Date
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/dashboard-test"
    $endTime = Get-Date
    $responseTime = ($endTime - $startTime).TotalMilliseconds
    $totalTime += $responseTime
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        $successCount++
    }
    
    Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
}

$averageTime = $totalTime / 10
Write-ColorOutput "✅ 연속 조회 완료 - 성공: $successCount/10, 평균 응답시간: $([math]::Round($averageTime, 2))ms" "Green"
Add-TestResult -TestName "대시보드 데이터 연속 조회" -Method "GET" -Endpoint "/debug/dashboard-test" -StatusCode 200 -Status "성공" -Details "성공률: $successCount/10, 평균 응답시간: $([math]::Round($averageTime, 2))ms"

if ($UserToken) {
    # 7.2 컨텍스트 디버그 정보 연속 조회 (부하 테스트)
    Write-ColorOutput "7.2 컨텍스트 디버그 정보 연속 조회 (5회)" "White"
    $contextSuccessCount = 0
    $contextTotalTime = 0
    
    for ($i = 1; $i -le 5; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/debug/context" -Headers $UserHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $contextTotalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $contextSuccessCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $contextAverageTime = $contextTotalTime / 5
    Write-ColorOutput "✅ 컨텍스트 연속 조회 완료 - 성공: $contextSuccessCount/5, 평균 응답시간: $([math]::Round($contextAverageTime, 2))ms" "Green"
    Add-TestResult -TestName "컨텍스트 디버그 정보 연속 조회" -Method "GET" -Endpoint "/debug/context" -StatusCode 200 -Status "성공" -Details "성공률: $contextSuccessCount/5, 평균 응답시간: $([math]::Round($contextAverageTime, 2))ms"
}

# ===================================================================
# 8. 테스트 후 리소스 정리
# ===================================================================
Write-ColorOutput "`n🧹 8. 테스트 후 리소스 정리" "Yellow"

# 참고: 실제 운영 환경에서는 디버그용으로 생성된 리소스를 정리하는 API가 필요할 수 있습니다.
# 현재는 디버그 라우터에 삭제 기능이 없으므로 정리 과정을 건너뜁니다.
Write-ColorOutput "⚠️ 디버그 라우터에 리소스 삭제 기능이 없어 수동 정리가 필요합니다" "Yellow"
Write-ColorOutput "   - 생성된 조직 ID: $CreatedOrgId" "Yellow"
if ($CreatedUserId) {
    Write-ColorOutput "   - 생성된 사용자 ID: $CreatedUserId" "Yellow"
}

Add-TestResult -TestName "리소스 정리" -Method "N/A" -Endpoint "N/A" -StatusCode 0 -Status "건너뜀" -Details "디버그 라우터에 삭제 기능 없음"

# ===================================================================
# 9. 테스트 결과 요약 및 저장
# ===================================================================
Write-ColorOutput "`n📊 9. 테스트 결과 요약" "Yellow"

$TestEndTime = Get-Date
$TotalDuration = $TestEndTime - $TestStartTime
$TotalTests = $TestResults.Count
$SuccessfulTests = ($TestResults | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
$FailedTests = ($TestResults | Where-Object { $_.Status -eq "실패" }).Count
$SkippedTests = ($TestResults | Where-Object { $_.Status -eq "건너뜀" }).Count

Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "🎯 SkyBoot Mail Debug Router 테스트 완료" "Cyan"
Write-ColorOutput "📅 테스트 종료 시간: $TestEndTime" "Blue"
Write-ColorOutput "⏱️ 총 소요 시간: $($TotalDuration.TotalSeconds) 초" "Blue"
Write-ColorOutput "📈 테스트 결과:" "Blue"
Write-ColorOutput "   - 총 테스트: $TotalTests" "White"
Write-ColorOutput "   - 성공: $SuccessfulTests" "Green"
Write-ColorOutput "   - 실패: $FailedTests" "Red"
Write-ColorOutput "   - 건너뜀: $SkippedTests" "Yellow"
Write-ColorOutput "   - 성공률: $([math]::Round(($SuccessfulTests / $TotalTests) * 100, 2))%" "Cyan"

# 실패한 테스트 상세 정보
if ($FailedTests -gt 0) {
    Write-ColorOutput "`n❌ 실패한 테스트 상세:" "Red"
    $TestResults | Where-Object { $_.Status -eq "실패" } | ForEach-Object {
        Write-ColorOutput "   - $($_.TestName): $($_.Details)" "Red"
    }
}

# 테스트 결과를 JSON 파일로 저장
$ResultsPath = "C:\Users\moon4\skyboot.mail2\test\debug_router_test_results.json"
$TestSummary = @{
    TestInfo = @{
        StartTime = $TestStartTime
        EndTime = $TestEndTime
        Duration = $TotalDuration.TotalSeconds
        BaseUrl = $BaseUrl
    }
    Summary = @{
        TotalTests = $TotalTests
        SuccessfulTests = $SuccessfulTests
        FailedTests = $FailedTests
        SkippedTests = $SkippedTests
        SuccessRate = [math]::Round(($SuccessfulTests / $TotalTests) * 100, 2)
    }
    DetailedResults = $TestResults
}

try {
    $TestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $ResultsPath -Encoding UTF8
    Write-ColorOutput "💾 테스트 결과가 저장되었습니다: $ResultsPath" "Green"
} catch {
    Write-ColorOutput "❌ 테스트 결과 저장 실패: $($_.Exception.Message)" "Red"
}

Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "🏁 Debug Router 테스트 스크립트 실행 완료" "Cyan"