# ===================================================================
# SkyBoot Mail SaaS - 메일 편의 라우터 테스트 시나리오
# 파일: mail_convenience_router_tests.ps1
# 설명: mail_convenience_router.py의 모든 엔드포인트 테스트
# 작성자: SkyBoot Mail Team
# 작성일: 2024-01-20
# ===================================================================

# 테스트 설정
$BaseUrl = "http://localhost:8001/api/v1"
$TestResults = @()
$TestStartTime = Get-Date

Write-Host "=== SkyBoot Mail 편의 라우터 테스트 시작 ===" -ForegroundColor Green
Write-Host "테스트 시작 시간: $TestStartTime" -ForegroundColor Yellow
Write-Host "기본 URL: $BaseUrl" -ForegroundColor Yellow

# 공통 함수 정의
function Invoke-ApiTest {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [int]$ExpectedStatus = 200,
        [string]$Description = ""
    )
    
    try {
        $StartTime = Get-Date
        $Uri = "$BaseUrl$Endpoint"
        
        $RequestParams = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $RequestParams.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        Write-Host "`n[$TestName] 테스트 실행 중..." -ForegroundColor Cyan
        Write-Host "  요청: $Method $Endpoint" -ForegroundColor Gray
        if ($Description) {
            Write-Host "  설명: $Description" -ForegroundColor Gray
        }
        
        $Response = Invoke-RestMethod @RequestParams
        $EndTime = Get-Date
        $Duration = ($EndTime - $StartTime).TotalMilliseconds
        
        $TestResult = @{
            TestName = $TestName
            Method = $Method
            Endpoint = $Endpoint
            Status = "PASS"
            StatusCode = 200
            Duration = $Duration
            Description = $Description
            Response = $Response
            Timestamp = $StartTime
        }
        
        Write-Host "  결과: PASS (${Duration}ms)" -ForegroundColor Green
        
    } catch {
        $EndTime = Get-Date
        $Duration = ($EndTime - $StartTime).TotalMilliseconds
        $StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        
        $TestResult = @{
            TestName = $TestName
            Method = $Method
            Endpoint = $Endpoint
            Status = if ($StatusCode -eq $ExpectedStatus) { "PASS" } else { "FAIL" }
            StatusCode = $StatusCode
            Duration = $Duration
            Description = $Description
            Error = $_.Exception.Message
            Timestamp = $StartTime
        }
        
        $StatusColor = if ($StatusCode -eq $ExpectedStatus) { "Green" } else { "Red" }
        Write-Host "  결과: $($TestResult.Status) - HTTP $StatusCode (${Duration}ms)" -ForegroundColor $StatusColor
        
        if ($TestResult.Status -eq "FAIL") {
            Write-Host "  오류: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    $script:TestResults += $TestResult
    return $TestResult
}

# 인증 토큰 저장 변수
$UserToken = $null
$AdminToken = $null

# ===================================================================
# 1. 사용자 인증 (user01)
# ===================================================================
Write-Host "`n=== 1. 사용자 인증 (user01) ===" -ForegroundColor Magenta

$LoginData = @{
    user_id = "user01"
    password = "test"
}

$LoginResult = Invoke-ApiTest -TestName "USER_LOGIN" -Method "POST" -Endpoint "/auth/login" -Body $LoginData -Description "일반 사용자 로그인"

if ($LoginResult.Status -eq "PASS" -and $LoginResult.Response.access_token) {
    $UserToken = $LoginResult.Response.access_token
    Write-Host "사용자 토큰 획득 성공" -ForegroundColor Green
} else {
    Write-Host "사용자 로그인 실패 - 테스트 중단" -ForegroundColor Red
    exit 1
}

# ===================================================================
# 2. 관리자 인증 (admin01)
# ===================================================================
Write-Host "`n=== 2. 관리자 인증 (admin01) ===" -ForegroundColor Magenta

$AdminLoginData = @{
    user_id = "admin01"
    password = "test"
}

$AdminLoginResult = Invoke-ApiTest -TestName "ADMIN_LOGIN" -Method "POST" -Endpoint "/auth/login" -Body $AdminLoginData -Description "관리자 로그인"

if ($AdminLoginResult.Status -eq "PASS" -and $AdminLoginResult.Response.access_token) {
    $AdminToken = $AdminLoginResult.Response.access_token
    Write-Host "관리자 토큰 획득 성공" -ForegroundColor Green
} else {
    Write-Host "관리자 로그인 실패 - 테스트 중단" -ForegroundColor Red
    exit 1
}

# 공통 헤더 설정
$UserHeaders = @{ "Authorization" = "Bearer $UserToken" }
$AdminHeaders = @{ "Authorization" = "Bearer $AdminToken" }

# ===================================================================
# 3. 메일함 관리 테스트
# ===================================================================
Write-Host "`n=== 3. 메일함 관리 테스트 ===" -ForegroundColor Magenta

# 3.1 메일함 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_MAILBOXES_USER" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -Headers $UserHeaders -Description "사용자 메일함 목록 조회"

# 3.2 메일함 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAILBOXES_ADMIN" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -Headers $AdminHeaders -Description "관리자 메일함 목록 조회"

# 3.3 메일함 생성 (사용자)
$CreateMailboxData = @{
    name = "테스트 메일함"
    description = "테스트용 사용자 정의 메일함"
    color = "#FF5722"
}
Invoke-ApiTest -TestName "CREATE_MAILBOX_USER" -Method "POST" -Endpoint "/mail-convenience/mailboxes" -Headers $UserHeaders -Body $CreateMailboxData -Description "사용자 메일함 생성"

# 3.4 메일함 생성 (관리자)
$CreateAdminMailboxData = @{
    name = "관리자 메일함"
    description = "관리자용 메일함"
    color = "#2196F3"
}
Invoke-ApiTest -TestName "CREATE_MAILBOX_ADMIN" -Method "POST" -Endpoint "/mail-convenience/mailboxes" -Headers $AdminHeaders -Body $CreateAdminMailboxData -Description "관리자 메일함 생성"

# 3.5 중복 메일함 생성 시도 (실패 케이스)
Invoke-ApiTest -TestName "CREATE_DUPLICATE_MAILBOX" -Method "POST" -Endpoint "/mail-convenience/mailboxes" -Headers $UserHeaders -Body $CreateMailboxData -ExpectedStatus 400 -Description "중복 메일함 생성 시도 (실패 예상)"

# 3.6 메일함 정보 조회
Invoke-ApiTest -TestName "GET_MAILBOX_INFO" -Method "GET" -Endpoint "/mail-convenience/mailboxes/1" -Headers $UserHeaders -Description "특정 메일함 정보 조회"

# 3.7 존재하지 않는 메일함 조회 (실패 케이스)
Invoke-ApiTest -TestName "GET_NONEXISTENT_MAILBOX" -Method "GET" -Endpoint "/mail-convenience/mailboxes/99999" -Headers $UserHeaders -ExpectedStatus 404 -Description "존재하지 않는 메일함 조회 (실패 예상)"

# 3.8 메일함 수정
$UpdateMailboxData = @{
    name = "수정된 테스트 메일함"
    description = "수정된 설명"
    color = "#4CAF50"
}
Invoke-ApiTest -TestName "UPDATE_MAILBOX" -Method "PUT" -Endpoint "/mail-convenience/mailboxes/1" -Headers $UserHeaders -Body $UpdateMailboxData -Description "메일함 정보 수정"

# 3.9 다른 사용자 메일함 수정 시도 (실패 케이스)
Invoke-ApiTest -TestName "UPDATE_OTHER_USER_MAILBOX" -Method "PUT" -Endpoint "/mail-convenience/mailboxes/2" -Headers $UserHeaders -Body $UpdateMailboxData -ExpectedStatus 403 -Description "다른 사용자 메일함 수정 시도 (실패 예상)"

# ===================================================================
# 4. 메일 검색 테스트
# ===================================================================
Write-Host "`n=== 4. 메일 검색 테스트 ===" -ForegroundColor Magenta

# 4.1 기본 메일 검색 (사용자)
Invoke-ApiTest -TestName "SEARCH_MAILS_BASIC_USER" -Method "GET" -Endpoint "/mail-convenience/search?q=test&page=1&limit=20" -Headers $UserHeaders -Description "기본 메일 검색 (사용자)"

# 4.2 기본 메일 검색 (관리자)
Invoke-ApiTest -TestName "SEARCH_MAILS_BASIC_ADMIN" -Method "GET" -Endpoint "/mail-convenience/search?q=admin&page=1&limit=20" -Headers $AdminHeaders -Description "기본 메일 검색 (관리자)"

# 4.3 고급 메일 검색 - 제목으로 검색
Invoke-ApiTest -TestName "SEARCH_MAILS_BY_SUBJECT" -Method "GET" -Endpoint "/mail-convenience/search?subject=테스트&page=1&limit=10" -Headers $UserHeaders -Description "제목으로 메일 검색"

# 4.4 고급 메일 검색 - 발송자로 검색
Invoke-ApiTest -TestName "SEARCH_MAILS_BY_SENDER" -Method "GET" -Endpoint "/mail-convenience/search?sender=admin01@test.com&page=1&limit=10" -Headers $UserHeaders -Description "발송자로 메일 검색"

# 4.5 고급 메일 검색 - 날짜 범위로 검색
$StartDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-dd")
$EndDate = (Get-Date).ToString("yyyy-MM-dd")
Invoke-ApiTest -TestName "SEARCH_MAILS_BY_DATE_RANGE" -Method "GET" -Endpoint "/mail-convenience/search?start_date=$StartDate&end_date=$EndDate&page=1&limit=10" -Headers $UserHeaders -Description "날짜 범위로 메일 검색"

# 4.6 고급 메일 검색 - 읽지 않은 메일만
Invoke-ApiTest -TestName "SEARCH_UNREAD_MAILS" -Method "GET" -Endpoint "/mail-convenience/search?is_read=false&page=1&limit=10" -Headers $UserHeaders -Description "읽지 않은 메일 검색"

# 4.7 고급 메일 검색 - 첨부파일 있는 메일만
Invoke-ApiTest -TestName "SEARCH_MAILS_WITH_ATTACHMENTS" -Method "GET" -Endpoint "/mail-convenience/search?has_attachments=true&page=1&limit=10" -Headers $UserHeaders -Description "첨부파일 있는 메일 검색"

# 4.8 복합 검색 조건
Invoke-ApiTest -TestName "SEARCH_MAILS_COMPLEX" -Method "GET" -Endpoint "/mail-convenience/search?q=test&sender=admin&is_read=false&has_attachments=true&page=1&limit=5" -Headers $UserHeaders -Description "복합 조건 메일 검색"

# 4.9 빈 검색어로 검색 (실패 케이스)
Invoke-ApiTest -TestName "SEARCH_MAILS_EMPTY_QUERY" -Method "GET" -Endpoint "/mail-convenience/search?q=&page=1&limit=10" -Headers $UserHeaders -ExpectedStatus 400 -Description "빈 검색어로 검색 (실패 예상)"

# 4.10 잘못된 페이지 번호로 검색 (실패 케이스)
Invoke-ApiTest -TestName "SEARCH_MAILS_INVALID_PAGE" -Method "GET" -Endpoint "/mail-convenience/search?q=test&page=0&limit=10" -Headers $UserHeaders -ExpectedStatus 400 -Description "잘못된 페이지 번호로 검색 (실패 예상)"

# ===================================================================
# 5. 메일 필터 관리 테스트
# ===================================================================
Write-Host "`n=== 5. 메일 필터 관리 테스트 ===" -ForegroundColor Magenta

# 5.1 메일 필터 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_MAIL_FILTERS_USER" -Method "GET" -Endpoint "/mail-convenience/filters" -Headers $UserHeaders -Description "사용자 메일 필터 목록 조회"

# 5.2 메일 필터 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_FILTERS_ADMIN" -Method "GET" -Endpoint "/mail-convenience/filters" -Headers $AdminHeaders -Description "관리자 메일 필터 목록 조회"

# 5.3 메일 필터 생성 (사용자)
$CreateFilterData = @{
    name = "스팸 필터"
    description = "스팸 메일 자동 분류"
    conditions = @(
        @{
            field = "subject"
            operator = "contains"
            value = "스팸"
        },
        @{
            field = "sender"
            operator = "contains"
            value = "spam"
        }
    )
    actions = @(
        @{
            type = "move_to_folder"
            value = "spam"
        },
        @{
            type = "mark_as_read"
            value = "true"
        }
    )
    is_active = $true
}
Invoke-ApiTest -TestName "CREATE_MAIL_FILTER_USER" -Method "POST" -Endpoint "/mail-convenience/filters" -Headers $UserHeaders -Body $CreateFilterData -Description "사용자 메일 필터 생성"

# 5.4 메일 필터 생성 (관리자)
$CreateAdminFilterData = @{
    name = "중요 메일 필터"
    description = "중요 메일 자동 분류"
    conditions = @(
        @{
            field = "subject"
            operator = "contains"
            value = "긴급"
        }
    )
    actions = @(
        @{
            type = "mark_as_important"
            value = "true"
        }
    )
    is_active = $true
}
Invoke-ApiTest -TestName "CREATE_MAIL_FILTER_ADMIN" -Method "POST" -Endpoint "/mail-convenience/filters" -Headers $AdminHeaders -Body $CreateAdminFilterData -Description "관리자 메일 필터 생성"

# 5.5 잘못된 필터 조건으로 생성 시도 (실패 케이스)
$InvalidFilterData = @{
    name = "잘못된 필터"
    conditions = @(
        @{
            field = "invalid_field"
            operator = "invalid_operator"
            value = "test"
        }
    )
    actions = @()
}
Invoke-ApiTest -TestName "CREATE_INVALID_MAIL_FILTER" -Method "POST" -Endpoint "/mail-convenience/filters" -Headers $UserHeaders -Body $InvalidFilterData -ExpectedStatus 400 -Description "잘못된 필터 조건으로 생성 시도 (실패 예상)"

# 5.6 메일 필터 정보 조회
Invoke-ApiTest -TestName "GET_MAIL_FILTER_INFO" -Method "GET" -Endpoint "/mail-convenience/filters/1" -Headers $UserHeaders -Description "특정 메일 필터 정보 조회"

# 5.7 존재하지 않는 필터 조회 (실패 케이스)
Invoke-ApiTest -TestName "GET_NONEXISTENT_FILTER" -Method "GET" -Endpoint "/mail-convenience/filters/99999" -Headers $UserHeaders -ExpectedStatus 404 -Description "존재하지 않는 필터 조회 (실패 예상)"

# 5.8 메일 필터 수정
$UpdateFilterData = @{
    name = "수정된 스팸 필터"
    description = "수정된 스팸 메일 자동 분류"
    conditions = @(
        @{
            field = "subject"
            operator = "contains"
            value = "광고"
        }
    )
    actions = @(
        @{
            type = "delete"
            value = "true"
        }
    )
    is_active = $false
}
Invoke-ApiTest -TestName "UPDATE_MAIL_FILTER" -Method "PUT" -Endpoint "/mail-convenience/filters/1" -Headers $UserHeaders -Body $UpdateFilterData -Description "메일 필터 수정"

# 5.9 다른 사용자 필터 수정 시도 (실패 케이스)
Invoke-ApiTest -TestName "UPDATE_OTHER_USER_FILTER" -Method "PUT" -Endpoint "/mail-convenience/filters/2" -Headers $UserHeaders -Body $UpdateFilterData -ExpectedStatus 403 -Description "다른 사용자 필터 수정 시도 (실패 예상)"

# 5.10 메일 필터 활성화/비활성화
$ToggleFilterData = @{
    is_active = $true
}
Invoke-ApiTest -TestName "TOGGLE_MAIL_FILTER" -Method "PATCH" -Endpoint "/mail-convenience/filters/1/toggle" -Headers $UserHeaders -Body $ToggleFilterData -Description "메일 필터 활성화/비활성화"

# ===================================================================
# 6. 메일 라벨 관리 테스트
# ===================================================================
Write-Host "`n=== 6. 메일 라벨 관리 테스트 ===" -ForegroundColor Magenta

# 6.1 메일 라벨 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_MAIL_LABELS_USER" -Method "GET" -Endpoint "/mail-convenience/labels" -Headers $UserHeaders -Description "사용자 메일 라벨 목록 조회"

# 6.2 메일 라벨 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_LABELS_ADMIN" -Method "GET" -Endpoint "/mail-convenience/labels" -Headers $AdminHeaders -Description "관리자 메일 라벨 목록 조회"

# 6.3 메일 라벨 생성 (사용자)
$CreateLabelData = @{
    name = "중요"
    color = "#F44336"
    description = "중요한 메일 표시용"
}
Invoke-ApiTest -TestName "CREATE_MAIL_LABEL_USER" -Method "POST" -Endpoint "/mail-convenience/labels" -Headers $UserHeaders -Body $CreateLabelData -Description "사용자 메일 라벨 생성"

# 6.4 메일 라벨 생성 (관리자)
$CreateAdminLabelData = @{
    name = "업무"
    color = "#2196F3"
    description = "업무 관련 메일"
}
Invoke-ApiTest -TestName "CREATE_MAIL_LABEL_ADMIN" -Method "POST" -Endpoint "/mail-convenience/labels" -Headers $AdminHeaders -Body $CreateAdminLabelData -Description "관리자 메일 라벨 생성"

# 6.5 중복 라벨 생성 시도 (실패 케이스)
Invoke-ApiTest -TestName "CREATE_DUPLICATE_LABEL" -Method "POST" -Endpoint "/mail-convenience/labels" -Headers $UserHeaders -Body $CreateLabelData -ExpectedStatus 400 -Description "중복 라벨 생성 시도 (실패 예상)"

# 6.6 메일 라벨 정보 조회
Invoke-ApiTest -TestName "GET_MAIL_LABEL_INFO" -Method "GET" -Endpoint "/mail-convenience/labels/1" -Headers $UserHeaders -Description "특정 메일 라벨 정보 조회"

# 6.7 메일 라벨 수정
$UpdateLabelData = @{
    name = "매우 중요"
    color = "#FF5722"
    description = "매우 중요한 메일 표시용"
}
Invoke-ApiTest -TestName "UPDATE_MAIL_LABEL" -Method "PUT" -Endpoint "/mail-convenience/labels/1" -Headers $UserHeaders -Body $UpdateLabelData -Description "메일 라벨 수정"

# 6.8 메일에 라벨 적용
$ApplyLabelData = @{
    mail_ids = @("mail_001", "mail_002", "mail_003")
    label_id = 1
}
Invoke-ApiTest -TestName "APPLY_LABEL_TO_MAILS" -Method "POST" -Endpoint "/mail-convenience/labels/1/apply" -Headers $UserHeaders -Body $ApplyLabelData -Description "메일에 라벨 적용"

# 6.9 메일에서 라벨 제거
$RemoveLabelData = @{
    mail_ids = @("mail_001", "mail_002")
}
Invoke-ApiTest -TestName "REMOVE_LABEL_FROM_MAILS" -Method "POST" -Endpoint "/mail-convenience/labels/1/remove" -Headers $UserHeaders -Body $RemoveLabelData -Description "메일에서 라벨 제거"

# ===================================================================
# 7. 메일 템플릿 관리 테스트
# ===================================================================
Write-Host "`n=== 7. 메일 템플릿 관리 테스트 ===" -ForegroundColor Magenta

# 7.1 메일 템플릿 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_MAIL_TEMPLATES_USER" -Method "GET" -Endpoint "/mail-convenience/templates" -Headers $UserHeaders -Description "사용자 메일 템플릿 목록 조회"

# 7.2 메일 템플릿 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_TEMPLATES_ADMIN" -Method "GET" -Endpoint "/mail-convenience/templates" -Headers $AdminHeaders -Description "관리자 메일 템플릿 목록 조회"

# 7.3 메일 템플릿 생성 (사용자)
$CreateTemplateData = @{
    name = "회의 초대 템플릿"
    subject = "회의 초대: {{meeting_title}}"
    content = @"
안녕하세요 {{recipient_name}}님,

{{meeting_date}}에 {{meeting_title}} 회의에 참석해 주시기 바랍니다.

일시: {{meeting_date}} {{meeting_time}}
장소: {{meeting_location}}
안건: {{meeting_agenda}}

감사합니다.
{{sender_name}}
"@
    variables = @("meeting_title", "recipient_name", "meeting_date", "meeting_time", "meeting_location", "meeting_agenda", "sender_name")
    category = "business"
    is_public = $false
}
Invoke-ApiTest -TestName "CREATE_MAIL_TEMPLATE_USER" -Method "POST" -Endpoint "/mail-convenience/templates" -Headers $UserHeaders -Body $CreateTemplateData -Description "사용자 메일 템플릿 생성"

# 7.4 메일 템플릿 생성 (관리자)
$CreateAdminTemplateData = @{
    name = "공지사항 템플릿"
    subject = "[공지] {{notice_title}}"
    content = @"
전체 직원 여러분께,

{{notice_content}}

공지일: {{notice_date}}
담당자: {{manager_name}}

문의사항이 있으시면 언제든 연락 주시기 바랍니다.
"@
    variables = @("notice_title", "notice_content", "notice_date", "manager_name")
    category = "announcement"
    is_public = $true
}
Invoke-ApiTest -TestName "CREATE_MAIL_TEMPLATE_ADMIN" -Method "POST" -Endpoint "/mail-convenience/templates" -Headers $AdminHeaders -Body $CreateAdminTemplateData -Description "관리자 메일 템플릿 생성"

# 7.5 메일 템플릿 정보 조회
Invoke-ApiTest -TestName "GET_MAIL_TEMPLATE_INFO" -Method "GET" -Endpoint "/mail-convenience/templates/1" -Headers $UserHeaders -Description "특정 메일 템플릿 정보 조회"

# 7.6 메일 템플릿 수정
$UpdateTemplateData = @{
    name = "수정된 회의 초대 템플릿"
    subject = "[회의] {{meeting_title}} - {{meeting_date}}"
    content = @"
{{recipient_name}}님께,

{{meeting_title}} 회의에 초대드립니다.

📅 일시: {{meeting_date}} {{meeting_time}}
📍 장소: {{meeting_location}}
📋 안건: {{meeting_agenda}}

참석 여부를 회신해 주시기 바랍니다.

{{sender_name}} 드림
"@
    variables = @("meeting_title", "recipient_name", "meeting_date", "meeting_time", "meeting_location", "meeting_agenda", "sender_name")
    category = "business"
    is_public = $false
}
Invoke-ApiTest -TestName "UPDATE_MAIL_TEMPLATE" -Method "PUT" -Endpoint "/mail-convenience/templates/1" -Headers $UserHeaders -Body $UpdateTemplateData -Description "메일 템플릿 수정"

# 7.7 템플릿으로 메일 발송
$SendFromTemplateData = @{
    template_id = 1
    recipients = @("user02@test.com")
    variables = @{
        meeting_title = "프로젝트 킥오프 미팅"
        recipient_name = "김철수"
        meeting_date = "2024-01-25"
        meeting_time = "14:00"
        meeting_location = "회의실 A"
        meeting_agenda = "프로젝트 계획 수립 및 역할 분담"
        sender_name = "홍길동"
    }
}
Invoke-ApiTest -TestName "SEND_MAIL_FROM_TEMPLATE" -Method "POST" -Endpoint "/mail-convenience/templates/1/send" -Headers $UserHeaders -Body $SendFromTemplateData -Description "템플릿으로 메일 발송"

# 7.8 잘못된 변수로 템플릿 메일 발송 시도 (실패 케이스)
$InvalidTemplateData = @{
    template_id = 1
    recipients = @("user02@test.com")
    variables = @{
        wrong_variable = "잘못된 값"
    }
}
Invoke-ApiTest -TestName "SEND_MAIL_INVALID_TEMPLATE_VARS" -Method "POST" -Endpoint "/mail-convenience/templates/1/send" -Headers $UserHeaders -Body $InvalidTemplateData -ExpectedStatus 400 -Description "잘못된 변수로 템플릿 메일 발송 시도 (실패 예상)"

# ===================================================================
# 8. 메일 자동 응답 관리 테스트
# ===================================================================
Write-Host "`n=== 8. 메일 자동 응답 관리 테스트 ===" -ForegroundColor Magenta

# 8.1 자동 응답 설정 조회 (사용자)
Invoke-ApiTest -TestName "GET_AUTO_REPLY_USER" -Method "GET" -Endpoint "/mail-convenience/auto-reply" -Headers $UserHeaders -Description "사용자 자동 응답 설정 조회"

# 8.2 자동 응답 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_AUTO_REPLY_ADMIN" -Method "GET" -Endpoint "/mail-convenience/auto-reply" -Headers $AdminHeaders -Description "관리자 자동 응답 설정 조회"

# 8.3 자동 응답 설정 생성/수정 (사용자)
$AutoReplyData = @{
    is_enabled = $true
    subject = "자동 응답: 부재중입니다"
    message = @"
안녕하세요,

현재 휴가로 인해 부재중입니다.
2024년 1월 30일에 복귀 예정이며, 긴급한 사안은 대리인에게 연락 바랍니다.

대리인: 김대리 (kim.deputy@test.com)

감사합니다.
"@
    start_date = "2024-01-20"
    end_date = "2024-01-30"
    send_to_internal_only = $false
    max_replies_per_sender = 1
}
Invoke-ApiTest -TestName "SET_AUTO_REPLY_USER" -Method "POST" -Endpoint "/mail-convenience/auto-reply" -Headers $UserHeaders -Body $AutoReplyData -Description "사용자 자동 응답 설정"

# 8.4 자동 응답 설정 생성/수정 (관리자)
$AdminAutoReplyData = @{
    is_enabled = $true
    subject = "자동 응답: 관리자 부재중"
    message = @"
관리자가 현재 부재중입니다.
업무 관련 문의는 다음 연락처로 부탁드립니다.

- 기술 지원: tech@test.com
- 일반 문의: support@test.com

빠른 시일 내에 답변드리겠습니다.
"@
    start_date = "2024-01-22"
    end_date = "2024-01-24"
    send_to_internal_only = $true
    max_replies_per_sender = 2
}
Invoke-ApiTest -TestName "SET_AUTO_REPLY_ADMIN" -Method "POST" -Endpoint "/mail-convenience/auto-reply" -Headers $AdminHeaders -Body $AdminAutoReplyData -Description "관리자 자동 응답 설정"

# 8.5 자동 응답 비활성화
$DisableAutoReplyData = @{
    is_enabled = $false
}
Invoke-ApiTest -TestName "DISABLE_AUTO_REPLY" -Method "PATCH" -Endpoint "/mail-convenience/auto-reply/toggle" -Headers $UserHeaders -Body $DisableAutoReplyData -Description "자동 응답 비활성화"

# 8.6 자동 응답 통계 조회
Invoke-ApiTest -TestName "GET_AUTO_REPLY_STATS" -Method "GET" -Endpoint "/mail-convenience/auto-reply/stats" -Headers $UserHeaders -Description "자동 응답 통계 조회"

# ===================================================================
# 9. 메일 백업 및 복원 테스트
# ===================================================================
Write-Host "`n=== 9. 메일 백업 및 복원 테스트 ===" -ForegroundColor Magenta

# 9.1 메일 백업 요청 (사용자)
$BackupRequestData = @{
    backup_type = "full"
    include_attachments = $true
    date_range = @{
        start_date = "2024-01-01"
        end_date = "2024-01-20"
    }
    format = "mbox"
}
Invoke-ApiTest -TestName "REQUEST_MAIL_BACKUP_USER" -Method "POST" -Endpoint "/mail-convenience/backup" -Headers $UserHeaders -Body $BackupRequestData -Description "사용자 메일 백업 요청"

# 9.2 메일 백업 요청 (관리자)
$AdminBackupRequestData = @{
    backup_type = "incremental"
    include_attachments = $false
    date_range = @{
        start_date = "2024-01-15"
        end_date = "2024-01-20"
    }
    format = "eml"
}
Invoke-ApiTest -TestName "REQUEST_MAIL_BACKUP_ADMIN" -Method "POST" -Endpoint "/mail-convenience/backup" -Headers $AdminHeaders -Body $AdminBackupRequestData -Description "관리자 메일 백업 요청"

# 9.3 백업 상태 조회
Invoke-ApiTest -TestName "GET_BACKUP_STATUS" -Method "GET" -Endpoint "/mail-convenience/backup/status" -Headers $UserHeaders -Description "백업 상태 조회"

# 9.4 백업 목록 조회
Invoke-ApiTest -TestName "GET_BACKUP_LIST" -Method "GET" -Endpoint "/mail-convenience/backup/list" -Headers $UserHeaders -Description "백업 목록 조회"

# 9.5 백업 다운로드 (시뮬레이션)
Invoke-ApiTest -TestName "DOWNLOAD_BACKUP" -Method "GET" -Endpoint "/mail-convenience/backup/download/1" -Headers $UserHeaders -Description "백업 파일 다운로드"

# ===================================================================
# 10. 권한 및 보안 테스트
# ===================================================================
Write-Host "`n=== 10. 권한 및 보안 테스트 ===" -ForegroundColor Magenta

# 10.1 인증 없이 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_WITHOUT_AUTH" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -ExpectedStatus 401 -Description "인증 없이 메일함 접근 시도 (실패 예상)"

# 10.2 잘못된 토큰으로 접근 시도 (실패 케이스)
$InvalidHeaders = @{ "Authorization" = "Bearer invalid_token_12345" }
Invoke-ApiTest -TestName "ACCESS_WITH_INVALID_TOKEN" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -Headers $InvalidHeaders -ExpectedStatus 401 -Description "잘못된 토큰으로 접근 시도 (실패 예상)"

# 10.3 만료된 토큰으로 접근 시도 (시뮬레이션)
$ExpiredHeaders = @{ "Authorization" = "Bearer expired.token.here" }
Invoke-ApiTest -TestName "ACCESS_WITH_EXPIRED_TOKEN" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -Headers $ExpiredHeaders -ExpectedStatus 401 -Description "만료된 토큰으로 접근 시도 (실패 예상)"

# ===================================================================
# 11. 성능 및 부하 테스트
# ===================================================================
Write-Host "`n=== 11. 성능 및 부하 테스트 ===" -ForegroundColor Magenta

# 11.1 대량 메일 검색 (성능 테스트)
Invoke-ApiTest -TestName "SEARCH_LARGE_DATASET" -Method "GET" -Endpoint "/mail-convenience/search?q=*&page=1&limit=100" -Headers $UserHeaders -Description "대량 데이터 검색 성능 테스트"

# 11.2 복잡한 필터 조건 검색 (성능 테스트)
$ComplexSearchQuery = "subject=test&sender=admin&content=important&has_attachments=true&is_read=false&start_date=2024-01-01&end_date=2024-01-20"
Invoke-ApiTest -TestName "COMPLEX_SEARCH_PERFORMANCE" -Method "GET" -Endpoint "/mail-convenience/search?$ComplexSearchQuery&page=1&limit=50" -Headers $UserHeaders -Description "복잡한 검색 조건 성능 테스트"

# 11.3 연속 API 호출 (부하 테스트)
Write-Host "연속 API 호출 부하 테스트 시작..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    Invoke-ApiTest -TestName "LOAD_TEST_$i" -Method "GET" -Endpoint "/mail-convenience/mailboxes" -Headers $UserHeaders -Description "부하 테스트 $i/5"
    Start-Sleep -Milliseconds 100
}

