# ===================================================================
# SkyBoot Mail SaaS - Address Book Router Test Scenarios
# ===================================================================
# File: addressbook_router_tests.ps1
# Description: Test all endpoints of address book management features
# Date: 2024-01-01
# ===================================================================

# Test Configuration
$BaseUrl = "http://localhost:8000/api/v1"
$TestResults = @()
$Headers = @{ "Content-Type" = "application/json" }

# Test User Information
$AdminUser = @{
    user_id = "admin01"
    password = "test"
}

$RegularUser = @{
    user_id = "user01"
    password = "test"
}

# Test Result Recording Function
function Add-TestResult {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Endpoint,
        [int]$StatusCode,
        [string]$Response,
        [bool]$Success,
        [string]$ErrorMessage = ""
    )
    
    $script:TestResults += [PSCustomObject]@{
        TestName = $TestName
        Method = $Method
        Endpoint = $Endpoint
        StatusCode = $StatusCode
        Response = $Response
        Success = $Success
        ErrorMessage = $ErrorMessage
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# API Request Function
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers,
        [string]$Body = $null
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        return @{
            Success = $true
            StatusCode = 200
            Content = $response | ConvertTo-Json -Depth 10
        }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        return @{
            Success = $false
            StatusCode = $statusCode
            Content = $_.Exception.Message
        }
    }
}

Write-Host "🚀 Starting Address Book Router Tests..." -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Yellow

# ===================================================================
# 1. Authentication Tests
# ===================================================================

Write-Host "`n📋 1. Authentication Tests" -ForegroundColor Cyan

# 1.1 Admin Login
$loginData = @{
    user_id = $AdminUser.user_id
    password = $AdminUser.password
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/auth/login" -Headers $Headers -Body $loginData

if ($response.Success) {
    $loginResponse = $response.Content | ConvertFrom-Json
    $AdminToken = $loginResponse.access_token
    $AdminHeaders = @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $AdminToken"
    }
    Add-TestResult -TestName "Admin Login" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Response $response.Content -Success $true
    Write-Host "✅ Admin login successful" -ForegroundColor Green
} else {
    Add-TestResult -TestName "Admin Login" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Response $response.Content -Success $false -ErrorMessage "Admin login failed"
    Write-Host "❌ Admin login failed" -ForegroundColor Red
    exit 1
}

# 1.2 Regular User Login
$loginData2 = @{
    user_id = $RegularUser.user_id
    password = $RegularUser.password
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/auth/login" -Headers $Headers -Body $loginData2

if ($response.Success) {
    $loginResponse = $response.Content | ConvertFrom-Json
    $UserToken = $loginResponse.access_token
    $UserHeaders = @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $UserToken"
    }
    Add-TestResult -TestName "Regular User Login" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Response $response.Content -Success $true
    Write-Host "✅ Regular user login successful" -ForegroundColor Green
} else {
    Add-TestResult -TestName "Regular User Login" -Method "POST" -Endpoint "/auth/login" -StatusCode $response.StatusCode -Response $response.Content -Success $false -ErrorMessage "Regular user login failed"
    Write-Host "❌ Regular user login failed" -ForegroundColor Red
    exit 1
}

# ===================================================================
# 2. Contact Management Tests
# ===================================================================

Write-Host "`n📋 2. Contact Management Tests" -ForegroundColor Cyan

# 2.1 Get Contact List (Empty)
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts" -Headers $AdminHeaders

