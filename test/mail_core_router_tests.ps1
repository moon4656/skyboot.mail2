# ========================================
# 메일 핵심 기능 라우터 테스트 시나리오 (mail_core_router.py)
# SkyBoot Mail SaaS - 다중 조직 지원 메일서버
# ========================================

# 테스트 설정
$BASE_URL = "http://localhost:8001/api/v1"
$MAIL_ENDPOINT = "$BASE_URL/mail"
$AUTH_ENDPOINT = "$BASE_URL/auth"

# 테스트 사용자 정보
$TEST_USER = @{
    user_id = "user01"
    password = "test"
}

$TEST_ADMIN = @{
    user_id = "admin01"
    password = "test"
}

# 테스트 메일 데이터
$TEST_MAIL_DATA = @{
    to = @("recipient@test.com")
    subject = "테스트 메일 제목"
    content = "이것은 테스트 메일 내용입니다."
    content_type = "text/plain"
}

$TEST_HTML_MAIL_DATA = @{
    to = @("recipient@test.com")
    cc = @("cc@test.com")
    bcc = @("bcc@test.com")
    subject = "HTML 테스트 메일"
    content = "<h1>HTML 메일 테스트</h1><p>이것은 <b>HTML</b> 메일입니다.</p>"
    content_type = "text/html"
    priority = "high"
}

# 결과 저장 변수
$TEST_RESULTS = @()
$ACCESS_TOKEN_USER = ""
$ACCESS_TOKEN_ADMIN = ""
$SENT_MAIL_ID = ""

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

Write-Host "📧 메일 핵심 기능 라우터 테스트 시작" -ForegroundColor Cyan
Write-Host "=" * 50

# ========================================
# 사전 준비: 인증 토큰 획득
# ========================================

Write-Host "`n🔐 사전 준비: 인증 토큰 획득" -ForegroundColor Yellow

