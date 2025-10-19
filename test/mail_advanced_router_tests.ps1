# ===================================================================
# SkyBoot Mail SaaS - 메일 고급 라우터 테스트 시나리오
# 파일: mail_advanced_router_tests.ps1
# 설명: mail_advanced_router.py의 모든 엔드포인트 테스트
# 작성자: SkyBoot Mail Team
# 작성일: 2024-01-20
# ===================================================================

# 테스트 설정
$BaseUrl = "http://localhost:8001/api/v1"
$TestResults = @()
$TestStartTime = Get-Date

Write-Host "=== SkyBoot Mail 고급 라우터 테스트 시작 ===" -ForegroundColor Green
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
# 3. 고급 메일 필터링 규칙 테스트
# ===================================================================
Write-Host "`n=== 3. 고급 메일 필터링 규칙 테스트 ===" -ForegroundColor Magenta

# 3.1 필터링 규칙 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_FILTER_RULES_USER" -Method "GET" -Endpoint "/mail-advanced/filter-rules" -Headers $UserHeaders -Description "사용자 필터링 규칙 목록 조회"

# 3.2 필터링 규칙 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_FILTER_RULES_ADMIN" -Method "GET" -Endpoint "/mail-advanced/filter-rules" -Headers $AdminHeaders -Description "관리자 필터링 규칙 목록 조회"

# 3.3 복합 필터링 규칙 생성 (사용자)
$ComplexFilterRuleData = @{
    name = "복합 스팸 필터"
    description = "다중 조건 스팸 메일 필터링"
    priority = 1
    is_active = $true
    conditions = @{
        operator = "AND"
        rules = @(
            @{
                field = "subject"
                operator = "contains"
                value = "광고"
                case_sensitive = $false
            },
            @{
                operator = "OR"
                rules = @(
                    @{
                        field = "sender"
                        operator = "not_in_domain"
                        value = "test.com"
                    },
                    @{
                        field = "content"
                        operator = "regex"
                        value = ".*\b(무료|할인|이벤트)\b.*"
                    }
                )
            }
        )
    }
    actions = @(
        @{
            type = "move_to_folder"
            value = "spam"
        },
        @{
            type = "add_label"
            value = "스팸"
        },
        @{
            type = "mark_as_read"
            value = "true"
        }
    )
}
Invoke-ApiTest -TestName "CREATE_COMPLEX_FILTER_RULE_USER" -Method "POST" -Endpoint "/mail-advanced/filter-rules" -Headers $UserHeaders -Body $ComplexFilterRuleData -Description "사용자 복합 필터링 규칙 생성"

# 3.4 시간 기반 필터링 규칙 생성 (관리자)
$TimeBasedFilterData = @{
    name = "업무시간 외 필터"
    description = "업무시간 외 메일 자동 분류"
    priority = 2
    is_active = $true
    schedule = @{
        type = "time_range"
        start_time = "18:00"
        end_time = "09:00"
        timezone = "Asia/Seoul"
        weekdays_only = $true
    }
    conditions = @{
        operator = "AND"
        rules = @(
            @{
                field = "received_time"
                operator = "outside_business_hours"
                value = "18:00-09:00"
            },
            @{
                field = "priority"
                operator = "not_equals"
                value = "urgent"
            }
        )
    }
    actions = @(
        @{
            type = "move_to_folder"
            value = "after_hours"
        },
        @{
            type = "set_auto_reply"
            value = "업무시간 외 메일입니다. 다음 업무일에 확인하겠습니다."
        }
    )
}
Invoke-ApiTest -TestName "CREATE_TIME_BASED_FILTER_ADMIN" -Method "POST" -Endpoint "/mail-advanced/filter-rules" -Headers $AdminHeaders -Body $TimeBasedFilterData -Description "관리자 시간 기반 필터링 규칙 생성"

# 3.5 첨부파일 기반 필터링 규칙 생성
$AttachmentFilterData = @{
    name = "첨부파일 보안 필터"
    description = "위험한 첨부파일 자동 차단"
    priority = 0
    is_active = $true
    conditions = @{
        operator = "OR"
        rules = @(
            @{
                field = "attachment_extension"
                operator = "in"
                value = @("exe", "bat", "cmd", "scr", "vbs")
            },
            @{
                field = "attachment_size"
                operator = "greater_than"
                value = "50MB"
            },
            @{
                field = "attachment_count"
                operator = "greater_than"
                value = 10
            }
        )
    }
    actions = @(
        @{
            type = "quarantine"
            value = "security"
        },
        @{
            type = "notify_admin"
            value = "위험한 첨부파일이 감지되었습니다."
        },
        @{
            type = "log_security_event"
            value = "attachment_security_violation"
        }
    )
}
Invoke-ApiTest -TestName "CREATE_ATTACHMENT_FILTER" -Method "POST" -Endpoint "/mail-advanced/filter-rules" -Headers $AdminHeaders -Body $AttachmentFilterData -Description "첨부파일 보안 필터링 규칙 생성"