# ===================================================================
# 12. 메일함 삭제 테스트 (정리)
# ===================================================================
Write-Host "`n=== 12. 메일함 삭제 테스트 (정리) ===" -ForegroundColor Magenta

# 12.1 메일함 삭제 (사용자)
Invoke-ApiTest -TestName "DELETE_MAILBOX_USER" -Method "DELETE" -Endpoint "/mail-convenience/mailboxes/1" -Headers $UserHeaders -Description "사용자 메일함 삭제"

# 12.2 메일함 삭제 (관리자)
Invoke-ApiTest -TestName "DELETE_MAILBOX_ADMIN" -Method "DELETE" -Endpoint "/mail-convenience/mailboxes/2" -Headers $AdminHeaders -Description "관리자 메일함 삭제"

# 12.3 이미 삭제된 메일함 삭제 시도 (실패 케이스)
Invoke-ApiTest -TestName "DELETE_ALREADY_DELETED_MAILBOX" -Method "DELETE" -Endpoint "/mail-convenience/mailboxes/1" -Headers $UserHeaders -ExpectedStatus 404 -Description "이미 삭제된 메일함 삭제 시도 (실패 예상)"

# 12.4 메일 필터 삭제
Invoke-ApiTest -TestName "DELETE_MAIL_FILTER" -Method "DELETE" -Endpoint "/mail-convenience/filters/1" -Headers $UserHeaders -Description "메일 필터 삭제"

