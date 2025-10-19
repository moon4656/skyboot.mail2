# SkyBoot Mail SaaS Test Results Analysis Script
# 테스트 결과 파일들을 분석하여 종합 리포트를 생성합니다.

param(
    [string]$TestResultsPath = ".",
    [switch]$Verbose
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SkyBoot Mail SaaS Test Results Analysis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# JSON 결과 파일들 찾기
$jsonFiles = Get-ChildItem -Path $TestResultsPath -Filter "*test_results*.json" | Sort-Object Name

if ($jsonFiles.Count -eq 0) {
    Write-Host "No test result files found in $TestResultsPath" -ForegroundColor Red
    exit 1
}

Write-Host "Found test result files: $($jsonFiles.Count)" -ForegroundColor Green
Write-Host ""

$totalTests = 0
$totalPassed = 0
$totalFailed = 0
$allFailures = @()

foreach ($file in $jsonFiles) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $testResult = $content | ConvertFrom-Json
        
        Write-Host "Analyzing: $($file.Name)" -ForegroundColor Yellow
        
        $passed = 0
        $failed = 0
        $failures = @()
        
        foreach ($test in $testResult) {
            if ($test.Success -eq $true) {
                $passed++
            } else {
                $failed++
                $failures += "  - $($test.TestName): $($test.StatusCode)"
            }
        }
        
        $successRate = if (($passed + $failed) -gt 0) { 
            [math]::Round(($passed / ($passed + $failed)) * 100, 2) 
        } else { 
            0 
        }
        
        Write-Host "  Passed: $passed" -ForegroundColor Green
        Write-Host "  Failed: $failed" -ForegroundColor Red
        Write-Host "  Success Rate: $successRate%" -ForegroundColor Cyan
        
        if ($failures.Count -gt 0) {
            Write-Host "  Failed Tests:" -ForegroundColor Red
            foreach ($failure in $failures) {
                Write-Host $failure -ForegroundColor Red
            }
        }
        
        Write-Host ""
        
        $totalTests += ($passed + $failed)
        $totalPassed += $passed
        $totalFailed += $failed
        $allFailures += $failures
        
    } catch {
        Write-Host "Error analyzing $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 전체 요약
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OVERALL SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$overallSuccessRate = if ($totalTests -gt 0) { 
    [math]::Round(($totalPassed / $totalTests) * 100, 2) 
} else { 
    0 
}

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Total Passed: $totalPassed" -ForegroundColor Green
Write-Host "Total Failed: $totalFailed" -ForegroundColor Red
Write-Host "Overall Success Rate: $overallSuccessRate%" -ForegroundColor Cyan
Write-Host ""

if ($allFailures.Count -gt 0) {
    Write-Host "All Failed Tests:" -ForegroundColor Red
    $uniqueFailures = $allFailures | Sort-Object | Get-Unique
    foreach ($failure in $uniqueFailures) {
        Write-Host $failure -ForegroundColor Red
    }
    Write-Host ""
}

# 상태 평가
if ($overallSuccessRate -ge 90) {
    Write-Host "Status: EXCELLENT (90%+ success rate)" -ForegroundColor Green
} elseif ($overallSuccessRate -ge 80) {
    Write-Host "Status: GOOD (80-89% success rate)" -ForegroundColor Yellow
} elseif ($overallSuccessRate -ge 70) {
    Write-Host "Status: FAIR (70-79% success rate)" -ForegroundColor Yellow
} else {
    Write-Host "Status: NEEDS IMPROVEMENT (<70% success rate)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "- Review failed tests and fix underlying issues" -ForegroundColor White
Write-Host "- Check API endpoints and authentication" -ForegroundColor White
Write-Host "- Verify database connections and data integrity" -ForegroundColor White
Write-Host "- Use -Verbose option for detailed failure analysis" -ForegroundColor White

Write-Host ""
Write-Host "Analysis Complete!" -ForegroundColor Green