# 3.6 잘못된 필터링 규칙 생성 시도 (실패 케이스)
$InvalidFilterData = @{
    name = "잘못된 필터"
    conditions = @{
        operator = "INVALID_OPERATOR"
        rules = @(
            @{
                field = "invalid_field"
                operator = "invalid_op"
                value = "test"
            }
        )
    }
    actions = @()
}
Invoke-ApiTest -TestName "CREATE_INVALID_FILTER_RULE" -Method "POST" -Endpoint "/mail-advanced/filter-rules" -Headers $UserHeaders -Body $InvalidFilterData -ExpectedStatus 400 -Description "잘못된 필터링 규칙 생성 시도 (실패 예상)"

# 3.7 필터링 규칙 정보 조회
Invoke-ApiTest -TestName "GET_FILTER_RULE_INFO" -Method "GET" -Endpoint "/mail-advanced/filter-rules/1" -Headers $UserHeaders -Description "특정 필터링 규칙 정보 조회"

# 3.8 필터링 규칙 수정
$UpdateFilterData = @{
    name = "수정된 복합 스팸 필터"
    description = "업데이트된 스팸 메일 필터링"
    priority = 1
    is_active = $true
    conditions = @{
        operator = "AND"
        rules = @(
            @{
                field = "subject"
                operator = "contains"
                value = "프로모션"
                case_sensitive = $false
            },
            @{
                field = "sender_reputation"
                operator = "less_than"
                value = 50
            }
        )
    }
    actions = @(
        @{
            type = "move_to_folder"
            value = "spam"
        },
        @{
            type = "decrease_sender_reputation"
            value = 10
        }
    )
}
Invoke-ApiTest -TestName "UPDATE_FILTER_RULE" -Method "PUT" -Endpoint "/mail-advanced/filter-rules/1" -Headers $UserHeaders -Body $UpdateFilterData -Description "필터링 규칙 수정"

# 3.9 필터링 규칙 우선순위 변경
$PriorityData = @{
    priority = 5
}
Invoke-ApiTest -TestName "UPDATE_FILTER_PRIORITY" -Method "PATCH" -Endpoint "/mail-advanced/filter-rules/1/priority" -Headers $UserHeaders -Body $PriorityData -Description "필터링 규칙 우선순위 변경"

# 3.10 필터링 규칙 활성화/비활성화
$ToggleData = @{
    is_active = $false
}
Invoke-ApiTest -TestName "TOGGLE_FILTER_RULE" -Method "PATCH" -Endpoint "/mail-advanced/filter-rules/1/toggle" -Headers $UserHeaders -Body $ToggleData -Description "필터링 규칙 활성화/비활성화"

# ===================================================================
# 4. 메일 자동화 워크플로우 테스트
# ===================================================================
Write-Host "`n=== 4. 메일 자동화 워크플로우 테스트 ===" -ForegroundColor Magenta

# 4.1 워크플로우 목록 조회 (사용자)
Invoke-ApiTest -TestName "GET_WORKFLOWS_USER" -Method "GET" -Endpoint "/mail-advanced/workflows" -Headers $UserHeaders -Description "사용자 워크플로우 목록 조회"

# 4.2 워크플로우 목록 조회 (관리자)
Invoke-ApiTest -TestName "GET_WORKFLOWS_ADMIN" -Method "GET" -Endpoint "/mail-advanced/workflows" -Headers $AdminHeaders -Description "관리자 워크플로우 목록 조회"

# 4.3 복합 자동화 워크플로우 생성 (사용자)
$ComplexWorkflowData = @{
    name = "고객 문의 자동 처리"
    description = "고객 문의 메일 자동 분류 및 응답"
    is_active = $true
    trigger = @{
        type = "mail_received"
        conditions = @{
            operator = "AND"
            rules = @(
                @{
                    field = "subject"
                    operator = "contains"
                    value = "문의"
                },
                @{
                    field = "sender"
                    operator = "not_in_organization"
                    value = "test.com"
                }
            )
        }
    }
    steps = @(
        @{
            type = "categorize"
            action = "add_label"
            value = "고객문의"
            order = 1
        },
        @{
            type = "assign"
            action = "assign_to_user"
            value = "support@test.com"
            order = 2
        },
        @{
            type = "auto_reply"
            action = "send_template_reply"
            value = "customer_inquiry_template"
            order = 3
        },
        @{
            type = "notification"
            action = "notify_team"
            value = "support_team"
            order = 4
        }
    )
    schedule = @{
        type = "immediate"
    }
}
Invoke-ApiTest -TestName "CREATE_COMPLEX_WORKFLOW_USER" -Method "POST" -Endpoint "/mail-advanced/workflows" -Headers $UserHeaders -Body $ComplexWorkflowData -Description "사용자 복합 자동화 워크플로우 생성"

