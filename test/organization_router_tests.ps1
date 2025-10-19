# ========================================
# 조직 관리 라우터 테스트 시나리오 (organization_router.py)
# SkyBoot Mail SaaS - 다중 조직 지원 메일서버
# ========================================

# 테스트 설정
$BASE_URL = "http://localhost:8001/api/v1"
$ORG_ENDPOINT = "$BASE_URL/organizations"
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
$TEST_ORG_ID = ""

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

Write-Host "🏢 조직 관리 라우터 테스트 시작" -ForegroundColor Cyan
Write-Host "=" * 50

# ========================================
# 사전 준비: 인증 토큰 획득
# ========================================

Write-Host "`n🔐 사전 준비: 인증 토큰 획득" -ForegroundColor Yellow

# 일반 사용자 로그인
$loginData = @{
    userId = $TEST_USER.userId
    password = $TEST_USER.password
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $loginData
if ($result.Success) {
    $ACCESS_TOKEN_USER = $result.Data.access_token
    Write-Host "✅ 일반 사용자 토큰 획득 성공" -ForegroundColor Green
} else {
    Write-Host "❌ 일반 사용자 로그인 실패: $($result.Error)" -ForegroundColor Red
    exit 1
}

# 관리자 로그인
$adminLoginData = @{
    userId = $TEST_ADMIN.userId
    password = $TEST_ADMIN.password
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Uri "$AUTH_ENDPOINT/login" -Body $adminLoginData
if ($result.Success) {
    $ACCESS_TOKEN_ADMIN = $result.Data.access_token
    Write-Host "✅ 관리자 토큰 획득 성공" -ForegroundColor Green
} else {
    Write-Host "❌ 관리자 로그인 실패: $($result.Error)" -ForegroundColor Red
    exit 1
}

# ========================================
# 1. 조직 생성 테스트 (POST /organizations)
# ========================================

Write-Host "`n🏗️ 1. 조직 생성 테스트" -ForegroundColor Yellow

# 1-1. 관리자 권한으로 조직 생성
$newOrgData = @{
    name = "테스트 조직"
    domain = "testorg.com"
    description = "테스트용 조직입니다"
    max_users = 50
    max_storage_gb = 100
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$ORG_ENDPOINT" -Headers $headers -Body $newOrgData

if ($result.Success) {
    $TEST_ORG_ID = $result.Data.org_uuid
    Add-TestResult -TestName "관리자 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "PASS" -Message "조직 ID: $TEST_ORG_ID"
} else {
    Add-TestResult -TestName "관리자 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-2. 일반 사용자 권한으로 조직 생성 시도 (권한 부족 예상)
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$ORG_ENDPOINT" -Headers $headers -Body $newOrgData

if (!$result.Success -and $result.StatusCode -eq 403) {
    Add-TestResult -TestName "일반 사용자 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
} else {
    Add-TestResult -TestName "일반 사용자 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
}

# 1-3. 중복 도메인으로 조직 생성 시도
$duplicateDomainData = @{
    name = "중복 도메인 조직"
    domain = "testorg.com"  # 위에서 사용한 도메인과 동일
    description = "중복 도메인 테스트"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$ORG_ENDPOINT" -Headers $headers -Body $duplicateDomainData

if (!$result.Success -and $result.StatusCode -eq 400) {
    Add-TestResult -TestName "중복 도메인 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 중복 거부"
} else {
    Add-TestResult -TestName "중복 도메인 조직 생성" -Method "POST" -Endpoint "/organizations" -StatusCode $result.StatusCode -Status "FAIL" -Message "중복 검증 실패"
}

# ========================================
# 2. 조직 목록 조회 테스트 (GET /organizations/list)
# ========================================

Write-Host "`n📋 2. 조직 목록 조회 테스트" -ForegroundColor Yellow

# 2-1. 관리자 권한으로 조직 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/list" -Headers $headers

if ($result.Success) {
    $orgCount = $result.Data.organizations.Count
    Add-TestResult -TestName "관리자 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "PASS" -Message "조직 수: $orgCount"
} else {
    Add-TestResult -TestName "관리자 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-2. 페이징 파라미터로 조직 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/list?page=1&limit=5" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "페이징 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "PASS" -Message "페이지: $($result.Data.page), 제한: $($result.Data.limit)"
} else {
    Add-TestResult -TestName "페이징 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-3. 검색 파라미터로 조직 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/list?search=테스트" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "검색 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "PASS" -Message "검색 결과: $($result.Data.organizations.Count)개"
} else {
    Add-TestResult -TestName "검색 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-4. 일반 사용자 권한으로 조직 목록 조회 시도 (권한 부족 예상)
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/list" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 403) {
    Add-TestResult -TestName "일반 사용자 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
} else {
    Add-TestResult -TestName "일반 사용자 조직 목록 조회" -Method "GET" -Endpoint "/organizations/list" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
}

# ========================================
# 3. 현재 조직 정보 조회 테스트 (GET /organizations/current)
# ========================================

Write-Host "`n🏢 3. 현재 조직 정보 조회 테스트" -ForegroundColor Yellow

# 3-1. 일반 사용자 권한으로 현재 조직 정보 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "사용자 현재 조직 정보 조회" -Method "GET" -Endpoint "/organizations/current" -StatusCode $result.StatusCode -Status "PASS" -Message "조직명: $($result.Data.name)"
} else {
    Add-TestResult -TestName "사용자 현재 조직 정보 조회" -Method "GET" -Endpoint "/organizations/current" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 3-2. 관리자 권한으로 현재 조직 정보 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 현재 조직 정보 조회" -Method "GET" -Endpoint "/organizations/current" -StatusCode $result.StatusCode -Status "PASS" -Message "조직명: $($result.Data.name)"
} else {
    Add-TestResult -TestName "관리자 현재 조직 정보 조회" -Method "GET" -Endpoint "/organizations/current" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 4. 특정 조직 정보 조회 테스트 (GET /organizations/{org_id})
# ========================================

Write-Host "`n🔍 4. 특정 조직 정보 조회 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 4-1. 관리자 권한으로 특정 조직 정보 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 특정 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "조직명: $($result.Data.name)"
    } else {
        Add-TestResult -TestName "관리자 특정 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 4-2. 일반 사용자 권한으로 다른 조직 정보 조회 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 다른 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 다른 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# 4-3. 존재하지 않는 조직 ID로 조회 시도
$fakeOrgId = "12345678-1234-1234-1234-123456789012"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$fakeOrgId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 조직 정보 조회" -Method "GET" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
}

# ========================================
# 5. 조직 정보 수정 테스트 (PUT /organizations/{org_id})
# ========================================

Write-Host "`n✏️ 5. 조직 정보 수정 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 5-1. 관리자 권한으로 조직 정보 수정
    $updateData = @{
        name = "수정된 테스트 조직"
        description = "수정된 설명입니다"
        max_users = 75
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID" -Headers $headers -Body $updateData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 조직 정보 수정" -Method "PUT" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "수정된 조직명: $($result.Data.name)"
    } else {
        Add-TestResult -TestName "관리자 조직 정보 수정" -Method "PUT" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 5-2. 일반 사용자 권한으로 조직 정보 수정 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID" -Headers $headers -Body $updateData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 정보 수정" -Method "PUT" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 정보 수정" -Method "PUT" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 6. 조직 통계 조회 테스트 (GET /organizations/{org_id}/stats)
# ========================================

Write-Host "`n📊 6. 조직 통계 조회 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 6-1. 관리자 권한으로 조직 통계 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/stats" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 조직 통계 조회" -Method "GET" -Endpoint "/organizations/{org_id}/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "통계 데이터 조회 성공"
    } else {
        Add-TestResult -TestName "관리자 조직 통계 조회" -Method "GET" -Endpoint "/organizations/{org_id}/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 6-2. 일반 사용자 권한으로 조직 통계 조회 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/stats" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 통계 조회" -Method "GET" -Endpoint "/organizations/{org_id}/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 통계 조회" -Method "GET" -Endpoint "/organizations/{org_id}/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 7. 현재 조직 통계 조회 테스트 (GET /organizations/current/stats)
# ========================================

Write-Host "`n📈 7. 현재 조직 통계 조회 테스트" -ForegroundColor Yellow

# 7-1. 일반 사용자 권한으로 현재 조직 통계 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current/stats" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "사용자 현재 조직 통계 조회" -Method "GET" -Endpoint "/organizations/current/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "현재 조직 통계 조회 성공"
} else {
    Add-TestResult -TestName "사용자 현재 조직 통계 조회" -Method "GET" -Endpoint "/organizations/current/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 7-2. 관리자 권한으로 현재 조직 통계 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current/stats" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 현재 조직 통계 조회" -Method "GET" -Endpoint "/organizations/current/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "현재 조직 통계 조회 성공"
} else {
    Add-TestResult -TestName "관리자 현재 조직 통계 조회" -Method "GET" -Endpoint "/organizations/current/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 8. 조직 설정 조회 테스트 (GET /organizations/{org_id}/settings)
# ========================================

Write-Host "`n⚙️ 8. 조직 설정 조회 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 8-1. 관리자 권한으로 조직 설정 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/settings" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 조직 설정 조회" -Method "GET" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "설정 데이터 조회 성공"
    } else {
        Add-TestResult -TestName "관리자 조직 설정 조회" -Method "GET" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 8-2. 일반 사용자 권한으로 조직 설정 조회 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/settings" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 설정 조회" -Method "GET" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 설정 조회" -Method "GET" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 9. 현재 조직 설정 조회 테스트 (GET /organizations/current/settings)
# ========================================

Write-Host "`n🔧 9. 현재 조직 설정 조회 테스트" -ForegroundColor Yellow

# 9-1. 일반 사용자 권한으로 현재 조직 설정 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current/settings" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "사용자 현재 조직 설정 조회" -Method "GET" -Endpoint "/organizations/current/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "현재 조직 설정 조회 성공"
} else {
    Add-TestResult -TestName "사용자 현재 조직 설정 조회" -Method "GET" -Endpoint "/organizations/current/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 9-2. 관리자 권한으로 현재 조직 설정 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$ORG_ENDPOINT/current/settings" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 현재 조직 설정 조회" -Method "GET" -Endpoint "/organizations/current/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "현재 조직 설정 조회 성공"
} else {
    Add-TestResult -TestName "관리자 현재 조직 설정 조회" -Method "GET" -Endpoint "/organizations/current/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 10. 조직 설정 수정 테스트 (PUT /organizations/{org_id}/settings)
# ========================================

Write-Host "`n🛠️ 10. 조직 설정 수정 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 10-1. 관리자 권한으로 조직 설정 수정
    $settingsUpdateData = @{
        max_mail_size_mb = 50
        max_attachment_size_mb = 25
        allow_external_mail = $true
        spam_filter_enabled = $true
        require_2fa = $false
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/settings" -Headers $headers -Body $settingsUpdateData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 조직 설정 수정" -Method "PUT" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "설정 수정 성공"
    } else {
        Add-TestResult -TestName "관리자 조직 설정 수정" -Method "PUT" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 10-2. 일반 사용자 권한으로 조직 설정 수정 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID/settings" -Headers $headers -Body $settingsUpdateData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 설정 수정" -Method "PUT" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 설정 수정" -Method "PUT" -Endpoint "/organizations/{org_id}/settings" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 11. 조직 삭제 테스트 (DELETE /organizations/{org_id})
# ========================================

Write-Host "`n🗑️ 11. 조직 삭제 테스트" -ForegroundColor Yellow

if ($TEST_ORG_ID) {
    # 11-1. 일반 사용자 권한으로 조직 삭제 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "DELETE" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 조직 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 조직 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
    
    # 11-2. 관리자 권한으로 조직 소프트 삭제
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "DELETE" -Uri "$ORG_ENDPOINT/$TEST_ORG_ID?force=false" -Headers $headers
    
    if ($result.Success -or $result.StatusCode -eq 204) {
        Add-TestResult -TestName "관리자 조직 소프트 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "소프트 삭제 성공"
    } else {
        Add-TestResult -TestName "관리자 조직 소프트 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 11-3. 존재하지 않는 조직 삭제 시도
$fakeOrgId = "12345678-1234-1234-1234-123456789012"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "DELETE" -Uri "$ORG_ENDPOINT/$fakeOrgId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 조직 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 조직 삭제" -Method "DELETE" -Endpoint "/organizations/{org_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
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
$resultFile = "organization_router_test_results.json"
$TEST_RESULTS | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host "`n💾 테스트 결과가 '$resultFile'에 저장되었습니다." -ForegroundColor Green

Write-Host "`n🏁 조직 관리 라우터 테스트 완료" -ForegroundColor Cyan