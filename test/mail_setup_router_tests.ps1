# ===================================================================
# SkyBoot Mail SaaS - 메일 설정 라우터 테스트 시나리오
# 파일: mail_setup_router_tests.ps1
# 설명: mail_setup_router.py의 모든 엔드포인트 테스트
# 작성자: SkyBoot Mail Team
# 작성일: 2024-01-20
# ===================================================================

# 테스트 설정
$BaseUrl = "http://localhost:8001/api/v1"
$TestResults = @()
$TestStartTime = Get-Date

Write-Host "=== SkyBoot Mail 설정 라우터 테스트 시작 ===" -ForegroundColor Green
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
    email = "user01@test.com"
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
    email = "admin01@test.com"
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
# 3. 메일 서버 설정 테스트
# ===================================================================
Write-Host "`n=== 3. 메일 서버 설정 테스트 ===" -ForegroundColor Magenta

# 3.1 메일 서버 설정 조회 (사용자)
Invoke-ApiTest -TestName "GET_MAIL_SERVER_CONFIG_USER" -Method "GET" -Endpoint "/mail-setup/server/config" -Headers $UserHeaders -Description "사용자 메일 서버 설정 조회"

# 3.2 메일 서버 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_SERVER_CONFIG_ADMIN" -Method "GET" -Endpoint "/mail-setup/server/config" -Headers $AdminHeaders -Description "관리자 메일 서버 설정 조회"

# 3.3 SMTP 서버 설정 업데이트 (관리자)
$SMTPConfigData = @{
    smtp_server = @{
        host = "smtp.test.com"
        port = 587
        use_tls = $true
        use_ssl = $false
        authentication_required = $true
        username = "smtp_user@test.com"
        password = "smtp_password_123"
        timeout = 30
        max_connections = 100
        connection_pool_size = 10
    }
    security = @{
        enable_starttls = $true
        require_tls = $true
        tls_version = "1.2"
        cipher_suites = @("ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-RSA-AES128-GCM-SHA256")
    }
    rate_limiting = @{
        max_emails_per_hour = 1000
        max_emails_per_day = 10000
        max_recipients_per_email = 100
        burst_limit = 50
    }
}
Invoke-ApiTest -TestName "UPDATE_SMTP_CONFIG" -Method "PUT" -Endpoint "/mail-setup/server/smtp" -Headers $AdminHeaders -Body $SMTPConfigData -Description "SMTP 서버 설정 업데이트"

# 3.4 IMAP 서버 설정 업데이트 (관리자)
$IMAPConfigData = @{
    imap_server = @{
        host = "imap.test.com"
        port = 993
        use_ssl = $true
        authentication_methods = @("PLAIN", "LOGIN", "CRAM-MD5")
        max_connections = 200
        idle_timeout = 1800
        connection_timeout = 30
    }
    mailbox_settings = @{
        default_quota = "1GB"
        max_quota = "10GB"
        auto_create_folders = $true
        default_folders = @("INBOX", "Sent", "Drafts", "Trash", "Spam")
    }
    security = @{
        require_ssl = $true
        enable_compression = $true
        max_login_attempts = 3
        lockout_duration = 300
    }
}
Invoke-ApiTest -TestName "UPDATE_IMAP_CONFIG" -Method "PUT" -Endpoint "/mail-setup/server/imap" -Headers $AdminHeaders -Body $IMAPConfigData -Description "IMAP 서버 설정 업데이트"

# 3.5 POP3 서버 설정 업데이트 (관리자)
$POP3ConfigData = @{
    pop3_server = @{
        host = "pop3.test.com"
        port = 995
        use_ssl = $true
        authentication_methods = @("USER", "APOP")
        max_connections = 50
        session_timeout = 600
    }
    settings = @{
        leave_messages_on_server = $false
        delete_after_days = 30
        max_message_size = "50MB"
    }
    security = @{
        require_ssl = $true
        max_login_attempts = 3
        lockout_duration = 300
    }
}
Invoke-ApiTest -TestName "UPDATE_POP3_CONFIG" -Method "PUT" -Endpoint "/mail-setup/server/pop3" -Headers $AdminHeaders -Body $POP3ConfigData -Description "POP3 서버 설정 업데이트"

# 3.6 메일 서버 연결 테스트 (관리자)
$ConnectionTestData = @{
    server_type = "smtp"
    test_email = "test@test.com"
    test_message = "메일 서버 연결 테스트"
}
Invoke-ApiTest -TestName "TEST_MAIL_SERVER_CONNECTION" -Method "POST" -Endpoint "/mail-setup/server/test-connection" -Headers $AdminHeaders -Body $ConnectionTestData -Description "메일 서버 연결 테스트"

