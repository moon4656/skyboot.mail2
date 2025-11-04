# ========================================
# 국제화(i18n) 라우터 테스트 시나리오 (i18n_router.py)
# SkyBoot Mail SaaS - 다중 조직 지원 메일서버
# ========================================

param(
    [string]$BaseUrl = "http://localhost:8001/api/v1"
)

$I18N_ENDPOINT = $BaseUrl
$AUTH_ENDPOINT = "$BaseUrl/auth"

# 테스트 계정 (기본값은 기존 테스트들과 동일 패턴)
$TEST_USER = @{ user_id = "user01"; password = "test" }
$TEST_ADMIN = @{ user_id = "admin01"; password = "test" }

$TEST_RESULTS = @()
$ACCESS_TOKEN_USER = ""
$ACCESS_TOKEN_ADMIN = ""

# ========================================
# 유틸 함수
# ========================================

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

    $icon = if ($Status -eq "PASS") { "✅" } else { "❌" }
    Write-Host "$icon [$Method] $Endpoint - $TestName ($StatusCode)" -ForegroundColor $(if ($Status -eq "PASS") { "Green" } else { "Red" })
    if ($Message) { Write-Host "   💬 $Message" -ForegroundColor Yellow }
}

function Invoke-ApiRequest {
    param(
        [Parameter(Mandatory=$true)][ValidateSet('GET','POST','PUT','DELETE')][string]$Method,
        [Parameter(Mandatory=$true)][string]$Uri,
        [hashtable]$Headers,
        [string]$Body
    )
    try {
        $params = @{ Method = $Method; Uri = $Uri; ErrorAction = 'Stop' }
        if ($Headers) { $params.Headers = $Headers }
        if ($Body) { $params.Body = $Body; $params.ContentType = 'application/json' }

        $response = Invoke-RestMethod @params
        [pscustomobject]@{
            Success = $true
            StatusCode = 200
            Data = $response
        }
    } catch {
        $status = 0
        $content = $null
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $content = $reader.ReadToEnd()
            } catch { $content = $_.Exception.Message }
        }
        [pscustomobject]@{
            Success = $false
            StatusCode = $status
            Error = $content
        }
    }
}

function Get-AuthHeaders {
    param([string]$Token)
    if ([string]::IsNullOrEmpty($Token)) { return @{} }
    return @{ "Authorization" = "Bearer $Token" }
}

Write-Host "🌐 i18n 라우터 테스트 시작" -ForegroundColor Cyan
Write-Host ('=' * 60)

# ========================================
# 0. 로그인 (토큰 획득)
# ========================================

Write-Host "`n🔐 사전 준비: 인증 토큰 획득" -ForegroundColor Yellow

$loginBodyUser = ($TEST_USER | ConvertTo-Json)
$res = Invoke-ApiRequest -Method POST -Uri "$AUTH_ENDPOINT/login" -Body $loginBodyUser
if ($res.Success) {
    $ACCESS_TOKEN_USER = $res.Data.access_token
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $res.StatusCode -Status "PASS" -Message "토큰 획득"
} else {
    Add-TestResult -TestName "일반 사용자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $res.StatusCode -Status "FAIL" -Message $res.Error
}

$loginBodyAdmin = ($TEST_ADMIN | ConvertTo-Json)
$res = Invoke-ApiRequest -Method POST -Uri "$AUTH_ENDPOINT/login" -Body $loginBodyAdmin
if ($res.Success) {
    $ACCESS_TOKEN_ADMIN = $res.Data.access_token
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $res.StatusCode -Status "PASS" -Message "관리자 토큰 획득"
} else {
    Add-TestResult -TestName "관리자 로그인" -Method "POST" -Endpoint "/auth/login" -StatusCode $res.StatusCode -Status "FAIL" -Message $res.Error
}