# 4.4 스케줄 기반 워크플로우 생성 (관리자)
$ScheduledWorkflowData = @{
    name = "주간 메일 정리"
    description = "매주 금요일 메일 자동 정리"
    is_active = $true
    trigger = @{
        type = "schedule"
        schedule = @{
            type = "weekly"
            day_of_week = "friday"
            time = "17:00"
            timezone = "Asia/Seoul"
        }
    }
    steps = @(
        @{
            type = "cleanup"
            action = "archive_old_mails"
            value = "30_days"
            order = 1
        },
        @{
            type = "cleanup"
            action = "delete_spam_mails"
            value = "7_days"
            order = 2
        },
        @{
            type = "report"
            action = "generate_weekly_report"
            value = "mail_statistics"
            order = 3
        },
        @{
            type = "notification"
            action = "send_report_to_admin"
            value = "weekly_mail_report"
            order = 4
        }
    )
}
Invoke-ApiTest -TestName "CREATE_SCHEDULED_WORKFLOW_ADMIN" -Method "POST" -Endpoint "/mail-advanced/workflows" -Headers $AdminHeaders -Body $ScheduledWorkflowData -Description "관리자 스케줄 기반 워크플로우 생성"

# 4.5 조건부 워크플로우 생성
$ConditionalWorkflowData = @{
    name = "VIP 고객 우선 처리"
    description = "VIP 고객 메일 우선 처리 워크플로우"
    is_active = $true
    trigger = @{
        type = "mail_received"
        conditions = @{
            operator = "OR"
            rules = @(
                @{
                    field = "sender"
                    operator = "in_list"
                    value = "vip_customers"
                },
                @{
                    field = "subject"
                    operator = "contains"
                    value = "긴급"
                }
            )
        }
    }
    steps = @(
        @{
            type = "prioritize"
            action = "set_priority"
            value = "high"
            order = 1
        },
        @{
            type = "notification"
            action = "immediate_notification"
            value = "manager@test.com"
            order = 2
            conditions = @{
                field = "business_hours"
                operator = "equals"
                value = $true
            }
        },
        @{
            type = "escalation"
            action = "escalate_to_manager"
            value = "30_minutes"
            order = 3
            conditions = @{
                field = "response_time"
                operator = "greater_than"
                value = "30_minutes"
            }
        }
    )
}
Invoke-ApiTest -TestName "CREATE_CONDITIONAL_WORKFLOW" -Method "POST" -Endpoint "/mail-advanced/workflows" -Headers $AdminHeaders -Body $ConditionalWorkflowData -Description "조건부 워크플로우 생성"

# 4.6 워크플로우 정보 조회
Invoke-ApiTest -TestName "GET_WORKFLOW_INFO" -Method "GET" -Endpoint "/mail-advanced/workflows/1" -Headers $UserHeaders -Description "특정 워크플로우 정보 조회"

# 4.7 워크플로우 수정
$UpdateWorkflowData = @{
    name = "수정된 고객 문의 자동 처리"
    description = "업데이트된 고객 문의 메일 자동 분류 및 응답"
    is_active = $true
    steps = @(
        @{
            type = "categorize"
            action = "add_label"
            value = "고객문의_v2"
            order = 1
        },
        @{
            type = "auto_reply"
            action = "send_template_reply"
            value = "customer_inquiry_template_v2"
            order = 2
        }
    )
}
Invoke-ApiTest -TestName "UPDATE_WORKFLOW" -Method "PUT" -Endpoint "/mail-advanced/workflows/1" -Headers $UserHeaders -Body $UpdateWorkflowData -Description "워크플로우 수정"