# 3.7 메일 서버 상태 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_SERVER_STATUS" -Method "GET" -Endpoint "/mail-setup/server/status" -Headers $AdminHeaders -Description "메일 서버 상태 조회"

# 3.8 메일 서버 로그 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_SERVER_LOGS" -Method "GET" -Endpoint "/mail-setup/server/logs?level=info&limit=100" -Headers $AdminHeaders -Description "메일 서버 로그 조회"

# 3.9 잘못된 서버 설정 업데이트 시도 (실패 케이스)
$InvalidSMTPConfig = @{
    smtp_server = @{
        host = ""
        port = -1
        use_tls = "invalid_boolean"
    }
}
Invoke-ApiTest -TestName "UPDATE_INVALID_SMTP_CONFIG" -Method "PUT" -Endpoint "/mail-setup/server/smtp" -Headers $AdminHeaders -Body $InvalidSMTPConfig -ExpectedStatus 400 -Description "잘못된 SMTP 설정 업데이트 시도 (실패 예상)"

# ===================================================================
# 4. 도메인 관리 테스트
# ===================================================================
Write-Host "`n=== 4. 도메인 관리 테스트 ===" -ForegroundColor Magenta

# 4.1 도메인 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_DOMAINS_USER" -Method "GET" -Endpoint "/mail-setup/domains" -Headers $UserHeaders -Description "사용자 도메인 목록 조회"

# 4.2 도메인 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_DOMAINS_ADMIN" -Method "GET" -Endpoint "/mail-setup/domains" -Headers $AdminHeaders -Description "관리자 도메인 목록 조회"

# 4.3 새 도메인 추가 (관리자)
$NewDomainData = @{
    domain_name = "newdomain.test.com"
    description = "새로운 테스트 도메인"
    is_primary = $false
    is_active = $true
    mx_records = @(
        @{
            priority = 10
            hostname = "mail.newdomain.test.com"
        },
        @{
            priority = 20
            hostname = "mail2.newdomain.test.com"
        }
    )
    spf_record = "v=spf1 include:_spf.test.com ~all"
    dkim_settings = @{
        enabled = $true
        selector = "default"
        key_size = 2048
    }
    dmarc_policy = @{
        policy = "quarantine"
        percentage = 100
        rua = @("mailto:dmarc@newdomain.test.com")
        ruf = @("mailto:dmarc-forensic@newdomain.test.com")
    }
}
Invoke-ApiTest -TestName "ADD_NEW_DOMAIN" -Method "POST" -Endpoint "/mail-setup/domains" -Headers $AdminHeaders -Body $NewDomainData -Description "새 도메인 추가"

# 4.4 서브도메인 추가 (관리자)
$SubdomainData = @{
    domain_name = "mail.newdomain.test.com"
    parent_domain = "newdomain.test.com"
    description = "메일 전용 서브도메인"
    is_active = $true
    subdomain_type = "mail"
    inherit_parent_settings = $true
}
Invoke-ApiTest -TestName "ADD_SUBDOMAIN" -Method "POST" -Endpoint "/mail-setup/domains/subdomain" -Headers $AdminHeaders -Body $SubdomainData -Description "서브도메인 추가"

# 4.5 도메인 정보 조회
Invoke-ApiTest -TestName "GET_DOMAIN_INFO" -Method "GET" -Endpoint "/mail-setup/domains/newdomain.test.com" -Headers $AdminHeaders -Description "특정 도메인 정보 조회"

# 4.6 도메인 설정 수정 (관리자)
$UpdateDomainData = @{
    description = "수정된 테스트 도메인"
    is_active = $true
    spf_record = "v=spf1 include:_spf.test.com include:_spf.google.com ~all"
    dkim_settings = @{
        enabled = $true
        selector = "updated"
        key_size = 4096
        rotation_enabled = $true
        rotation_interval_days = 90
    }
    dmarc_policy = @{
        policy = "reject"
        percentage = 100
        rua = @("mailto:dmarc@newdomain.test.com")
        ruf = @("mailto:dmarc-forensic@newdomain.test.com")
        adkim = "s"
        aspf = "s"
    }
}
Invoke-ApiTest -TestName "UPDATE_DOMAIN_SETTINGS" -Method "PUT" -Endpoint "/mail-setup/domains/newdomain.test.com" -Headers $AdminHeaders -Body $UpdateDomainData -Description "도메인 설정 수정"

