# ===================================================================
# SkyBoot Mail SaaS - Monitoring Router 테스트 시나리오
# ===================================================================
# 파일: monitoring_router_tests.ps1
# 설명: 모니터링 라우터의 모든 엔드포인트에 대한 종합적인 테스트
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

Write-ColorOutput "🚀 SkyBoot Mail Monitoring Router 테스트 시작" "Cyan"
Write-ColorOutput "📅 테스트 시작 시간: $TestStartTime" "Blue"
Write-ColorOutput "🌐 기본 URL: $BaseUrl" "Blue"
Write-ColorOutput "=" * 80 "Blue"

# ===================================================================
# 1. 사용자 로그인
# ===================================================================
Write-ColorOutput "`n🔐 1. 사용자 로그인" "Yellow"

# 1.1 일반 사용자 로그인
Write-ColorOutput "1.1 일반 사용자 로그인 (user01/test)" "White"
$loginData = @{
    user_id = "user01"
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

# 1.2 관리자 로그인
Write-ColorOutput "1.2 관리자 로그인 (admin01/test)" "White"
$adminLoginData = @{
    user_id = "admin01"
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
# 2. 모니터링 시스템 상태 확인 테스트
# ===================================================================
Write-ColorOutput "`n🔍 2. 모니터링 시스템 상태 확인 테스트" "Yellow"

if ($UserToken) {
    # 2.1 일반 사용자 상태 확인
    Write-ColorOutput "2.1 일반 사용자 상태 확인" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/health" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 모니터링 시스템 상태 확인 성공" "Green"
        Write-ColorOutput "   - 메시지: $($response.Content.message)" "Green"
        Add-TestResult -TestName "일반 사용자 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 모니터링 시스템 상태 확인 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "일반 사용자 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

if ($AdminToken) {
    # 2.2 관리자 상태 확인
    Write-ColorOutput "2.2 관리자 상태 확인" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/health" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 관리자 모니터링 시스템 상태 확인 성공" "Green"
        Write-ColorOutput "   - 메시지: $($response.Content.message)" "Green"
        Add-TestResult -TestName "관리자 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 관리자 모니터링 시스템 상태 확인 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "관리자 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# 2.3 인증 없이 상태 확인 시도 (실패 예상)
Write-ColorOutput "2.3 인증 없이 상태 확인 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/health"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 상태 확인" -Method "GET" -Endpoint "/monitoring/health" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 3. 사용량 통계 조회 테스트
# ===================================================================
Write-ColorOutput "`n📊 3. 사용량 통계 조회 테스트" "Yellow"

if ($UserToken) {
    # 3.1 기본 사용량 통계 조회
    Write-ColorOutput "3.1 기본 사용량 통계 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 사용량 통계 조회 성공" "Green"
        if ($response.Content.current_usage) {
            Write-ColorOutput "   - 현재 사용량 정보 포함됨" "Green"
        }
        if ($response.Content.limits) {
            Write-ColorOutput "   - 제한 정보 포함됨" "Green"
        }
        if ($response.Content.usage_percentages) {
            Write-ColorOutput "   - 사용률 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "기본 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 사용량 통계 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "기본 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.2 일일 통계 포함 사용량 조회
    Write-ColorOutput "3.2 일일 통계 포함 사용량 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage?include_daily=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 일일 통계 포함 사용량 조회 성공" "Green"
        if ($response.Content.daily_stats) {
            Write-ColorOutput "   - 일일 통계 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "일일 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 일일 통계 포함 사용량 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "일일 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.3 주간 통계 포함 사용량 조회
    Write-ColorOutput "3.3 주간 통계 포함 사용량 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage?include_weekly=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 주간 통계 포함 사용량 조회 성공" "Green"
        if ($response.Content.weekly_stats) {
            Write-ColorOutput "   - 주간 통계 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "주간 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 주간 통계 포함 사용량 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "주간 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.4 월간 통계 포함 사용량 조회
    Write-ColorOutput "3.4 월간 통계 포함 사용량 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage?include_monthly=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 월간 통계 포함 사용량 조회 성공" "Green"
        if ($response.Content.monthly_stats) {
            Write-ColorOutput "   - 월간 통계 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "월간 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 월간 통계 포함 사용량 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "월간 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.5 모든 통계 포함 사용량 조회
    Write-ColorOutput "3.5 모든 통계 포함 사용량 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage?include_daily=true&include_weekly=true&include_monthly=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 모든 통계 포함 사용량 조회 성공" "Green"
        $statsCount = 0
        if ($response.Content.daily_stats) { $statsCount++ }
        if ($response.Content.weekly_stats) { $statsCount++ }
        if ($response.Content.monthly_stats) { $statsCount++ }
        Write-ColorOutput "   - 포함된 통계 유형: $statsCount개" "Green"
        Add-TestResult -TestName "모든 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 모든 통계 포함 사용량 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "모든 통계 포함 사용량 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 4. 감사 로그 조회 테스트
# ===================================================================
Write-ColorOutput "`n📋 4. 감사 로그 조회 테스트" "Yellow"

if ($AdminToken) {
    # 4.1 기본 감사 로그 조회 (관리자)
    Write-ColorOutput "4.1 기본 감사 로그 조회 (관리자)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 감사 로그 조회 성공" "Green"
        if ($response.Content.logs) {
            Write-ColorOutput "   - 로그 수: $($response.Content.logs.Count)" "Green"
        }
        if ($response.Content.total) {
            Write-ColorOutput "   - 전체 로그 수: $($response.Content.total)" "Green"
        }
        if ($response.Content.page) {
            Write-ColorOutput "   - 현재 페이지: $($response.Content.page)" "Green"
        }
        Add-TestResult -TestName "기본 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 감사 로그 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "기본 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 4.2 페이징 감사 로그 조회
    Write-ColorOutput "4.2 페이징 감사 로그 조회 (페이지 1, 제한 10)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit?page=1&limit=10" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 페이징 감사 로그 조회 성공" "Green"
        if ($response.Content.logs) {
            Write-ColorOutput "   - 현재 페이지 로그 수: $($response.Content.logs.Count)" "Green"
        }
        Add-TestResult -TestName "페이징 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 페이징 감사 로그 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "페이징 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 4.3 날짜 범위 필터링 감사 로그 조회
    Write-ColorOutput "4.3 날짜 범위 필터링 감사 로그 조회" "White"
    $startDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ss")
    $endDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit?start_date=$startDate&end_date=$endDate" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 날짜 범위 필터링 감사 로그 조회 성공" "Green"
        if ($response.Content.filters) {
            Write-ColorOutput "   - 적용된 필터 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "날짜 범위 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 날짜 범위 필터링 감사 로그 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "날짜 범위 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 4.4 액션 타입 필터링 감사 로그 조회
    Write-ColorOutput "4.4 액션 타입 필터링 감사 로그 조회 (LOGIN)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit?action=LOGIN" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 액션 타입 필터링 감사 로그 조회 성공" "Green"
        Add-TestResult -TestName "액션 타입 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 액션 타입 필터링 감사 로그 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "액션 타입 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 4.5 리소스 타입 필터링 감사 로그 조회
    Write-ColorOutput "4.5 리소스 타입 필터링 감사 로그 조회 (email)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit?resource_type=email" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 리소스 타입 필터링 감사 로그 조회 성공" "Green"
        Add-TestResult -TestName "리소스 타입 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 리소스 타입 필터링 감사 로그 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "리소스 타입 필터링 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

if ($UserToken) {
    # 4.6 일반 사용자 감사 로그 조회 시도 (실패 예상)
    Write-ColorOutput "4.6 일반 사용자 감사 로그 조회 시도" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit" -Headers $UserHeaders
    
    if ($response.StatusCode -eq 403) {
        Write-ColorOutput "✅ 일반 사용자 감사 로그 접근 시 403 오류 정상 반환" "Green"
        Add-TestResult -TestName "일반 사용자 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "권한 없음"
    } else {
        Write-ColorOutput "❌ 일반 사용자 감사 로그 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "일반 사용자 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
}

# ===================================================================
# 5. 대시보드 데이터 조회 테스트
# ===================================================================
Write-ColorOutput "`n📊 5. 대시보드 데이터 조회 테스트" "Yellow"

if ($UserToken) {
    # 5.1 기본 대시보드 데이터 조회
    Write-ColorOutput "5.1 기본 대시보드 데이터 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 대시보드 데이터 조회 성공" "Green"
        if ($response.Content.usage_stats) {
            Write-ColorOutput "   - 사용량 통계 포함됨" "Green"
        }
        if ($response.Content.recent_activities) {
            Write-ColorOutput "   - 최근 활동 정보 포함됨" "Green"
        }
        if ($response.Content.system_status) {
            Write-ColorOutput "   - 시스템 상태 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "기본 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 대시보드 데이터 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "기본 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.2 캐시 새로고침 대시보드 데이터 조회
    Write-ColorOutput "5.2 캐시 새로고침 대시보드 데이터 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard?refresh_cache=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 캐시 새로고침 대시보드 데이터 조회 성공" "Green"
        Add-TestResult -TestName "캐시 새로고침 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 캐시 새로고침 대시보드 데이터 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "캐시 새로고침 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.3 알림 포함 대시보드 데이터 조회
    Write-ColorOutput "5.3 알림 포함 대시보드 데이터 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard?include_alerts=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 알림 포함 대시보드 데이터 조회 성공" "Green"
        if ($response.Content.alerts) {
            Write-ColorOutput "   - 알림 정보 포함됨" "Green"
        }
        Add-TestResult -TestName "알림 포함 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 알림 포함 대시보드 데이터 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "알림 포함 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.4 모든 옵션 포함 대시보드 데이터 조회
    Write-ColorOutput "5.4 모든 옵션 포함 대시보드 데이터 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard?refresh_cache=true&include_alerts=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 모든 옵션 포함 대시보드 데이터 조회 성공" "Green"
        Add-TestResult -TestName "모든 옵션 포함 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 모든 옵션 포함 대시보드 데이터 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "모든 옵션 포함 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

if ($AdminToken) {
    # 5.5 관리자 대시보드 데이터 조회
    Write-ColorOutput "5.5 관리자 대시보드 데이터 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard" -Headers $AdminHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 관리자 대시보드 데이터 조회 성공" "Green"
        Add-TestResult -TestName "관리자 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 관리자 대시보드 데이터 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "관리자 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 6. 권한 및 보안 테스트
# ===================================================================
Write-ColorOutput "`n🔒 6. 권한 및 보안 테스트" "Yellow"

# 6.1 인증 없이 사용량 통계 조회 시도
Write-ColorOutput "6.1 인증 없이 사용량 통계 조회 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 사용량 통계 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 사용량 통계 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 6.2 인증 없이 대시보드 데이터 조회 시도
Write-ColorOutput "6.2 인증 없이 대시보드 데이터 조회 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 대시보드 데이터 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 대시보드 데이터 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 대시보드 데이터 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 6.3 인증 없이 감사 로그 조회 시도
Write-ColorOutput "6.3 인증 없이 감사 로그 조회 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 감사 로그 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 감사 로그 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 감사 로그 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 6.4 잘못된 토큰으로 접근 시도
Write-ColorOutput "6.4 잘못된 토큰으로 사용량 통계 조회 시도" "White"
$invalidHeaders = @{ "Authorization" = "Bearer invalid-token-12345" }
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage" -Headers $invalidHeaders

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 잘못된 토큰으로 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "잘못된 토큰으로 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 토큰"
} else {
    Write-ColorOutput "❌ 잘못된 토큰으로 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "잘못된 토큰으로 사용량 통계 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 7. 성능 및 부하 테스트
# ===================================================================
Write-ColorOutput "`n⚡ 7. 성능 및 부하 테스트" "Yellow"

if ($UserToken) {
    # 7.1 사용량 통계 연속 조회 (부하 테스트)
    Write-ColorOutput "7.1 사용량 통계 연속 조회 (5회)" "White"
    $successCount = 0
    $totalTime = 0
    
    for ($i = 1; $i -le 5; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/usage" -Headers $UserHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $totalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $successCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $averageTime = $totalTime / 5
    Write-ColorOutput "✅ 사용량 통계 연속 조회 완료 - 성공: $successCount/5, 평균 응답시간: $([math]::Round($averageTime, 2))ms" "Green"
    Add-TestResult -TestName "사용량 통계 연속 조회" -Method "GET" -Endpoint "/monitoring/usage" -StatusCode 200 -Status "성공" -Details "성공률: $successCount/5, 평균 응답시간: $([math]::Round($averageTime, 2))ms"
    
    # 7.2 대시보드 데이터 연속 조회 (부하 테스트)
    Write-ColorOutput "7.2 대시보드 데이터 연속 조회 (5회)" "White"
    $dashboardSuccessCount = 0
    $dashboardTotalTime = 0
    
    for ($i = 1; $i -le 5; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/dashboard" -Headers $UserHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $dashboardTotalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $dashboardSuccessCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $dashboardAverageTime = $dashboardTotalTime / 5
    Write-ColorOutput "✅ 대시보드 데이터 연속 조회 완료 - 성공: $dashboardSuccessCount/5, 평균 응답시간: $([math]::Round($dashboardAverageTime, 2))ms" "Green"
    Add-TestResult -TestName "대시보드 데이터 연속 조회" -Method "GET" -Endpoint "/monitoring/dashboard" -StatusCode 200 -Status "성공" -Details "성공률: $dashboardSuccessCount/5, 평균 응답시간: $([math]::Round($dashboardAverageTime, 2))ms"
}

if ($AdminToken) {
    # 7.3 감사 로그 연속 조회 (부하 테스트)
    Write-ColorOutput "7.3 감사 로그 연속 조회 (3회)" "White"
    $auditSuccessCount = 0
    $auditTotalTime = 0
    
    for ($i = 1; $i -le 3; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/monitoring/audit?limit=10" -Headers $AdminHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $auditTotalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $auditSuccessCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $auditAverageTime = $auditTotalTime / 3
    Write-ColorOutput "✅ 감사 로그 연속 조회 완료 - 성공: $auditSuccessCount/3, 평균 응답시간: $([math]::Round($auditAverageTime, 2))ms" "Green"
    Add-TestResult -TestName "감사 로그 연속 조회" -Method "GET" -Endpoint "/monitoring/audit" -StatusCode 200 -Status "성공" -Details "성공률: $auditSuccessCount/3, 평균 응답시간: $([math]::Round($auditAverageTime, 2))ms"
}

# ===================================================================
# 8. 테스트 결과 요약 및 저장
# ===================================================================
Write-ColorOutput "`n📊 8. 테스트 결과 요약" "Yellow"

$TestEndTime = Get-Date
$TotalDuration = $TestEndTime - $TestStartTime
$TotalTests = $TestResults.Count
$SuccessfulTests = ($TestResults | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
$FailedTests = ($TestResults | Where-Object { $_.Status -eq "실패" }).Count
$SkippedTests = ($TestResults | Where-Object { $_.Status -eq "건너뜀" }).Count

Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "🎯 SkyBoot Mail Monitoring Router 테스트 완료" "Cyan"
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
$ResultsPath = "C:\Users\moon4\skyboot.mail2\test\monitoring_router_test_results.json"
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
Write-ColorOutput "🏁 Monitoring Router 테스트 스크립트 실행 완료" "Cyan"