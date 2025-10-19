# SkyBoot Mail SaaS - Test Results Analysis Script
param(
    [string]$TestResultsDir = ".",
    [switch]$Verbose = $false
)

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{
        "Red" = "Red"; "Green" = "Green"; "Yellow" = "Yellow"
        "Blue" = "Blue"; "Cyan" = "Cyan"; "Magenta" = "Magenta"
        "White" = "White"
    }
    Write-Host $Message -ForegroundColor $colors[$Color]
}

Write-ColorOutput "SkyBoot Mail SaaS Test Results Analysis" "Cyan"
Write-ColorOutput "=" * 60 "Blue"

# Find test result JSON files
$jsonFiles = Get-ChildItem -Path $TestResultsDir -Filter "*test_results*.json" | Sort-Object LastWriteTime -Descending

if ($jsonFiles.Count -eq 0) {
    Write-ColorOutput "No test result JSON files found." "Red"
    exit 1
}

Write-ColorOutput "Found test result files: $($jsonFiles.Count)" "Green"

$totalTests = 0
$totalPassed = 0
$totalFailed = 0
$routerSummary = @()

foreach ($file in $jsonFiles) {
    Write-ColorOutput "`nAnalyzing: $($file.Name)" "Yellow"
    
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
        
        Write-ColorOutput "  Passed: $routerPassed" "Green"
        Write-ColorOutput "  Failed: $routerFailed" "Red"
        Write-ColorOutput "  Success Rate: $routerSuccessRate%" "Blue"
        
        if ($Verbose -and $routerFailed -gt 0) {
            Write-ColorOutput "  Failed Tests:" "Yellow"
            $failedTests = $tests | Where-Object { $_.Success -eq $false }
            foreach ($failedTest in $failedTests) {
                Write-ColorOutput "    - $($failedTest.TestName): $($failedTest.StatusCode)" "Red"
            }
        }
        
    } catch {
        Write-ColorOutput "Error processing file: $($_.Exception.Message)" "Red"
    }
}

# Overall summary
$overallSuccessRate = if ($totalTests -gt 0) { [math]::Round(($totalPassed / $totalTests) * 100, 2) } else { 0 }

Write-ColorOutput "`n" + "=" * 60 "Blue"
Write-ColorOutput "Overall Test Results Summary" "Cyan"
Write-ColorOutput "=" * 60 "Blue"
Write-ColorOutput "Total Tests: $totalTests" "White"
Write-ColorOutput "Passed: $totalPassed" "Green"
Write-ColorOutput "Failed: $totalFailed" "Red"
Write-ColorOutput "Overall Success Rate: $overallSuccessRate%" "Blue"

# Router details
Write-ColorOutput "`nRouter Details:" "Cyan"
Write-ColorOutput "-" * 80 "Blue"

$headerFormat = "{0,-25} {1,8} {2,8} {3,8} {4,10}"
Write-ColorOutput ($headerFormat -f "Router", "Total", "Passed", "Failed", "Rate") "White"
Write-ColorOutput "-" * 80 "Blue"

foreach ($router in ($routerSummary | Sort-Object SuccessRate -Descending)) {
    $color = if ($router.SuccessRate -ge 80) { "Green" } elseif ($router.SuccessRate -ge 60) { "Yellow" } else { "Red" }
    $routerFormat = "{0,-25} {1,8} {2,8} {3,8} {4,9}%"
    Write-ColorOutput ($routerFormat -f $router.RouterName, $router.TotalTests, $router.Passed, $router.Failed, $router.SuccessRate) $color
}

# Performance grade
Write-ColorOutput "`nPerformance Grade:" "Cyan"
$grade = if ($overallSuccessRate -ge 95) { "A+ (Excellent)" }
         elseif ($overallSuccessRate -ge 90) { "A (Very Good)" }
         elseif ($overallSuccessRate -ge 80) { "B (Good)" }
         elseif ($overallSuccessRate -ge 70) { "C (Average)" }
         elseif ($overallSuccessRate -ge 60) { "D (Needs Improvement)" }
         else { "F (Critical Issues)" }

$gradeColor = if ($overallSuccessRate -ge 80) { "Green" } elseif ($overallSuccessRate -ge 60) { "Yellow" } else { "Red" }
Write-ColorOutput "Current Grade: $grade" $gradeColor

# Recommendations
Write-ColorOutput "`nRecommendations:" "Cyan"
if ($overallSuccessRate -lt 80) {
    Write-ColorOutput "- Fix failed tests as priority" "Yellow"
    Write-ColorOutput "- Review API endpoints and business logic" "Yellow"
}
if ($totalFailed -gt 0) {
    Write-ColorOutput "- Use -Verbose option for detailed failure analysis" "Yellow"
}
if ($overallSuccessRate -ge 90) {
    Write-ColorOutput "- Excellent test results!" "Green"
}

Write-ColorOutput "`n" + "=" * 60 "Blue"
Write-ColorOutput "Analysis Complete!" "Cyan"
Write-ColorOutput "=" * 60 "Blue"