# 4.7 도메인 DNS 레코드 검증 (관리자)
$DNSVerificationData = @{
    domain_name = "newdomain.test.com"
    record_types = @("MX", "SPF", "DKIM", "DMARC")
    check_propagation = $true
}
Invoke-ApiTest -TestName "VERIFY_DOMAIN_DNS" -Method "POST" -Endpoint "/mail-setup/domains/verify-dns" -Headers $AdminHeaders -Body $DNSVerificationData -Description "도메인 DNS 레코드 검증"

# 4.8 도메인 인증서 설정 (관리자)
$CertificateData = @{
    domain_name = "newdomain.test.com"
    certificate_type = "letsencrypt"
    auto_renewal = $true
    certificate_data = @{
        certificate = "-----BEGIN CERTIFICATE-----\n[인증서 내용 시뮬레이션]\n-----END CERTIFICATE-----"
        private_key = "-----BEGIN PRIVATE KEY-----\n[개인키 내용 시뮬레이션]\n-----END PRIVATE KEY-----"
        chain = "-----BEGIN CERTIFICATE-----\n[체인 인증서 내용 시뮬레이션]\n-----END CERTIFICATE-----"
    }
    expiry_notification_days = 30
}
Invoke-ApiTest -TestName "SETUP_DOMAIN_CERTIFICATE" -Method "POST" -Endpoint "/mail-setup/domains/certificate" -Headers $AdminHeaders -Body $CertificateData -Description "도메인 인증서 설정"

# 4.9 도메인 별칭 설정 (관리자)
$DomainAliasData = @{
    primary_domain = "newdomain.test.com"
    alias_domains = @("alias1.test.com", "alias2.test.com")
    redirect_type = "permanent"
    preserve_path = $true
}
Invoke-ApiTest -TestName "SETUP_DOMAIN_ALIASES" -Method "POST" -Endpoint "/mail-setup/domains/aliases" -Headers $AdminHeaders -Body $DomainAliasData -Description "도메인 별칭 설정"

# 4.10 중복 도메인 추가 시도 (실패 케이스)
$DuplicateDomainData = @{
    domain_name = "newdomain.test.com"
    description = "중복 도메인"
}
Invoke-ApiTest -TestName "ADD_DUPLICATE_DOMAIN" -Method "POST" -Endpoint "/mail-setup/domains" -Headers $AdminHeaders -Body $DuplicateDomainData -ExpectedStatus 409 -Description "중복 도메인 추가 시도 (실패 예상)"

# ===================================================================
# 5. 메일박스 및 사용자 계정 설정 테스트
# ===================================================================
Write-Host "`n=== 5. 메일박스 및 사용자 계정 설정 테스트 ===" -ForegroundColor Magenta

# 5.1 메일박스 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_MAILBOXES_ADMIN" -Method "GET" -Endpoint "/mail-setup/mailboxes?page=1&limit=20" -Headers $AdminHeaders -Description "관리자 메일박스 목록 조회"

# 5.2 메일박스 생성 (관리자)
$NewMailboxData = @{
    email = "newuser@newdomain.test.com"
    password = "SecurePassword123!"
    display_name = "새로운 사용자"
    quota = "2GB"
    enabled = $true
    domain = "newdomain.test.com"
    mailbox_settings = @{
        auto_create_folders = $true
        default_folders = @("INBOX", "Sent", "Drafts", "Trash", "Spam", "Archive")
        spam_threshold = 5.0
        virus_scanning = $true
    }
    forwarding = @{
        enabled = $false
        forward_to = @()
        keep_local_copy = $true
    }
    auto_reply = @{
        enabled = $false
        subject = ""
        message = ""
        start_date = $null
        end_date = $null
    }
}
Invoke-ApiTest -TestName "CREATE_MAILBOX" -Method "POST" -Endpoint "/mail-setup/mailboxes" -Headers $AdminHeaders -Body $NewMailboxData -Description "새 메일박스 생성"

# 5.3 메일박스 정보 조회
Invoke-ApiTest -TestName "GET_MAILBOX_INFO" -Method "GET" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com" -Headers $AdminHeaders -Description "특정 메일박스 정보 조회"

# 5.4 메일박스 설정 수정 (관리자)
$UpdateMailboxData = @{
    display_name = "수정된 사용자 이름"
    quota = "5GB"
    enabled = $true
    mailbox_settings = @{
        spam_threshold = 3.0
        virus_scanning = $true
        auto_delete_spam_days = 30
        auto_delete_trash_days = 30
    }
    forwarding = @{
        enabled = $true
        forward_to = @("backup@test.com")
        keep_local_copy = $true
    }
}
Invoke-ApiTest -TestName "UPDATE_MAILBOX_SETTINGS" -Method "PUT" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com" -Headers $AdminHeaders -Body $UpdateMailboxData -Description "메일박스 설정 수정"

