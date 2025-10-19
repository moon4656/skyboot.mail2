# ===================================================================
# SkyBoot Mail SaaS - Master Test Runner Script
# ===================================================================
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$AdminUserId = "admin01",
    [string]$AdminPassword = "test",
    [string]$UserId = "user01", 
    [string]$UserPassword = "test",
    [switch]$SkipCleanup = $false,
    [switch]$ContinueOnError = $true,
    [string]$OutputDir = "C:\Users\moon4\skyboot.mail2\test\results",
    [string[]]$IncludeRouters = @(),
    [string[]]$ExcludeRouters = @(),
    [switch]$GenerateReport = $true
)

# Global variables and settings
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$MasterTestStartTime = Get-Date

# Color output function
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        "Magenta" { Write-Host $Message -ForegroundColor Magenta }
        "Gray" { Write-Host $Message -ForegroundColor Gray }
        default { Write-Host $Message }
    }
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-ColorOutput "Created output directory: $OutputDir" "Green"
}

# Test router definitions
$TestDir = "C:\Users\moon4\skyboot.mail2\test"

# Router name and script path mapping
$RouterScripts = @{
    "Auth Router" = "auth_router_tests.ps1"
    "Organization Router" = "organization_router_tests.ps1"
    "User Router" = "user_router_tests.ps1"
    "Mail Core Router" = "mail_core_router_tests.ps1"
    "Mail Convenience Router" = "mail_convenience_router_tests.ps1"
    "Mail Advanced Router" = "mail_advanced_router_tests.ps1"
    "Mail Setup Router" = "mail_setup_router_tests.ps1"
    "Addressbook Router" = "addressbook_router_tests.ps1"
    "Debug Router" = "debug_router_tests.ps1"
    "Monitoring Router" = "monitoring_router_tests.ps1"
    "Theme Router" = "theme_router_tests.ps1"
}

# Execution order definition
$ExecutionOrder = @(
    "Auth Router",
    "Organization Router", 
    "User Router",
    "Mail Core Router",
    "Mail Convenience Router",
    "Mail Advanced Router",
    "Mail Setup Router",
    "Addressbook Router",
    "Debug Router",
    "Monitoring Router",
    "Theme Router"
)

# Include/exclude router filtering
if ($IncludeRouters.Count -gt 0) {
    $ExecutionOrder = $ExecutionOrder | Where-Object { $_ -in $IncludeRouters }
    Write-ColorOutput "Included routers: $($IncludeRouters -join ', ')" "Yellow"
}

if ($ExcludeRouters.Count -gt 0) {
    $ExecutionOrder = $ExecutionOrder | Where-Object { $_ -notin $ExcludeRouters }
    Write-ColorOutput "Excluded routers: $($ExcludeRouters -join ', ')" "Yellow"
}

# Test result tracking variables
$MasterTestResults = @()
$RouterExecutionResults = @()
$TotalRouters = $ExecutionOrder.Count
$CompletedRouters = 0
$FailedRouters = 0

# Header output
Write-ColorOutput "=" * 100 "Blue"
Write-ColorOutput "SkyBoot Mail SaaS - Master Test Runner" "Cyan"
Write-ColorOutput "Test start time: $MasterTestStartTime" "Blue"
Write-ColorOutput "Base URL: $BaseUrl" "Blue"
Write-ColorOutput "Total test routers: $TotalRouters" "Blue"
Write-ColorOutput "Results output path: $OutputDir" "Blue"
Write-ColorOutput "=" * 100 "Blue"

# Server connection check
Write-ColorOutput "`nChecking server connection..." "Yellow"

try {
    $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10
    Write-ColorOutput "Server connection successful" "Green"
} catch {
    Write-ColorOutput "Server connection failed: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Please check if the server is running and try again." "Yellow"
    exit 1
}

# Router-wise test execution
Write-ColorOutput "`nStarting router-wise test execution..." "Yellow"