# 4.8 워크플로우 실행 테스트
$TestExecutionData = @{
    test_data = @{
        subject = "문의 드립니다"
        sender = "customer@external.com"
        content = "제품에 대해 문의드립니다."
        received_time = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
}
Invoke-ApiTest -TestName "TEST_WORKFLOW_EXECUTION" -Method "POST" -Endpoint "/mail-advanced/workflows/1/test" -Headers $UserHeaders -Body $TestExecutionData -Description "워크플로우 실행 테스트"

# 4.9 워크플로우 실행 이력 조회
Invoke-ApiTest -TestName "GET_WORKFLOW_EXECUTION_HISTORY" -Method "GET" -Endpoint "/mail-advanced/workflows/1/executions?page=1&limit=10" -Headers $UserHeaders -Description "워크플로우 실행 이력 조회"

# 4.10 워크플로우 통계 조회
Invoke-ApiTest -TestName "GET_WORKFLOW_STATISTICS" -Method "GET" -Endpoint "/mail-advanced/workflows/1/stats" -Headers $UserHeaders -Description "워크플로우 통계 조회"

# ===================================================================
# 5. 메일 분석 및 인사이트 테스트
# ===================================================================
Write-Host "`n=== 5. 메일 분석 및 인사이트 테스트 ===" -ForegroundColor Magenta

# 5.1 메일 패턴 분석 (사용자)
Invoke-ApiTest -TestName "GET_MAIL_PATTERNS_USER" -Method "GET" -Endpoint "/mail-advanced/analytics/patterns?period=30d" -Headers $UserHeaders -Description "사용자 메일 패턴 분석"

# 5.2 메일 패턴 분석 (관리자)
Invoke-ApiTest -TestName "GET_MAIL_PATTERNS_ADMIN" -Method "GET" -Endpoint "/mail-advanced/analytics/patterns?period=30d" -Headers $AdminHeaders -Description "관리자 메일 패턴 분석"

# 5.3 발송자 평판 분석
Invoke-ApiTest -TestName "GET_SENDER_REPUTATION" -Method "GET" -Endpoint "/mail-advanced/analytics/sender-reputation?sender=admin01@test.com" -Headers $UserHeaders -Description "발송자 평판 분석"

# 5.4 메일 트렌드 분석
$TrendAnalysisParams = @{
    start_date = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")
    end_date = (Get-Date).ToString("yyyy-MM-dd")
    granularity = "daily"
    metrics = "volume,response_rate,spam_rate"
}
$TrendQuery = ($TrendAnalysisParams.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
Invoke-ApiTest -TestName "GET_MAIL_TRENDS" -Method "GET" -Endpoint "/mail-advanced/analytics/trends?$TrendQuery" -Headers $AdminHeaders -Description "메일 트렌드 분석"

# 5.5 키워드 분석
$KeywordAnalysisData = @{
    period = "7d"
    min_frequency = 5
    exclude_common_words = $true
    categories = @("subject", "content")
}
Invoke-ApiTest -TestName "ANALYZE_KEYWORDS" -Method "POST" -Endpoint "/mail-advanced/analytics/keywords" -Headers $UserHeaders -Body $KeywordAnalysisData -Description "메일 키워드 분석"

# 5.6 응답 시간 분석
Invoke-ApiTest -TestName "GET_RESPONSE_TIME_ANALYSIS" -Method "GET" -Endpoint "/mail-advanced/analytics/response-times?period=30d&group_by=sender" -Headers $UserHeaders -Description "응답 시간 분석"

# 5.7 메일 볼륨 예측
$PredictionData = @{
    period = "next_7_days"
    factors = @("historical_data", "seasonal_patterns", "business_events")
    confidence_level = 0.95
}
Invoke-ApiTest -TestName "PREDICT_MAIL_VOLUME" -Method "POST" -Endpoint "/mail-advanced/analytics/predictions/volume" -Headers $AdminHeaders -Body $PredictionData -Description "메일 볼륨 예측"

# 5.8 이상 탐지 분석
$AnomalyDetectionData = @{
    metrics = @("volume", "response_time", "spam_rate")
    sensitivity = "medium"
    period = "30d"
}
Invoke-ApiTest -TestName "DETECT_ANOMALIES" -Method "POST" -Endpoint "/mail-advanced/analytics/anomalies" -Headers $AdminHeaders -Body $AnomalyDetectionData -Description "메일 이상 탐지 분석"

# ===================================================================
# 6. 고급 스팸 및 보안 필터링 테스트
# ===================================================================
Write-Host "`n=== 6. 고급 스팸 및 보안 필터링 테스트 ===" -ForegroundColor Magenta

# 6.1 스팸 필터 설정 조회 (사용자)
Invoke-ApiTest -TestName "GET_SPAM_FILTER_SETTINGS_USER" -Method "GET" -Endpoint "/mail-advanced/security/spam-filter" -Headers $UserHeaders -Description "사용자 스팸 필터 설정 조회"

# 6.2 스팸 필터 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_SPAM_FILTER_SETTINGS_ADMIN" -Method "GET" -Endpoint "/mail-advanced/security/spam-filter" -Headers $AdminHeaders -Description "관리자 스팸 필터 설정 조회"

# 6.3 고급 스팸 필터 설정 업데이트
$SpamFilterSettings = @{
    enabled = $true
    sensitivity = "high"
    machine_learning_enabled = $true
    bayesian_filter_enabled = $true
    reputation_filter_enabled = $true
    content_analysis = @{
        enabled = $true
        check_links = $true
        check_attachments = $true
        check_images = $true
    }
    whitelist = @("trusted@domain.com", "partner@company.com")
    blacklist = @("spam@badsite.com", "*.suspicious.com")
    custom_rules = @(
        @{
            pattern = ".*\b(무료|공짜|이벤트)\b.*"
            action = "quarantine"
            weight = 5.0
        }
    )
}
Invoke-ApiTest -TestName "UPDATE_SPAM_FILTER_SETTINGS" -Method "PUT" -Endpoint "/mail-advanced/security/spam-filter" -Headers $AdminHeaders -Body $SpamFilterSettings -Description "고급 스팸 필터 설정 업데이트"

# 6.4 피싱 메일 탐지 설정
$PhishingDetectionSettings = @{
    enabled = $true
    check_sender_reputation = $true
    check_domain_reputation = $true
    check_url_reputation = $true
    check_attachment_safety = $true
    machine_learning_detection = $true
    suspicious_patterns = @(
        "urgent.*action.*required",
        "verify.*account.*immediately",
        "click.*here.*now"
    )
    action_on_detection = "quarantine"
    notify_admin = $true
}
Invoke-ApiTest -TestName "UPDATE_PHISHING_DETECTION" -Method "PUT" -Endpoint "/mail-advanced/security/phishing-detection" -Headers $AdminHeaders -Body $PhishingDetectionSettings -Description "피싱 메일 탐지 설정 업데이트"

# 6.5 멀웨어 스캔 설정
$MalwareScanSettings = @{
    enabled = $true
    scan_attachments = $true
    scan_embedded_content = $true
    scan_links = $true
    quarantine_on_detection = $true
    scan_engines = @("clamav", "windows_defender", "custom_engine")
    max_file_size = "100MB"
    allowed_file_types = @("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg", "png")
    blocked_file_types = @("exe", "bat", "cmd", "scr", "vbs", "js")
}
Invoke-ApiTest -TestName "UPDATE_MALWARE_SCAN_SETTINGS" -Method "PUT" -Endpoint "/mail-advanced/security/malware-scan" -Headers $AdminHeaders -Body $MalwareScanSettings -Description "멀웨어 스캔 설정 업데이트"

# 6.6 메일 보안 스캔 실행
$SecurityScanData = @{
    scan_type = "full"
    target = "all_mails"
    period = "last_24_hours"
    include_attachments = $true
    deep_scan = $true
}
Invoke-ApiTest -TestName "RUN_SECURITY_SCAN" -Method "POST" -Endpoint "/mail-advanced/security/scan" -Headers $AdminHeaders -Body $SecurityScanData -Description "메일 보안 스캔 실행"

# 6.7 보안 스캔 결과 조회
Invoke-ApiTest -TestName "GET_SECURITY_SCAN_RESULTS" -Method "GET" -Endpoint "/mail-advanced/security/scan/results?page=1&limit=20" -Headers $AdminHeaders -Description "보안 스캔 결과 조회"

# 6.8 격리된 메일 목록 조회
Invoke-ApiTest -TestName "GET_QUARANTINED_MAILS" -Method "GET" -Endpoint "/mail-advanced/security/quarantine?page=1&limit=20" -Headers $AdminHeaders -Description "격리된 메일 목록 조회"

# 6.9 격리된 메일 복원
$RestoreMailData = @{
    mail_ids = @("quarantine_001", "quarantine_002")
    reason = "False positive - legitimate business email"
}
Invoke-ApiTest -TestName "RESTORE_QUARANTINED_MAILS" -Method "POST" -Endpoint "/mail-advanced/security/quarantine/restore" -Headers $AdminHeaders -Body $RestoreMailData -Description "격리된 메일 복원"

# 6.10 보안 이벤트 로그 조회
Invoke-ApiTest -TestName "GET_SECURITY_EVENT_LOGS" -Method "GET" -Endpoint "/mail-advanced/security/events?page=1&limit=20&severity=high" -Headers $AdminHeaders -Description "보안 이벤트 로그 조회"

# ===================================================================
# 7. 메일 암호화 및 디지털 서명 테스트
# ===================================================================
Write-Host "`n=== 7. 메일 암호화 및 디지털 서명 테스트 ===" -ForegroundColor Magenta

# 7.1 암호화 설정 조회 (사용자)
Invoke-ApiTest -TestName "GET_ENCRYPTION_SETTINGS_USER" -Method "GET" -Endpoint "/mail-advanced/encryption/settings" -Headers $UserHeaders -Description "사용자 암호화 설정 조회"

# 7.2 암호화 설정 조회 (관리자)
Invoke-ApiTest -TestName "GET_ENCRYPTION_SETTINGS_ADMIN" -Method "GET" -Endpoint "/mail-advanced/encryption/settings" -Headers $AdminHeaders -Description "관리자 암호화 설정 조회"

# 7.3 PGP 키 생성
$PGPKeyData = @{
    key_type = "RSA"
    key_size = 4096
    user_id = "user01@test.com"
    passphrase = "secure_passphrase_123"
    expiry_days = 365
}
Invoke-ApiTest -TestName "GENERATE_PGP_KEY" -Method "POST" -Endpoint "/mail-advanced/encryption/pgp/generate-key" -Headers $UserHeaders -Body $PGPKeyData -Description "PGP 키 생성"

# 7.4 PGP 공개키 목록 조회
Invoke-ApiTest -TestName "GET_PGP_PUBLIC_KEYS" -Method "GET" -Endpoint "/mail-advanced/encryption/pgp/public-keys" -Headers $UserHeaders -Description "PGP 공개키 목록 조회"

# 7.5 PGP 공개키 가져오기
$ImportKeyData = @{
    public_key = @"
-----BEGIN PGP PUBLIC KEY BLOCK-----
[PGP 공개키 내용 시뮬레이션]
mQENBGH...
-----END PGP PUBLIC KEY BLOCK-----
"@
    trust_level = "marginal"
}
Invoke-ApiTest -TestName "IMPORT_PGP_PUBLIC_KEY" -Method "POST" -Endpoint "/mail-advanced/encryption/pgp/import-key" -Headers $UserHeaders -Body $ImportKeyData -Description "PGP 공개키 가져오기"

# 7.6 S/MIME 인증서 설정
$SMIMECertData = @{
    certificate = "-----BEGIN CERTIFICATE-----\n[인증서 내용 시뮬레이션]\n-----END CERTIFICATE-----"
    private_key = "-----BEGIN PRIVATE KEY-----\n[개인키 내용 시뮬레이션]\n-----END PRIVATE KEY-----"
    passphrase = "cert_passphrase_456"
    auto_encrypt = $true
    auto_sign = $true
}
Invoke-ApiTest -TestName "SETUP_SMIME_CERTIFICATE" -Method "POST" -Endpoint "/mail-advanced/encryption/smime/setup" -Headers $UserHeaders -Body $SMIMECertData -Description "S/MIME 인증서 설정"

# 7.7 암호화된 메일 발송
$EncryptedMailData = @{
    recipients = @("admin01@test.com")
    subject = "암호화된 테스트 메일"
    content = "이 메일은 암호화되어 전송됩니다."
    encryption_type = "pgp"
    sign_message = $true
    encryption_algorithm = "AES256"
}
Invoke-ApiTest -TestName "SEND_ENCRYPTED_MAIL" -Method "POST" -Endpoint "/mail-advanced/encryption/send" -Headers $UserHeaders -Body $EncryptedMailData -Description "암호화된 메일 발송"

# 7.8 디지털 서명 검증
$VerifySignatureData = @{
    mail_id = "encrypted_mail_001"
    verify_chain = $true
    check_revocation = $true
}
Invoke-ApiTest -TestName "VERIFY_DIGITAL_SIGNATURE" -Method "POST" -Endpoint "/mail-advanced/encryption/verify-signature" -Headers $UserHeaders -Body $VerifySignatureData -Description "디지털 서명 검증"

# 7.9 암호화 통계 조회
Invoke-ApiTest -TestName "GET_ENCRYPTION_STATISTICS" -Method "GET" -Endpoint "/mail-advanced/encryption/stats?period=30d" -Headers $AdminHeaders -Description "암호화 통계 조회"

# ===================================================================
# 8. 메일 아카이빙 및 규정 준수 테스트
# ===================================================================
Write-Host "`n=== 8. 메일 아카이빙 및 규정 준수 테스트 ===" -ForegroundColor Magenta

# 8.1 아카이빙 정책 조회 (관리자)
Invoke-ApiTest -TestName "GET_ARCHIVING_POLICIES" -Method "GET" -Endpoint "/mail-advanced/compliance/archiving/policies" -Headers $AdminHeaders -Description "아카이빙 정책 조회"

# 8.2 아카이빙 정책 생성
$ArchivingPolicyData = @{
    name = "법적 보존 정책"
    description = "법적 요구사항에 따른 메일 보존"
    retention_period = "7_years"
    auto_archive_after = "1_year"
    archive_criteria = @{
        operator = "OR"
        rules = @(
            @{
                field = "subject"
                operator = "contains"
                value = "계약"
            },
            @{
                field = "sender_domain"
                operator = "equals"
                value = "legal.company.com"
            },
            @{
                field = "has_attachments"
                operator = "equals"
                value = $true
            }
        )
    }
    encryption_required = $true
    immutable_storage = $true
    compliance_tags = @("legal", "contract", "financial")
}
Invoke-ApiTest -TestName "CREATE_ARCHIVING_POLICY" -Method "POST" -Endpoint "/mail-advanced/compliance/archiving/policies" -Headers $AdminHeaders -Body $ArchivingPolicyData -Description "아카이빙 정책 생성"

# 8.3 규정 준수 검색
$ComplianceSearchData = @{
    query = "계약 AND 2024"
    date_range = @{
        start_date = "2024-01-01"
        end_date = "2024-12-31"
    }
    search_scope = @("inbox", "sent", "archive")
    include_attachments = $true
    case_sensitive = $false
    legal_hold = $true
}
Invoke-ApiTest -TestName "COMPLIANCE_SEARCH" -Method "POST" -Endpoint "/mail-advanced/compliance/search" -Headers $AdminHeaders -Body $ComplianceSearchData -Description "규정 준수 검색"

# 8.4 법적 보존 설정
$LegalHoldData = @{
    case_name = "계약 분쟁 사건 2024-001"
    description = "ABC 회사와의 계약 분쟁 관련 메일 보존"
    custodians = @("user01@test.com", "admin01@test.com", "legal@test.com")
    search_criteria = @{
        keywords = @("ABC 회사", "계약", "분쟁")
        date_range = @{
            start_date = "2023-01-01"
            end_date = "2024-12-31"
        }
    }
    notification_required = $true
    auto_preserve = $true
}
Invoke-ApiTest -TestName "CREATE_LEGAL_HOLD" -Method "POST" -Endpoint "/mail-advanced/compliance/legal-hold" -Headers $AdminHeaders -Body $LegalHoldData -Description "법적 보존 설정"

# 8.5 감사 로그 조회
Invoke-ApiTest -TestName "GET_AUDIT_LOGS" -Method "GET" -Endpoint "/mail-advanced/compliance/audit-logs?page=1&limit=50&action=mail_access" -Headers $AdminHeaders -Description "감사 로그 조회"

# 8.6 데이터 내보내기 요청
$ExportRequestData = @{
    export_type = "compliance"
    format = "pst"
    search_criteria = @{
        user_id = "user01@test.com"
        date_range = @{
            start_date = "2024-01-01"
            end_date = "2024-01-31"
        }
    }
    include_metadata = $true
    encryption_required = $true
    reason = "법적 요구사항에 따른 데이터 제출"
}
Invoke-ApiTest -TestName "REQUEST_DATA_EXPORT" -Method "POST" -Endpoint "/mail-advanced/compliance/export" -Headers $AdminHeaders -Body $ExportRequestData -Description "데이터 내보내기 요청"

# 8.7 규정 준수 보고서 생성
$ComplianceReportData = @{
    report_type = "monthly_compliance"
    period = @{
        start_date = "2024-01-01"
        end_date = "2024-01-31"
    }
    include_sections = @("archiving_summary", "legal_holds", "audit_events", "policy_violations")
    format = "pdf"
    recipients = @("compliance@test.com", "admin01@test.com")
}
Invoke-ApiTest -TestName "GENERATE_COMPLIANCE_REPORT" -Method "POST" -Endpoint "/mail-advanced/compliance/reports" -Headers $AdminHeaders -Body $ComplianceReportData -Description "규정 준수 보고서 생성"

# ===================================================================
# 9. 권한 및 보안 테스트
# ===================================================================
Write-Host "`n=== 9. 권한 및 보안 테스트 ===" -ForegroundColor Magenta

# 9.1 인증 없이 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_WITHOUT_AUTH" -Method "GET" -Endpoint "/mail-advanced/filter-rules" -ExpectedStatus 401 -Description "인증 없이 필터 규칙 접근 시도 (실패 예상)"

# 9.2 잘못된 토큰으로 접근 시도 (실패 케이스)
$InvalidHeaders = @{ "Authorization" = "Bearer invalid_token_12345" }
Invoke-ApiTest -TestName "ACCESS_WITH_INVALID_TOKEN" -Method "GET" -Endpoint "/mail-advanced/workflows" -Headers $InvalidHeaders -ExpectedStatus 401 -Description "잘못된 토큰으로 워크플로우 접근 시도 (실패 예상)"

# 9.3 일반 사용자가 관리자 기능 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "USER_ACCESS_ADMIN_FUNCTION" -Method "GET" -Endpoint "/mail-advanced/compliance/audit-logs" -Headers $UserHeaders -ExpectedStatus 403 -Description "일반 사용자가 감사 로그 접근 시도 (실패 예상)"

# 9.4 다른 사용자의 리소스 접근 시도 (실패 케이스)
Invoke-ApiTest -TestName "ACCESS_OTHER_USER_RESOURCE" -Method "GET" -Endpoint "/mail-advanced/filter-rules/999" -Headers $UserHeaders -ExpectedStatus 404 -Description "다른 사용자의 필터 규칙 접근 시도 (실패 예상)"

# ===================================================================
# 10. 성능 및 부하 테스트
# ===================================================================
Write-Host "`n=== 10. 성능 및 부하 테스트 ===" -ForegroundColor Magenta

# 10.1 대량 필터 규칙 처리 (성능 테스트)
Invoke-ApiTest -TestName "PERFORMANCE_LARGE_FILTER_RULES" -Method "GET" -Endpoint "/mail-advanced/filter-rules?page=1&limit=100" -Headers $AdminHeaders -Description "대량 필터 규칙 조회 성능 테스트"

# 10.2 복잡한 워크플로우 실행 (성능 테스트)
$ComplexWorkflowTest = @{
    test_data = @{
        subject = "복잡한 테스트 메일"
        sender = "performance@test.com"
        content = "성능 테스트를 위한 복잡한 메일 내용입니다."
        attachments = @(
            @{ name = "test1.pdf"; size = "1MB" },
            @{ name = "test2.docx"; size = "2MB" }
        )
    }
}
Invoke-ApiTest -TestName "PERFORMANCE_COMPLEX_WORKFLOW" -Method "POST" -Endpoint "/mail-advanced/workflows/1/test" -Headers $UserHeaders -Body $ComplexWorkflowTest -Description "복잡한 워크플로우 실행 성능 테스트"

# 10.3 연속 API 호출 (부하 테스트)
Write-Host "연속 API 호출 부하 테스트 시작..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    Invoke-ApiTest -TestName "LOAD_TEST_$i" -Method "GET" -Endpoint "/mail-advanced/analytics/patterns?period=7d" -Headers $UserHeaders -Description "부하 테스트 $i/5"
    Start-Sleep -Milliseconds 200
}

# ===================================================================
# 11. 정리 작업 (리소스 삭제)
# ===================================================================
Write-Host "`n=== 11. 정리 작업 (리소스 삭제) ===" -ForegroundColor Magenta

# 11.1 필터링 규칙 삭제
Invoke-ApiTest -TestName "DELETE_FILTER_RULE" -Method "DELETE" -Endpoint "/mail-advanced/filter-rules/1" -Headers $UserHeaders -Description "필터링 규칙 삭제"

# 11.2 워크플로우 삭제
Invoke-ApiTest -TestName "DELETE_WORKFLOW" -Method "DELETE" -Endpoint "/mail-advanced/workflows/1" -Headers $UserHeaders -Description "워크플로우 삭제"

# 11.3 아카이빙 정책 삭제
Invoke-ApiTest -TestName "DELETE_ARCHIVING_POLICY" -Method "DELETE" -Endpoint "/mail-advanced/compliance/archiving/policies/1" -Headers $AdminHeaders -Description "아카이빙 정책 삭제"

# 11.4 법적 보존 해제
Invoke-ApiTest -TestName "RELEASE_LEGAL_HOLD" -Method "DELETE" -Endpoint "/mail-advanced/compliance/legal-hold/1" -Headers $AdminHeaders -Description "법적 보존 해제"

# 11.5 이미 삭제된 리소스 삭제 시도 (실패 케이스)
Invoke-ApiTest -TestName "DELETE_ALREADY_DELETED_RESOURCE" -Method "DELETE" -Endpoint "/mail-advanced/filter-rules/1" -Headers $UserHeaders -ExpectedStatus 404 -Description "이미 삭제된 필터 규칙 삭제 시도 (실패 예상)"

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

$OutputFile = "C:\Users\moon4\skyboot.mail2\test\mail_advanced_router_test_results.json"
$TestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "`n테스트 결과가 저장되었습니다: $OutputFile" -ForegroundColor Green
Write-Host "=== SkyBoot Mail 고급 라우터 테스트 완료 ===" -ForegroundColor Green