# 5.5 메일박스 비밀번호 변경 (관리자)
$PasswordChangeData = @{
    new_password = "NewSecurePassword456!"
    force_change_on_login = $true
}
Invoke-ApiTest -TestName "CHANGE_MAILBOX_PASSWORD" -Method "PUT" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com/password" -Headers $AdminHeaders -Body $PasswordChangeData -Description "메일박스 비밀번호 변경"

# 5.6 메일박스 할당량 조회
Invoke-ApiTest -TestName "GET_MAILBOX_QUOTA" -Method "GET" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com/quota" -Headers $AdminHeaders -Description "메일박스 할당량 조회"

# 5.7 메일박스 사용량 통계 조회
Invoke-ApiTest -TestName "GET_MAILBOX_USAGE_STATS" -Method "GET" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com/stats" -Headers $AdminHeaders -Description "메일박스 사용량 통계 조회"

# 5.8 메일박스 백업 생성 (관리자)
$BackupData = @{
    mailbox = "newuser@newdomain.test.com"
    backup_type = "full"
    include_attachments = $true
    compression = $true
    encryption = $true
    retention_days = 90
}
Invoke-ApiTest -TestName "CREATE_MAILBOX_BACKUP" -Method "POST" -Endpoint "/mail-setup/mailboxes/backup" -Headers $AdminHeaders -Body $BackupData -Description "메일박스 백업 생성"

# 5.9 메일박스 복원 (관리자)
$RestoreData = @{
    mailbox = "newuser@newdomain.test.com"
    backup_id = "backup_001"
    restore_type = "selective"
    date_range = @{
        start_date = "2024-01-01"
        end_date = "2024-01-31"
    }
    overwrite_existing = $false
}
Invoke-ApiTest -TestName "RESTORE_MAILBOX" -Method "POST" -Endpoint "/mail-setup/mailboxes/restore" -Headers $AdminHeaders -Body $RestoreData -Description "메일박스 복원"

# 5.10 잘못된 이메일 형식으로 메일박스 생성 시도 (실패 케이스)
$InvalidMailboxData = @{
    email = "invalid-email-format"
    password = "weak"
    quota = "invalid_quota"
}
Invoke-ApiTest -TestName "CREATE_INVALID_MAILBOX" -Method "POST" -Endpoint "/mail-setup/mailboxes" -Headers $AdminHeaders -Body $InvalidMailboxData -ExpectedStatus 400 -Description "잘못된 이메일 형식으로 메일박스 생성 시도 (실패 예상)"

# ===================================================================
# 6. 메일 라우팅 및 전달 규칙 테스트
# ===================================================================
Write-Host "`n=== 6. 메일 라우팅 및 전달 규칙 테스트 ===" -ForegroundColor Magenta

# 6.1 라우팅 규칙 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_ROUTING_RULES" -Method "GET" -Endpoint "/mail-setup/routing/rules" -Headers $AdminHeaders -Description "라우팅 규칙 목록 조회"

# 6.2 새 라우팅 규칙 생성 (관리자)
$RoutingRuleData = @{
    name = "고객 지원 라우팅"
    description = "고객 지원 메일 자동 라우팅"
    priority = 1
    is_active = $true
    conditions = @{
        operator = "OR"
        rules = @(
            @{
                field = "recipient"
                operator = "equals"
                value = "support@newdomain.test.com"
            },
            @{
                field = "subject"
                operator = "contains"
                value = "지원"
            }
        )
    }
    actions = @(
        @{
            type = "forward_to"
            value = "support-team@newdomain.test.com"
        },
        @{
            type = "add_header"
            value = "X-Support-Routing: auto-routed"
        },
        @{
            type = "set_priority"
            value = "high"
        }
    )
}
Invoke-ApiTest -TestName "CREATE_ROUTING_RULE" -Method "POST" -Endpoint "/mail-setup/routing/rules" -Headers $AdminHeaders -Body $RoutingRuleData -Description "새 라우팅 규칙 생성"