if (-not $ACCESS_TOKEN_ADMIN) {
    Write-Host "❌ 관리자 토큰이 없어 테스트를 중단합니다." -ForegroundColor Red
    exit 1
}

$authHeaders = Get-AuthHeaders -Token $ACCESS_TOKEN_ADMIN

# ========================================
# 1) 지원 언어 목록
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/languages" -Headers $authHeaders
Add-TestResult -TestName "지원 언어 목록 조회" -Method "GET" -Endpoint "/languages" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"총 언어 수: $($res.Data.total_count)"}else{$res.Error})

# ========================================
# 2) 언어 자동 감지
# ========================================
$queryText = [uri]::EscapeDataString("안녕하세요. Hello!")
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/detect?text=$queryText" -Headers $authHeaders
Add-TestResult -TestName "언어 자동 감지" -Method "GET" -Endpoint "/detect" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"감지: $($res.Data.detected_language)"}else{$res.Error})

# ========================================
# 3) 텍스트 번역(조회)
# ========================================
$translateBody = @{ language = "en"; namespace = "common"; keys = @("welcome","login") } | ConvertTo-Json
$res = Invoke-ApiRequest -Method POST -Uri "$I18N_ENDPOINT/translate" -Headers $authHeaders -Body $translateBody
Add-TestResult -TestName "번역 조회(키 목록)" -Method "POST" -Endpoint "/translate" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"키 수: $($res.Data.translations.PSObject.Properties.Name.Count)"}else{$res.Error})

# ========================================
# 4) 언어별 번역 데이터 조회
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/translations/en?namespace=common" -Headers $authHeaders
Add-TestResult -TestName "번역 데이터 조회(en/common)" -Method "GET" -Endpoint "/translations/en" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"항목: $($res.Data.translations.PSObject.Properties.Name.Count)"}else{$res.Error})

# ========================================
# 5) 번역 업데이트 (ko/common)
# ========================================
$updateBody = @{ language = "ko"; namespace = "common"; overwrite = $true; translations = @{ hello_world = "안녕하세요 세계"; app_title = "스카이부트 메일" } } | ConvertTo-Json
$res = Invoke-ApiRequest -Method PUT -Uri "$I18N_ENDPOINT/translations/ko" -Headers $authHeaders -Body $updateBody
Add-TestResult -TestName "번역 업데이트(ko/common)" -Method "PUT" -Endpoint "/translations/ko" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"updated: $($res.Data.updated_count)"}else{$res.Error})

# ========================================
# 6) 누락된 번역 조회
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/missing?language_code=ko&namespace=common" -Headers $authHeaders
Add-TestResult -TestName "누락된 번역 조회(ko/common)" -Method "GET" -Endpoint "/missing" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"OK"}else{$res.Error})

# ========================================
# 7) 번역 통계 조회
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/stats" -Headers $authHeaders
Add-TestResult -TestName "번역 통계 조회" -Method "GET" -Endpoint "/stats" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"완성도: $($res.Data.completion_rate)%"}else{$res.Error})

# ========================================
# 8) 조직 언어 설정 조회 및 업데이트
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/config" -Headers $authHeaders
Add-TestResult -TestName "조직 언어 설정 조회" -Method "GET" -Endpoint "/config" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"기본: $($res.Data.default_language)"}else{$res.Error})

$configBody = @{ default_language = "ko"; supported_languages = @("ko","en"); fallback_language = "en"; auto_detect = $true } | ConvertTo-Json
$res = Invoke-ApiRequest -Method PUT -Uri "$I18N_ENDPOINT/config" -Headers $authHeaders -Body $configBody
Add-TestResult -TestName "조직 언어 설정 업데이트" -Method "PUT" -Endpoint "/config" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"기본: $($res.Data.default_language)"}else{$res.Error})

# ========================================
# 9) 사용자 언어 설정 조회/업데이트
# ========================================
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/user/preference" -Headers $authHeaders
Add-TestResult -TestName "사용자 언어 설정 조회" -Method "GET" -Endpoint "/user/preference" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"선호: $($res.Data.preferred_language)"}else{$res.Error})

