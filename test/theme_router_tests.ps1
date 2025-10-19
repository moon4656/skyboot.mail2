# ===================================================================
# SkyBoot Mail SaaS - Theme Router 테스트 시나리오
# ===================================================================
# 파일: theme_router_tests.ps1
# 설명: 테마 라우터의 모든 엔드포인트에 대한 종합적인 테스트
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

Write-ColorOutput "🚀 SkyBoot Mail Theme Router 테스트 시작" "Cyan"
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

# 1.2 관리자 로그인
Write-ColorOutput "1.2 관리자 로그인 (admin01/test)" "White"
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
# 2. 기본 테마 목록 조회 테스트
# ===================================================================
Write-ColorOutput "`n🎨 2. 기본 테마 목록 조회 테스트" "Yellow"

if ($UserToken) {
    # 2.1 기본 테마 목록 조회
    Write-ColorOutput "2.1 기본 테마 목록 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/defaults" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 기본 테마 목록 조회 성공" "Green"
        if ($response.Content.themes) {
            Write-ColorOutput "   - 테마 수: $($response.Content.themes.Count)" "Green"
        }
        Add-TestResult -TestName "기본 테마 목록 조회" -Method "GET" -Endpoint "/themes/defaults" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 기본 테마 목록 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "기본 테마 목록 조회" -Method "GET" -Endpoint "/themes/defaults" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 2.2 색상 팔레트 목록 조회
    Write-ColorOutput "2.2 색상 팔레트 목록 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/color-palettes" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 색상 팔레트 목록 조회 성공" "Green"
        if ($response.Content.predefined_palettes) {
            Write-ColorOutput "   - 미리 정의된 팔레트 수: $($response.Content.predefined_palettes.Count)" "Green"
        }
        Add-TestResult -TestName "색상 팔레트 목록 조회" -Method "GET" -Endpoint "/themes/color-palettes" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 색상 팔레트 목록 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "색상 팔레트 목록 조회" -Method "GET" -Endpoint "/themes/color-palettes" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 2.3 사용 가능한 폰트 목록 조회
    Write-ColorOutput "2.3 사용 가능한 폰트 목록 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/fonts" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 폰트 목록 조회 성공" "Green"
        if ($response.Content.system_fonts) {
            Write-ColorOutput "   - 시스템 폰트 수: $($response.Content.system_fonts.Count)" "Green"
        }
        Add-TestResult -TestName "폰트 목록 조회" -Method "GET" -Endpoint "/themes/fonts" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 폰트 목록 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "폰트 목록 조회" -Method "GET" -Endpoint "/themes/fonts" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 3. 조직 테마 관리 테스트
# ===================================================================
Write-ColorOutput "`n🏢 3. 조직 테마 관리 테스트" "Yellow"

if ($UserToken) {
    # 3.1 조직 테마 목록 조회
    Write-ColorOutput "3.1 조직 테마 목록 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 조직 테마 목록 조회 성공" "Green"
        if ($response.Content.themes) {
            Write-ColorOutput "   - 조직 테마 수: $($response.Content.themes.Count)" "Green"
        }
        if ($response.Content.total) {
            Write-ColorOutput "   - 전체 테마 수: $($response.Content.total)" "Green"
        }
        Add-TestResult -TestName "조직 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 조직 테마 목록 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "조직 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.2 페이징 테마 목록 조회
    Write-ColorOutput "3.2 페이징 테마 목록 조회 (페이지 1, 제한 5)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/?page=1&limit=5" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 페이징 테마 목록 조회 성공" "Green"
        if ($response.Content.themes) {
            Write-ColorOutput "   - 현재 페이지 테마 수: $($response.Content.themes.Count)" "Green"
        }
        Add-TestResult -TestName "페이징 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 페이징 테마 목록 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "페이징 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.3 활성 테마만 조회
    Write-ColorOutput "3.3 활성 테마만 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/?is_active=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 활성 테마 조회 성공" "Green"
        Add-TestResult -TestName "활성 테마 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 활성 테마 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "활성 테마 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 3.4 테마 타입별 조회
    Write-ColorOutput "3.4 테마 타입별 조회 (LIGHT)" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/?theme_type=LIGHT" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 타입별 조회 성공" "Green"
        Add-TestResult -TestName "테마 타입별 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 타입별 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 타입별 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 4. 테마 생성 및 관리 테스트
# ===================================================================
Write-ColorOutput "`n🎨 4. 테마 생성 및 관리 테스트" "Yellow"

$CreatedThemeId = $null

if ($UserToken) {
    # 4.1 새 테마 생성
    Write-ColorOutput "4.1 새 테마 생성" "White"
    $themeData = @{
        name = "테스트 테마 $(Get-Date -Format 'yyyyMMdd_HHmmss')"
        description = "PowerShell 테스트로 생성된 테마"
        theme_type = "CUSTOM"
        color_palette = @{
            primary = "#007bff"
            secondary = "#6c757d"
            success = "#28a745"
            danger = "#dc3545"
            warning = "#ffc107"
            info = "#17a2b8"
            light = "#f8f9fa"
            dark = "#343a40"
            background = "#ffffff"
            surface = "#f5f5f5"
            text_primary = "#212529"
            text_secondary = "#6c757d"
        }
        typography = @{
            font_family = "Arial, sans-serif"
            font_size_base = 14
            font_weight_normal = 400
            font_weight_bold = 700
            line_height = 1.5
            letter_spacing = 0
        }
        layout = @{
            container_max_width = 1200
            grid_columns = 12
            grid_gutter = 16
            border_radius = 4
            box_shadow = "0 2px 4px rgba(0,0,0,0.1)"
        }
        branding = @{
            logo_url = ""
            favicon_url = ""
            brand_colors = @{
                primary = "#007bff"
                accent = "#17a2b8"
            }
        }
        animation = @{
            transition_duration = 300
            easing_function = "ease-in-out"
            hover_effects = $true
            loading_animations = $true
        }
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/" -Headers $UserHeaders -Body $themeData
    
    if ($response.Success -and $response.StatusCode -eq 201) {
        $CreatedThemeId = $response.Content.theme_id
        Write-ColorOutput "✅ 테마 생성 성공" "Green"
        Write-ColorOutput "   - 테마 ID: $CreatedThemeId" "Green"
        Write-ColorOutput "   - 테마 이름: $($response.Content.name)" "Green"
        Add-TestResult -TestName "테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 생성 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 4.2 중복 이름으로 테마 생성 시도 (실패 예상)
    Write-ColorOutput "4.2 중복 이름으로 테마 생성 시도" "White"
    $duplicateThemeData = @{
        name = $themeData.name
        description = "중복 이름 테스트"
        theme_type = "LIGHT"
        color_palette = @{
            primary = "#000000"
            secondary = "#ffffff"
        }
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/" -Headers $UserHeaders -Body $duplicateThemeData
    
    if ($response.StatusCode -eq 400 -or $response.StatusCode -eq 409) {
        Write-ColorOutput "✅ 중복 이름 테마 생성 시 오류 정상 반환" "Green"
        Add-TestResult -TestName "중복 이름 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "중복 이름"
    } else {
        Write-ColorOutput "❌ 중복 이름 테마 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "중복 이름 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
    
    # 4.3 잘못된 데이터로 테마 생성 시도 (실패 예상)
    Write-ColorOutput "4.3 잘못된 데이터로 테마 생성 시도" "White"
    $invalidThemeData = @{
        name = ""  # 빈 이름
        theme_type = "INVALID_TYPE"  # 잘못된 타입
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/" -Headers $UserHeaders -Body $invalidThemeData
    
    if ($response.StatusCode -eq 400 -or $response.StatusCode -eq 422) {
        Write-ColorOutput "✅ 잘못된 데이터로 테마 생성 시 오류 정상 반환" "Green"
        Add-TestResult -TestName "잘못된 데이터 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 데이터"
    } else {
        Write-ColorOutput "❌ 잘못된 데이터로 테마 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "잘못된 데이터 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
}

# ===================================================================
# 5. 테마 조회 및 수정 테스트
# ===================================================================
Write-ColorOutput "`n🔍 5. 테마 조회 및 수정 테스트" "Yellow"

if ($UserToken -and $CreatedThemeId) {
    # 5.1 특정 테마 조회
    Write-ColorOutput "5.1 특정 테마 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/$CreatedThemeId" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 특정 테마 조회 성공" "Green"
        Write-ColorOutput "   - 테마 이름: $($response.Content.name)" "Green"
        Write-ColorOutput "   - 테마 타입: $($response.Content.theme_type)" "Green"
        Add-TestResult -TestName "특정 테마 조회" -Method "GET" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 특정 테마 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "특정 테마 조회" -Method "GET" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.2 테마 업데이트
    Write-ColorOutput "5.2 테마 업데이트" "White"
    $updateData = @{
        name = "업데이트된 테스트 테마"
        description = "PowerShell 테스트로 업데이트된 테마"
        color_palette = @{
            primary = "#28a745"
            secondary = "#17a2b8"
            background = "#f8f9fa"
        }
        typography = @{
            font_size_base = 16
            line_height = 1.6
        }
    }
    
    $response = Invoke-ApiRequest -Method "PUT" -Uri "$BaseUrl/themes/$CreatedThemeId" -Headers $UserHeaders -Body $updateData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 업데이트 성공" "Green"
        Write-ColorOutput "   - 업데이트된 이름: $($response.Content.name)" "Green"
        Add-TestResult -TestName "테마 업데이트" -Method "PUT" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 업데이트 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 업데이트" -Method "PUT" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.3 테마 복제
    Write-ColorOutput "5.3 테마 복제" "White"
    $newThemeName = "복제된 테마 $(Get-Date -Format 'yyyyMMdd_HHmmss')"
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/$CreatedThemeId/duplicate?new_name=$([System.Web.HttpUtility]::UrlEncode($newThemeName))" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 201) {
        $DuplicatedThemeId = $response.Content.theme_id
        Write-ColorOutput "✅ 테마 복제 성공" "Green"
        Write-ColorOutput "   - 복제된 테마 ID: $DuplicatedThemeId" "Green"
        Write-ColorOutput "   - 복제된 테마 이름: $($response.Content.name)" "Green"
        Add-TestResult -TestName "테마 복제" -Method "POST" -Endpoint "/themes/{theme_id}/duplicate" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 복제 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 복제" -Method "POST" -Endpoint "/themes/{theme_id}/duplicate" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        $DuplicatedThemeId = $null
    }
    
    # 5.4 테마 활성화
    Write-ColorOutput "5.4 테마 활성화" "White"
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/$CreatedThemeId/activate" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 활성화 성공" "Green"
        Write-ColorOutput "   - 메시지: $($response.Content.message)" "Green"
        Add-TestResult -TestName "테마 활성화" -Method "POST" -Endpoint "/themes/{theme_id}/activate" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 활성화 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 활성화" -Method "POST" -Endpoint "/themes/{theme_id}/activate" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 5.5 테마 유효성 검증
    Write-ColorOutput "5.5 테마 유효성 검증" "White"
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/$CreatedThemeId/validate" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 유효성 검증 성공" "Green"
        if ($response.Content.is_valid) {
            Write-ColorOutput "   - 유효성: $($response.Content.is_valid)" "Green"
        }
        if ($response.Content.validation_errors) {
            Write-ColorOutput "   - 검증 오류 수: $($response.Content.validation_errors.Count)" "Yellow"
        }
        Add-TestResult -TestName "테마 유효성 검증" -Method "POST" -Endpoint "/themes/{theme_id}/validate" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 유효성 검증 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 유효성 검증" -Method "POST" -Endpoint "/themes/{theme_id}/validate" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 6. 테마 CSS 생성 및 미리보기 테스트
# ===================================================================
Write-ColorOutput "`n🎨 6. 테마 CSS 생성 및 미리보기 테스트" "Yellow"

if ($UserToken -and $CreatedThemeId) {
    # 6.1 테마 CSS 생성
    Write-ColorOutput "6.1 테마 CSS 생성" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/$CreatedThemeId/css" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 CSS 생성 성공" "Green"
        Write-ColorOutput "   - CSS 길이: $($response.Content.Length) 문자" "Green"
        Add-TestResult -TestName "테마 CSS 생성" -Method "GET" -Endpoint "/themes/{theme_id}/css" -StatusCode $response.StatusCode -Status "성공"
    } else {
        Write-ColorOutput "❌ 테마 CSS 생성 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 CSS 생성" -Method "GET" -Endpoint "/themes/{theme_id}/css" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 6.2 압축된 테마 CSS 생성
    Write-ColorOutput "6.2 압축된 테마 CSS 생성" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/$CreatedThemeId/css?minified=true" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 압축된 테마 CSS 생성 성공" "Green"
        Write-ColorOutput "   - 압축된 CSS 길이: $($response.Content.Length) 문자" "Green"
        Add-TestResult -TestName "압축된 테마 CSS 생성" -Method "GET" -Endpoint "/themes/{theme_id}/css" -StatusCode $response.StatusCode -Status "성공"
    } else {
        Write-ColorOutput "❌ 압축된 테마 CSS 생성 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "압축된 테마 CSS 생성" -Method "GET" -Endpoint "/themes/{theme_id}/css" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 6.3 테마 미리보기
    Write-ColorOutput "6.3 테마 미리보기" "White"
    $previewData = @{
        theme_settings = @{
            color_palette = @{
                primary = "#ff6b6b"
                secondary = "#4ecdc4"
                background = "#f7f7f7"
            }
            typography = @{
                font_family = "Roboto, sans-serif"
                font_size_base = 15
            }
        }
        components = @("header", "sidebar", "content", "footer")
        preview_mode = "desktop"
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/preview" -Headers $UserHeaders -Body $previewData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 미리보기 성공" "Green"
        if ($response.Content.preview_url) {
            Write-ColorOutput "   - 미리보기 URL: $($response.Content.preview_url)" "Green"
        }
        Add-TestResult -TestName "테마 미리보기" -Method "POST" -Endpoint "/themes/preview" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 미리보기 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 미리보기" -Method "POST" -Endpoint "/themes/preview" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 7. 테마 가져오기/내보내기 테스트
# ===================================================================
Write-ColorOutput "`n📤 7. 테마 가져오기/내보내기 테스트" "Yellow"

if ($UserToken -and $CreatedThemeId) {
    # 7.1 테마 내보내기 (JSON 형식)
    Write-ColorOutput "7.1 테마 내보내기 (JSON 형식)" "White"
    $exportData = @{
        format = "json"
        include_assets = $false
        include_metadata = $true
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/$CreatedThemeId/export" -Headers $UserHeaders -Body $exportData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 내보내기 성공" "Green"
        if ($response.Content.export_url) {
            Write-ColorOutput "   - 내보내기 URL: $($response.Content.export_url)" "Green"
        }
        if ($response.Content.file_size) {
            Write-ColorOutput "   - 파일 크기: $($response.Content.file_size) bytes" "Green"
        }
        Add-TestResult -TestName "테마 내보내기 JSON" -Method "POST" -Endpoint "/themes/{theme_id}/export" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 내보내기 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 내보내기 JSON" -Method "POST" -Endpoint "/themes/{theme_id}/export" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 7.2 테마 내보내기 (CSS 형식)
    Write-ColorOutput "7.2 테마 내보내기 (CSS 형식)" "White"
    $exportCssData = @{
        format = "css"
        include_assets = $true
        minified = $false
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/$CreatedThemeId/export" -Headers $UserHeaders -Body $exportCssData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 CSS 내보내기 성공" "Green"
        Add-TestResult -TestName "테마 내보내기 CSS" -Method "POST" -Endpoint "/themes/{theme_id}/export" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 CSS 내보내기 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 내보내기 CSS" -Method "POST" -Endpoint "/themes/{theme_id}/export" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 7.3 테마 가져오기
    Write-ColorOutput "7.3 테마 가져오기" "White"
    $importData = @{
        theme_data = @{
            name = "가져온 테마 $(Get-Date -Format 'yyyyMMdd_HHmmss')"
            description = "PowerShell 테스트로 가져온 테마"
            theme_type = "CUSTOM"
            color_palette = @{
                primary = "#e74c3c"
                secondary = "#3498db"
                success = "#2ecc71"
                background = "#ecf0f1"
            }
            typography = @{
                font_family = "Open Sans, sans-serif"
                font_size_base = 14
            }
        }
        import_mode = "create"
        validate_before_import = $true
    }
    
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/import" -Headers $UserHeaders -Body $importData
    
    if ($response.Success -and $response.StatusCode -eq 201) {
        $ImportedThemeId = $response.Content.theme_id
        Write-ColorOutput "✅ 테마 가져오기 성공" "Green"
        Write-ColorOutput "   - 가져온 테마 ID: $ImportedThemeId" "Green"
        Write-ColorOutput "   - 가져온 테마 이름: $($response.Content.name)" "Green"
        Add-TestResult -TestName "테마 가져오기" -Method "POST" -Endpoint "/themes/import" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 가져오기 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 가져오기" -Method "POST" -Endpoint "/themes/import" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        $ImportedThemeId = $null
    }
}

# ===================================================================
# 8. 사용자 테마 설정 테스트
# ===================================================================
Write-ColorOutput "`n👤 8. 사용자 테마 설정 테스트" "Yellow"

if ($UserToken) {
    # 8.1 사용자 테마 설정 조회
    Write-ColorOutput "8.1 사용자 테마 설정 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/user/preference" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 사용자 테마 설정 조회 성공" "Green"
        if ($response.Content.preferred_theme_id) {
            Write-ColorOutput "   - 선호 테마 ID: $($response.Content.preferred_theme_id)" "Green"
        }
        if ($response.Content.color_scheme) {
            Write-ColorOutput "   - 색상 스키마: $($response.Content.color_scheme)" "Green"
        }
        Add-TestResult -TestName "사용자 테마 설정 조회" -Method "GET" -Endpoint "/themes/user/preference" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 사용자 테마 설정 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "사용자 테마 설정 조회" -Method "GET" -Endpoint "/themes/user/preference" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 8.2 사용자 테마 설정 업데이트
    Write-ColorOutput "8.2 사용자 테마 설정 업데이트" "White"
    $preferenceData = @{
        preferred_theme_id = $CreatedThemeId
        color_scheme = "auto"
        font_size = "medium"
        custom_settings = @{
            sidebar_collapsed = $false
            show_animations = $true
            high_contrast = $false
        }
    }
    
    $response = Invoke-ApiRequest -Method "PUT" -Uri "$BaseUrl/themes/user/preference" -Headers $UserHeaders -Body $preferenceData
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 사용자 테마 설정 업데이트 성공" "Green"
        Write-ColorOutput "   - 업데이트된 선호 테마: $($response.Content.preferred_theme_id)" "Green"
        Add-TestResult -TestName "사용자 테마 설정 업데이트" -Method "PUT" -Endpoint "/themes/user/preference" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 사용자 테마 설정 업데이트 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "사용자 테마 설정 업데이트" -Method "PUT" -Endpoint "/themes/user/preference" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 9. 테마 통계 및 캐시 관리 테스트
# ===================================================================
Write-ColorOutput "`n📊 9. 테마 통계 및 캐시 관리 테스트" "Yellow"

if ($UserToken) {
    # 9.1 테마 사용 통계 조회
    Write-ColorOutput "9.1 테마 사용 통계 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/stats" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 통계 조회 성공" "Green"
        if ($response.Content.total_themes) {
            Write-ColorOutput "   - 전체 테마 수: $($response.Content.total_themes)" "Green"
        }
        if ($response.Content.active_themes) {
            Write-ColorOutput "   - 활성 테마 수: $($response.Content.active_themes)" "Green"
        }
        Add-TestResult -TestName "테마 통계 조회" -Method "GET" -Endpoint "/themes/stats" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 통계 조회 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 통계 조회" -Method "GET" -Endpoint "/themes/stats" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 9.2 테마 캐시 초기화
    Write-ColorOutput "9.2 테마 캐시 초기화" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/cache/clear" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 캐시 초기화 성공" "Green"
        Write-ColorOutput "   - 메시지: $($response.Content.message)" "Green"
        Add-TestResult -TestName "테마 캐시 초기화" -Method "GET" -Endpoint "/themes/cache/clear" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 캐시 초기화 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 캐시 초기화" -Method "GET" -Endpoint "/themes/cache/clear" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
    
    # 9.3 특정 테마 캐시 초기화
    if ($CreatedThemeId) {
        Write-ColorOutput "9.3 특정 테마 캐시 초기화" "White"
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/cache/clear?theme_id=$CreatedThemeId" -Headers $UserHeaders
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            Write-ColorOutput "✅ 특정 테마 캐시 초기화 성공" "Green"
            Add-TestResult -TestName "특정 테마 캐시 초기화" -Method "GET" -Endpoint "/themes/cache/clear" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
        } else {
            Write-ColorOutput "❌ 특정 테마 캐시 초기화 실패: $($response.Content.detail)" "Red"
            Add-TestResult -TestName "특정 테마 캐시 초기화" -Method "GET" -Endpoint "/themes/cache/clear" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        }
    }
    
    # 9.4 테마 설정 초기화
    Write-ColorOutput "9.4 테마 설정 초기화" "White"
    $response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/reset" -Headers $UserHeaders
    
    if ($response.Success -and $response.StatusCode -eq 200) {
        Write-ColorOutput "✅ 테마 설정 초기화 성공" "Green"
        Write-ColorOutput "   - 메시지: $($response.Content.message)" "Green"
        Add-TestResult -TestName "테마 설정 초기화" -Method "POST" -Endpoint "/themes/reset" -StatusCode $response.StatusCode -Status "성공" -Response $response.Content
    } else {
        Write-ColorOutput "❌ 테마 설정 초기화 실패: $($response.Content.detail)" "Red"
        Add-TestResult -TestName "테마 설정 초기화" -Method "POST" -Endpoint "/themes/reset" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
    }
}

# ===================================================================
# 10. 존재하지 않는 테마 접근 테스트
# ===================================================================
Write-ColorOutput "`n❌ 10. 존재하지 않는 테마 접근 테스트" "Yellow"

if ($UserToken) {
    $nonExistentThemeId = "non-existent-theme-id-12345"
    
    # 10.1 존재하지 않는 테마 조회
    Write-ColorOutput "10.1 존재하지 않는 테마 조회" "White"
    $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/$nonExistentThemeId" -Headers $UserHeaders
    
    if ($response.StatusCode -eq 404) {
        Write-ColorOutput "✅ 존재하지 않는 테마 조회 시 404 오류 정상 반환" "Green"
        Add-TestResult -TestName "존재하지 않는 테마 조회" -Method "GET" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "테마 없음"
    } else {
        Write-ColorOutput "❌ 존재하지 않는 테마 조회 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "존재하지 않는 테마 조회" -Method "GET" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
    
    # 10.2 존재하지 않는 테마 업데이트 시도
    Write-ColorOutput "10.2 존재하지 않는 테마 업데이트 시도" "White"
    $updateData = @{
        name = "업데이트 시도"
        description = "존재하지 않는 테마 업데이트"
    }
    
    $response = Invoke-ApiRequest -Method "PUT" -Uri "$BaseUrl/themes/$nonExistentThemeId" -Headers $UserHeaders -Body $updateData
    
    if ($response.StatusCode -eq 404) {
        Write-ColorOutput "✅ 존재하지 않는 테마 업데이트 시 404 오류 정상 반환" "Green"
        Add-TestResult -TestName "존재하지 않는 테마 업데이트" -Method "PUT" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "테마 없음"
    } else {
        Write-ColorOutput "❌ 존재하지 않는 테마 업데이트 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "존재하지 않는 테마 업데이트" -Method "PUT" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
    
    # 10.3 존재하지 않는 테마 삭제 시도
    Write-ColorOutput "10.3 존재하지 않는 테마 삭제 시도" "White"
    $response = Invoke-ApiRequest -Method "DELETE" -Uri "$BaseUrl/themes/$nonExistentThemeId" -Headers $UserHeaders
    
    if ($response.StatusCode -eq 404) {
        Write-ColorOutput "✅ 존재하지 않는 테마 삭제 시 404 오류 정상 반환" "Green"
        Add-TestResult -TestName "존재하지 않는 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "테마 없음"
    } else {
        Write-ColorOutput "❌ 존재하지 않는 테마 삭제 시 예상과 다른 응답: $($response.StatusCode)" "Red"
        Add-TestResult -TestName "존재하지 않는 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
    }
}

# ===================================================================
# 11. 권한 및 보안 테스트
# ===================================================================
Write-ColorOutput "`n🔒 11. 권한 및 보안 테스트" "Yellow"

# 11.1 인증 없이 테마 목록 조회 시도
Write-ColorOutput "11.1 인증 없이 테마 목록 조회 시도" "White"
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/"

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 테마 목록 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 테마 목록 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 11.2 인증 없이 테마 생성 시도
Write-ColorOutput "11.2 인증 없이 테마 생성 시도" "White"
$themeData = @{
    name = "무인증 테마"
    theme_type = "LIGHT"
}

$response = Invoke-ApiRequest -Method "POST" -Uri "$BaseUrl/themes/" -Body $themeData

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 인증 없이 테마 생성 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "인증 없이 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "인증 필요"
} else {
    Write-ColorOutput "❌ 인증 없이 테마 생성 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "인증 없이 테마 생성" -Method "POST" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# 11.3 잘못된 토큰으로 접근 시도
Write-ColorOutput "11.3 잘못된 토큰으로 테마 목록 조회 시도" "White"
$invalidHeaders = @{ "Authorization" = "Bearer invalid-token-12345" }
$response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/" -Headers $invalidHeaders

if ($response.StatusCode -eq 401) {
    Write-ColorOutput "✅ 잘못된 토큰으로 접근 시 401 오류 정상 반환" "Green"
    Add-TestResult -TestName "잘못된 토큰으로 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "성공 (예상된 실패)" -Details "잘못된 토큰"
} else {
    Write-ColorOutput "❌ 잘못된 토큰으로 접근 시 예상과 다른 응답: $($response.StatusCode)" "Red"
    Add-TestResult -TestName "잘못된 토큰으로 테마 목록 조회" -Method "GET" -Endpoint "/themes/" -StatusCode $response.StatusCode -Status "실패" -Details "예상과 다른 응답"
}

# ===================================================================
# 12. 성능 및 부하 테스트
# ===================================================================
Write-ColorOutput "`n⚡ 12. 성능 및 부하 테스트" "Yellow"

if ($UserToken) {
    # 12.1 테마 목록 연속 조회 (부하 테스트)
    Write-ColorOutput "12.1 테마 목록 연속 조회 (5회)" "White"
    $successCount = 0
    $totalTime = 0
    
    for ($i = 1; $i -le 5; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/" -Headers $UserHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $totalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $successCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $averageTime = $totalTime / 5
    Write-ColorOutput "✅ 테마 목록 연속 조회 완료 - 성공: $successCount/5, 평균 응답시간: $([math]::Round($averageTime, 2))ms" "Green"
    Add-TestResult -TestName "테마 목록 연속 조회" -Method "GET" -Endpoint "/themes/" -StatusCode 200 -Status "성공" -Details "성공률: $successCount/5, 평균 응답시간: $([math]::Round($averageTime, 2))ms"
    
    # 12.2 기본 테마 연속 조회 (부하 테스트)
    Write-ColorOutput "12.2 기본 테마 연속 조회 (3회)" "White"
    $defaultSuccessCount = 0
    $defaultTotalTime = 0
    
    for ($i = 1; $i -le 3; $i++) {
        $startTime = Get-Date
        $response = Invoke-ApiRequest -Method "GET" -Uri "$BaseUrl/themes/defaults" -Headers $UserHeaders
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $defaultTotalTime += $responseTime
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            $defaultSuccessCount++
        }
        
        Write-ColorOutput "   요청 $i : $([math]::Round($responseTime, 2))ms" "White"
    }
    
    $defaultAverageTime = $defaultTotalTime / 3
    Write-ColorOutput "✅ 기본 테마 연속 조회 완료 - 성공: $defaultSuccessCount/3, 평균 응답시간: $([math]::Round($defaultAverageTime, 2))ms" "Green"
    Add-TestResult -TestName "기본 테마 연속 조회" -Method "GET" -Endpoint "/themes/defaults" -StatusCode 200 -Status "성공" -Details "성공률: $defaultSuccessCount/3, 평균 응답시간: $([math]::Round($defaultAverageTime, 2))ms"
}

# ===================================================================
# 13. 테스트 후 리소스 정리
# ===================================================================
Write-ColorOutput "`n🧹 13. 테스트 후 리소스 정리" "Yellow"

if ($UserToken) {
    # 13.1 생성된 테마 삭제
    if ($CreatedThemeId) {
        Write-ColorOutput "13.1 생성된 테마 삭제 (ID: $CreatedThemeId)" "White"
        $response = Invoke-ApiRequest -Method "DELETE" -Uri "$BaseUrl/themes/$CreatedThemeId" -Headers $UserHeaders
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            Write-ColorOutput "✅ 생성된 테마 삭제 성공" "Green"
            Add-TestResult -TestName "생성된 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공"
        } else {
            Write-ColorOutput "❌ 생성된 테마 삭제 실패: $($response.Content.detail)" "Red"
            Add-TestResult -TestName "생성된 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        }
    }
    
    # 13.2 복제된 테마 삭제
    if ($DuplicatedThemeId) {
        Write-ColorOutput "13.2 복제된 테마 삭제 (ID: $DuplicatedThemeId)" "White"
        $response = Invoke-ApiRequest -Method "DELETE" -Uri "$BaseUrl/themes/$DuplicatedThemeId" -Headers $UserHeaders
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            Write-ColorOutput "✅ 복제된 테마 삭제 성공" "Green"
            Add-TestResult -TestName "복제된 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공"
        } else {
            Write-ColorOutput "❌ 복제된 테마 삭제 실패: $($response.Content.detail)" "Red"
            Add-TestResult -TestName "복제된 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        }
    }
    
    # 13.3 가져온 테마 삭제
    if ($ImportedThemeId) {
        Write-ColorOutput "13.3 가져온 테마 삭제 (ID: $ImportedThemeId)" "White"
        $response = Invoke-ApiRequest -Method "DELETE" -Uri "$BaseUrl/themes/$ImportedThemeId" -Headers $UserHeaders
        
        if ($response.Success -and $response.StatusCode -eq 200) {
            Write-ColorOutput "✅ 가져온 테마 삭제 성공" "Green"
            Add-TestResult -TestName "가져온 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "성공"
        } else {
            Write-ColorOutput "❌ 가져온 테마 삭제 실패: $($response.Content.detail)" "Red"
            Add-TestResult -TestName "가져온 테마 삭제" -Method "DELETE" -Endpoint "/themes/{theme_id}" -StatusCode $response.StatusCode -Status "실패" -Details $response.Content.detail
        }
    }
}

# ===================================================================
# 14. 테스트 결과 요약 및 저장
# ===================================================================
Write-ColorOutput "`n📊 14. 테스트 결과 요약" "Yellow"

$TestEndTime = Get-Date
$TotalTestTime = $TestEndTime - $TestStartTime

# 결과 통계 계산
$TotalTests = $TestResults.Count
$SuccessfulTests = ($TestResults | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
$FailedTests = ($TestResults | Where-Object { $_.Status -eq "실패" }).Count
$SuccessRate = if ($TotalTests -gt 0) { [math]::Round(($SuccessfulTests / $TotalTests) * 100, 2) } else { 0 }

# 상태 코드별 통계
$StatusCodeStats = $TestResults | Group-Object StatusCode | Sort-Object Name

Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "🎯 SkyBoot Mail Theme Router 테스트 완료" "Cyan"
Write-ColorOutput "📅 테스트 종료 시간: $TestEndTime" "Blue"
Write-ColorOutput "⏱️  총 테스트 시간: $($TotalTestTime.TotalSeconds) 초" "Blue"
Write-ColorOutput "📈 테스트 결과 통계:" "Blue"
Write-ColorOutput "   - 전체 테스트: $TotalTests 개" "White"
Write-ColorOutput "   - 성공: $SuccessfulTests 개" "Green"
Write-ColorOutput "   - 실패: $FailedTests 개" "Red"
Write-ColorOutput "   - 성공률: $SuccessRate%" "$(if ($SuccessRate -ge 80) { 'Green' } elseif ($SuccessRate -ge 60) { 'Yellow' } else { 'Red' })"

Write-ColorOutput "`n📊 상태 코드별 통계:" "Blue"
foreach ($stat in $StatusCodeStats) {
    $color = switch ($stat.Name) {
        "200" { "Green" }
        "201" { "Green" }
        "400" { "Yellow" }
        "401" { "Yellow" }
        "404" { "Yellow" }
        "422" { "Yellow" }
        default { "Red" }
    }
    Write-ColorOutput "   - $($stat.Name): $($stat.Count) 개" $color
}

# 실패한 테스트 상세 정보
if ($FailedTests -gt 0) {
    Write-ColorOutput "`n❌ 실패한 테스트 상세:" "Red"
    $FailedTestDetails = $TestResults | Where-Object { $_.Status -eq "실패" }
    foreach ($test in $FailedTestDetails) {
        Write-ColorOutput "   - $($test.TestName): $($test.Details)" "Red"
    }
}

# 테스트 결과를 JSON 파일로 저장
$ResultsFile = "C:\Users\moon4\skyboot.mail2\test\theme_router_test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

$TestSummary = @{
    TestInfo = @{
        TestName = "SkyBoot Mail Theme Router 테스트"
        StartTime = $TestStartTime
        EndTime = $TestEndTime
        Duration = $TotalTestTime.TotalSeconds
        BaseUrl = $BaseUrl
    }
    Statistics = @{
        TotalTests = $TotalTests
        SuccessfulTests = $SuccessfulTests
        FailedTests = $FailedTests
        SuccessRate = $SuccessRate
    }
    StatusCodeStats = $StatusCodeStats | ForEach-Object { 
        @{ StatusCode = $_.Name; Count = $_.Count } 
    }
    TestResults = $TestResults
}

try {
    $TestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $ResultsFile -Encoding UTF8
    Write-ColorOutput "💾 테스트 결과가 저장되었습니다: $ResultsFile" "Green"
} catch {
    Write-ColorOutput "❌ 테스트 결과 저장 실패: $($_.Exception.Message)" "Red"
}

Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "🏁 Theme Router 테스트 완료!" "Cyan"

# 최종 종료 코드 설정
if ($FailedTests -eq 0) {
    Write-ColorOutput "✅ 모든 테스트가 성공적으로 완료되었습니다!" "Green"
    exit 0
} else {
    Write-ColorOutput "⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요." "Yellow"
    exit 1
}