foreach ($routerName in $ExecutionOrder) {
    $routerStartTime = Get-Date
    $scriptFileName = $RouterScripts[$routerName]
    $scriptPath = Join-Path $TestDir $scriptFileName
    
    Write-ColorOutput "`n" + "=" * 80 "Blue"
    Write-ColorOutput "[$($CompletedRouters + 1)/$TotalRouters] Starting $routerName test" "Cyan"
    Write-ColorOutput "Script: $scriptPath" "Blue"
    
    # Check script file existence
    if (-not (Test-Path $scriptPath)) {
        Write-ColorOutput "Test script not found: $scriptPath" "Red"
        
        $RouterExecutionResults += [PSCustomObject]@{
            RouterName = $routerName
            Status = "Script Not Found"
            StartTime = $routerStartTime
            EndTime = Get-Date
            Duration = 0
            ExitCode = -1
            ErrorMessage = "Test script file does not exist"
            ResultFile = $null
        }
        
        $FailedRouters++
        
        if (-not $ContinueOnError) {
            Write-ColorOutput "ContinueOnError is false, stopping test execution." "Red"
            break
        }
        continue
    }
    
    # Execute test script
    try {
        Write-ColorOutput "Executing test..." "White"
        
        $arguments = @(
            "-ExecutionPolicy", "Bypass",
            "-File", $scriptPath,
            "-BaseUrl", $BaseUrl,
            "-AdminUserId", $AdminUserId,
            "-AdminPassword", $AdminPassword,
            "-UserId", $UserId,
            "-UserPassword", $UserPassword
        )
        
        if ($SkipCleanup) {
            $arguments += "-SkipCleanup"
        }
        
        $outputLog = "$OutputDir\$($routerName -replace ' ', '_')_output.log"
        $errorLog = "$OutputDir\$($routerName -replace ' ', '_')_error.log"
        
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Wait -PassThru -NoNewWindow -RedirectStandardOutput $outputLog -RedirectStandardError $errorLog
        $exitCode = $process.ExitCode
        $routerEndTime = Get-Date
        $routerDuration = ($routerEndTime - $routerStartTime).TotalSeconds
        
        # Find result file
        $resultPattern = "$OutputDir\*$($routerName -replace ' ', '_')*test_results_*.json"
        $resultFiles = Get-ChildItem -Path $resultPattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
        $latestResultFile = if ($resultFiles) { $resultFiles[0].FullName } else { $null }
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "$routerName test completed (Duration: $([math]::Round($routerDuration, 2))s)" "Green"
            $status = "Success"
        } else {
            Write-ColorOutput "$routerName test failed (Exit code: $exitCode, Duration: $([math]::Round($routerDuration, 2))s)" "Red"
            $status = "Failed"
            $FailedRouters++
        }
        
        $RouterExecutionResults += [PSCustomObject]@{
            RouterName = $routerName
            Status = $status
            StartTime = $routerStartTime
            EndTime = $routerEndTime
            Duration = $routerDuration
            ExitCode = $exitCode
            ErrorMessage = if ($exitCode -ne 0) { "Test execution failed (Exit code: $exitCode)" } else { $null }
            ResultFile = $latestResultFile
            OutputLog = $outputLog
            ErrorLog = $errorLog
        }
        
    } catch {
        $routerEndTime = Get-Date
        $routerDuration = ($routerEndTime - $routerStartTime).TotalSeconds
        
        Write-ColorOutput "$routerName test execution error: $($_.Exception.Message)" "Red"
        
        $RouterExecutionResults += [PSCustomObject]@{
            RouterName = $routerName
            Status = "Error"
            StartTime = $routerStartTime
            EndTime = $routerEndTime
            Duration = $routerDuration
            ExitCode = -1
            ErrorMessage = $_.Exception.Message
            ResultFile = $null
        }
        
        $FailedRouters++
        
        if (-not $ContinueOnError) {
            Write-ColorOutput "ContinueOnError is false, stopping test execution." "Red"
            break
        }
    }
    
    $CompletedRouters++
    
    # Progress display
    $progressPercent = [math]::Round(($CompletedRouters / $TotalRouters) * 100, 1)
    Write-ColorOutput "Overall progress: $progressPercent% ($CompletedRouters/$TotalRouters)" "Blue"
}

# Integrate individual test results
Write-ColorOutput "`nIntegrating individual test results..." "Yellow"

foreach ($routerResult in $RouterExecutionResults) {
    if ($routerResult.ResultFile -and (Test-Path $routerResult.ResultFile)) {
        try {
            $routerTestData = Get-Content $routerResult.ResultFile -Raw | ConvertFrom-Json
            
            # Add router information
            foreach ($testResult in $routerTestData.TestResults) {
                $testResult | Add-Member -NotePropertyName "RouterName" -NotePropertyValue $routerResult.RouterName -Force
                $MasterTestResults += $testResult
            }
            
            Write-ColorOutput "$($routerResult.RouterName) results integrated ($($routerTestData.TestResults.Count) tests)" "Green"
        } catch {
            Write-ColorOutput "$($routerResult.RouterName) result file read failed: $($_.Exception.Message)" "Red"
        }
    } else {
        Write-ColorOutput "$($routerResult.RouterName) result file not found." "Yellow"
    }
}

