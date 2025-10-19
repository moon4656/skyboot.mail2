# ===================================================================
# SkyBoot Mail SaaS - 간단한 테스트 결과 분석 스크립트
# ===================================================================

param(
    [string]$TestResultsDir = ".",
    [switch]$Verbose = $false
)

# 색상 출력 함수
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{
        "Red" = "Red"; "Green" = "Green"; "Yellow" = "Yellow"
        "Blue" = "Blue"; "Cyan" = "Cyan"; "Magenta" = "Magenta"
        "White" = "White"
    }
    Write-Host $Message -ForegroundColor $colors[$Color]
}

Write-ColorOutput "🚀 SkyBoot Mail SaaS 테스트 결과 분석 시작" "Cyan"
Write-ColorOutput "=" * 60 "Blue"

# 테스트 결과 JSON 파일 찾기
$jsonFiles = Get-ChildItem -Path $TestResultsDir -Filter "*test_results*.json" | Sort-Object LastWriteTime -Descending

if ($jsonFiles.Count -eq 0) {
    Write-ColorOutput "❌ 테스트 결과 JSON 파일을 찾을 수 없습니다." "Red"
    exit 1
}

Write-ColorOutput "📁 발견된 테스트 결과 파일: $($jsonFiles.Count)개" "Green"

$totalTests = 0
$totalPassed = 0
$totalFailed = 0
$routerSummary = @()

foreach ($file in $jsonFiles) {
    Write-ColorOutput "`n📄 분석 중: $($file.Name)" "Yellow"
    
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $testData = $content | ConvertFrom-Json
        
        if ($testData -is [array]) {
            $tests = $testData
        } else {
            $tests = @($testData)
        }
        
        $routerName = $file.BaseName -replace "_test_results.*", ""
        $routerTests = $tests.Count
        $routerPassed = ($tests | Where-Object { $_.Success -eq $true }).Count
        $routerFailed = $routerTests - $routerPassed
        $routerSuccessRate = if ($routerTests -gt 0) { [math]::Round(($routerPassed / $routerTests) * 100, 2) } else { 0 }
        
        $routerSummary += [PSCustomObject]@{
            RouterName = $routerName
            TotalTests = $routerTests
            Passed = $routerPassed
            Failed = $routerFailed
            SuccessRate = $routerSuccessRate
            FileName = $file.Name
        }
        
        $totalTests += $routerTests
        $totalPassed += $routerPassed
        $totalFailed += $routerFailed
        
        Write-ColorOutput "  ✅ 성공: $routerPassed" "Green"
        Write-ColorOutput "  ❌ 실패: $routerFailed" "Red"
        Write-ColorOutput "  📊 성공률: $routerSuccessRate%" "Blue"
        
        if ($Verbose -and $routerFailed -gt 0) {
            Write-ColorOutput "  🔍 실패한 테스트:" "Yellow"
            $failedTests = $tests | Where-Object { $_.Success -eq $false }
            foreach ($failedTest in $failedTests) {
                Write-ColorOutput "    - $($failedTest.TestName): $($failedTest.StatusCode)" "Red"
            }
        }
        
    } catch {
        Write-ColorOutput "❌ 파일 처리 오류: $($_.Exception.Message)" "Red"
    }
}

# 전체 요약
$overallSuccessRate = if ($totalTests -gt 0) { [math]::Round(($totalPassed / $totalTests) * 100, 2) } else { 0 }

Write-ColorOutput "`n" + "=" * 60 "Blue"
Write-ColorOutput "📊 전체 테스트 결과 요약" "Cyan"
Write-ColorOutput "=" * 60 "Blue"
Write-ColorOutput "📋 총 테스트: $totalTests" "White"
Write-ColorOutput "✅ 성공: $totalPassed" "Green"
Write-ColorOutput "❌ 실패: $totalFailed" "Red"
Write-ColorOutput "📈 전체 성공률: $overallSuccessRate%" "Blue"

# 라우터별 상세 결과
Write-ColorOutput "`n📋 라우터별 상세 결과:" "Cyan"
Write-ColorOutput "-" * 80 "Blue"
$headerFormat = "{0,-25} {1,8} {2,8} {3,8} {4,10}"
Write-ColorOutput ($headerFormat -f "라우터", "총 테스트", "성공", "실패", "성공률") "White"
Write-ColorOutput "-" * 80 "Blue"

foreach ($router in ($routerSummary | Sort-Object SuccessRate -Descending)) {
    $color = if ($router.SuccessRate -ge 80) { "Green" } elseif ($router.SuccessRate -ge 60) { "Yellow" } else { "Red" }
    $routerFormat = "{0,-25} {1,8} {2,8} {3,8} {4,9}%"
    Write-ColorOutput ($routerFormat -f $router.RouterName, $router.TotalTests, $router.Passed, $router.Failed, $router.SuccessRate) $color
}

# 성능 등급 평가
Write-ColorOutput "`n🏆 성능 등급 평가:" "Cyan"
$grade = if ($overallSuccessRate -ge 95) { "A+ (우수)" }
         elseif ($overallSuccessRate -ge 90) { "A (매우 좋음)" }
         elseif ($overallSuccessRate -ge 80) { "B (좋음)" }
         elseif ($overallSuccessRate -ge 70) { "C (보통)" }
         elseif ($overallSuccessRate -ge 60) { "D (개선 필요)" }
         else { "F (심각한 문제)" }

$gradeColor = if ($overallSuccessRate -ge 80) { "Green" } elseif ($overallSuccessRate -ge 60) { "Yellow" } else { "Red" }
Write-ColorOutput "🎯 현재 등급: $grade" $gradeColor

# 권장사항
Write-ColorOutput "`n💡 권장사항:" "Cyan"
if ($overallSuccessRate -lt 80) {
    Write-ColorOutput "⚠️  실패한 테스트들을 우선적으로 수정하세요." "Yellow"
    Write-ColorOutput "🔧 API 엔드포인트와 비즈니스 로직을 점검하세요." "Yellow"
}
if ($totalFailed -gt 0) {
    Write-ColorOutput "🐛 실패한 테스트 상세 분석을 위해 -Verbose 옵션을 사용하세요." "Yellow"
}
if ($overallSuccessRate -ge 90) {
    Write-ColorOutput "🎉 훌륭한 테스트 결과입니다!" "Green"
}

Write-ColorOutput "`n" + "=" * 60 "Blue"
Write-ColorOutput "🏁 분석 완료!" "Cyan"
Write-ColorOutput "=" * 60 "Blue"