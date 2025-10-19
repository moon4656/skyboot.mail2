# ===================================================================
# SkyBoot Mail SaaS - 테스트 결과 분석 및 리포트 생성 스크립트
# ===================================================================
# 설명: 개별 또는 통합 테스트 결과를 분석하고 상세한 리포트를 생성합니다.
# 작성자: SkyBoot Mail 개발팀
# 생성일: 2024-12-19
# 버전: 1.0.0
# ===================================================================

param(
    [string]$ResultsDir = "C:\Users\moon4\skyboot.mail2\test\results",
    [string]$OutputDir = "C:\Users\moon4\skyboot.mail2\test\reports",
    [string]$SpecificResultFile = "",
    [switch]$GenerateDetailedReport = $true,
    [switch]$GenerateCharts = $true,
    [switch]$CompareWithPrevious = $false,
    [string]$ComparisonFile = "",
    [switch]$OpenReport = $false
)

# ===================================================================
# 전역 변수 및 설정
# ===================================================================
$ErrorActionPreference = "Continue"
$AnalysisStartTime = Get-Date

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
        "Cyan" = [ConsoleColor]::Cyan
        "Magenta" = [ConsoleColor]::Magenta
        "White" = [ConsoleColor]::White
        "Gray" = [ConsoleColor]::Gray
    }
    
    $consoleColor = $colorMap[$Color]
    if ($consoleColor) {
        Write-Host $Message -ForegroundColor $consoleColor
    } else {
        Write-Host $Message
    }
}

# 출력 디렉토리 생성
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-ColorOutput "📁 리포트 디렉토리 생성: $OutputDir" "Green"
}

# ===================================================================
# 헤더 출력
# ===================================================================
Write-ColorOutput "=" * 80 "Blue"
Write-ColorOutput "📊 SkyBoot Mail SaaS - 테스트 결과 분석" "Cyan"
Write-ColorOutput "📅 분석 시작 시간: $AnalysisStartTime" "Blue"
Write-ColorOutput "📁 결과 디렉토리: $ResultsDir" "Blue"
Write-ColorOutput "📁 리포트 디렉토리: $OutputDir" "Blue"
Write-ColorOutput "=" * 80 "Blue"

# ===================================================================
# 결과 파일 수집
# ===================================================================
Write-ColorOutput "`n🔍 테스트 결과 파일 수집" "Yellow"

$ResultFiles = @()

if ($SpecificResultFile -and (Test-Path $SpecificResultFile)) {
    $ResultFiles += Get-Item $SpecificResultFile
    Write-ColorOutput "📄 지정된 결과 파일: $SpecificResultFile" "Green"
} else {
    if (Test-Path $ResultsDir) {
        $ResultFiles = Get-ChildItem -Path $ResultsDir -Filter "*test_results*.json" | Sort-Object LastWriteTime -Descending
        Write-ColorOutput "📄 발견된 결과 파일: $($ResultFiles.Count) 개" "Green"
        
        foreach ($file in $ResultFiles | Select-Object -First 5) {
            Write-ColorOutput "   - $($file.Name) (수정: $($file.LastWriteTime))" "White"
        }
        
        if ($ResultFiles.Count -gt 5) {
            Write-ColorOutput "   ... 그 외 $($ResultFiles.Count - 5)개 파일" "Gray"
        }
    } else {
        Write-ColorOutput "❌ 결과 디렉토리를 찾을 수 없습니다: $ResultsDir" "Red"
        exit 1
    }
}

if ($ResultFiles.Count -eq 0) {
    Write-ColorOutput "❌ 분석할 테스트 결과 파일이 없습니다." "Red"
    exit 1
}

# ===================================================================
# 결과 데이터 로드 및 통합
# ===================================================================
Write-ColorOutput "`n📥 테스트 결과 데이터 로드" "Yellow"

$AllTestResults = @()
$RouterSummaries = @()
$LoadedFiles = @()