# 12.5 메일 라벨 삭제
Invoke-ApiTest -TestName "DELETE_MAIL_LABEL" -Method "DELETE" -Endpoint "/mail-convenience/labels/1" -Headers $UserHeaders -Description "메일 라벨 삭제"

# 12.6 메일 템플릿 삭제
Invoke-ApiTest -TestName "DELETE_MAIL_TEMPLATE" -Method "DELETE" -Endpoint "/mail-convenience/templates/1" -Headers $UserHeaders -Description "메일 템플릿 삭제"

# ===================================================================
# 테스트 결과 요약 및 저장
# ===================================================================
Write-Host "`n=== 테스트 결과 요약 ===" -ForegroundColor Green

$TestEndTime = Get-Date
$TotalDuration = ($TestEndTime - $TestStartTime).TotalSeconds
$TotalTests = $TestResults.Count
$PassedTests = ($TestResults | Where-Object { $_.Status -eq "PASS" }).Count
$FailedTests = ($TestResults | Where-Object { $_.Status -eq "FAIL" }).Count
$SuccessRate = [math]::Round(($PassedTests / $TotalTests) * 100, 2)

Write-Host "테스트 완료 시간: $TestEndTime" -ForegroundColor Yellow
Write-Host "총 테스트 시간: $([math]::Round($TotalDuration, 2))초" -ForegroundColor Yellow
Write-Host "총 테스트 수: $TotalTests" -ForegroundColor White
Write-Host "성공: $PassedTests" -ForegroundColor Green
Write-Host "실패: $FailedTests" -ForegroundColor Red
Write-Host "성공률: $SuccessRate%" -ForegroundColor $(if ($SuccessRate -ge 90) { "Green" } elseif ($SuccessRate -ge 70) { "Yellow" } else { "Red" })