# Integrated result analysis
Write-ColorOutput "`nAnalyzing integrated results..." "Yellow"

$MasterTestEndTime = Get-Date
$TotalMasterTestTime = $MasterTestEndTime - $MasterTestStartTime

# Overall statistics
$TotalTests = $MasterTestResults.Count
$SuccessfulTests = ($MasterTestResults | Where-Object { $_.Status -eq "Success" -or $_.Status -eq "Success (Expected Failure)" }).Count
$FailedTests = ($MasterTestResults | Where-Object { $_.Status -eq "Failed" }).Count
$OverallSuccessRate = if ($TotalTests -gt 0) { [math]::Round(($SuccessfulTests / $TotalTests) * 100, 2) } else { 0 }

# Router-wise statistics
$RouterStats = @()
foreach ($routerResult in $RouterExecutionResults) {
    $routerName = $routerResult.RouterName
    $routerTests = $MasterTestResults | Where-Object { $_.RouterName -eq $routerName }
    $routerSuccessful = ($routerTests | Where-Object { $_.Status -eq "Success" -or $_.Status -eq "Success (Expected Failure)" }).Count
    $routerFailed = ($routerTests | Where-Object { $_.Status -eq "Failed" }).Count
    $routerTotal = $routerTests.Count
    $routerSuccessRate = if ($routerTotal -gt 0) { [math]::Round(($routerSuccessful / $routerTotal) * 100, 2) } else { 0 }
    
    $RouterStats += [PSCustomObject]@{
        RouterName = $routerName
        ExecutionStatus = $routerResult.Status
        Duration = $routerResult.Duration
        TotalTests = $routerTotal
        SuccessfulTests = $routerSuccessful
        FailedTests = $routerFailed
        SuccessRate = $routerSuccessRate
        ExitCode = $routerResult.ExitCode
    }
}

# Status code statistics
$StatusCodeStats = $MasterTestResults | Group-Object StatusCode | Sort-Object Name

# HTTP method statistics
$MethodStats = $MasterTestResults | Group-Object Method | Sort-Object Name

# Result output
Write-ColorOutput "`n" + "=" * 100 "Blue"
Write-ColorOutput "SkyBoot Mail SaaS - Overall Test Results Summary" "Cyan"
Write-ColorOutput "Test end time: $MasterTestEndTime" "Blue"
Write-ColorOutput "Total test time: $([math]::Round($TotalMasterTestTime.TotalSeconds, 2)) seconds" "Blue"
Write-ColorOutput "=" * 100 "Blue"

Write-ColorOutput "`nOverall Test Statistics:" "Blue"
Write-ColorOutput "   - Executed routers: $CompletedRouters/$TotalRouters" "White"
Write-ColorOutput "   - Successful routers: $($CompletedRouters - $FailedRouters)" "Green"
Write-ColorOutput "   - Failed routers: $FailedRouters" "Red"
Write-ColorOutput "   - Total tests: $TotalTests" "White"
Write-ColorOutput "   - Successful tests: $SuccessfulTests" "Green"
Write-ColorOutput "   - Failed tests: $FailedTests" "Red"
Write-ColorOutput "   - Overall success rate: $OverallSuccessRate%" "$(if ($OverallSuccessRate -ge 80) { 'Green' } elseif ($OverallSuccessRate -ge 60) { 'Yellow' } else { 'Red' })"

Write-ColorOutput "`nRouter Execution Results:" "Blue"
foreach ($stat in $RouterStats) {
    $statusColor = switch ($stat.ExecutionStatus) {
        "Success" { "Green" }
        "Failed" { "Red" }
        "Error" { "Red" }
        "Script Not Found" { "Yellow" }
        default { "White" }
    }
    
    Write-ColorOutput "   - $($stat.RouterName):" "White"
    Write-ColorOutput "      - Execution status: $($stat.ExecutionStatus)" $statusColor
    Write-ColorOutput "      - Duration: $([math]::Round($stat.Duration, 2))s" "White"
    Write-ColorOutput "      - Test results: $($stat.SuccessfulTests)/$($stat.TotalTests) success ($($stat.SuccessRate)%)" "$(if ($stat.SuccessRate -ge 80) { 'Green' } elseif ($stat.SuccessRate -ge 60) { 'Yellow' } else { 'Red' })"
}