# 6.3 조건부 라우팅 규칙 생성 (관리자)
$ConditionalRoutingData = @{
    name = "시간 기반 라우팅"
    description = "업무시간에 따른 메일 라우팅"
    priority = 2
    is_active = $true
    schedule = @{
        business_hours = @{
            start_time = "09:00"
            end_time = "18:00"
            timezone = "Asia/Seoul"
            weekdays_only = $true
        }
    }
    conditions = @{
        operator = "AND"
        rules = @(
            @{
                field = "recipient_domain"
                operator = "equals"
                value = "newdomain.test.com"
            },
            @{
                field = "current_time"
                operator = "outside_business_hours"
                value = "09:00-18:00"
            }
        )
    }
    actions = @(
        @{
            type = "forward_to"
            value = "after-hours@newdomain.test.com"
        },
        @{
            type = "auto_reply"
            value = "업무시간 외 메일입니다. 다음 업무일에 확인하겠습니다."
        }
    )
}
Invoke-ApiTest -TestName "CREATE_CONDITIONAL_ROUTING" -Method "POST" -Endpoint "/mail-setup/routing/rules" -Headers $AdminHeaders -Body $ConditionalRoutingData -Description "조건부 라우팅 규칙 생성"

# 6.4 라우팅 규칙 정보 조회
Invoke-ApiTest -TestName "GET_ROUTING_RULE_INFO" -Method "GET" -Endpoint "/mail-setup/routing/rules/1" -Headers $AdminHeaders -Description "특정 라우팅 규칙 정보 조회"

# 6.5 라우팅 규칙 수정 (관리자)
$UpdateRoutingData = @{
    name = "수정된 고객 지원 라우팅"
    description = "업데이트된 고객 지원 메일 자동 라우팅"
    priority = 1
    is_active = $true
    actions = @(
        @{
            type = "forward_to"
            value = "new-support-team@newdomain.test.com"
        },
        @{
            type = "add_label"
            value = "customer-support"
        }
    )
}
Invoke-ApiTest -TestName "UPDATE_ROUTING_RULE" -Method "PUT" -Endpoint "/mail-setup/routing/rules/1" -Headers $AdminHeaders -Body $UpdateRoutingData -Description "라우팅 규칙 수정"

# 6.6 라우팅 규칙 테스트 (관리자)
$RoutingTestData = @{
    test_email = @{
        sender = "customer@external.com"
        recipient = "support@newdomain.test.com"
        subject = "지원 요청"
        content = "도움이 필요합니다."
    }
    rule_id = 1
}
Invoke-ApiTest -TestName "TEST_ROUTING_RULE" -Method "POST" -Endpoint "/mail-setup/routing/rules/test" -Headers $AdminHeaders -Body $RoutingTestData -Description "라우팅 규칙 테스트"

# 6.7 전역 전달 설정 (관리자)
$GlobalForwardingData = @{
    enabled = $true
    default_forward_to = "archive@newdomain.test.com"
    forward_all_external = $false
    forward_all_internal = $false
    exceptions = @("admin@newdomain.test.com", "security@newdomain.test.com")
    retention_policy = @{
        keep_original = $true
        delete_after_days = 365
    }
}
Invoke-ApiTest -TestName "SETUP_GLOBAL_FORWARDING" -Method "PUT" -Endpoint "/mail-setup/routing/global-forwarding" -Headers $AdminHeaders -Body $GlobalForwardingData -Description "전역 전달 설정"

# 6.8 라우팅 통계 조회 (관리자)
Invoke-ApiTest -TestName "GET_ROUTING_STATISTICS" -Method "GET" -Endpoint "/mail-setup/routing/stats?period=30d" -Headers $AdminHeaders -Description "라우팅 통계 조회"

# ===================================================================
# 7. 보안 및 인증 설정 테스트
# ===================================================================
Write-Host "`n=== 7. 보안 및 인증 설정 테스트 ===" -ForegroundColor Magenta

# 7.1 보안 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_SECURITY_SETTINGS" -Method "GET" -Endpoint "/mail-setup/security/settings" -Headers $AdminHeaders -Description "보안 설정 조회"

# 7.2 인증 정책 설정 (관리자)
$AuthPolicyData = @{
    password_policy = @{
        min_length = 12
        require_uppercase = $true
        require_lowercase = $true
        require_numbers = $true
        require_special_chars = $true
        max_age_days = 90
        history_count = 5
        lockout_attempts = 5
        lockout_duration_minutes = 30
    }
    two_factor_auth = @{
        enabled = $true
        required_for_admin = $true
        methods = @("totp", "sms", "email")
        backup_codes_count = 10
    }
    session_management = @{
        max_concurrent_sessions = 3
        idle_timeout_minutes = 30
        absolute_timeout_hours = 8
        secure_cookies = $true
    }
}
Invoke-ApiTest -TestName "UPDATE_AUTH_POLICY" -Method "PUT" -Endpoint "/mail-setup/security/auth-policy" -Headers $AdminHeaders -Body $AuthPolicyData -Description "인증 정책 설정"