foreach ($file in $ResultFiles) {
    try {
        Write-ColorOutput "📖 로딩: $($file.Name)" "White"
        $resultData = Get-Content $file.FullName -Raw | ConvertFrom-Json
        
        # 파일 정보 저장
        $LoadedFiles += @{
            FileName = $file.Name
            FilePath = $file.FullName
            LastModified = $file.LastWriteTime
            TestInfo = $resultData.TestInfo
            Statistics = $resultData.Statistics
        }
        
        # 개별 테스트 결과 통합
        if ($resultData.TestResults) {
            foreach ($test in $resultData.TestResults) {
                $test | Add-Member -NotePropertyName "SourceFile" -NotePropertyValue $file.Name -Force
                $test | Add-Member -NotePropertyName "TestDate" -NotePropertyValue $file.LastWriteTime -Force
                $AllTestResults += $test
            }
        }
        
        # 라우터 요약 정보 (마스터 결과 파일인 경우)
        if ($resultData.RouterStatistics) {
            $RouterSummaries += $resultData.RouterStatistics
        }
        
        Write-ColorOutput "✅ 로딩 완료: $($resultData.TestResults.Count) 개 테스트" "Green"
    } catch {
        Write-ColorOutput "❌ 파일 로딩 실패: $($file.Name) - $($_.Exception.Message)" "Red"
    }
}

Write-ColorOutput "📊 총 로딩된 테스트: $($AllTestResults.Count) 개" "Green"

# ===================================================================
# 데이터 분석
# ===================================================================
Write-ColorOutput "`n🔬 테스트 데이터 분석" "Yellow"