if ($StatusCodeStats) {
    Write-ColorOutput "`nStatus Code Statistics:" "Blue"
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
        Write-ColorOutput "   - $($stat.Name): $($stat.Count) tests" $color
    }
}

if ($MethodStats) {
    Write-ColorOutput "`nHTTP Method Statistics:" "Blue"
    foreach ($stat in $MethodStats) {
        Write-ColorOutput "   - $($stat.Name): $($stat.Count) tests" "White"
    }
}

# Failed router details
if ($FailedRouters -gt 0) {
    Write-ColorOutput "`nFailed Router Details:" "Red"
    $FailedRouterDetails = $RouterExecutionResults | Where-Object { $_.Status -ne "Success" }
    foreach ($router in $FailedRouterDetails) {
        Write-ColorOutput "   - $($router.RouterName): $($router.ErrorMessage)" "Red"
    }
}

# Failed test details (top 10)
if ($FailedTests -gt 0) {
    Write-ColorOutput "`nFailed Test Details (Top 10):" "Red"
    $FailedTestDetails = $MasterTestResults | Where-Object { $_.Status -eq "Failed" } | Select-Object -First 10
    foreach ($test in $FailedTestDetails) {
        Write-ColorOutput "   - [$($test.RouterName)] $($test.TestName): $($test.Details)" "Red"
    }
    
    if ($FailedTests -gt 10) {
        Write-ColorOutput "   ... and $($FailedTests - 10) more failed tests." "Yellow"
    }
}

# Save integrated results
if ($GenerateReport) {
    Write-ColorOutput "`nSaving integrated results..." "Yellow"
    
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $masterResultFile = "$OutputDir\master_test_results_$timestamp.json"
    
    # Save JSON results
    $MasterTestSummary = @{
        TestInfo = @{
            TestName = "SkyBoot Mail SaaS - Master Test Runner"
            StartTime = $MasterTestStartTime
            EndTime = $MasterTestEndTime
            Duration = $TotalMasterTestTime.TotalSeconds
            BaseUrl = $BaseUrl
            TotalRouters = $TotalRouters
            CompletedRouters = $CompletedRouters
            FailedRouters = $FailedRouters
        }
        OverallStatistics = @{
            TotalTests = $TotalTests
            SuccessfulTests = $SuccessfulTests
            FailedTests = $FailedTests
            OverallSuccessRate = $OverallSuccessRate
        }
        RouterStatistics = $RouterStats
        StatusCodeStats = if ($StatusCodeStats) { $StatusCodeStats | ForEach-Object { @{ StatusCode = $_.Name; Count = $_.Count } } } else { @() }
        MethodStats = if ($MethodStats) { $MethodStats | ForEach-Object { @{ Method = $_.Name; Count = $_.Count } } } else { @() }
        RouterExecutionResults = $RouterExecutionResults
        AllTestResults = $MasterTestResults
    }
    
    try {
        $MasterTestSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $masterResultFile -Encoding UTF8
        Write-ColorOutput "Integrated results JSON saved: $masterResultFile" "Green"
    } catch {
        Write-ColorOutput "Failed to save integrated results JSON: $($_.Exception.Message)" "Red"
    }
}

# Final result summary
Write-ColorOutput "`n" + "=" * 100 "Blue"
Write-ColorOutput "Test execution completed!" "Cyan"
Write-ColorOutput "Final result: $SuccessfulTests/$TotalTests success ($OverallSuccessRate%)" "$(if ($OverallSuccessRate -ge 80) { 'Green' } elseif ($OverallSuccessRate -ge 60) { 'Yellow' } else { 'Red' })"
Write-ColorOutput "Total duration: $([math]::Round($TotalMasterTestTime.TotalSeconds, 2)) seconds" "Blue"
Write-ColorOutput "Result files: $OutputDir" "Blue"
Write-ColorOutput "=" * 100 "Blue"

# Set exit code
if ($FailedRouters -gt 0 -or $FailedTests -gt 0) {
    exit 1
} else {
    exit 0
}