# 7.3 IP 화이트리스트 설정 (관리자)
$IPWhitelistData = @{
    enabled = $true
    whitelist = @(
        @{
            ip_address = "192.168.1.0/24"
            description = "내부 네트워크"
            enabled = $true
        },
        @{
            ip_address = "203.0.113.10"
            description = "외부 파트너"
            enabled = $true
        }
    )
    blacklist = @(
        @{
            ip_address = "198.51.100.0/24"
            description = "차단된 네트워크"
            enabled = $true
        }
    )
    default_action = "deny"
}
Invoke-ApiTest -TestName "SETUP_IP_WHITELIST" -Method "PUT" -Endpoint "/mail-setup/security/ip-whitelist" -Headers $AdminHeaders -Body $IPWhitelistData -Description "IP 화이트리스트 설정"

# 7.4 암호화 설정 (관리자)
$EncryptionSettingsData = @{
    transport_encryption = @{
        require_tls = $true
        min_tls_version = "1.2"
        cipher_suites = @("ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-RSA-AES128-GCM-SHA256")
        hsts_enabled = $true
        hsts_max_age = 31536000
    }
    storage_encryption = @{
        encrypt_at_rest = $true
        encryption_algorithm = "AES-256"
        key_rotation_days = 90
        backup_encryption = $true
    }
    message_encryption = @{
        auto_encrypt_external = $false
        auto_encrypt_internal = $false
        pgp_enabled = $true
        smime_enabled = $true
    }
}
Invoke-ApiTest -TestName "UPDATE_ENCRYPTION_SETTINGS" -Method "PUT" -Endpoint "/mail-setup/security/encryption" -Headers $AdminHeaders -Body $EncryptionSettingsData -Description "암호화 설정"

# 7.5 감사 로그 설정 (관리자)
$AuditLogSettingsData = @{
    enabled = $true
    log_level = "detailed"
    events_to_log = @(
        "login_success",
        "login_failure",
        "mail_send",
        "mail_receive",
        "config_change",
        "user_creation",
        "user_deletion",
        "permission_change"
    )
    retention_days = 365
    export_format = "json"
    real_time_alerts = @{
        enabled = $true
        alert_on = @("multiple_login_failures", "config_changes", "suspicious_activity")
        notification_email = "security@newdomain.test.com"
    }
}
Invoke-ApiTest -TestName "SETUP_AUDIT_LOGGING" -Method "PUT" -Endpoint "/mail-setup/security/audit-log" -Headers $AdminHeaders -Body $AuditLogSettingsData -Description "감사 로그 설정"

# 7.6 보안 스캔 실행 (관리자)
$SecurityScanData = @{
    scan_type = "comprehensive"
    targets = @("mail_server", "user_accounts", "configurations", "certificates")
    include_vulnerability_scan = $true
    include_compliance_check = $true
}
Invoke-ApiTest -TestName "RUN_SECURITY_SCAN" -Method "POST" -Endpoint "/mail-setup/security/scan" -Headers $AdminHeaders -Body $SecurityScanData -Description "보안 스캔 실행"

# 7.7 보안 스캔 결과 조회 (관리자)
Invoke-ApiTest -TestName "GET_SECURITY_SCAN_RESULTS" -Method "GET" -Endpoint "/mail-setup/security/scan/results?latest=true" -Headers $AdminHeaders -Description "보안 스캔 결과 조회"

# ===================================================================
# 8. 모니터링 및 알림 설정 테스트
# ===================================================================
Write-Host "`n=== 8. 모니터링 및 알림 설정 테스트 ===" -ForegroundColor Magenta

# 8.1 모니터링 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_MONITORING_SETTINGS" -Method "GET" -Endpoint "/mail-setup/monitoring/settings" -Headers $AdminHeaders -Description "모니터링 설정 조회"

# 8.2 알림 규칙 설정 (관리자)
$AlertRulesData = @{
    rules = @(
        @{
            name = "메일 서버 다운"
            description = "메일 서버 서비스 중단 감지"
            metric = "server_status"
            condition = "equals"
            threshold = "down"
            severity = "critical"
            notification_channels = @("email", "sms", "webhook")
            cooldown_minutes = 5
        },
        @{
            name = "높은 메일 볼륨"
            description = "비정상적으로 높은 메일 발송량 감지"
            metric = "mail_volume_per_hour"
            condition = "greater_than"
            threshold = 1000
            severity = "warning"
            notification_channels = @("email")
            cooldown_minutes = 30
        },
        @{
            name = "디스크 사용량 경고"
            description = "디스크 사용량 임계값 초과"
            metric = "disk_usage_percentage"
            condition = "greater_than"
            threshold = 85
            severity = "warning"
            notification_channels = @("email", "webhook")
            cooldown_minutes = 60
        }
    )
}
Invoke-ApiTest -TestName "SETUP_ALERT_RULES" -Method "PUT" -Endpoint "/mail-setup/monitoring/alert-rules" -Headers $AdminHeaders -Body $AlertRulesData -Description "알림 규칙 설정"

