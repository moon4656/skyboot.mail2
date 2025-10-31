# ========================================
# 휴지통 내역 생성 테스트 스크립트
# SkyBoot Mail SaaS - 다중 조직 메일서버
# ========================================

param(
  [string]$BaseUrl = "http://localhost:8000/api/v1",
  [string]$AdminUserId = "user01",
  [string]$AdminPassword = "test",
  [string]$RecipientEmail = "user01@example.com"
)

function Invoke-Api {
  param(
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = @{},
    [object]$Body = $null,
    [string]$ContentType = "application/json"
  )
  try {
    if ($Body -ne $null) {
      if ($ContentType -eq "application/json") {
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers -ContentType $ContentType -Body ($Body | ConvertTo-Json -Depth 6)
      } else {
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers -ContentType $ContentType -Body $Body
      }
    } else {
      return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers
    }
  } catch {
    Write-Host "❌ 요청 실패: $Url" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errorText = $reader.ReadToEnd()
      Write-Host $errorText -ForegroundColor Yellow
    }
    throw
  }
}

Write-Host "\n🔐 로그인 진행" -ForegroundColor Yellow
$loginUrl = "$BaseUrl/auth/login"
$loginBody = @{ user_id = $AdminUserId; password = $AdminPassword }
$loginRes = Invoke-Api -Method POST -Url $loginUrl -Body $loginBody
$accessToken = $loginRes.access_token
Write-Host "✅ 로그인 성공, 토큰 발급" -ForegroundColor Green

$headers = @{ Authorization = "Bearer $accessToken" }

Write-Host "\n📤 테스트 메일 발송(폼 데이터)" -ForegroundColor Yellow
$sendUrl = "$BaseUrl/mail/send"
$mailForm = @{
  to_emails = $RecipientEmail;
  subject = "휴지통 테스트 메일 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')";
  content = "휴지통 기능 검증용 테스트 메일입니다.";
  priority = "normal"
}
$sendRes = Invoke-Api -Method POST -Url $sendUrl -Headers $headers -Body $mailForm -ContentType "application/x-www-form-urlencoded"
$mailUuid = $sendRes.data.mail_id
if (-not $mailUuid) { $mailUuid = $sendRes.mail_uuid }
Write-Host "✅ 메일 발송 성공, mail_uuid: $mailUuid" -ForegroundColor Green

# 보낸 메일함에서 최신 메일 UUID 재확인 (호환성 대비)
try {
  Write-Host "\n📤 보낸 메일함에서 최신 메일 확인" -ForegroundColor Yellow
  $sentUrl = "$BaseUrl/mail/sent?page=1&limit=1"
  $sentRes = Invoke-Api -Method GET -Url $sentUrl -Headers $headers
  $latest = $null
  if ($sentRes.data -and $sentRes.data.mails -and $sentRes.data.mails.Count -gt 0) {
    $latest = $sentRes.data.mails[0]
  } elseif ($sentRes.mails -and $sentRes.mails.Count -gt 0) {
    $latest = $sentRes.mails[0]
  }
  if ($latest) {
    if (-not $mailUuid) { $mailUuid = $latest.mail_uuid }
    if (-not $mailUuid) { $mailUuid = $latest.mail_id }
    Write-Host "✅ 최신 보낸 메일 UUID 확인: $mailUuid" -ForegroundColor Green
  } else {
    Write-Host "⚠️ 보낸 메일 목록에서 최신 항목을 찾지 못했습니다." -ForegroundColor Yellow
  }
} catch {}

Write-Host "\n🗑️ 메일을 휴지통으로 이동(소프트 삭제)" -ForegroundColor Yellow
$deleteUrl = "$BaseUrl/mail/${mailUuid}?force=false"
Write-Host ("삭제 요청 URL: {0}" -f $deleteUrl) -ForegroundColor Yellow
$deleteRes = Invoke-Api -Method DELETE -Url $deleteUrl -Headers $headers
Write-Host "✅ 메일 소프트 삭제 완료" -ForegroundColor Green

# 반영 지연 대비 잠시 대기
Start-Sleep -Seconds 2

Write-Host "\n🔎 휴지통 내역 조회" -ForegroundColor Yellow
$trashUrl = "$BaseUrl/mail/trash?page=1&limit=10"
$trashRes = Invoke-Api -Method GET -Url $trashUrl -Headers $headers
# 응답 호환성: data.mails 또는 mails 형태 모두 지원
$trashCount = 0
if ($trashRes -and $trashRes.data -and $trashRes.data.mails) {
  $trashCount = $trashRes.data.mails.Count
} elseif ($trashRes -and $trashRes.mails) {
  $trashCount = $trashRes.mails.Count
} elseif ($trashRes -and $trashRes.data -is [array]) {
  $trashCount = $trashRes.data.Count
}
Write-Host ("✅ 휴지통 항목 수: {0}" -f $trashCount) -ForegroundColor Green

$outputPath = Join-Path (Split-Path -Parent $PSCommandPath) "trash_history_result_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$trashRes | ConvertTo-Json -Depth 6 | Out-File -FilePath $outputPath -Encoding UTF8
Write-Host "\n💾 결과 저장: $outputPath" -ForegroundColor Cyan