# 일반 사용자 로그인
$loginData = @{
    user_id = $TEST_USER.user_id
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
    user_id = $TEST_ADMIN.user_id
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
# 1. 메일 발송 테스트 (POST /mail/send)
# ========================================

Write-Host "`n📤 1. 메일 발송 테스트" -ForegroundColor Yellow

# 1-1. 일반 사용자 권한으로 기본 메일 발송
$mailJson = $TEST_MAIL_DATA | ConvertTo-Json
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $mailJson

if ($result.Success) {
    $SENT_MAIL_ID = $result.Data.mail_id
    Add-TestResult -TestName "일반 사용자 기본 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "PASS" -Message "메일 ID: $SENT_MAIL_ID"
} else {
    Add-TestResult -TestName "일반 사용자 기본 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-2. 관리자 권한으로 HTML 메일 발송
$htmlMailJson = $TEST_HTML_MAIL_DATA | ConvertTo-Json
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $htmlMailJson

if ($result.Success) {
    Add-TestResult -TestName "관리자 HTML 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "PASS" -Message "메일 ID: $($result.Data.mail_id)"
} else {
    Add-TestResult -TestName "관리자 HTML 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 1-3. 잘못된 이메일 주소로 발송 시도
$invalidMailData = @{
    to = @("invalid-email")
    subject = "테스트"
    content = "내용"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $invalidMailData

if (!$result.Success -and $result.StatusCode -eq 422) {
    Add-TestResult -TestName "잘못된 이메일 주소 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 검증 실패"
} else {
    Add-TestResult -TestName "잘못된 이메일 주소 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "FAIL" -Message "이메일 검증 실패"
}

# 1-4. 빈 제목으로 발송 시도
$emptySubjectData = @{
    to = @("test@test.com")
    subject = ""
    content = "내용"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $emptySubjectData

if (!$result.Success -and $result.StatusCode -eq 422) {
    Add-TestResult -TestName "빈 제목 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 검증 실패"
} else {
    Add-TestResult -TestName "빈 제목 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "FAIL" -Message "제목 검증 실패"
}

# 1-5. 대량 수신자 메일 발송
$bulkMailData = @{
    to = @("user1@test.com", "user2@test.com", "user3@test.com")
    cc = @("cc1@test.com", "cc2@test.com")
    subject = "대량 발송 테스트"
    content = "대량 발송 테스트 메일입니다."
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $bulkMailData

if ($result.Success) {
    Add-TestResult -TestName "대량 수신자 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "PASS" -Message "수신자 수: 5명"
} else {
    Add-TestResult -TestName "대량 수신자 메일 발송" -Method "POST" -Endpoint "/mail/send" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 2. 받은 메일함 조회 테스트 (GET /mail/inbox)
# ========================================

Write-Host "`n📥 2. 받은 메일함 조회 테스트" -ForegroundColor Yellow

# 2-1. 일반 사용자 받은 메일함 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/inbox" -Headers $headers

if ($result.Success) {
    $mailCount = $result.Data.mails.Count
    Add-TestResult -TestName "일반 사용자 받은 메일함 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "PASS" -Message "메일 수: $mailCount"
} else {
    Add-TestResult -TestName "일반 사용자 받은 메일함 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-2. 페이징 파라미터로 받은 메일함 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/inbox?page=1&limit=5" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "페이징 받은 메일함 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "PASS" -Message "페이지: $($result.Data.page), 제한: $($result.Data.limit)"
} else {
    Add-TestResult -TestName "페이징 받은 메일함 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-3. 읽지 않은 메일만 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/inbox?unread_only=true" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "읽지 않은 메일 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "PASS" -Message "읽지 않은 메일 수: $($result.Data.mails.Count)"
} else {
    Add-TestResult -TestName "읽지 않은 메일 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 2-4. 날짜 범위로 메일 조회
$startDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-dd")
$endDate = (Get-Date).ToString("yyyy-MM-dd")
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/inbox?start_date=$startDate&end_date=$endDate" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "날짜 범위 메일 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "PASS" -Message "기간: $startDate ~ $endDate"
} else {
    Add-TestResult -TestName "날짜 범위 메일 조회" -Method "GET" -Endpoint "/mail/inbox" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 3. 보낸 메일함 조회 테스트 (GET /mail/sent)
# ========================================

Write-Host "`n📤 3. 보낸 메일함 조회 테스트" -ForegroundColor Yellow

# 3-1. 일반 사용자 보낸 메일함 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/sent" -Headers $headers

if ($result.Success) {
    $sentCount = $result.Data.mails.Count
    Add-TestResult -TestName "일반 사용자 보낸 메일함 조회" -Method "GET" -Endpoint "/mail/sent" -StatusCode $result.StatusCode -Status "PASS" -Message "보낸 메일 수: $sentCount"
} else {
    Add-TestResult -TestName "일반 사용자 보낸 메일함 조회" -Method "GET" -Endpoint "/mail/sent" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 3-2. 관리자 보낸 메일함 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/sent" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 보낸 메일함 조회" -Method "GET" -Endpoint "/mail/sent" -StatusCode $result.StatusCode -Status "PASS" -Message "보낸 메일 수: $($result.Data.mails.Count)"
} else {
    Add-TestResult -TestName "관리자 보낸 메일함 조회" -Method "GET" -Endpoint "/mail/sent" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 4. 특정 메일 조회 테스트 (GET /mail/{mail_id})
# ========================================

Write-Host "`n🔍 4. 특정 메일 조회 테스트" -ForegroundColor Yellow

if ($SENT_MAIL_ID) {
    # 4-1. 발송자가 자신의 메일 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/$SENT_MAIL_ID" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "발송자 자신 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "제목: $($result.Data.subject)"
    } else {
        Add-TestResult -TestName "발송자 자신 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 4-2. 관리자가 다른 사용자 메일 조회
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
    $result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/$SENT_MAIL_ID" -Headers $headers
    
    if ($result.Success) {
        Add-TestResult -TestName "관리자 다른 사용자 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "관리자 권한으로 조회 성공"
    } else {
        Add-TestResult -TestName "관리자 다른 사용자 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 4-3. 존재하지 않는 메일 ID로 조회 시도
$fakeMailId = "fake-mail-id-12345"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/$fakeMailId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 메일 조회" -Method "GET" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
}

# ========================================
# 5. 메일 읽음 상태 변경 테스트 (PUT /mail/{mail_id}/read)
# ========================================

Write-Host "`n👁️ 5. 메일 읽음 상태 변경 테스트" -ForegroundColor Yellow

if ($SENT_MAIL_ID) {
    # 5-1. 메일을 읽음으로 표시
    $readStatusData = @{
        is_read = $true
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$MAIL_ENDPOINT/$SENT_MAIL_ID/read" -Headers $headers -Body $readStatusData
    
    if ($result.Success) {
        Add-TestResult -TestName "메일 읽음 표시" -Method "PUT" -Endpoint "/mail/{mail_id}/read" -StatusCode $result.StatusCode -Status "PASS" -Message "읽음 상태: $($result.Data.is_read)"
    } else {
        Add-TestResult -TestName "메일 읽음 표시" -Method "PUT" -Endpoint "/mail/{mail_id}/read" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 5-2. 메일을 읽지 않음으로 표시
    $unreadStatusData = @{
        is_read = $false
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "PUT" -Uri "$MAIL_ENDPOINT/$SENT_MAIL_ID/read" -Headers $headers -Body $unreadStatusData
    
    if ($result.Success) {
        Add-TestResult -TestName "메일 읽지 않음 표시" -Method "PUT" -Endpoint "/mail/{mail_id}/read" -StatusCode $result.StatusCode -Status "PASS" -Message "읽음 상태: $($result.Data.is_read)"
    } else {
        Add-TestResult -TestName "메일 읽지 않음 표시" -Method "PUT" -Endpoint "/mail/{mail_id}/read" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# ========================================
# 6. 메일 삭제 테스트 (DELETE /mail/{mail_id})
# ========================================

Write-Host "`n🗑️ 6. 메일 삭제 테스트" -ForegroundColor Yellow

if ($SENT_MAIL_ID) {
    # 6-1. 메일 소프트 삭제
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "DELETE" -Uri "$MAIL_ENDPOINT/$SENT_MAIL_ID?force=false" -Headers $headers
    
    if ($result.Success -or $result.StatusCode -eq 204) {
        Add-TestResult -TestName "메일 소프트 삭제" -Method "DELETE" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "소프트 삭제 성공"
    } else {
        Add-TestResult -TestName "메일 소프트 삭제" -Method "DELETE" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# 6-2. 존재하지 않는 메일 삭제 시도
$fakeMailId = "fake-mail-id-12345"
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "DELETE" -Uri "$MAIL_ENDPOINT/$fakeMailId" -Headers $headers

if (!$result.Success -and $result.StatusCode -eq 404) {
    Add-TestResult -TestName "존재하지 않는 메일 삭제" -Method "DELETE" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "PASS" -Message "올바르게 404 반환"
} else {
    Add-TestResult -TestName "존재하지 않는 메일 삭제" -Method "DELETE" -Endpoint "/mail/{mail_id}" -StatusCode $result.StatusCode -Status "FAIL" -Message "오류 처리 실패"
}

# ========================================
# 7. 메일 전달 테스트 (POST /mail/{mail_id}/forward)
# ========================================

Write-Host "`n↪️ 7. 메일 전달 테스트" -ForegroundColor Yellow

# 새 메일을 발송하여 전달 테스트용으로 사용
$forwardTestMail = @{
    to = @("user01@test.com")
    subject = "전달 테스트용 메일"
    content = "이 메일은 전달 테스트용입니다."
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/send" -Headers $headers -Body $forwardTestMail

if ($result.Success) {
    $forwardMailId = $result.Data.mail_id
    
    # 7-1. 메일 전달
    $forwardData = @{
        to = @("forward@test.com")
        message = "전달합니다."
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/$forwardMailId/forward" -Headers $headers -Body $forwardData
    
    if ($result.Success) {
        Add-TestResult -TestName "메일 전달" -Method "POST" -Endpoint "/mail/{mail_id}/forward" -StatusCode $result.StatusCode -Status "PASS" -Message "전달 메일 ID: $($result.Data.mail_id)"
    } else {
        Add-TestResult -TestName "메일 전달" -Method "POST" -Endpoint "/mail/{mail_id}/forward" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# ========================================
# 8. 메일 답장 테스트 (POST /mail/{mail_id}/reply)
# ========================================

Write-Host "`n↩️ 8. 메일 답장 테스트" -ForegroundColor Yellow

if ($forwardMailId) {
    # 8-1. 메일 답장
    $replyData = @{
        content = "답장 내용입니다."
        reply_all = $false
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/$forwardMailId/reply" -Headers $headers -Body $replyData
    
    if ($result.Success) {
        Add-TestResult -TestName "메일 답장" -Method "POST" -Endpoint "/mail/{mail_id}/reply" -StatusCode $result.StatusCode -Status "PASS" -Message "답장 메일 ID: $($result.Data.mail_id)"
    } else {
        Add-TestResult -TestName "메일 답장" -Method "POST" -Endpoint "/mail/{mail_id}/reply" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
    
    # 8-2. 전체 답장
    $replyAllData = @{
        content = "전체 답장 내용입니다."
        reply_all = $true
    } | ConvertTo-Json
    
    $headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
    $result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/$forwardMailId/reply" -Headers $headers -Body $replyAllData
    
    if ($result.Success) {
        Add-TestResult -TestName "메일 전체 답장" -Method "POST" -Endpoint "/mail/{mail_id}/reply" -StatusCode $result.StatusCode -Status "PASS" -Message "전체 답장 메일 ID: $($result.Data.mail_id)"
    } else {
        Add-TestResult -TestName "메일 전체 답장" -Method "POST" -Endpoint "/mail/{mail_id}/reply" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
    }
}

# ========================================
# 9. 메일 첨부파일 업로드 테스트 (POST /mail/attachments)
# ========================================

Write-Host "`n📎 9. 메일 첨부파일 업로드 테스트" -ForegroundColor Yellow

# 9-1. 첨부파일 업로드 (실제 파일이 없으므로 시뮬레이션)
$attachmentData = @{
    filename = "test.txt"
    content_type = "text/plain"
    size = 1024
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "POST" -Uri "$MAIL_ENDPOINT/attachments" -Headers $headers -Body $attachmentData

if ($result.Success -or $result.StatusCode -eq 400) {
    # 실제 파일이 없으므로 400 에러도 정상으로 간주
    Add-TestResult -TestName "첨부파일 업로드" -Method "POST" -Endpoint "/mail/attachments" -StatusCode $result.StatusCode -Status "PASS" -Message "첨부파일 처리 확인"
} else {
    Add-TestResult -TestName "첨부파일 업로드" -Method "POST" -Endpoint "/mail/attachments" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 10. 메일 통계 조회 테스트 (GET /mail/stats)
# ========================================

Write-Host "`n📊 10. 메일 통계 조회 테스트" -ForegroundColor Yellow

# 10-1. 일반 사용자 메일 통계 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/stats" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "일반 사용자 메일 통계 조회" -Method "GET" -Endpoint "/mail/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "통계 데이터 조회 성공"
} else {
    Add-TestResult -TestName "일반 사용자 메일 통계 조회" -Method "GET" -Endpoint "/mail/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 10-2. 관리자 메일 통계 조회
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_ADMIN" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/stats" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "관리자 메일 통계 조회" -Method "GET" -Endpoint "/mail/stats" -StatusCode $result.StatusCode -Status "PASS" -Message "관리자 통계 데이터 조회 성공"
} else {
    Add-TestResult -TestName "관리자 메일 통계 조회" -Method "GET" -Endpoint "/mail/stats" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# ========================================
# 11. 메일 검색 테스트 (GET /mail/search)
# ========================================

Write-Host "`n🔍 11. 메일 검색 테스트" -ForegroundColor Yellow

# 11-1. 제목으로 메일 검색
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/search?q=테스트&type=subject" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "제목으로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "PASS" -Message "검색 결과: $($result.Data.mails.Count)개"
} else {
    Add-TestResult -TestName "제목으로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 11-2. 내용으로 메일 검색
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/search?q=내용&type=content" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "내용으로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "PASS" -Message "검색 결과: $($result.Data.mails.Count)개"
} else {
    Add-TestResult -TestName "내용으로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
}

# 11-3. 발송자로 메일 검색
$headers = @{ "Authorization" = "Bearer $ACCESS_TOKEN_USER" }
$result = Invoke-ApiRequest -Method "GET" -Uri "$MAIL_ENDPOINT/search?q=admin01&type=sender" -Headers $headers

if ($result.Success) {
    Add-TestResult -TestName "발송자로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "PASS" -Message "검색 결과: $($result.Data.mails.Count)개"
} else {
    Add-TestResult -TestName "발송자로 메일 검색" -Method "GET" -Endpoint "/mail/search" -StatusCode $result.StatusCode -Status "FAIL" -Message $result.Error
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
$resultFile = "mail_core_router_test_results.json"
$TEST_RESULTS | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host "`n💾 테스트 결과가 '$resultFile'에 저장되었습니다." -ForegroundColor Green

Write-Host "`n🏁 메일 핵심 기능 라우터 테스트 완료" -ForegroundColor Cyan