# 기본 통계
$TotalTests = $AllTestResults.Count
$SuccessfulTests = ($AllTestResults | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
$FailedTests = ($AllTestResults | Where-Object { $_.Status -eq "실패" }).Count
$OverallSuccessRate = if ($TotalTests -gt 0) { [math]::Round(($SuccessfulTests / $TotalTests) * 100, 2) } else { 0 }

# 라우터별 분석
$RouterAnalysis = $AllTestResults | Group-Object RouterName | ForEach-Object {
    $routerTests = $_.Group
    $routerSuccessful = ($routerTests | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
    $routerFailed = ($routerTests | Where-Object { $_.Status -eq "실패" }).Count
    $routerTotal = $routerTests.Count
    $routerSuccessRate = if ($routerTotal -gt 0) { [math]::Round(($routerSuccessful / $routerTotal) * 100, 2) } else { 0 }
    
    @{
        RouterName = $_.Name
        TotalTests = $routerTotal
        SuccessfulTests = $routerSuccessful
        FailedTests = $routerFailed
        SuccessRate = $routerSuccessRate
        Tests = $routerTests
    }
} | Sort-Object RouterName

# HTTP 메서드별 분석
$MethodAnalysis = $AllTestResults | Group-Object Method | ForEach-Object {
    $methodTests = $_.Group
    $methodSuccessful = ($methodTests | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
    $methodFailed = ($methodTests | Where-Object { $_.Status -eq "실패" }).Count
    $methodTotal = $methodTests.Count
    $methodSuccessRate = if ($methodTotal -gt 0) { [math]::Round(($methodSuccessful / $methodTotal) * 100, 2) } else { 0 }
    
    @{
        Method = $_.Name
        TotalTests = $methodTotal
        SuccessfulTests = $methodSuccessful
        FailedTests = $methodFailed
        SuccessRate = $methodSuccessRate
    }
} | Sort-Object Method

# 상태 코드별 분석
$StatusCodeAnalysis = $AllTestResults | Group-Object StatusCode | ForEach-Object {
    @{
        StatusCode = $_.Name
        Count = $_.Count
        Percentage = if ($TotalTests -gt 0) { [math]::Round(($_.Count / $TotalTests) * 100, 2) } else { 0 }
    }
} | Sort-Object { [int]$_.StatusCode }

# 엔드포인트별 분석
$EndpointAnalysis = $AllTestResults | Group-Object Endpoint | ForEach-Object {
    $endpointTests = $_.Group
    $endpointSuccessful = ($endpointTests | Where-Object { $_.Status -eq "성공" -or $_.Status -eq "성공 (예상된 실패)" }).Count
    $endpointFailed = ($endpointTests | Where-Object { $_.Status -eq "실패" }).Count
    $endpointTotal = $endpointTests.Count
    $endpointSuccessRate = if ($endpointTotal -gt 0) { [math]::Round(($endpointSuccessful / $endpointTotal) * 100, 2) } else { 0 }
    
    @{
        Endpoint = $_.Name
        TotalTests = $endpointTotal
        SuccessfulTests = $endpointSuccessful
        FailedTests = $endpointFailed
        SuccessRate = $endpointSuccessRate
        FailedTests_Details = ($endpointTests | Where-Object { $_.Status -eq "실패" })
    }
} | Sort-Object SuccessRate

# 실패 패턴 분석
$FailurePatterns = $AllTestResults | Where-Object { $_.Status -eq "실패" } | Group-Object Details | ForEach-Object {
    @{
        ErrorPattern = $_.Name
        Count = $_.Count
        AffectedTests = $_.Group | Select-Object TestName, RouterName, Endpoint
    }
} | Sort-Object Count -Descending

# ===================================================================
# 콘솔 결과 출력
# ===================================================================
Write-ColorOutput "`n📈 분석 결과 요약" "Blue"
Write-ColorOutput "   - 총 테스트: $TotalTests 개" "White"
Write-ColorOutput "   - 성공: $SuccessfulTests 개" "Green"
Write-ColorOutput "   - 실패: $FailedTests 개" "Red"
Write-ColorOutput "   - 전체 성공률: $OverallSuccessRate%" "$(if ($OverallSuccessRate -ge 80) { 'Green' } elseif ($OverallSuccessRate -ge 60) { 'Yellow' } else { 'Red' })"

Write-ColorOutput "`n🎯 라우터별 성공률 (상위 5개):" "Blue"
$RouterAnalysis | Sort-Object SuccessRate -Descending | Select-Object -First 5 | ForEach-Object {
    $color = if ($_.SuccessRate -ge 80) { "Green" } elseif ($_.SuccessRate -ge 60) { "Yellow" } else { "Red" }
    Write-ColorOutput "   - $($_.RouterName): $($_.SuccessRate)% ($($_.SuccessfulTests)/$($_.TotalTests))" $color
}

Write-ColorOutput "`n❌ 주요 실패 패턴 (상위 3개):" "Red"
$FailurePatterns | Select-Object -First 3 | ForEach-Object {
    Write-ColorOutput "   - $($_.ErrorPattern): $($_.Count) 회" "Red"
}

# ===================================================================
# 상세 HTML 리포트 생성
# ===================================================================
if ($GenerateDetailedReport) {
    Write-ColorOutput "`n📄 상세 HTML 리포트 생성" "Yellow"
    
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $reportFile = "$OutputDir\detailed_analysis_report_$timestamp.html"
    
    # CSS 색상 코드를 변수로 분리
    $primaryColor = "#667eea"
    $secondaryColor = "#764ba2"
    $successColor = "#56ab2f"
    $warningColor = "#f093fb"
    $errorColor = "#e74c3c"
    
    $htmlContent = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyBoot Mail SaaS - 상세 테스트 분석 리포트</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, $primaryColor 0%, $secondaryColor 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; background-color: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, $primaryColor 0%, $secondaryColor 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
        .summary-card { background: linear-gradient(135deg, $warningColor 0%, #f5576c 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .summary-card.success { background: linear-gradient(135deg, $successColor 0%, #a8e6cf 100%); }
        .summary-card.warning { background: linear-gradient(135deg, $warningColor 0%, #f5576c 100%); }
        .summary-card.info { background: linear-gradient(135deg, $primaryColor 0%, $secondaryColor 100%); }
        .summary-card h3 { margin: 0 0 15px 0; font-size: 16px; opacity: 0.9; font-weight: 400; }
        .summary-card .value { font-size: 36px; font-weight: 700; margin-bottom: 5px; }
        .summary-card .subtitle { font-size: 14px; opacity: 0.8; }
        h2 { color: #2c3e50; border-left: 5px solid #3498db; padding-left: 15px; margin-top: 40px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: left; font-weight: 500; }
        td { padding: 12px 15px; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background-color: #f8f9fa; }
        .status-success { color: #27ae60; font-weight: 600; }
        .status-failed { color: #e74c3c; font-weight: 600; }
        .status-warning { color: #f39c12; font-weight: 600; }
        .progress-container { margin: 15px 0; }
        .progress-bar { width: 100%; height: 25px; background: linear-gradient(90deg, #ecf0f1 0%, #bdc3c7 100%); border-radius: 15px; overflow: hidden; position: relative; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%); transition: width 0.5s ease; border-radius: 15px; }
        .progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #2c3e50; font-weight: 600; font-size: 14px; }
        .chart-placeholder { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border: 2px dashed #dee2e6; border-radius: 8px; padding: 40px; text-align: center; color: #6c757d; margin: 20px 0; }
        .failure-details { background: #fff5f5; border-left: 4px solid #e74c3c; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }
        .failure-details h4 { color: #e74c3c; margin: 0 0 10px 0; }
        .test-item { background: #f8f9fa; padding: 8px 12px; margin: 5px 0; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px; }
        .footer { background: #2c3e50; color: white; padding: 20px; text-align: center; margin-top: 40px; }
        .section { margin: 30px 0; }
        .highlight { background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 SkyBoot Mail SaaS</h1>
            <p>상세 테스트 분석 리포트</p>
            <p>생성 시간: $AnalysisStartTime</p>
        </div>
        
        <div class="content">
            <div class="summary-grid">
                <div class="summary-card info">
                    <h3>총 테스트</h3>
                    <div class="value">$TotalTests</div>
                    <div class="subtitle">개</div>
                </div>
                <div class="summary-card success">
                    <h3>성공한 테스트</h3>
                    <div class="value">$SuccessfulTests</div>
                    <div class="subtitle">개</div>
                </div>
                <div class="summary-card warning">
                    <h3>실패한 테스트</h3>
                    <div class="value">$FailedTests</div>
                    <div class="subtitle">개</div>
                </div>
                <div class="summary-card info">
                    <h3>전체 성공률</h3>
                    <div class="value">$OverallSuccessRate</div>
                    <div class="subtitle">%</div>
                </div>
                <div class="summary-card info">
                    <h3>분석된 라우터</h3>
                    <div class="value">$($RouterAnalysis.Count)</div>
                    <div class="subtitle">개</div>
                </div>
                <div class="summary-card info">
                    <h3>분석된 파일</h3>
                    <div class="value">$($LoadedFiles.Count)</div>
                    <div class="subtitle">개</div>
                </div>
            </div>

            <div class="section">
                <h2>📊 전체 성공률</h2>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: $OverallSuccessRate%"></div>
                        <div class="progress-text">$OverallSuccessRate% ($SuccessfulTests/$TotalTests)</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🎯 라우터별 성능 분석</h2>
                <table>
                    <thead>
                        <tr>
                            <th>라우터명</th>
                            <th>총 테스트</th>
                            <th>성공</th>
                            <th>실패</th>
                            <th>성공률</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
"@

    foreach ($router in ($RouterAnalysis | Sort-Object SuccessRate -Descending)) {
        $statusClass = if ($router.SuccessRate -ge 80) { "status-success" } elseif ($router.SuccessRate -ge 60) { "status-warning" } else { "status-failed" }
        $statusText = if ($router.SuccessRate -ge 80) { "우수" } elseif ($router.SuccessRate -ge 60) { "보통" } else { "개선 필요" }
        
        $htmlContent += @"
                        <tr>
                            <td><strong>$($router.RouterName)</strong></td>
                            <td>$($router.TotalTests)</td>
                            <td class="status-success">$($router.SuccessfulTests)</td>
                            <td class="status-failed">$($router.FailedTests)</td>
                            <td>$($router.SuccessRate)%</td>
                            <td class="$statusClass">$statusText</td>
                        </tr>
"@
    }

    $htmlContent += @"
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>🔧 HTTP 메서드별 분석</h2>
                <table>
                    <thead>
                        <tr>
                            <th>HTTP 메서드</th>
                            <th>총 테스트</th>
                            <th>성공</th>
                            <th>실패</th>
                            <th>성공률</th>
                        </tr>
                    </thead>
                    <tbody>
"@

    foreach ($method in $MethodAnalysis) {
        $htmlContent += @"
                        <tr>
                            <td><strong>$($method.Method)</strong></td>
                            <td>$($method.TotalTests)</td>
                            <td class="status-success">$($method.SuccessfulTests)</td>
                            <td class="status-failed">$($method.FailedTests)</td>
                            <td>$($method.SuccessRate)%</td>
                        </tr>
"@
    }

    $htmlContent += @"
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>📊 상태 코드 분포</h2>
                <table>
                    <thead>
                        <tr>
                            <th>상태 코드</th>
                            <th>개수</th>
                            <th>비율</th>
                            <th>설명</th>
                        </tr>
                    </thead>
                    <tbody>
"@

    foreach ($status in $StatusCodeAnalysis) {
        $description = switch ($status.StatusCode) {
            "200" { "성공" }
            "201" { "생성됨" }
            "400" { "잘못된 요청" }
            "401" { "인증 실패" }
            "403" { "권한 없음" }
            "404" { "찾을 수 없음" }
            "422" { "처리할 수 없는 엔티티" }
            "500" { "서버 오류" }
            default { "기타" }
        }
        
        $htmlContent += @"
                        <tr>
                            <td><strong>$($status.StatusCode)</strong></td>
                            <td>$($status.Count)</td>
                            <td>$($status.Percentage)%</td>
                            <td>$description</td>
                        </tr>
"@
    }

    $htmlContent += @"
                    </tbody>
                </table>
            </div>
"@

    # 실패 패턴 분석 추가
    if ($FailurePatterns.Count -gt 0) {
        $htmlContent += @"
            <div class="section">
                <h2>❌ 실패 패턴 분석</h2>
"@
        
        foreach ($pattern in ($FailurePatterns | Select-Object -First 5)) {
            $htmlContent += @"
                <div class="failure-details">
                    <h4>$($pattern.ErrorPattern) ($($pattern.Count) 회 발생)</h4>
                    <p><strong>영향받은 테스트:</strong></p>
"@
            
            foreach ($test in ($pattern.AffectedTests | Select-Object -First 3)) {
                $htmlContent += @"
                    <div class="test-item">[$($test.RouterName)] $($test.TestName) - $($test.Endpoint)</div>
"@
            }
            
            if ($pattern.AffectedTests.Count -gt 3) {
                $htmlContent += @"
                    <div class="test-item">... 그 외 $($pattern.AffectedTests.Count - 3)개 테스트</div>
"@
            }
            
            $htmlContent += "</div>"
        }
        
        $htmlContent += "</div>"
    }

    # 차트 플레이스홀더 (향후 확장용)
    if ($GenerateCharts) {
        $htmlContent += @"
            <div class="section">
                <h2>📈 시각화 차트</h2>
                <div class="chart-placeholder">
                    <h3>📊 차트 영역</h3>
                    <p>향후 Chart.js 또는 D3.js를 사용한 인터랙티브 차트가 여기에 표시됩니다.</p>
                    <ul style="text-align: left; display: inline-block;">
                        <li>라우터별 성공률 파이 차트</li>
                        <li>시간별 테스트 실행 트렌드</li>
                        <li>상태 코드 분포 도넛 차트</li>
                        <li>실패 패턴 히트맵</li>
                    </ul>
                </div>
            </div>
"@
    }

    $htmlContent += @"
            <div class="section">
                <h2>📁 분석된 파일 목록</h2>
                <table>
                    <thead>
                        <tr>
                            <th>파일명</th>
                            <th>수정 시간</th>
                            <th>테스트 수</th>
                            <th>테스트명</th>
                        </tr>
                    </thead>
                    <tbody>
"@

    foreach ($file in $LoadedFiles) {
        $testCount = ($AllTestResults | Where-Object { $_.SourceFile -eq $file.FileName }).Count
        $testName = if ($file.TestInfo -and $file.TestInfo.TestName) { $file.TestInfo.TestName } else { "N/A" }
        
        $htmlContent += @"
                        <tr>
                            <td>$($file.FileName)</td>
                            <td>$($file.LastModified)</td>
                            <td>$testCount</td>
                            <td>$testName</td>
                        </tr>
"@
    }

    $htmlContent += @"
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>🏢 SkyBoot Mail SaaS 개발팀 | 📅 생성 시간: $AnalysisStartTime</p>
            <p>이 리포트는 자동으로 생성되었습니다.</p>
        </div>
    </div>
</body>
</html>
"@

    try {
        $htmlContent | Out-File -FilePath $reportFile -Encoding UTF8
        Write-ColorOutput "✅ 상세 HTML 리포트 생성 완료: $reportFile" "Green"
        
        if ($OpenReport) {
            Start-Process $reportFile
            Write-ColorOutput "🌐 리포트를 기본 브라우저에서 열었습니다." "Green"
        }
    } catch {
        Write-ColorOutput "❌ HTML 리포트 생성 실패: $($_.Exception.Message)" "Red"
    }
}

# ===================================================================
# JSON 분석 결과 저장
# ===================================================================
Write-ColorOutput "`n💾 분석 결과 저장" "Yellow"

$analysisResultFile = "$OutputDir\analysis_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

$AnalysisResults = @{
    AnalysisInfo = @{
        AnalysisTime = $AnalysisStartTime
        ResultsDirectory = $ResultsDir
        AnalyzedFiles = $LoadedFiles.Count
        TotalTestsAnalyzed = $TotalTests
    }
    OverallStatistics = @{
        TotalTests = $TotalTests
        SuccessfulTests = $SuccessfulTests
        FailedTests = $FailedTests
        OverallSuccessRate = $OverallSuccessRate
    }
    RouterAnalysis = $RouterAnalysis
    MethodAnalysis = $MethodAnalysis
    StatusCodeAnalysis = $StatusCodeAnalysis
    EndpointAnalysis = $EndpointAnalysis | Select-Object -First 20  # 상위 20개만
    FailurePatterns = $FailurePatterns | Select-Object -First 10   # 상위 10개만
    LoadedFiles = $LoadedFiles
}

try {
    $AnalysisResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $analysisResultFile -Encoding UTF8
    Write-ColorOutput "✅ 분석 결과 JSON 저장 완료: $analysisResultFile" "Green"
} catch {
    Write-ColorOutput "❌ 분석 결과 저장 실패: $($_.Exception.Message)" "Red"
}

# ===================================================================
# 완료 메시지
# ===================================================================
$AnalysisEndTime = Get-Date
$AnalysisDuration = $AnalysisEndTime - $AnalysisStartTime

Write-ColorOutput "`n" + "=" * 80 "Blue"
Write-ColorOutput "🏁 테스트 결과 분석 완료!" "Cyan"
Write-ColorOutput "⏱️  분석 소요 시간: $([math]::Round($AnalysisDuration.TotalSeconds, 2)) 초" "Blue"
Write-ColorOutput "📊 분석된 테스트: $TotalTests 개" "Blue"
Write-ColorOutput "📁 생성된 리포트: $OutputDir" "Blue"
Write-ColorOutput "=" * 80 "Blue"

exit 0