Add-TestResult -TestName "Get Contact List (Empty)" -Method "GET" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.2 Create Contact (Admin)
$contactData = @{
    name = "John Doe"
    email = "john@example.com"
    phone = "010-1234-5678"
    mobile = "010-9876-5432"
    company = "Example Corp"
    title = "Manager"
    address = "Seoul, Korea"
    memo = "Admin contact"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts" -Headers $AdminHeaders -Body $contactData

if ($response.Success -and $response.StatusCode -eq 200) {
    $contactResponse = $response.Content | ConvertFrom-Json
    $ContactUuid = $contactResponse.contact_uuid
    Add-TestResult -TestName "Create Contact (Admin)" -Method "POST" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success $true
    Write-Host "✅ Contact created successfully: $ContactUuid" -ForegroundColor Green
} else {
    Add-TestResult -TestName "Create Contact (Admin)" -Method "POST" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success $false -ErrorMessage "Contact creation failed"
    Write-Host "❌ Contact creation failed" -ForegroundColor Red
}

# 2.3 Create Contact (Regular User)
$contactData2 = @{
    name = "Jane Smith"
    email = "jane.smith@example.com"  # 고유한 이메일 사용
    phone = "010-2345-6789"
    company = "Tech Corp"
    title = "Developer"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts" -Headers $UserHeaders -Body $contactData2

Add-TestResult -TestName "Create Contact (Regular User)" -Method "POST" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.4 Create Duplicate Contact
$duplicateContactData = @{
    name = "John Doe Duplicate"
    email = "john@example.com"  # Same email as first contact
    phone = "010-1111-2222"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts" -Headers $AdminHeaders -Body $duplicateContactData

Add-TestResult -TestName "Create Duplicate Contact" -Method "POST" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 400)

# 2.5 Create Contact with Invalid Email
$invalidEmailContactData = @{
    name = "Invalid Email User"
    email = "invalid-email"
    phone = "010-3333-4444"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts" -Headers $AdminHeaders -Body $invalidEmailContactData

Add-TestResult -TestName "Create Contact with Invalid Email" -Method "POST" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 422)

# 2.6 Get Contact List (With Data)
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts" -Headers $AdminHeaders

Add-TestResult -TestName "Get Contact List (With Data)" -Method "GET" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.7 Get Contact List with Pagination
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts?page=1&size=1" -Headers $AdminHeaders

Add-TestResult -TestName "Get Contact List with Pagination" -Method "GET" -Endpoint "/addressbook/contacts?page=1&size=1" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.8 Search Contacts by Name
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts?q=John" -Headers $AdminHeaders

Add-TestResult -TestName "Search Contacts by Name" -Method "GET" -Endpoint "/addressbook/contacts?q=John" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.9 Search Contacts by Email
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts?q=john@example.com" -Headers $AdminHeaders

Add-TestResult -TestName "Search Contacts by Email" -Method "GET" -Endpoint "/addressbook/contacts?q=john@example.com" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 2.10 Get Contact by UUID
if ($ContactUuid) {
    $response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts/$ContactUuid" -Headers $AdminHeaders

    Add-TestResult -TestName "Get Contact by UUID" -Method "GET" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 2.11 Get Non-existent Contact
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts/non-existent-uuid" -Headers $AdminHeaders

Add-TestResult -TestName "Get Non-existent Contact" -Method "GET" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)

# 2.12 Update Contact
if ($ContactUuid) {
    $updateData = @{
        name = "John Doe Updated"
        email = "john.updated@example.com"
        phone = "010-1234-9999"
        company = "Updated Corp"
        title = "Senior Manager"
    } | ConvertTo-Json

    $response = Invoke-ApiRequest -Method "PUT" -Url "$BaseUrl/addressbook/contacts/$ContactUuid" -Headers $AdminHeaders -Body $updateData

    Add-TestResult -TestName "Update Contact" -Method "PUT" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 2.13 Update Non-existent Contact
$updateData = @{
    name = "Non-existent Contact"
    email = "nonexistent@example.com"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "PUT" -Url "$BaseUrl/addressbook/contacts/non-existent-uuid" -Headers $AdminHeaders -Body $updateData

Add-TestResult -TestName "Update Non-existent Contact" -Method "PUT" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)

# ===================================================================
# 3. Group Management Tests
# ===================================================================

Write-Host "`n📋 3. Group Management Tests" -ForegroundColor Cyan

# 3.1 Get Group List (Empty)
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/groups" -Headers $AdminHeaders

Add-TestResult -TestName "Get Group List (Empty)" -Method "GET" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 3.2 Create Group
$groupData = @{
    name = "VIP Customers"
    description = "Important customers group"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/groups" -Headers $AdminHeaders -Body $groupData

if ($response.Success -and $response.StatusCode -eq 200) {
    $groupResponse = $response.Content | ConvertFrom-Json
    $GroupId = $groupResponse.id
    Add-TestResult -TestName "Create Group" -Method "POST" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success $true
    Write-Host "✅ Group created successfully: $GroupId" -ForegroundColor Green
} else {
    Add-TestResult -TestName "Create Group" -Method "POST" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success $false -ErrorMessage "Group creation failed"
    Write-Host "❌ Group creation failed" -ForegroundColor Red
}

# 3.3 Create Second Group
$groupData2 = @{
    name = "Business Partners"  # 고유한 그룹명 사용
    description = "Business partners group"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/groups" -Headers $AdminHeaders -Body $groupData2

if ($response.Success -and $response.StatusCode -eq 200) {
    $groupResponse2 = $response.Content | ConvertFrom-Json
    $GroupId2 = $groupResponse2.id
    Add-TestResult -TestName "Create Second Group" -Method "POST" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success $true
} else {
    Add-TestResult -TestName "Create Second Group" -Method "POST" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success $false -ErrorMessage "Second group creation failed"
}

# 3.4 Create Duplicate Group
$duplicateGroupData = @{
    name = "VIP Customers"  # Same name as first group
    description = "Duplicate group"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/groups" -Headers $AdminHeaders -Body $duplicateGroupData

Add-TestResult -TestName "Create Duplicate Group" -Method "POST" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 409)

# 3.5 Get Group List (With Data)
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/groups" -Headers $AdminHeaders

Add-TestResult -TestName "Get Group List (With Data)" -Method "GET" -Endpoint "/addressbook/groups" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 3.6 Update Group
if ($GroupId) {
    $updateGroupData = @{
        name = "VIP Customers Updated"
        description = "Updated VIP customers group"
    } | ConvertTo-Json

    $response = Invoke-ApiRequest -Method "PUT" -Url "$BaseUrl/addressbook/groups/$GroupId" -Headers $AdminHeaders -Body $updateGroupData

    Add-TestResult -TestName "Update Group" -Method "PUT" -Endpoint "/addressbook/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 3.7 Update Non-existent Group
$updateGroupData = @{
    name = "Non-existent Group"
    description = "This group does not exist"
} | ConvertTo-Json

$response = Invoke-ApiRequest -Method "PUT" -Url "$BaseUrl/addressbook/groups/99999" -Headers $AdminHeaders -Body $updateGroupData

Add-TestResult -TestName "Update Non-existent Group" -Method "PUT" -Endpoint "/addressbook/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)

# ===================================================================
# 4. Contact-Group Association Tests
# ===================================================================

Write-Host "`n📋 4. Contact-Group Association Tests" -ForegroundColor Cyan

# 4.1 Add Contact to Group
if ($ContactUuid -and $GroupId) {
    $response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts/$ContactUuid/groups/$GroupId" -Headers $AdminHeaders

    Add-TestResult -TestName "Add Contact to Group" -Method "POST" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 4.2 Add Contact to Second Group
if ($ContactUuid -and $GroupId2) {
    $response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts/$ContactUuid/groups/$GroupId2" -Headers $AdminHeaders

    Add-TestResult -TestName "Add Contact to Second Group" -Method "POST" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 4.3 Add Non-existent Contact to Group
if ($GroupId) {
    $response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts/non-existent-uuid/groups/$GroupId" -Headers $AdminHeaders

    Add-TestResult -TestName "Add Non-existent Contact to Group" -Method "POST" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)
}

# 4.4 Add Contact to Non-existent Group
if ($ContactUuid) {
    $response = Invoke-ApiRequest -Method "POST" -Url "$BaseUrl/addressbook/contacts/$ContactUuid/groups/99999" -Headers $AdminHeaders

    Add-TestResult -TestName "Add Contact to Non-existent Group" -Method "POST" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)
}

# 4.5 Get Contact with Groups
if ($ContactUuid) {
    $response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts/$ContactUuid" -Headers $AdminHeaders

    Add-TestResult -TestName "Get Contact with Groups" -Method "GET" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 4.6 Remove Contact from Group
if ($ContactUuid -and $GroupId) {
    $response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/contacts/$ContactUuid/groups/$GroupId" -Headers $AdminHeaders

    Add-TestResult -TestName "Remove Contact from Group" -Method "DELETE" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 4.7 Remove Contact from Group Again (Should fail)
if ($ContactUuid -and $GroupId) {
    $response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/contacts/$ContactUuid/groups/$GroupId" -Headers $AdminHeaders

    Add-TestResult -TestName "Remove Contact from Group Again" -Method "DELETE" -Endpoint "/addressbook/contacts/{uuid}/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)
}

# ===================================================================
# 5. Export and Permission Tests
# ===================================================================

Write-Host "`n📋 5. Export and Permission Tests" -ForegroundColor Cyan

# 5.1 Export Contacts to CSV
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts/export" -Headers $AdminHeaders

Add-TestResult -TestName "Export Contacts to CSV" -Method "GET" -Endpoint "/addressbook/contacts/export" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)

# 5.2 Access without Authentication
$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts" -Headers $Headers

Add-TestResult -TestName "Access without Authentication" -Method "GET" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 401 -or $response.StatusCode -eq 403)

# 5.3 Access with Invalid Token
$invalidHeaders = @{ 
    "Content-Type" = "application/json"
    "Authorization" = "Bearer invalid-token"
}

$response = Invoke-ApiRequest -Method "GET" -Url "$BaseUrl/addressbook/contacts" -Headers $invalidHeaders

Add-TestResult -TestName "Access with Invalid Token" -Method "GET" -Endpoint "/addressbook/contacts" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 401 -or $response.StatusCode -eq 403)

# ===================================================================
# 6. Cleanup Tests
# ===================================================================

Write-Host "`n📋 6. Cleanup Tests" -ForegroundColor Cyan

# 6.1 Delete Contact
if ($ContactUuid) {
    $response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/contacts/$ContactUuid" -Headers $AdminHeaders

    Add-TestResult -TestName "Delete Contact" -Method "DELETE" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 6.2 Delete Non-existent Contact
$response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/contacts/non-existent-uuid" -Headers $AdminHeaders

Add-TestResult -TestName "Delete Non-existent Contact" -Method "DELETE" -Endpoint "/addressbook/contacts/{uuid}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)

# 6.3 Delete Group
if ($GroupId) {
    $response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/groups/$GroupId" -Headers $AdminHeaders

    Add-TestResult -TestName "Delete Group" -Method "DELETE" -Endpoint "/addressbook/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 200)
}

# 6.4 Delete Non-existent Group
$response = Invoke-ApiRequest -Method "DELETE" -Url "$BaseUrl/addressbook/groups/99999" -Headers $AdminHeaders

Add-TestResult -TestName "Delete Non-existent Group" -Method "DELETE" -Endpoint "/addressbook/groups/{id}" -StatusCode $response.StatusCode -Response $response.Content -Success ($response.StatusCode -eq 404)

# ===================================================================
# Test Results Summary
# ===================================================================

Write-Host "`n📊 Test Results Summary" -ForegroundColor Magenta

$TotalTests = $TestResults.Count
$PassedTests = ($TestResults | Where-Object { $_.Success -eq $true }).Count
$FailedTests = $TotalTests - $PassedTests
$SuccessRate = [math]::Round(($PassedTests / $TotalTests) * 100, 2)

Write-Host "Total Tests: $TotalTests" -ForegroundColor White
Write-Host "Passed: $PassedTests" -ForegroundColor Green
Write-Host "Failed: $FailedTests" -ForegroundColor Red
Write-Host "Success Rate: $SuccessRate%" -ForegroundColor Yellow

# Save detailed results to JSON file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "addressbook_router_test_results_$timestamp.json"
$TestResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $resultFile -Encoding UTF8

Write-Host "`n📄 Detailed results saved to: $resultFile" -ForegroundColor Blue

# Display failed tests
if ($FailedTests -gt 0) {
    Write-Host "`n❌ Failed Tests:" -ForegroundColor Red
    $TestResults | Where-Object { $_.Success -eq $false } | ForEach-Object {
        Write-Host "  - $($_.TestName): $($_.ErrorMessage)" -ForegroundColor Red
    }
}

Write-Host "`n🏁 Address Book Router Tests Completed!" -ForegroundColor Green