# 8.3 알림 채널 설정 (관리자)
$NotificationChannelsData = @{
    email = @{
        enabled = $true
        recipients = @("admin@newdomain.test.com", "ops@newdomain.test.com")
        smtp_settings = @{
            server = "smtp.newdomain.test.com"
            port = 587
            use_tls = $true
            username = "alerts@newdomain.test.com"
            password = "alert_password_123"
        }
    }
    sms = @{
        enabled = $true
        provider = "twilio"
        recipients = @("+821012345678", "+821087654321")
        api_key = "twilio_api_key"
        api_secret = "twilio_api_secret"
    }
    webhook = @{
        enabled = $true
        urls = @(
            @{
                url = "https://example.com/webhook/dummy-url-for-testing"
                method = "POST"
                headers = @{
                    "Content-Type" = "application/json"
                }
            }
        )
    }
}
Invoke-ApiTest -TestName "SETUP_NOTIFICATION_CHANNELS" -Method "PUT" -Endpoint "/mail-setup/monitoring/notification-channels" -Headers $AdminHeaders -Body $NotificationChannelsData -Description "알림 채널 설정"

# 8.4 성능 메트릭 설정 (관리자)
$PerformanceMetricsData = @{
    collection_interval_seconds = 60
    retention_days = 90
    metrics = @(
        @{
            name = "mail_throughput"
            description = "메일 처리량"
            unit = "emails_per_minute"
            enabled = $true
        },
        @{
            name = "response_time"
            description = "응답 시간"
            unit = "milliseconds"
            enabled = $true
        },
        @{
            name = "error_rate"
            description = "오류율"
            unit = "percentage"
            enabled = $true
        },
        @{
            name = "queue_size"
            description = "메일 큐 크기"
            unit = "count"
            enabled = $true
        }
    )
    aggregation = @{
        enabled = $true
        intervals = @("1m", "5m", "1h", "1d")
    }
}
Invoke-ApiTest -TestName "SETUP_PERFORMANCE_METRICS" -Method "PUT" -Endpoint "/mail-setup/monitoring/performance-metrics" -Headers $AdminHeaders -Body $PerformanceMetricsData -Description "성능 메트릭 설정"

# 8.5 헬스체크 설정 (관리자)
$HealthCheckData = @{
    enabled = $true
    interval_seconds = 30
    timeout_seconds = 10
    checks = @(
        @{
            name = "smtp_server"
            type = "tcp"
            target = "localhost:587"
            enabled = $true
        },
        @{
            name = "imap_server"
            type = "tcp"
            target = "localhost:993"
            enabled = $true
        },
        @{
            name = "database"
            type = "database"
            target = "postgresql://localhost:5432/maildb"
            enabled = $true
        },
        @{
            name = "disk_space"
            type = "disk"
            target = "/var/mail"
            threshold = 90
            enabled = $true
        }
    )
}
Invoke-ApiTest -TestName "SETUP_HEALTH_CHECKS" -Method "PUT" -Endpoint "/mail-setup/monitoring/health-checks" -Headers $AdminHeaders -Body $HealthCheckData -Description "헬스체크 설정"

# 8.6 현재 시스템 상태 조회 (관리자)
Invoke-ApiTest -TestName "GET_SYSTEM_STATUS" -Method "GET" -Endpoint "/mail-setup/monitoring/status" -Headers $AdminHeaders -Description "현재 시스템 상태 조회"

# 8.7 성능 메트릭 조회 (관리자)
Invoke-ApiTest -TestName "GET_PERFORMANCE_METRICS" -Method "GET" -Endpoint "/mail-setup/monitoring/metrics?period=1h&metric=mail_throughput" -Headers $AdminHeaders -Description "성능 메트릭 조회"

# ===================================================================
# 9. 권한 및 보안 테스트
# ===================================================================
Write-Host "`n=== 9. 권한 및 보안 테스트 ===" -ForegroundColor Magenta

# 9.1 인증 없이 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_WITHOUT_AUTH" -Method "GET" -Endpoint "/mail-setup/server/config" -ExpectedStatus 401 -Description "인증 없이 서버 설정 접근 시도 (실패 예상)"

