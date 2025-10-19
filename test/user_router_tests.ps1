# ========================================
# 사용자 관리 라우터 테스트 시나리오 (user_router.py)
# SkyBoot Mail SaaS - 다중 조직 지원 메일서버
# ========================================

# 테스트 설정
$BASE_URL = "http://localhost:8001/api/v1"
$USER_ENDPOINT = "$BASE_URL/users"
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

# 새 사용자 생성용 데이터
$NEW_USER_DATA = @{
    userId = "newuser01"
    password = "newpassword123"
    full_name = "새로운 사용자"
    role = "user"
}

# 결과 저장 변수
$TEST_RESULTS = @()
$ACCESS_TOKEN_USER = ""
$ACCESS_TOKEN_ADMIN = ""
$NEW_USER_ID = ""

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

Write-Host "👤 사용자 관리 라우터 테스트 시작" -ForegroundColor Cyan
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
# 1. 사용자 생성 테스트 (POST /users)
# ========================================

Write-Host "`n👥 1. 사용자 생성 테스트" -ForegroundColor Yellow

# 1-1. 관리자 권한으로 새 사용자 생성
$newUserJson = $NEW_USER_DATA | ConvertTo-Json
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$USER_ENDPOINT" -Headers $headers -Body $newUserJson

if ($result.Success) {
    $NEW_USER_ID = $result.Data.user_uuid
    Add-TestResult -TestName "관리자 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "사용자 ID: $NEW_USER_ID"
} else {
    Add-TestResult -TestName "관리자 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-2. 일반 사용자 권한으로 사용자 생성 시도 (권한 부족 예상)
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$USER_ENDPOINT" -Headers $headers -Body $newUserJson

if (!$result.Success -and $result.StatusCode -eq 403) {
    Add-TestResult -TestName "일반 사용자 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
} else {
    Add-TestResult -TestName "일반 사용자 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
}

# 1-3. 중복 이메일로 사용자 생성 시도
$duplicateUserData = @{
    email = $NEW_USER_DATA.email  # 위에서 사용한 이메일과 동일
    password = "anotherpassword"
    full_name = "중복 사용자"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$USER_ENDPOINT" -Headers $headers -Body $duplicateUserData

if (!$result.Success -and $result.StatusCode -eq 400) {
    Add-TestResult -TestName "중복 이메일 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 중복 거부"
} else {
    Add-TestResult -TestName "중복 이메일 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message "중복 검증 실패"
}

# 1-4. 잘못된 데이터로 사용자 생성 시도
$invalidUserData = @{
    email = "invalid-email"  # 잘못된 이메일 형식
    password = "123"         # 너무 짧은 비밀번호
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$USER_ENDPOINT" -Headers $headers -Body $invalidUserData

if (!$result.Success -and $result.StatusCode -eq 422) {
    Add-TestResult -TestName "잘못된 데이터 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 검증 실패"
} else {
    Add-TestResult -TestName "잘못된 데이터 사용자 생성" -Method "POST" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message "데이터 검증 실패"
}

# ========================================
# 2. 사용자 목록 조회 테스트 (GET /users)
# ========================================

Write-Host "`n📋 2. 사용자 목록 조회 테스트" -ForegroundColor Yellow

# 2-1. 관리자 권한으로 사용자 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT" -Headers $headers

if ($result.Success) {
    $userCount = $result.Data.users.Count
    Add-TestResult -TestName "관리자 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "사용자 수: $userCount"
} else {
    Add-TestResult -TestName "관리자 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-2. 페이징 파라미터로 사용자 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT?page=1&limit=5" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "페이징 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "페이지: $($result.Data.page), 제한: $($result.Data.limit)"
} else {
    Add-TestResult -TestName "페이징 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-3. 검색 파라미터로 사용자 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT?search=user01" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "검색 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "검색 결과: $($result.Data.users.Count)개"
} else {
    Add-TestResult -TestName "검색 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-4. 역할 필터로 사용자 목록 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT?role=admin" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "역할 필터 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "관리자 수: $($result.Data.users.Count)개"
} else {
    Add-TestResult -TestName "역할 필터 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-5. 일반 사용자 권한으로 사용자 목록 조회 시도 (권한 부족 예상)
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 403) {
    Add-TestResult -TestName "일반 사용자 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
} else {
    Add-TestResult -TestName "일반 사용자 사용자 목록 조회" -Method "GET" -Endpoint "/users" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
}

# ========================================
# 3. 현재 사용자 정보 조회 테스트 (GET /users/me)
# ========================================

Write-Host "`n👤 3. 현재 사용자 정보 조회 테스트" -ForegroundColor Yellow

# 3-1. 일반 사용자 권한으로 자신의 정보 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/me" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "일반 사용자 자신 정보 조회" -Method "GET" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "PASS" -Message "이메일: $($result.Data.email)"
} else {
    Add-TestResult -TestName "일반 사용자 자신 정보 조회" -Method "GET" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 3-2. 관리자 권한으로 자신의 정보 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/me" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 자신 정보 조회" -Method "GET" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "PASS" -Message "이메일: $($result.Data.email)"
} else {
    Add-TestResult -TestName "관리자 자신 정보 조회" -Method "GET" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 4. 특정 사용자 정보 조회 테스트 (GET /users/{user_id})
# ========================================

Write-Host "`n🔍 4. 특정 사용자 정보 조회 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 4-1. 관리자 권한으로 특정 사용자 정보 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/$NEW_USER_ID" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 특정 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "이메일: $($result.Data.email)"
    } else {
        Add-TestResult -TestName "관리자 특정 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 4-2. 일반 사용자 권한으로 다른 사용자 정보 조회 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/$NEW_USER_ID" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 다른 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 다른 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# 4-3. 존재하지 않는 사용자 ID로 조회 시도
$fakeUserId = "12345678-1234-1234-1234-123456789012"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/$fakeUserId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 사용자 정보 조회" -Method "GET" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
}

# ========================================
# 5. 사용자 정보 수정 테스트 (PUT /users/{user_id})
# ========================================

Write-Host "`n✏️ 5. 사용자 정보 수정 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 5-1. 관리자 권한으로 사용자 정보 수정
    $updateData = @{
        full_name = "수정된 사용자 이름"
        phone = "010-1234-5678"
        department = "개발팀"
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID" -Headers $headers -Body $updateData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 사용자 정보 수정" -Method "PUT" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "수정된 이름: $($result.Data.full_name)"
    } else {
        Add-TestResult -TestName "관리자 사용자 정보 수정" -Method "PUT" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 5-2. 일반 사용자 권한으로 다른 사용자 정보 수정 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID" -Headers $headers -Body $updateData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 다른 사용자 정보 수정" -Method "PUT" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 다른 사용자 정보 수정" -Method "PUT" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# 5-3. 일반 사용자가 자신의 정보 수정
$selfUpdateData = @{
    full_name = "수정된 내 이름"
    phone = "010-9876-5432"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/me" -Headers $headers -Body $selfUpdateData

if ($result.Success) {
    Add-TestResult -TestName "일반 사용자 자신 정보 수정" -Method "PUT" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "PASS" -Message "수정된 이름: $($result.Data.full_name)"
} else {
    Add-TestResult -TestName "일반 사용자 자신 정보 수정" -Method "PUT" -Endpoint "/users/me" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 6. 사용자 역할 변경 테스트 (PUT /users/{user_id}/role)
# ========================================

Write-Host "`n🔑 6. 사용자 역할 변경 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 6-1. 관리자 권한으로 사용자 역할 변경
    $roleChangeData = @{
        role = "admin"
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/role" -Headers $headers -Body $roleChangeData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 사용자 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "PASS" -Message "새 역할: $($result.Data.role)"
    } else {
        Add-TestResult -TestName "관리자 사용자 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 6-2. 일반 사용자 권한으로 역할 변경 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/role" -Headers $headers -Body $roleChangeData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# 6-3. 잘못된 역할로 변경 시도
$invalidRoleData = @{
    role = "invalid_role"
} | ConvertTo-Json

if ($NEW_USER_ID) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/role" -Headers $headers -Body $invalidRoleData
    
    if (!$result.Success -and $result.StatusCode -eq 422) {
        Add-TestResult -TestName "잘못된 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 검증 실패"
    } else {
        Add-TestResult -TestName "잘못된 역할 변경" -Method "PUT" -Endpoint "/users/{user_id}/role" -StatusCode $result.StatusCode -Status "FAIL" -Message "역할 검증 실패"
    }
}

# ========================================
# 7. 사용자 활성화/비활성화 테스트 (PUT /users/{user_id}/status)
# ========================================

Write-Host "`n🔄 7. 사용자 활성화/비활성화 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 7-1. 관리자 권한으로 사용자 비활성화
    $statusChangeData = @{
        is_active = $false
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/status" -Headers $headers -Body $statusChangeData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 사용자 비활성화" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "PASS" -Message "활성화 상태: $($result.Data.is_active)"
    } else {
        Add-TestResult -TestName "관리자 사용자 비활성화" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 7-2. 관리자 권한으로 사용자 재활성화
    $statusChangeData = @{
        is_active = $true
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/status" -Headers $headers -Body $statusChangeData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 사용자 재활성화" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "PASS" -Message "활성화 상태: $($result.Data.is_active)"
    } else {
        Add-TestResult -TestName "관리자 사용자 재활성화" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 7-3. 일반 사용자 권한으로 상태 변경 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/status" -Headers $headers -Body $statusChangeData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 상태 변경" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 상태 변경" -Method "PUT" -Endpoint "/users/{user_id}/status" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# ========================================
# 8. 사용자 비밀번호 재설정 테스트 (PUT /users/{user_id}/password)
# ========================================

Write-Host "`n🔒 8. 사용자 비밀번호 재설정 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 8-1. 관리자 권한으로 사용자 비밀번호 재설정
    $passwordResetData = @{
        new_password = "newpassword456"
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/password" -Headers $headers -Body $passwordResetData
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "PASS" -Message "비밀번호 재설정 성공"
    } else {
        Add-TestResult -TestName "관리자 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 8-2. 일반 사용자 권한으로 다른 사용자 비밀번호 재설정 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/password" -Headers $headers -Body $passwordResetData
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 다른 사용자 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 다른 사용자 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
}

# 8-3. 너무 짧은 비밀번호로 재설정 시도
$weakPasswordData = @{
    new_password = "123"
} | ConvertTo-Json

if ($NEW_USER_ID) {
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$USER_ENDPOINT/$NEW_USER_ID/password" -Headers $headers -Body $weakPasswordData
    
    if (!$result.Success -and $result.StatusCode -eq 422) {
        Add-TestResult -TestName "약한 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 검증 실패"
    } else {
        Add-TestResult -TestName "약한 비밀번호 재설정" -Method "PUT" -Endpoint "/users/{user_id}/password" -StatusCode $result.StatusCode -Status "FAIL" -Message "비밀번호 검증 실패"
    }
}

# ========================================
# 9. 사용자 삭제 테스트 (DELETE /users/{user_id})
# ========================================

Write-Host "`n🗑️ 9. 사용자 삭제 테스트" -ForegroundColor Yellow

if ($NEW_USER_ID) {
    # 9-1. 일반 사용자 권한으로 사용자 삭제 시도 (권한 부족 예상)
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "DELETE" -Uri "$USER_ENDPOINT/$NEW_USER_ID" -Headers $headers
    
    if (!$result.Success -and $result.StatusCode -eq 403) {
        Add-TestResult -TestName "일반 사용자 사용자 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
    } else {
        Add-TestResult -TestName "일반 사용자 사용자 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
    }
    
    # 9-2. 관리자 권한으로 사용자 소프트 삭제
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "DELETE" -Uri "$USER_ENDPOINT/$NEW_USER_ID?force=false" -Headers $headers
    
    if ($result.Success -or $result.StatusCode -eq 204) {
        Add-TestResult -TestName "관리자 사용자 소프트 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "소프트 삭제 성공"
    } else {
        Add-TestResult -TestName "관리자 사용자 소프트 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 9-3. 존재하지 않는 사용자 삭제 시도
$fakeUserId = "12345678-1234-1234-1234-123456789012"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "DELETE" -Uri "$USER_ENDPOINT/$fakeUserId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 사용자 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 사용자 삭제" -Method "DELETE" -Endpoint "/users/{user_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
}

# ========================================
# 10. 사용자 통계 조회 테스트 (GET /users/stats)
# ========================================

Write-Host "`n📊 10. 사용자 통계 조회 테스트" -ForegroundColor Yellow

# 10-1. 관리자 권한으로 사용자 통계 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/stats" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 사용자 통계 조회" -Method "GET" -Endpoint "/users/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "통계 데이터 조회 성공"
} else {
    Add-TestResult -TestName "관리자 사용자 통계 조회" -Method "GET" -Endpoint "/users/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 10-2. 일반 사용자 권한으로 사용자 통계 조회 시도 (권한 부족 예상)
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$USER_ENDPOINT/stats" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 403) {
    Add-TestResult -TestName "일반 사용자 사용자 통계 조회" -Method "GET" -Endpoint "/users/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 권한 거부"
} else {
    Add-TestResult -TestName "일반 사용자 사용자 통계 조회" -Method "GET" -Endpoint "/users/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message "권한 제어 실패"
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
$resultFile = "user_router_test_results.json"
$TEST_RESULTS | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host "`n💾 테스트 결과가 '$resultFile'에 저장되었습니다." -ForegroundColor Green

Write-Host "`n🏁 사용자 관리 라우터 테스트 완료" -ForegroundColor Cyan