# 스키마상 user_id 필드가 필요하므로 임의 값(0) 사용 — 서비스는 실제로 current_user.id를 사용
$prefBody = @{ user_id = 0; preferred_language = "ko"; timezone = "Asia/Seoul"; date_format = "YYYY-MM-DD"; time_format = "HH:mm" } | ConvertTo-Json
$res = Invoke-ApiRequest -Method PUT -Uri "$I18N_ENDPOINT/user/preference" -Headers $authHeaders -Body $prefBody
Add-TestResult -TestName "사용자 언어 설정 업데이트" -Method "PUT" -Endpoint "/user/preference" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"선호: $($res.Data.preferred_language)"}else{$res.Error})

# ========================================
# 10) 브라우저 언어 감지 (헤더 사용)
# ========================================
$headersBL = $authHeaders.Clone()
$headersBL["Accept-Language"] = "ko,en;q=0.8"
$res = Invoke-ApiRequest -Method GET -Uri "$I18N_ENDPOINT/browser-language" -Headers $headersBL
Add-TestResult -TestName "브라우저 언어 감지" -Method "GET" -Endpoint "/browser-language" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"감지: $($res.Data.detected_language)"}else{$res.Error})

# ========================================
# 11) 번역 내보내기
# ========================================
$exportBody = @{ languages = @("ko","en"); namespaces = @("common","mail"); format = "json" } | ConvertTo-Json
$res = Invoke-ApiRequest -Method POST -Uri "$I18N_ENDPOINT/export" -Headers $authHeaders -Body $exportBody
Add-TestResult -TestName "번역 내보내기" -Method "POST" -Endpoint "/export" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"파일: $($res.Data.download_url)"}else{$res.Error})

# ========================================
# 12) 번역 가져오기 (로컬 샘플 파일 생성 후)
# ========================================
$sampleDir = Join-Path $PSScriptRoot "i18n_samples"
if (-not (Test-Path $sampleDir)) { New-Item -Path $sampleDir -ItemType Directory | Out-Null }
$importJsonPath = Join-Path $sampleDir "import_payload.json"
$importPayload = @{ translations = @{ ko = @{ common = @{ hello_world = "안녕하세요 세계 (import)" } } } } | ConvertTo-Json -Depth 5
Set-Content -Path $importJsonPath -Value $importPayload -Encoding UTF8

$importBody = @{ file_url = $importJsonPath; format = "json"; overwrite = $true; validate_only = $false } | ConvertTo-Json
$res = Invoke-ApiRequest -Method POST -Uri "$I18N_ENDPOINT/import" -Headers $authHeaders -Body $importBody
Add-TestResult -TestName "번역 가져오기" -Method "POST" -Endpoint "/import" -StatusCode $res.StatusCode -Status $(if($res.Success){"PASS"}else{"FAIL"}) -Message $(if($res.Success){"imported: $($res.Data.imported_count)"}else{$res.Error})

# ========================================
# 요약 출력
# ========================================
Write-Host "`n📋 테스트 요약" -ForegroundColor Cyan
$pass = ($TEST_RESULTS | Where-Object { $_.Status -eq 'PASS' }).Count
$fail = ($TEST_RESULTS | Where-Object { $_.Status -eq 'FAIL' }).Count
Write-Host ("PASS: {0} / FAIL: {1}" -f $pass, $fail) -ForegroundColor $(if ($fail -gt 0) { 'Red' } else { 'Green' })

# JSON 결과 저장 (선택)
$outPath = Join-Path $PSScriptRoot ("i18n_router_test_results_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$TEST_RESULTS | ConvertTo-Json -Depth 6 | Set-Content -Path $outPath -Encoding UTF8
Write-Host "📝 결과 저장: $outPath" -ForegroundColor DarkCyan