# 9.2 잘못된 토큰으로 접근 시도 (실패 케이스)
$InvalidHeaders = @{ "Authorization" = "Bearer invalid_token_12345" }
Invoke-ApiTest -TestName "ACCESS_WITH_INVALID_TOKEN" -Method "GET" -Endpoint "/mail-setup/domains" -Headers $InvalidHeaders -ExpectedStatus 401 -Description "잘못된 토큰으로 도메인 설정 접근 시도 (실패 예상)"

# 9.3 일반 사용자가 관리자 기능 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "USER_ACCESS_ADMIN_FUNCTION" -Method "PUT" -Endpoint "/mail-setup/server/smtp" -Headers $UserHeaders -ExpectedStatus 403 -Description "일반 사용자가 SMTP 설정 수정 시도 (실패 예상)"

# 9.4 존재하지 않는 도메인 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_NONEXISTENT_DOMAIN" -Method "GET" -Endpoint "/mail-setup/domains/nonexistent.domain.com" -Headers $AdminHeaders -ExpectedStatus 404 -Description "존재하지 않는 도메인 접근 시도 (실패 예상)"

# 9.5 존재하지 않는 메일박스 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_NONEXISTENT_MAILBOX" -Method "GET" -Endpoint "/mail-setup/mailboxes/nonexistent@domain.com" -Headers $AdminHeaders -ExpectedStatus 404 -Description "존재하지 않는 메일박스 접근 시도 (실패 예상)"

# ===================================================================
# 10. 성능 및 부하 테스트
# ===================================================================
Write-Host "`n=== 10. 성능 및 부하 테스트 ===" -ForegroundColor Magenta

# 10.1 대량 도메인 조회 (성능 테스트)
Invoke-ApiTest -TestName "PERFORMANCE_LARGE_DOMAIN_LIST" -Method "GET" -Endpoint "/mail-setup/domains?page=1&limit=100" -Headers $AdminHeaders -Description "대량 도메인 목록 조회 성능 테스트"

# 10.2 대량 메일박스 조회 (성능 테스트)
Invoke-ApiTest -TestName "PERFORMANCE_LARGE_MAILBOX_LIST" -Method "GET" -Endpoint "/mail-setup/mailboxes?page=1&limit=100" -Headers $AdminHeaders -Description "대량 메일박스 목록 조회 성능 테스트"

# 10.3 연속 API 호출 (부하 테스트)
Write-Host "연속 API 호출 부하 테스트 시작..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    Invoke-ApiTest -TestName "LOAD_TEST_$i" -Method "GET" -Endpoint "/mail-setup/server/status" -Headers $AdminHeaders -Description "부하 테스트 $i/5"
    Start-Sleep -Milliseconds 200
}

# ===================================================================
# 11. 정리 작업 (리소스 삭제)
# ===================================================================
Write-Host "`n=== 11. 정리 작업 (리소스 삭제) ===" -ForegroundColor Magenta

# 11.1 메일박스 삭제
Invoke-ApiTest -TestName "DELETE_MAILBOX" -Method "DELETE" -Endpoint "/mail-setup/mailboxes/newuser@newdomain.test.com" -Headers $AdminHeaders -Description "메일박스 삭제"

# 11.2 라우팅 규칙 삭제
Invoke-ApiTest -TestName "DELETE_ROUTING_RULE" -Method "DELETE" -Endpoint "/mail-setup/routing/rules/1" -Headers $AdminHeaders -Description "라우팅 규칙 삭제"

# 11.3 서브도메인 삭제
Invoke-ApiTest -TestName "DELETE_SUBDOMAIN" -Method "DELETE" -Endpoint "/mail-setup/domains/mail.newdomain.test.com" -Headers $AdminHeaders -Description "서브도메인 삭제"

# 11.4 도메인 삭제
Invoke-ApiTest -TestName "DELETE_DOMAIN" -Method "DELETE" -Endpoint "/mail-setup/domains/newdomain.test.com" -Headers $AdminHeaders -Description "도메인 삭제"

# 11.5 이미 삭제된 리소스 삭제 시도 (실패 케이스)
Invoke-ApiTest -TestName "DELETE_ALREADY_DELETED_DOMAIN" -Method "DELETE" -Endpoint "/mail-setup/domains/newdomain.test.com" -Headers $AdminHeaders -ExpectedStatus 404 -Description "이미 삭제된 도메인 삭제 시도 (실패 예상)"

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

$OutputFile = "C:\Users\moon4\skyboot.mail2\test\mail_setup_router_test_results.json"
$TestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "`n테스트 결과가 저장되었습니다: $OutputFile" -ForegroundColor Green
Write-Host "=== SkyBoot Mail 설정 라우터 테스트 완료 ===" -ForegroundColor Green