# 실패한 테스트 상세 정보 출력
if ($FailedTests -gt 0) {
    Write-Host "`n=== 실패한 테스트 상세 ===" -ForegroundColor Red
    $TestResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "❌ $($_.TestName): $($_.Error)" -ForegroundColor Red
    }
}

# 성능 통계
$AvgDuration = [math]::Round(($TestResults | Measure-Object -Property Duration -Average).Average, 2)
$MaxDuration = [math]::Round(($TestResults | Measure-Object -Property Duration -Maximum).Maximum, 2)
$MinDuration = [math]::Round(($TestResults | Measure-Object -Property Duration -Minimum).Minimum, 2)

Write-Host "`n=== 성능 통계 ===" -ForegroundColor Cyan
Write-Host "평균 응답 시간: ${AvgDuration}ms" -ForegroundColor White
Write-Host "최대 응답 시간: ${MaxDuration}ms" -ForegroundColor White
Write-Host "최소 응답 시간: ${MinDuration}ms" -ForegroundColor White

# 테스트 결과를 JSON 파일로 저장
$TestSummary = @{
    TestInfo = @{
        StartTime = $TestStartTime
        EndTime = $TestEndTime
        TotalDuration = $TotalDuration
        BaseUrl = $BaseUrl
    }
    Statistics = @{
        TotalTests = $TotalTests
        PassedTests = $PassedTests
        FailedTests = $FailedTests
        SuccessRate = $SuccessRate
        AvgDuration = $AvgDuration
        MaxDuration = $MaxDuration
        MinDuration = $MinDuration
    }
    TestResults = $TestResults
}

$OutputFile = "C:\Users\moon4\skyboot.mail2\test\mail_convenience_router_test_results.json"
$TestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "`n테스트 결과가 저장되었습니다: $OutputFile" -ForegroundColor Green
Write-Host "=== SkyBoot Mail 편의 라우터 테스트 완료 ===" -ForegroundColor Green